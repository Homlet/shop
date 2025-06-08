import httpx
import logging
from typing import List, Dict, Any, Optional
import uuid

from ..config import settings

logger = logging.getLogger(__name__)


class HomeAssistantListProvider:
    """Integration with the Home Assistant Todo List API."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        # When running as an addon, the default URL works without modification
        self.base_url = settings.ha_url
        # Set up headers with authentication token
        self.headers = {
            "Authorization": f"Bearer {settings.ha_token}",
            "Content-Type": "application/json"
        }
        # The entity ID of the todo list to use
        self.todo_list_entity_id = settings.todo_list_entity_id
        logger.info(f"Initialized with todo list entity ID: {self.todo_list_entity_id}")
    
    async def get_list_items(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get items from the configured todo list.
        
        Args:
            limit: Optional maximum number of items to return
            
        Returns:
            Dict containing items and total count
        """
        list_id = self.todo_list_entity_id
        logger.info(f"Getting items for configured list: {list_id}")
        
        # First, detect the integration type
        integration_type = await self._detect_integration_type(list_id)
        logger.info(f"Detected integration type: {integration_type}")
        
        # Get all items using the appropriate method
        all_items = await self._get_items_by_integration(list_id, integration_type)
        total_count = len(all_items)
        
        # Apply limit if specified
        items_to_return = all_items
        if limit and limit > 0 and limit < len(all_items):
            items_to_return = all_items[:limit]
        
        return {
            "items": items_to_return,
            "total_count": total_count,
            "truncated": limit is not None and total_count > limit
        }
    
    async def _detect_integration_type(self, list_id: str) -> str:
        """Detect the integration type for a todo list."""
        try:
            # Get the entity state to check supported_features
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                state_data = response.json()
                attrs = state_data.get("attributes", {})
                supported_features = attrs.get("supported_features", 0)
                
                # Detect if this is likely a Bring! integration (supported_features=71)
                if supported_features == 71:
                    logger.info(f"Detected entity {list_id} as Bring! integration based on supported_features=71")
                    return "bring"
                
                # Check for integration attribute
                if "integration" in attrs:
                    integration = attrs.get("integration")
                    logger.info(f"Found integration attribute: {integration}")
                    return integration
                
                # Check if this is a legacy shopping list
                if list_id == "shopping_list.shopping_list":
                    return "legacy_shopping_list"
                
                # Default to unknown
                return "unknown"
                
            return "unknown"
            
        except Exception as e:
            logger.exception(f"Error detecting integration type: {str(e)}")
            return "unknown"
    
    async def _get_items_by_integration(self, list_id: str, integration_type: str) -> List[Dict[str, Any]]:
        """Get items using the appropriate method for the integration type."""
        # Specialized handling for different integration types
        if integration_type == "local_todo":
            logger.info("Using local_todo handler")
            return await self._get_local_todo_items(list_id)
        elif integration_type == "google_tasks":
            logger.info("Using google_tasks handler")
            return await self._get_google_tasks_items(list_id)
        elif integration_type == "todoist":
            logger.info("Using todoist handler")
            return await self._get_todoist_items(list_id)
        elif integration_type == "caldav":
            logger.info("Using caldav handler")
            return await self._get_caldav_items(list_id)
        elif integration_type == "alexa_todo":
            logger.info("Using alexa_todo handler")
            return await self._get_alexa_todo_items(list_id)
        elif integration_type == "bring":
            logger.info("Using bring handler")
            return await self._get_bring_items(list_id)
        elif integration_type == "legacy_shopping_list":
            logger.info("Using legacy_shopping_list handler")
            return await self._get_legacy_shopping_list_items()
        else:
            # Use the generic method for unknown integration types
            logger.info("Using generic handler for unknown integration type")
            return await self._get_generic_items(list_id)
    
    async def _get_generic_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Generic method to get items from a todo list."""
        try:
            # First, try to get the entity state to see the items attribute
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                state_data = response.json()
                attributes = state_data.get("attributes", {})
                
                # Log the full attributes for debugging
                logger.info(f"Entity attributes for {list_id}: {attributes}")
                
                # Try multiple possible attribute names where items might be stored
                potential_item_attributes = [
                    attributes.get("items", []),
                    attributes.get("item", []),
                    attributes.get("todo_items", []),
                    attributes.get("entity_items", [])
                ]
                
                # Try to get items from any of these attributes
                for items_attribute in potential_item_attributes:
                    if items_attribute:
                        logger.info(f"Found {len(items_attribute)} items in state data for {list_id}")
                        
                        # Filter for incomplete items and format them
                        active_items = []
                        
                        # Process each item, with careful handling for different formats
                        for i, item in enumerate(items_attribute):
                            # Skip completed items
                            if item.get("complete", False) or item.get("status", "") == "completed":
                                continue
                                
                            # Try to extract item ID and name with fallbacks
                            item_id = (item.get("uid", "") or 
                                     item.get("id", "") or 
                                     item.get("item_id", "") or 
                                     str(i))
                                     
                            item_name = (item.get("summary", "") or 
                                       item.get("name", "") or 
                                       item.get("description", "") or 
                                       item.get("title", "") or
                                       str(item))
                            
                            # If the item is a simple string, use it as the name
                            if isinstance(item, str):
                                item_id = f"item_{i}"
                                item_name = item
                            
                            active_items.append({
                                "id": item_id,
                                "name": item_name,
                                "status": item.get("status", "needs_action")
                            })
                        
                        logger.info(f"Filtered to {len(active_items)} active items")
                        return active_items
                
                # Try to handle the case where the 'state' field holds items count or information
                if attributes.get("friendly_name", ""):
                    state_value = state_data.get("state")
                    logger.info(f"Entity state value: {state_value}")
            
            # If the above doesn't work, try the todo API endpoint
            logger.info(f"Trying to fetch items through todo API for {list_id}")
            response = await self.client.get(
                f"{self.base_url}/api/todo/items", 
                headers=self.headers,
                params={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                items = response.json()
                logger.info(f"Found {len(items)} items through todo API")
                
                # Filter for incomplete items and format them
                active_items = [
                    {
                        "id": item.get("uid", ""),
                        "name": item.get("summary", ""),
                        "status": item.get("status", "needs_action")
                    } 
                    for item in items 
                    if item.get("status") != "completed"
                ]
                
                logger.info(f"Filtered to {len(active_items)} active items")
                return active_items
            else:
                logger.error(f"Failed to fetch todo list items: {response.status_code} - {response.text}")
                
            # Last resort: try the todo.get_items service
            logger.info(f"Trying to fetch items through todo.get_items service for {list_id}")
            response = await self.client.post(
                f"{self.base_url}/api/services/todo/get_items?return_response", 
                headers=self.headers,
                json={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                service_result = response.json()
                items = service_result.get("items", [])
                logger.info(f"Found {len(items)} items through todo.get_items service")
                
                # Filter for incomplete items and format them
                active_items = [
                    {
                        "id": item.get("uid", ""),
                        "name": item.get("summary", ""),
                        "status": item.get("status", "needs_action")
                    } 
                    for item in items 
                    if item.get("status") != "completed"
                ]
                
                logger.info(f"Filtered to {len(active_items)} active items")
                return active_items
            else:
                logger.error(f"Failed to fetch items through service: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.exception(f"Error fetching todo list items: {str(e)}")
            return []
    
    async def _get_local_todo_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from a local_todo integration list."""
        logger.info(f"Using specialized handling for local_todo integration with list {list_id}")
        try:
            # For local_todo, items are stored in the state
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get state for {list_id}: {response.status_code}")
                return []
            
            state_data = response.json()
            items = state_data.get("attributes", {}).get("items", [])
            logger.info(f"Found {len(items)} items in local_todo state")
            
            # Format and filter the items
            active_items = [
                {"id": item.get("id", f"item_{i}"), "name": item.get("name", "")} 
                for i, item in enumerate(items) 
                if not item.get("complete", False) and not item.get("completed", False)
            ]
            
            logger.info(f"Filtered to {len(active_items)} active items")
            return active_items
            
        except Exception as e:
            logger.exception(f"Error fetching local_todo items: {str(e)}")
            return []
    
    async def _get_google_tasks_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from a Google Tasks integration list."""
        logger.info(f"Using specialized handling for Google Tasks integration with list {list_id}")
        try:
            # Try the specific Google Tasks service if available
            response = await self.client.post(
                f"{self.base_url}/api/services/todo/get_items?return_response", 
                headers=self.headers,
                json={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                logger.info(f"Found {len(items)} items via service call")
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("id", ""), "name": item.get("summary", "")} 
                    for item in items 
                    if item.get("status", "") != "completed"
                ]
                
                logger.info(f"Filtered to {len(active_items)} active items")
                return active_items
                
            # Fallback to state data
            state_response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if state_response.status_code == 200:
                state_data = state_response.json()
                items = state_data.get("attributes", {}).get("items", [])
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("id", ""), "name": item.get("summary", "") or item.get("title", "")} 
                    for item in items 
                    if item.get("status", "") != "completed"
                ]
                
                return active_items
                
            return []
            
        except Exception as e:
            logger.exception(f"Error fetching Google Tasks items: {str(e)}")
            return []
    
    async def _get_todoist_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from a Todoist integration list."""
        logger.info(f"Using specialized handling for Todoist integration with list {list_id}")
        try:
            # For Todoist, try to get items through the service
            response = await self.client.post(
                f"{self.base_url}/api/services/todo/get_items?return_response", 
                headers=self.headers,
                json={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("id", ""), "name": item.get("content", "") or item.get("name", "")} 
                    for item in items 
                    if not item.get("checked", False) and not item.get("completed", False)
                ]
                
                return active_items
            
            # Fallback to state
            state_response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if state_response.status_code == 200:
                state_data = state_response.json()
                items = state_data.get("attributes", {}).get("items", [])
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("id", ""), "name": item.get("content", "") or item.get("name", "")} 
                    for item in items 
                    if not item.get("checked", False) and not item.get("completed", False)
                ]
                
                return active_items
                
            return []
            
        except Exception as e:
            logger.exception(f"Error fetching Todoist items: {str(e)}")
            return []
    
    async def _get_caldav_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from a CalDAV integration list."""
        logger.info(f"Using specialized handling for CalDAV integration with list {list_id}")
        try:
            # For CalDAV, items are usually in the state
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                state_data = response.json()
                items = state_data.get("attributes", {}).get("todos", [])
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("uid", ""), "name": item.get("summary", "") or item.get("description", "")} 
                    for item in items 
                    if item.get("status", "") != "COMPLETED"
                ]
                
                return active_items
                
            return []
            
        except Exception as e:
            logger.exception(f"Error fetching CalDAV items: {str(e)}")
            return []
    
    async def _get_alexa_todo_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from an Alexa Todo integration list."""
        logger.info(f"Using specialized handling for Alexa Todo integration with list {list_id}")
        try:
            # First try to call a service specific to alexa
            response = await self.client.post(
                f"{self.base_url}/api/services/todo/get_items?return_response", 
                headers=self.headers,
                json={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                logger.info(f"Found {len(items)} items via service call")
                
                # Format and filter the items
                active_items = [
                    {"id": item.get("itemId", "") or item.get("id", ""), 
                     "name": item.get("text", "") or item.get("name", "")} 
                    for item in items 
                    if item.get("complete", False) != True
                ]
                
                return active_items
            
            # Fall back to checking entity state
            state_response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if state_response.status_code == 200:
                state_data = state_response.json()
                logger.info(f"Entity state data: {state_data}")
                
                # Try different attribute names where items might be stored
                for attr_name in ["items", "item_names", "todos", "to_dos", "tasks"]:
                    items = state_data.get("attributes", {}).get(attr_name, [])
                    if items:
                        logger.info(f"Found {len(items)} items in attribute '{attr_name}'")
                        
                        # Format items, handling both object and string formats
                        active_items = []
                        for i, item in enumerate(items):
                            if isinstance(item, dict):
                                if item.get("complete", False) or item.get("completed", False):
                                    continue
                                    
                                item_id = item.get("itemId", "") or item.get("id", str(i))
                                item_name = item.get("text", "") or item.get("name", "")
                            else:
                                # Item is a simple string
                                item_id = f"item_{i}"
                                item_name = str(item)
                                
                            active_items.append({"id": item_id, "name": item_name})
                            
                        return active_items
            
            return []
            
        except Exception as e:
            logger.exception(f"Error fetching Alexa Todo items: {str(e)}")
            return []
    
    async def _get_legacy_shopping_list_items(self) -> List[Dict[str, Any]]:
        """Get items from the legacy shopping list."""
        logger.info("Using legacy shopping list API")
        try:
            response = await self.client.get(
                f"{self.base_url}/api/shopping_list", 
                headers=self.headers
            )
            
            if response.status_code != 200:
                return []
            
            all_items = response.json()
            active_items = [
                {"id": item.get("id", ""), "name": item.get("name", "")} 
                for item in all_items 
                if not item.get("complete", False)
            ]
            return active_items
        except Exception as e:
            logger.exception(f"Error fetching legacy shopping list items: {str(e)}")
            return []
    
    async def _get_bring_items(self, list_id: str) -> List[Dict[str, Any]]:
        """Get items from a Bring! integration list."""
        logger.info(f"Using specialized handling for Bring! integration with list {list_id}")
        try:
            # For Bring!, we need to use the todo.get_items service call
            # The API endpoint doesn't work reliably with Bring!
            response = await self.client.post(
                f"{self.base_url}/api/services/todo/get_items?return_response", 
                headers=self.headers,
                json={"entity_id": list_id}
            )
            
            if response.status_code == 200:
                service_result = response.json()
                logger.info(f"Bring! service response: {service_result}")
                
                # Try to parse the nested structure from Bring! service response
                # Format: {'changed_states': [], 'service_response': {'todo.home': {'items': [...]}}}
                items = []
                
                # Check if we have the nested service_response structure
                if "service_response" in service_result:
                    service_response = service_result.get("service_response", {})
                    
                    # The entity_id is a key in the service_response
                    if list_id in service_response:
                        entity_data = service_response.get(list_id, {})
                        items = entity_data.get("items", [])
                        logger.info(f"Found {len(items)} items in nested Bring! service response")
                else:
                    # Try the direct items array if not nested
                    items = service_result.get("items", [])
                    logger.info(f"Found {len(items)} items directly in Bring! service response")
                
                # Bring! has a specific format for items - they're typically in the "summary" field
                # and don't use the standard "status" field for completion
                active_items = []
                for i, item in enumerate(items):
                    # Skip completed items - Bring! may use different fields
                    if (item.get("status", "") == "completed" or 
                        item.get("complete", False) or 
                        item.get("checked", False) or
                        item.get("purchase", False)):  # Bring! specific field
                        continue
                    
                    # Try to extract item ID and name with Bring!-specific fallbacks
                    item_id = (item.get("uid", "") or 
                             item.get("id", "") or 
                             item.get("item_id", "") or 
                             str(uuid.uuid4()))  # Bring! might not provide stable IDs
                    
                    # Bring! typically uses "summary" or "name" for the item name
                    item_name = (item.get("summary", "") or 
                               item.get("name", "") or 
                               item.get("text", "") or
                               str(item))
                    
                    # Add quantity information if available (Bring! specific)
                    if item.get("quantity"):
                        item_name = f"{item_name} ({item.get('quantity')})"
                    
                    # If the item is a simple string, use it as the name
                    if isinstance(item, str):
                        item_id = f"item_{i}"
                        item_name = item
                    
                    active_items.append({
                        "id": item_id,
                        "name": item_name
                    })
                
                logger.info(f"Filtered to {len(active_items)} active Bring! items")
                return active_items
            
            # If service call fails, try the entity state as a fallback
            logger.info(f"Service call failed, trying to fetch Bring! items from state for {list_id}")
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                state_data = response.json()
                attributes = state_data.get("attributes", {})
                
                # Try different attribute names where Bring! might store items
                for attr_name in ["items", "item_names", "purchases", "shopping_list", "products"]:
                    items = attributes.get(attr_name, [])
                    if items:
                        logger.info(f"Found {len(items)} items in Bring! attribute '{attr_name}'")
                        
                        # Process each item with careful handling for Bring!'s format
                        active_items = []
                        for i, item in enumerate(items):
                            # Skip completed items
                            if isinstance(item, dict):
                                if (item.get("status", "") == "completed" or 
                                    item.get("complete", False) or 
                                    item.get("purchase", False)):
                                    continue
                                
                                item_id = item.get("uid", "") or item.get("id", "") or str(i)
                                item_name = item.get("summary", "") or item.get("name", "") or str(item)
                                
                                # Add quantity if available
                                if item.get("quantity"):
                                    item_name = f"{item_name} ({item.get('quantity')})"
                            else:
                                # If the item is a simple string, use it as the name
                                item_id = f"item_{i}"
                                item_name = str(item)
                            
                            active_items.append({
                                "id": item_id,
                                "name": item_name
                            })
                        
                        return active_items
                
                # Check for Bring!-specific purchase_items attribute
                if "purchase_items" in attributes:
                    purchase_items = attributes.get("purchase_items", {})
                    
                    # Parse the purchase_items structure (may be nested)
                    active_items = []
                    for item_key, item_data in purchase_items.items():
                        if isinstance(item_data, dict):
                            # Skip completed/purchased items
                            if item_data.get("purchased", False):
                                continue
                            
                            item_id = item_key
                            item_name = item_data.get("name", "") or item_key
                            
                            # Add quantity if available
                            if item_data.get("quantity"):
                                item_name = f"{item_name} ({item_data.get('quantity')})"
                            
                            active_items.append({
                                "id": item_id,
                                "name": item_name
                            })
                    
                    if active_items:
                        return active_items
            
            # Try Bring!-specific service call format as a last resort
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/services/todo/get_items?return_response", 
                    headers=self.headers,
                    json={
                        "entity_id": list_id,
                        "list_id": list_id.replace("todo.", "")  # Bring! might need a raw list ID
                    }
                )
                
                if response.status_code == 200:
                    service_result = response.json()
                    
                    # Check for nested service_response structure
                    if "service_response" in service_result:
                        service_response = service_result.get("service_response", {})
                        
                        if list_id in service_response:
                            entity_data = service_response.get(list_id, {})
                            items = entity_data.get("items", [])
                            
                            # Process items
                            active_items = []
                            for i, item in enumerate(items):
                                if isinstance(item, dict):
                                    if (item.get("status", "") == "completed" or 
                                        item.get("complete", False) or 
                                        item.get("purchased", False)):
                                        continue
                                    
                                    item_id = item.get("uid", "") or item.get("id", "") or str(i)
                                    item_name = item.get("name", "") or item.get("summary", "") or str(item)
                                    
                                    active_items.append({
                                        "id": item_id,
                                        "name": item_name
                                    })
                                else:
                                    active_items.append({
                                        "id": f"item_{i}",
                                        "name": str(item)
                                    })
                            
                            if active_items:
                                return active_items
            except Exception:
                pass
            
            # If all else fails, return an empty list
            return []
            
        except Exception as e:
            logger.exception(f"Error fetching Bring! items: {str(e)}")
            return []
    
    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()


# Factory function for getting the list provider
def get_list_provider():
    return HomeAssistantListProvider()