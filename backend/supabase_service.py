from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: Optional[Client] = None
    
    def connect(self):
        """Connect to Supabase"""
        try:
            self.client = create_client(self.url, self.key)
            logger.info("Supabase connected successfully")
        except Exception as e:
            logger.error(f"Supabase connection error: {e}")
            raise
    
    async def get_or_create_user(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Get or create WhatsApp user in Supabase"""
        if not self.client:
            raise Exception("Supabase not connected")
        
        try:
            # Try to get user
            response = self.client.table('whatsapp_users').select('*').eq('phone_number', phone_number).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new user
            new_user = {
                'phone_number': phone_number,
                'name': name
            }
            response = self.client.table('whatsapp_users').insert(new_user).execute()
            return response.data[0] if response.data else new_user
        except Exception as e:
            logger.error(f"Supabase get_or_create_user error: {e}")
            # Fallback to local storage
            return {'phone_number': phone_number, 'name': name}
    
    async def save_message(self, conversation_id: str, sender: str, content: str):
        """Save message to Supabase"""
        if not self.client:
            return
        
        try:
            message = {
                'conversation_id': conversation_id,
                'sender': sender,
                'content': content
            }
            self.client.table('messages').insert(message).execute()
        except Exception as e:
            logger.error(f"Supabase save_message error: {e}")