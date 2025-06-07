import httpx
import logging
import json
from typing import List, Dict, Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class AnyListProvider:
    """Integration with the AnyList service to fetch shopping lists."""
    
    BASE_URL = "https://www.anylist.com/api"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with AnyList and store the auth token."""
        if not settings.anylist_email or not settings.anylist_password:
            logger.error("AnyList credentials not configured")
            return False
            
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/auth/login",
                json={
                    "email": settings.anylist_email,
                    "password": settings.anylist_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("auth_token")
                if self.auth_token:
                    logger.info("Successfully authenticated with AnyList")
                    return True
                else:
                    logger.error("Authentication successful but no token received")
                    return False
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.exception(f"Error authenticating with AnyList: {str(e)}")
            return False
    
    async def get_lists(self) -> List[Dict[str, Any]]:
        """Get all available lists from AnyList."""
        if not self.auth_token:
            success = await self.authenticate()
            if not success:
                return []
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{self.BASE_URL}/lists", headers=headers)
            
            if response.status_code == 200:
                return response.json().get("lists", [])
            elif response.status_code == 401:
                # Token expired, try re-authenticating
                logger.info("Auth token expired, re-authenticating")
                success = await self.authenticate()
                if success:
                    return await self.get_lists()
                return []
            else:
                logger.error(f"Failed to fetch lists: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.exception(f"Error fetching lists from AnyList: {str(e)}")
            return []
    
    async def get_list_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get all items from a specific list."""
        if not self.auth_token:
            success = await self.authenticate()
            if not success:
                return []
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(
                f"{self.BASE_URL}/lists/{list_id}/items", 
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("items", [])
            elif response.status_code == 401:
                # Token expired, try re-authenticating
                logger.info("Auth token expired, re-authenticating")
                success = await self.authenticate()
                if success:
                    return await self.get_list_items(list_id)
                return []
            else:
                logger.error(f"Failed to fetch list items: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.exception(f"Error fetching list items from AnyList: {str(e)}")
            return []
    
    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()


# Factory function for getting the right list provider
def get_list_provider():
    return AnyListProvider()