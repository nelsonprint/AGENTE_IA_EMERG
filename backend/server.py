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
    Conversation, Message, WebhookPayload, SendMessageRequest
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from bot_service import BotService
from redis_service import RedisService
from supabase_service import SupabaseService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services (will be initialized when settings are configured)
redis_service: Optional[RedisService] = None
supabase_service: Optional[SupabaseService] = None

# ============ AUTH ROUTES ============
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: AdminUserCreate):
    Register new admin user
    # Check if user already exists
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
    
    # Create new user
    hashed_pwd = hash_password(user_data.password)
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_pwd,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admin_users.insert_one(user_doc)
    
    # Create access token
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
    Login admin user
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

# ============ SETTINGS ROUTES ============
@api_router.get("/settings", response_model=Settings)
async def get_settings(current_user: dict = Depends(get_current_user)):
    Get current settings
    settings = await db.settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Return default settings
        return Settings()
    
    return Settings(**settings)

@api_router.put("/settings", response_model=Settings)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    Update settings
    global redis_service, supabase_service
    
    # Get existing settings or create new
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
    
    # Initialize services if credentials are provided
    if settings.get("redis_url"):
        try:
            redis_service = RedisService(
                settings["redis_url"],
                settings.get("redis_password")
            )
            await redis_service.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
    
    if settings.get("supabase_url") and settings.get("supabase_key"):
        try:
            supabase_service = SupabaseService(
                settings["supabase_url"],
                settings["supabase_key"]
            )
            supabase_service.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
    
    return Settings(**settings)

# ============ PROMPTS ROUTES ============
@api_router.get("/prompts", response_model=List[BotPrompt])
async def get_prompts(current_user: dict = Depends(get_current_user)):
    Get all bot prompts
    prompts = await db.bot_prompts.find({}, {"_id": 0}).to_list(1000)
    return [BotPrompt(**p) for p in prompts]

@api_router.post("/prompts", response_model=BotPrompt)
async def create_prompt(
    prompt_data: BotPromptCreate,
    current_user: dict = Depends(get_current_user)
):
    Create new bot prompt
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
    Update bot prompt
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
    Delete bot prompt
    result = await db.bot_prompts.delete_one({"id": prompt_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return {"message": "Prompt deleted successfully"}

@api_router.get("/prompts/active", response_model=BotPrompt)
async def get_active_prompt():
    Get active bot prompt (for webhook use)
    prompt = await db.bot_prompts.find_one({"is_active": True}, {"_id": 0})
    
    if not prompt:
        # Return default prompt
        return BotPrompt(
            name="Default",
            system_prompt="Você é um assistente virtual útil e prestativo. Responda de forma clara e educada.",
            is_active=True
        )
    
    return BotPrompt(**prompt)

# ============ CONVERSATIONS ROUTES ============
@api_router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    Get all conversations with optional status filter
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
    Get specific conversation with messages
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return Conversation(**conversation)

@api_router.post("/conversations/{conversation_id}/transfer")
async def transfer_to_human(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    Transfer conversation to human agent
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
    Close conversation
    global redis_service
    
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "closed"}}
    )
    
    # Remove from Redis cache
    if redis_service:
        await redis_service.delete_conversation(conversation["phone_number"])
    
    return {"message": "Conversation closed"}

# ============ WEBHOOK ROUTE ============
@api_router.post("/webhook/{webhook_id}")
async def webhook_handler(webhook_id: str, payload: dict):
    Handle incoming WhatsApp messages from Evolution API
    try:
        logger.info(f"Received webhook: {payload}")
        
        # Extract data from Evolution API webhook
        data = payload.get("data", {})
        message_data = data.get("message", {})
        key = data.get("key", {})
        
        # Check if message is from user (not from bot)
        if key.get("fromMe"):
            return {"status": "ignored", "reason": "Message from bot"}
        
        phone_number = key.get("remoteJid", "").split("@")[0]
        user_name = payload.get("pushName", "Unknown")
        message_content = message_data.get("conversation", "")
        
        if not message_content or not phone_number:
            return {"status": "ignored", "reason": "No message content or phone"}
        
        # Get settings
        settings = await db.settings.find_one({}, {"_id": 0})
        if not settings or not settings.get("openai_api_key"):
            logger.error("OpenAI API key not configured")
            return {"status": "error", "message": "API key not configured"}
        
        # Get active prompt
        active_prompt = await db.bot_prompts.find_one({"is_active": True}, {"_id": 0})
        system_prompt = active_prompt["system_prompt"] if active_prompt else "Você é um assistente virtual útil."
        
        # Check if user wants to talk to human
        bot_service = BotService(settings["openai_api_key"], system_prompt)
        should_transfer = bot_service.should_transfer_to_human(message_content)
        
        # Get or create conversation
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
        
        # Add user message
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
        
        # If transferred to human, don't respond with AI
        if conversation.get("transferred_to_human") or should_transfer:
            if should_transfer and not conversation.get("transferred_to_human"):
                await db.conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {"transferred_to_human": True, "status": "transferred"}}
                )
                
                # Send transfer message
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
            
            return {"status": "transferred_to_human"}
        
        # Generate AI response
        session_id = f"session_{phone_number}"
        ai_response = await bot_service.generate_response(session_id, message_content)
        
        # Add bot message
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
        
        # TODO: Send response back to WhatsApp via Evolution API
        # This would require making HTTP request to Evolution API
        
        return {
            "status": "success",
            "response": ai_response
        }
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ DASHBOARD STATS ============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    Get dashboard statistics
    # Count active conversations
    active_conversations = await db.conversations.count_documents({"status": "active"})
    
    # Count transferred conversations
    transferred = await db.conversations.count_documents({"status": "transferred"})
    
    # Count messages today
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.isoformat()
    
    # Get all conversations and count messages
    all_conversations = await db.conversations.find({}, {"_id": 0, "messages": 1}).to_list(10000)
    messages_today = 0
    for conv in all_conversations:
        for msg in conv.get("messages", []):
            msg_time = datetime.fromisoformat(msg["timestamp"]) if isinstance(msg["timestamp"], str) else msg["timestamp"]
            if msg_time >= today:
                messages_today += 1
    
    # Count total users
    total_users = await db.conversations.count_documents({})
    
    return {
        "active_conversations": active_conversations,
        "transferred_conversations": transferred,
        "messages_today": messages_today,
        "total_users": total_users
    }

# ============ SEND MESSAGE (MANUAL) ============
@api_router.post("/send-message")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    Send manual message to WhatsApp user (for human agent)
    # Get conversation
    conversation = await db.conversations.find_one(
        {"phone_number": request.phone_number},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add message to conversation
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
    
    # TODO: Send to WhatsApp via Evolution API
    
    return {"status": "success", "message": "Message sent"}

# Include the router in the main app
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
