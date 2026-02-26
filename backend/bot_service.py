from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

class BotService:
    def __init__(self, api_key: str, system_message: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.system_message = system_message
        self.model = model
        self.conversations = {}  # In-memory cache of conversations
    
    def detect_menu_options(self, message: str) -> dict:
        """
        Detect if message contains a numbered menu and extract options.
        Returns: {"is_menu": bool, "options": {number: description}, "best_option": number or None}
        """
        # Patterns for menu options: "1 - Text", "*1* Text", "1) Text", "1. Text"
        patterns = [
            r'[\*]?(\d+)[\*]?\s*[-–—\.)\]]\s*([^\n\d]+)',  # *1* - Text or 1 - Text or 1) Text
            r'(\d+)\s*[-–—]\s*([^\n]+)',  # 1 - Text
            r'(\d+)\)\s*([^\n]+)',  # 1) Text
            r'(\d+)\.\s*([^\n]+)',  # 1. Text
        ]
        
        options = {}
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                num = match[0].strip()
                desc = match[1].strip()
                if num.isdigit() and desc:
                    options[int(num)] = desc.lower()
        
        if len(options) < 2:
            return {"is_menu": False, "options": {}, "best_option": None}
        
        # Priority keywords for selection
        priority_keywords = [
            ["administrativo", "administração", "adm"],
            ["financeiro", "financeira", "finanças"],
            ["gerência", "gerente", "gestão", "gestor"],
            ["obras", "construção", "engenharia"],
            ["comercial", "vendas", "venda"]
        ]
        
        best_option = None
        for keywords in priority_keywords:
            for num, desc in options.items():
                for keyword in keywords:
                    if keyword in desc:
                        best_option = num
                        break
                if best_option:
                    break
            if best_option:
                break
        
        return {"is_menu": True, "options": options, "best_option": best_option}
    
    def detect_name_request(self, message: str) -> bool:
        """Detect if message is asking for a name"""
        name_patterns = [
            r'qual\s+(é\s+)?o?\s*seu\s+nome',
            r'com\s+quem\s+(eu\s+)?falo',
            r'quem\s+está\s+falando',
            r'me\s+informe\s+seu\s+nome',
            r'informe\s+seu\s+nome',
            r'seu\s+nome\s*[,:]?\s*por\s+favor',
            r'poderia\s+me\s+dizer\s+seu\s+nome',
            r'como\s+você\s+se\s+chama',
            r'digite\s+seu\s+nome',
            r'escreva\s+seu\s+nome',
        ]
        
        message_lower = message.lower()
        for pattern in name_patterns:
            if re.search(pattern, message_lower):
                return True
        return False
    
    def detect_bot_response(self, message: str) -> bool:
        """Detect if message is from an automated bot (to ignore)"""
        bot_indicators = [
            "assistente virtual",
            "pré-atendimento",
            "agradece seu contato",
            "em breve um consultor",
            "em breve entraremos em contato",
            "atendimento automático",
            "mensagem automática",
            "obrigado pelo contato",
            "aguarde um momento",
            "sua mensagem foi recebida"
        ]
        
        message_lower = message.lower()
        for indicator in bot_indicators:
            if indicator in message_lower:
                return True
        return False
    
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
            # Replace name placeholders in system prompt
            full_prompt = self._replace_name_placeholders(self.system_message, customer_name)
            
            # Build context from history - format it clearly for the AI
            context = ""
            if conversation_history and len(conversation_history) > 0:
                context = "\n\n========================================\nHISTÓRICO DA CONVERSA ATUAL (use para manter contexto e NÃO repetir perguntas já feitas):\n========================================\n"
                for msg in conversation_history[-15:]:  # Last 15 messages for better context
                    role = "CLIENTE" if msg["sender"] == "user" else "VOCÊ (Eduardo)"
                    context += f"{role}: {msg['content']}\n"
                context += "========================================\n"
                context += "\nIMPORTANTE: Baseado no histórico acima, continue a conversa de forma natural. NÃO repita perguntas que você já fez. Se o cliente já respondeu algo, siga para o próximo passo do fluxo.\n"
            
            # Add context to prompt
            if context:
                full_prompt += context
            
            # Add current message indicator
            full_prompt += f"\nMENSAGEM ATUAL DO CLIENTE: {user_message}\n"
            full_prompt += "\nSua resposta (lembre-se: uma pergunta por vez, aguarde resposta, não repita o que já perguntou):"
            
            # Use emergentintegrations
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
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