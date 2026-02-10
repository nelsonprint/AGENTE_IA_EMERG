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
    
    def _replace_name_placeholders(self, text: str, customer_name: str) -> str:
        """Replace name placeholders in the prompt with customer's actual name"""
        if not customer_name or customer_name.lower() in ["unknown", "desconhecido", ""]:
            customer_name = "Cliente"
        
        # Replace common placeholders
        placeholders = [
            "[Nome do Proprietário]",
            "[Nome do Cliente]",
            "[customer_name]",
            "[nome]",
            "{nome}",
            "{customer_name}",
            "{{nome}}",
            "{{customer_name}}"
        ]
        
        result = text
        for placeholder in placeholders:
            if placeholder in result:
                logger.info(f"Replacing placeholder '{placeholder}' with '{customer_name}'")
                result = result.replace(placeholder, customer_name)
        
        return result
    
    async def generate_response(self, session_id: str, user_message: str, conversation_history: List[Dict] = None, customer_name: str = None) -> str:
        """Generate AI response using OpenAI with conversation history"""
        try:
            # Build context from history
            context = ""
            if conversation_history and len(conversation_history) > 0:
                context = "\n\nHistórico da conversa:\n"
                for msg in conversation_history[-10:]:  # Last 10 messages
                    role = "Cliente" if msg["sender"] == "user" else "Você"
                    context += f"{role}: {msg['content']}\n"
            
            # Create prompt with history and replace name placeholders
            full_prompt = self._replace_name_placeholders(self.system_message, customer_name)
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
    
    def should_transfer_to_human(self, message: str, custom_keywords: List[str] = None) -> bool:
        """Keyword detection for human transfer"""
        # Default keywords if none provided
        default_keywords = [
            "falar com atendente",
            "atendente humano",
            "falar com alguém",
            "preciso de ajuda humana",
            "transferir",
            "humano",
            "falar com o dono",
            "falar com dono",
            "falar com gerente",
            "falar com o gerente",
            "falar com comercial",
            "falar com o comercial",
            "falar com responsável",
            "falar com o responsável",
            "falar com supervisor",
            "falar com o supervisor",
            "falar com vendedor",
            "falar com o vendedor",
            "quero falar com",
            "passar para",
            "me transfere",
            "atendimento humano",
            "pessoa real",
            "falar com pessoa",
            "falar com uma pessoa"
        ]
        
        # Use custom keywords if provided, otherwise use defaults
        keywords = custom_keywords if custom_keywords and len(custom_keywords) > 0 else default_keywords
        
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in keywords)