import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EvolutionAPIService:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, instance: str, phone_number: str, message: str) -> bool:
        """
        Send text message via Evolution API
        
        Args:
            instance: Evolution instance name
            phone_number: Phone number with country code (e.g., 5511999999999)
            message: Text message to send
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Format phone number for WhatsApp (add @s.whatsapp.net if not present)
            if "@" not in phone_number:
                phone_number = f"{phone_number}@s.whatsapp.net"
            
            url = f"{self.api_url}/message/sendText/{instance}"
            
            payload = {
                "number": phone_number,
                "text": message
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"Message sent successfully to {phone_number}")
                    return True
                else:
                    logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending message via Evolution API: {e}")
            return False
    
    async def get_instance_status(self, instance: str) -> dict:
        """Check instance status"""
        try:
            url = f"{self.api_url}/instance/connectionState/{instance}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    return response.json()
                return {"state": "unknown"}
                
        except Exception as e:
            logger.error(f"Error checking instance status: {e}")
            return {"state": "error", "message": str(e)}
