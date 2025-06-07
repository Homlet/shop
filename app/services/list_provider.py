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
    
    async def get_lists(self) -> List[Dict[str, Any]]:
        """
        Get all todo lists from Home Assistant.
        
        Returns a list of todo lists with their IDs, names, and item counts.
        """
        try:
            # Get all todo list entities from the states API
            response = await self.client.get(
                f"{self.base_url}/api/states", 
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get states from Home Assistant: {response.status_code} - {response.text}")
                return []
            
            # Extract todo lists from states
            states = response.json()
            todo_lists = []
            
            # Log the number of states
            logger.info(f"Found {len(states)} total states")
            
            # First, try to identify what todo integration is being used
            todo_entities = [state for state in states if state.get("entity_id", "").startswith("todo.")]
            logger.info(f"Found {len(todo_entities)} todo entities")
            
            # Check specifically for Bring! integration entities
            bring_entities = []
            for entity in todo_entities:
                entity_id = entity.get("entity_id", "")
                attrs = entity.get("attributes", {})
                supported_features = attrs.get("supported_features", 0)
                
                # Bring! integration has a specific supported_features value (typically 71)
                if supported_features == 71:
                    bring_entities.append(entity)
                    logger.info(f"Detected potential Bring! integration entity: {entity_id}")
            
            # Let's analyze a todo entity to understand its structure
            if todo_entities:
                example = todo_entities[0]
                entity_id = example.get("entity_id", "")
                attrs = example.get("attributes", {})
                logger.info(f"Example todo entity: {entity_id}")
                logger.info(f"Entity state: {example.get('state')}")
                logger.info(f"Entity friendly_name: {attrs.get('friendly_name')}")
                logger.info(f"Entity supported_features: {attrs.get('supported_features')}")
                logger.info(f"Integration data: {attrs.get('integration', 'unknown')}")
            
            # Process all todo entities
            for state in states:
                entity_id = state.get("entity_id", "")
                
                # Check if this is a todo list entity
                if entity_id.startswith("todo."):
                    list_id = entity_id
                    attrs = state.get("attributes", {})
                    friendly_name = attrs.get("friendly_name", entity_id.replace("todo.", ""))
                    supported_features = attrs.get("supported_features", 0)
                    
                    # Detect if this is likely a Bring! integration
                    is_bring = supported_features == 71
                    
                    # For debugging, log the attribute value
                    logger.info(f"Integration attribute: {attrs.get('integration')}")
                    
                    # For Bring! integrations, force the type to "bring" regardless of the attribute
                    integration_type = "bring" if is_bring else attrs.get("integration", "unknown")
                    
                    # Log the detection decision
                    if is_bring:
                        logger.info(f"Detected entity {entity_id} as Bring! integration based on supported_features=71")
                    
                    # Log detection details
                    logger.info(f"Integration detection: supported_features={supported_features}, is_bring={is_bring}")
                    logger.info(f"Processing todo list: {entity_id} ({friendly_name}), Integration: {integration_type}")
                    
                    # Get item count - we'll count active items only
                    # Pass the integration type to the get_list_items method
                    items = await self.get_list_items(list_id, integration_type=integration_type)
                    item_count = len(items)
                    
                    logger.info(f"List {entity_id} has {item_count} active items")
                    
                    # Ensure integration_type is properly stored
                    list_data = {
                        "id": list_id,
                        "name": friendly_name,
                        "item_count": item_count,
                        "integration": integration_type
                    }
                    
                    # Log the list data we're storing
                    logger.info(f"Adding todo list with data: {list_data}")
                    
                    todo_lists.append(list_data)
            
            # If no todo lists were found, try the legacy shopping list as a fallback
            if not todo_lists:
                logger.info("No todo lists found, trying legacy shopping list")
                shopping_list = await self._try_legacy_shopping_list()
                if shopping_list:
                    todo_lists.append(shopping_list)
            
            return todo_lists
                
        except Exception as e:
            logger.exception(f"Error fetching todo lists from Home Assistant: {str(e)}")
            return []
    
    async def _try_legacy_shopping_list(self) -> Optional[Dict[str, Any]]:
        """Try to use the legacy shopping list API as a fallback."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/shopping_list", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                items = response.json()
                active_items = [item for item in items if not item.get("complete", False)]
                return {
                    "id": "shopping_list.shopping_list",
                    "name": "Shopping List (Legacy)",
                    "item_count": len(active_items)
                }
            return None
        except Exception:
            logger.exception("Error accessing legacy shopping list")
            return None
    
    async def get_list_items(self, list_id: str, integration_type: str = "unknown") -> List[Dict[str, Any]]:
        """
        Get all active items from a specific todo list.
        
        Args:
            list_id: The entity ID of the todo list
            integration_type: The type of integration detected from entity attributes
            
        Returns:
            List of active todo list items
        """
        logger.info(f"Getting items for list {list_id} with integration type: {integration_type}")
        
        # Log integration type for debugging
        logger.info(f"Integration type in get_list_items: '{integration_type}'")
        
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
        try:
            # Check if this is a legacy shopping list
            if list_id == "shopping_list.shopping_list":
                return await self._get_legacy_shopping_list_items()
            
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
                    
                    # If no items found in attributes, try to infer from the state
                    # but this is a last resort and may not be accurate
                    try:
                        # See if we can access raw entity data with entity_id
                        resp = await self.client.get(
                            f"{self.base_url}/api/states", 
                            headers=self.headers
                        )
                        
                        if resp.status_code == 200:
                            all_states = resp.json()
                            
                            # Look for related entities that might contain the actual items
                            related_entities = [
                                entity for entity in all_states 
                                if entity.get("entity_id", "").startswith("todo.") and 
                                   entity.get("entity_id") != list_id
                            ]
                            
                            logger.info(f"Found {len(related_entities)} related Todo entities")
                            
                            # Check each related entity for items
                            for entity in related_entities:
                                entity_items = entity.get("attributes", {}).get("items", [])
                                if entity_items:
                                    logger.info(f"Found {len(entity_items)} items in related entity {entity.get('entity_id')}")
                                    
                                    # Filter for incomplete items and format them
                                    active_items = []
                                    for i, item in enumerate(entity_items):
                                        if item.get("complete", False) or item.get("status", "") == "completed":
                                            continue
                                            
                                        item_id = item.get("uid", "") or item.get("id", "") or str(i)
                                        item_name = item.get("summary", "") or item.get("name", "") or str(item)
                                        
                                        if isinstance(item, str):
                                            item_id = f"item_{i}"
                                            item_name = item
                                        
                                        active_items.append({
                                            "id": item_id,
                                            "name": item_name,
                                            "status": "needs_action"
                                        })
                                    
                                    if active_items:
                                        logger.info(f"Using {len(active_items)} items from related entity")
                                        return active_items
                    except Exception as e:
                        logger.exception(f"Error looking for related entities: {str(e)}")
            
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
            
            # If we couldn't find any items, try a general approach
            response = await self.client.get(
                f"{self.base_url}/api/services/todo", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                services = response.json()
                logger.info(f"Available todo services: {[s.get('service') for s in services]}")
                
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
        """Get items from a Bring! integration list.
        
        The Bring! integration has a unique structure and requires specific handling.
        It uses the todo.get_items service with a specific format.
        """
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
            
            # Fallback: try to get the entity state to see if items are in attributes
            logger.info(f"Service call returned empty items, trying to fetch Bring! items from state for {list_id}")
            response = await self.client.get(
                f"{self.base_url}/api/states/{list_id}", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                state_data = response.json()
                logger.info(f"Full Bring! entity state data: {state_data}")
                attributes = state_data.get("attributes", {})
                
                # Log the full attributes for debugging
                logger.info(f"Bring! entity attributes: {attributes}")
                
                # Try different attribute names where Bring! might store items
                # Bring! often stores items in "items" or "item_names"
                for attr_name in ["items", "item_names", "purchases", "shopping_list", "products"]:
                    items = attributes.get(attr_name, [])
                    if items:
                        logger.info(f"Found {len(items)} items in Bring! attribute '{attr_name}'")
                        
                        # Process each item, with careful handling for Bring!'s format
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
                
                # Bring! integration might use purchase_items attribute
                if "purchase_items" in attributes:
                    try:
                        logger.info("Trying to parse purchase_items attribute")
                        purchase_items = attributes.get("purchase_items", {})
                        logger.info(f"Purchase items: {purchase_items}")
                        
                        # Try to parse the purchase_items structure (may be nested)
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
                            logger.info(f"Found {len(active_items)} items in purchase_items attribute")
                            return active_items
                    except Exception as e:
                        logger.exception(f"Error parsing purchase_items: {str(e)}")
                
                # Check if there's a state value that indicates the number of items
                state_value = state_data.get("state")
                logger.info(f"Bring! entity state value: {state_value}")
                
                # If state is a number and not 0, but we found no items, we might need to examine related entities
                try:
                    state_num = int(state_value)
                    if state_num > 0:
                        logger.info(f"State value {state_num} suggests there are items, looking for related entities")
                        
                        # Look for related entities that might contain the actual items
                        resp = await self.client.get(
                            f"{self.base_url}/api/states", 
                            headers=self.headers
                        )
                        
                        if resp.status_code == 200:
                            all_states = resp.json()
                            
                            # Find entities with similar names that might be related to this Bring! list
                            list_base_name = list_id.replace("todo.", "")
                            related_entities = [
                                entity for entity in all_states 
                                if (entity.get("entity_id", "").startswith("todo.") or 
                                    entity.get("entity_id", "").startswith("sensor."))
                                and entity.get("entity_id") != list_id
                                and (list_base_name in entity.get("entity_id", "") or 
                                     "bring" in entity.get("entity_id", "").lower())
                            ]
                            
                            logger.info(f"Found {len(related_entities)} potentially related entities")
                            for entity in related_entities:
                                entity_id = entity.get("entity_id", "")
                                entity_attrs = entity.get("attributes", {})
                                logger.info(f"Examining related entity: {entity_id}")
                                logger.info(f"Related entity attributes: {entity_attrs}")
                                
                                # Check for items in attributes
                                for attr_name in ["items", "item_names", "purchases", "shopping_list", "products"]:
                                    items = entity_attrs.get(attr_name, [])
                                    if items:
                                        logger.info(f"Found {len(items)} items in related entity attribute '{attr_name}'")
                                        
                                        # Format items
                                        active_items = []
                                        for i, item in enumerate(items):
                                            if isinstance(item, dict):
                                                if (item.get("status", "") == "completed" or 
                                                    item.get("complete", False) or 
                                                    item.get("purchase", False)):
                                                    continue
                                                
                                                item_id = item.get("uid", "") or item.get("id", "") or str(i)
                                                item_name = item.get("summary", "") or item.get("name", "") or str(item)
                                            else:
                                                item_id = f"item_{i}"
                                                item_name = str(item)
                                            
                                            active_items.append({
                                                "id": item_id,
                                                "name": item_name
                                            })
                                        
                                        if active_items:
                                            logger.info(f"Using {len(active_items)} items from related entity {entity_id}")
                                            return active_items
                except Exception as e:
                    logger.exception(f"Error examining related entities: {str(e)}")
            
            # Try one more Bring!-specific approach - using the HA developer tools service call format
            logger.info("Trying Bring!-specific service call format as a last resort")
            try:
                # The Home Assistant documentation for Bring! mentions a specific format for service calls
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
                    logger.info(f"Bring!-specific service call response: {service_result}")
                    
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
                            logger.info(f"Found {len(items)} items in nested Bring!-specific service response")
                    else:
                        # Try the direct items array if not nested
                        items = service_result.get("items", [])
                        logger.info(f"Found {len(items)} items directly in Bring!-specific service response")
                    
                    if items:
                        logger.info(f"Found {len(items)} items with Bring!-specific service call")
                        active_items = []
                        for i, item in enumerate(items):
                            # Process item based on Bring! format
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
                                # Simple string item
                                active_items.append({
                                    "id": f"item_{i}",
                                    "name": str(item)
                                })
                        
                        if active_items:
                            return active_items
            except Exception as e:
                logger.exception(f"Error with Bring!-specific service call: {str(e)}")
            
            # If all else fails, log the issue and return an empty list
            logger.error(f"Failed to fetch Bring! items through all methods for {list_id}")
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