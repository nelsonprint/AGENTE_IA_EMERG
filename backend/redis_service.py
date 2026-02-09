import redis.asyncio as redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, url: str, password: Optional[str] = None):
        self.url = url
        self.password = password
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                self.url,
                password=self.password,
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def set_conversation_active(self, phone_number: str, ttl: int = 720):
        """Set conversation as active with TTL"""
        if not self.client:
            return
        try:
            await self.client.setex(f"atendimento.{phone_number}", ttl, "true")
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def get_conversation_active(self, phone_number: str) -> bool:
        """Check if conversation is active"""
        if not self.client:
            return False
        try:
            result = await self.client.get(f"atendimento.{phone_number}")
            return result == "true"
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return False
    
    async def delete_conversation(self, phone_number: str):
        """Delete conversation from cache"""
        if not self.client:
            return
        try:
            await self.client.delete(f"atendimento.{phone_number}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")