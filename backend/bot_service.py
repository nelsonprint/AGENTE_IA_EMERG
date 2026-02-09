from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BotService:
    def __init__(self, api_key: str, system_message: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.system_message = system_message
        self.model = model
    
    async def generate_response(self, session_id: str, user_message: str) -> str:
        """Generate AI response using OpenAI via emergentintegrations"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("openai", self.model)
            
            message = UserMessage(text=user_message)
            response = await chat.send_message(message)
            
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