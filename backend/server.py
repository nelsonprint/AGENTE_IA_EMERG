from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from models import (
    AdminUserCreate, AdminUserLogin, TokenResponse,
    Settings, SettingsUpdate,
    BotPrompt, BotPromptCreate, BotPromptUpdate,
    Conversation, Message, WebhookPayload, SendMessageRequest,
    EvolutionInstance, EvolutionInstanceCreate
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from bot_service import BotService
from redis_service import RedisService
from supabase_service import SupabaseService
from evolution_service import EvolutionAPIService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

redis_service: Optional[RedisService] = None
supabase_service: Optional[SupabaseService] = None
evolution_service: Optional[EvolutionAPIService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize Redis on startup"""
    global redis_service
    
    # Try to connect to local Redis
    redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')
    try:
        redis_service = RedisService(redis_url, None)
        await redis_service.connect()
        if redis_service.client:
            logger.info("✓ Redis initialized successfully for conversation memory")
        else:
            logger.warning("Redis not available - conversation memory disabled")
            redis_service = None
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        redis_service = None

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: AdminUserCreate):
    existing_user = await db.admin_users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    }, {"_id": 0})
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    hashed_pwd = hash_password(user_data.password)
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_pwd,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admin_users.insert_one(user_doc)
    
    token = create_access_token({"sub": user_data.username, "email": user_data.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user_data.username,
            "email": user_data.email
        }
    }

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: AdminUserLogin):
    user = await db.admin_users.find_one({"username": credentials.username}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    token = create_access_token({"sub": user["username"], "email": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"]
        }
    }

@api_router.get("/settings", response_model=Settings)
async def get_settings(current_user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({}, {"_id": 0})
    
    if not settings:
        return Settings()
    
    return Settings(**settings)

@api_router.put("/settings", response_model=Settings)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    global redis_service, supabase_service, evolution_service
    
    existing = await db.settings.find_one({}, {"_id": 0})
    
    update_data = settings_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if existing:
        await db.settings.update_one({}, {"$set": update_data})
        settings = await db.settings.find_one({}, {"_id": 0})
    else:
        settings_doc = Settings(**update_data).model_dump()
        settings_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.settings.insert_one(settings_doc)
        settings = settings_doc
    
    if settings.get("redis_url"):
        try:
            redis_service = RedisService(
                settings["redis_url"],
                settings.get("redis_password")
            )
            await redis_service.connect()
            if redis_service.client:
                logger.info("✓ Redis cache enabled")
            else:
                logger.info("✗ Redis disabled - system will work without cache")
                redis_service = None
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            redis_service = None
    else:
        logger.info("Redis not configured - system will work without cache")
    
    if settings.get("supabase_url") and settings.get("supabase_key"):
        try:
            supabase_service = SupabaseService(
                settings["supabase_url"],
                settings["supabase_key"]
            )
            supabase_service.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
    
    if settings.get("evolution_api_url") and settings.get("evolution_api_key"):
        try:
            evolution_service = EvolutionAPIService(
                settings["evolution_api_url"],
                settings["evolution_api_key"]
            )
            logger.info("Evolution API service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Evolution API: {e}")
    
    return Settings(**settings)

@api_router.get("/prompts", response_model=List[BotPrompt])
async def get_prompts(current_user: dict = Depends(get_current_user)):
    prompts = await db.bot_prompts.find({}, {"_id": 0}).to_list(1000)
    return [BotPrompt(**p) for p in prompts]

@api_router.post("/prompts", response_model=BotPrompt)
async def create_prompt(
    prompt_data: BotPromptCreate,
    current_user: dict = Depends(get_current_user)
):
    prompt = BotPrompt(**prompt_data.model_dump())
    prompt_doc = prompt.model_dump()
    prompt_doc["created_at"] = prompt_doc["created_at"].isoformat()
    prompt_doc["updated_at"] = prompt_doc["updated_at"].isoformat()
    
    await db.bot_prompts.insert_one(prompt_doc)
    return prompt

@api_router.put("/prompts/{prompt_id}", response_model=BotPrompt)
async def update_prompt(
    prompt_id: str,
    prompt_update: BotPromptUpdate,
    current_user: dict = Depends(get_current_user)
):
    existing = await db.bot_prompts.find_one({"id": prompt_id}, {"_id": 0})
    
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    update_data = prompt_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.bot_prompts.update_one({"id": prompt_id}, {"$set": update_data})
    
    updated = await db.bot_prompts.find_one({"id": prompt_id}, {"_id": 0})
    return BotPrompt(**updated)

@api_router.delete("/prompts/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    current_user: dict = Depends(get_current_user)
):
    result = await db.bot_prompts.delete_one({"id": prompt_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return {"message": "Prompt deleted successfully"}

@api_router.get("/prompts/active", response_model=BotPrompt)
async def get_active_prompt():
    prompt = await db.bot_prompts.find_one({"is_active": True}, {"_id": 0})
    
    if not prompt:
        return BotPrompt(
            name="Default",
            system_prompt="Você é um assistente virtual útil e prestativo. Responda de forma clara e educada.",
            is_active=True
        )
    
    return BotPrompt(**prompt)

@api_router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    
    conversations = await db.conversations.find(query, {"_id": 0}).sort("last_message_at", -1).to_list(1000)
    return [Conversation(**c) for c in conversations]

@api_router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return Conversation(**conversation)

@api_router.post("/conversations/{conversation_id}/transfer")
async def transfer_to_human(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "transferred_to_human": True,
            "status": "transferred"
        }}
    )
    
    return {"message": "Conversation transferred to human agent"}

@api_router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    global redis_service
    
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "closed"}}
    )
    
    if redis_service:
        await redis_service.delete_conversation(conversation["phone_number"])
    
    return {"message": "Conversation closed"}

@api_router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    global redis_service
    
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete conversation from database
    await db.conversations.delete_one({"id": conversation_id})
    
    # Clear from Redis if available
    if redis_service:
        await redis_service.delete_conversation(conversation["phone_number"])
    
    logger.info(f"Conversation {conversation_id} deleted by user")
    return {"message": "Conversation deleted successfully"}

@api_router.post("/webhook/{webhook_id}")
async def webhook_handler(webhook_id: str, payload: dict):
    try:
        logger.info(f"Received webhook: {payload}")
        
        data = payload.get("data", {})
        message_data = data.get("message", {})
        key = data.get("key", {})
        
        if key.get("fromMe"):
            return {"status": "ignored", "reason": "Message from bot"}
        
        phone_number = key.get("remoteJid", "").split("@")[0]
        user_name = payload.get("pushName", "Unknown")
        message_content = message_data.get("conversation", "")
        
        if not message_content or not phone_number:
            return {"status": "ignored", "reason": "No message content or phone"}
        
        settings = await db.settings.find_one({}, {"_id": 0})
        if not settings or not settings.get("openai_api_key"):
            logger.error("OpenAI API key not configured")
            return {"status": "error", "message": "API key not configured"}
        
        active_prompt = await db.bot_prompts.find_one({"is_active": True}, {"_id": 0})
        system_prompt = active_prompt["system_prompt"] if active_prompt else "Você é um assistente virtual útil."
        
        bot_service = BotService(settings["openai_api_key"], system_prompt)
        should_transfer = bot_service.should_transfer_to_human(message_content)
        
        conversation = await db.conversations.find_one({"phone_number": phone_number, "status": {"$ne": "closed"}}, {"_id": 0})
        
        if not conversation:
            conversation = Conversation(
                user_id=phone_number,
                phone_number=phone_number,
                user_name=user_name,
                messages=[]
            ).model_dump()
            conversation["started_at"] = conversation["started_at"].isoformat()
            conversation["last_message_at"] = conversation["last_message_at"].isoformat()
            await db.conversations.insert_one(conversation)
        
        user_message = Message(
            conversation_id=conversation["id"],
            sender="user",
            content=message_content
        ).model_dump()
        user_message["timestamp"] = user_message["timestamp"].isoformat()
        
        await db.conversations.update_one(
            {"id": conversation["id"]},
            {
                "$push": {"messages": user_message},
                "$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        if conversation.get("transferred_to_human") or should_transfer:
            if should_transfer and not conversation.get("transferred_to_human"):
                await db.conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {"transferred_to_human": True, "status": "transferred"}}
                )
                
                transfer_msg = Message(
                    conversation_id=conversation["id"],
                    sender="bot",
                    content="Um momento, vou transferir você para um atendente humano."
                ).model_dump()
                transfer_msg["timestamp"] = transfer_msg["timestamp"].isoformat()
                
                await db.conversations.update_one(
                    {"id": conversation["id"]},
                    {"$push": {"messages": transfer_msg}}
                )
                
                # Send notification to owner's WhatsApp
                notification_phone = settings.get("notification_whatsapp")
                if notification_phone and default_instance:
                    # Clean notification phone number
                    clean_notification_phone = notification_phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                    
                    notification_message = f"""🔔 NOVO ATENDIMENTO SOLICITADO

Cliente: {user_name}
https://wa.me/+{phone_number}
Última mensagem: "{message_content}"
"""
                    
                    instance_service = EvolutionAPIService(
                        default_instance["api_url"],
                        default_instance["api_key"]
                    )
                    instance_name = default_instance["instance_name"]
                    
                    logger.info(f"Sending transfer notification to {clean_notification_phone}")
                    await instance_service.send_text_message(instance_name, clean_notification_phone, notification_message)
                
                # Send transfer message to client
                if default_instance:
                    instance_service = EvolutionAPIService(
                        default_instance["api_url"],
                        default_instance["api_key"]
                    )
                    instance_name = default_instance["instance_name"]
                    await instance_service.send_text_message(instance_name, phone_number, "Um momento, vou transferir você para um atendente humano.")
            
            return {"status": "transferred_to_human"}
        
        # Get conversation history for context
        conversation_with_history = await db.conversations.find_one(
            {"id": conversation["id"]},
            {"_id": 0}
        )
        
        session_id = f"session_{phone_number}"
        conversation_history = conversation_with_history.get("messages", [])
        
        # Generate response with full conversation history and customer name
        ai_response = await bot_service.generate_response(
            session_id, 
            message_content,
            conversation_history,
            customer_name=user_name
        )
        
        bot_message = Message(
            conversation_id=conversation["id"],
            sender="bot",
            content=ai_response
        ).model_dump()
        bot_message["timestamp"] = bot_message["timestamp"].isoformat()
        
        await db.conversations.update_one(
            {"id": conversation["id"]},
            {
                "$push": {"messages": bot_message},
                "$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Send response back via Evolution API
        default_instance = await db.evolution_instances.find_one({"is_default": True}, {"_id": 0})
        
        if default_instance:
            instance_service = EvolutionAPIService(
                default_instance["api_url"],
                default_instance["api_key"]
            )
            instance_name = default_instance["instance_name"]
            
            logger.info(f"Attempting to send message to {phone_number} via instance {instance_name}")
            logger.info(f"Message content: {ai_response[:100]}...")
            
            success = await instance_service.send_text_message(instance_name, phone_number, ai_response)
            
            if success:
                logger.info(f"✓ Message sent successfully to {phone_number}")
            else:
                logger.error(f"✗ Failed to send message to {phone_number}")
        else:
            logger.warning("No default Evolution instance configured - message not sent to WhatsApp")
        
        return {
            "status": "success",
            "response": ai_response,
            "sent_to_whatsapp": default_instance is not None
        }
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    active_conversations = await db.conversations.count_documents({"status": "active"})
    transferred = await db.conversations.count_documents({"status": "transferred"})
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    all_conversations = await db.conversations.find({}, {"_id": 0, "messages": 1}).to_list(10000)
    messages_today = 0
    for conv in all_conversations:
        for msg in conv.get("messages", []):
            try:
                if isinstance(msg["timestamp"], str):
                    msg_time = datetime.fromisoformat(msg["timestamp"])
                    if msg_time.tzinfo is None:
                        msg_time = msg_time.replace(tzinfo=timezone.utc)
                else:
                    msg_time = msg["timestamp"]
                    if msg_time.tzinfo is None:
                        msg_time = msg_time.replace(tzinfo=timezone.utc)
                
                if msg_time >= today:
                    messages_today += 1
            except:
                pass
    
    total_users = await db.conversations.count_documents({})
    
    return {
        "active_conversations": active_conversations,
        "transferred_conversations": transferred,
        "messages_today": messages_today,
        "total_users": total_users
    }

@api_router.post("/send-message")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    conversation = await db.conversations.find_one(
        {"phone_number": request.phone_number},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    bot_message = Message(
        conversation_id=conversation["id"],
        sender="agent",
        content=request.message
    ).model_dump()
    bot_message["timestamp"] = bot_message["timestamp"].isoformat()
    
    await db.conversations.update_one(
        {"id": conversation["id"]},
        {
            "$push": {"messages": bot_message},
            "$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Send via Evolution API
    default_instance = await db.evolution_instances.find_one({"is_default": True}, {"_id": 0})
    
    if default_instance:
        instance_service = EvolutionAPIService(
            default_instance["api_url"],
            default_instance["api_key"]
        )
        instance_name = default_instance["instance_name"]
        phone = request.phone_number.replace("@s.whatsapp.net", "")
        
        logger.info(f"Sending message to {phone} via instance {instance_name}")
        success = await instance_service.send_text_message(instance_name, phone, request.message)
        
        if not success:
            logger.warning(f"Failed to send message via Evolution API to {phone}")
            return {"status": "saved", "sent": False, "message": "Message saved but failed to send via WhatsApp"}
        
        return {"status": "success", "sent": True, "message": "Message sent"}
    else:
        logger.warning("No default Evolution instance configured")
        return {"status": "saved", "sent": False, "message": "Evolution API not configured"}

@api_router.get("/evolution/test")
async def test_evolution_connection(current_user: dict = Depends(get_current_user)):
    """Test Evolution API connection"""
    if not evolution_service:
        return {"status": "error", "message": "Evolution API not configured"}
    
    settings = await db.settings.find_one({}, {"_id": 0})
    if not settings or not settings.get("evolution_api_url"):
        return {"status": "error", "message": "Evolution API credentials not set"}
    
    instance = settings.get("evolution_instance", "default")
    status = await evolution_service.get_instance_status(instance)
    
    return {
        "status": "success",
        "instance": instance,
        "connection": status,
        "api_url": settings.get("evolution_api_url")
    }

# ============ EVOLUTION INSTANCES MANAGEMENT ============
@api_router.get("/evolution-instances", response_model=List[EvolutionInstance])
async def get_evolution_instances(current_user: dict = Depends(get_current_user)):
    """Get all Evolution API instances"""
    instances = await db.evolution_instances.find({}, {"_id": 0}).to_list(1000)
    return [EvolutionInstance(**inst) for inst in instances]

@api_router.post("/evolution-instances", response_model=EvolutionInstance)
async def create_evolution_instance(
    instance_data: EvolutionInstanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new Evolution API instance"""
    # If this is the first instance, make it default
    existing_count = await db.evolution_instances.count_documents({})
    is_default = existing_count == 0
    
    instance = EvolutionInstance(
        **instance_data.model_dump(),
        is_default=is_default
    )
    instance_doc = instance.model_dump()
    instance_doc["created_at"] = instance_doc["created_at"].isoformat()
    
    await db.evolution_instances.insert_one(instance_doc)
    return instance

@api_router.delete("/evolution-instances/{instance_id}")
async def delete_evolution_instance(
    instance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete Evolution API instance"""
    result = await db.evolution_instances.delete_one({"id": instance_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    return {"message": "Instance deleted successfully"}

@api_router.post("/evolution-instances/{instance_id}/set-default")
async def set_default_instance(
    instance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Set instance as default"""
    # Unset all defaults
    await db.evolution_instances.update_many({}, {"$set": {"is_default": False}})
    
    # Set this one as default
    result = await db.evolution_instances.update_one(
        {"id": instance_id},
        {"$set": {"is_default": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    return {"message": "Default instance set successfully"}

@api_router.post("/evolution-instances/{instance_id}/test")
async def test_instance_connection(
    instance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Test specific Evolution API instance connection"""
    instance = await db.evolution_instances.find_one({"id": instance_id}, {"_id": 0})
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Create temporary service to test
    temp_service = EvolutionAPIService(instance["api_url"], instance["api_key"])
    status = await temp_service.get_instance_status(instance["instance_name"])
    
    return {
        "status": "success",
        "instance": instance["instance_name"],
        "connection": status
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    if redis_service:
        await redis_service.disconnect()
