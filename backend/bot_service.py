from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BotService:
    def __init__(self, api_key: str, system_message: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.system_message = system_message
        self.model = model
        self.conversations = {}  # In-memory cache of conversations
    
    def get_conversation_history(self, session_id: str, messages: List[Dict]) -> str:
        """Build conversation history from MongoDB messages"""
        history = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role = "user" if msg["sender"] == "user" else "assistant"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)
    
    async def generate_response(self, session_id: str, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Generate AI response using OpenAI with conversation history"""
        try:
            # Build context from history
            context = ""
            if conversation_history and len(conversation_history) > 0:
                context = "\n\nHistórico da conversa:\n"
                for msg in conversation_history[-10:]:  # Last 10 messages
                    role = "Cliente" if msg["sender"] == "user" else "Você"
                    context += f"{role}: {msg['content']}\n"
            
            # Create prompt with history
            full_prompt = self.system_message
            if context:
                full_prompt += context
            
            # Use emergentintegrations without session persistence (manual history)
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,  # Still use for potential future persistence
                system_message=full_prompt
            ).with_model("openai", self.model)
            
            message = UserMessage(text=user_message)
            response = await chat.send_message(message)
            
            logger.info(f"Generated response for session {session_id}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
    
    def should_transfer_to_human(self, message: str) -> bool:
        """Simple keyword detection for human transfer"""
        transfer_keywords = [
            "falar com atendente",
            "atendente humano",
            "falar com alguém",
            "preciso de ajuda humana",
            "transferir",
            "humano"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in transfer_keywords)