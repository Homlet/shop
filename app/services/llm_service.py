import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import llm

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs to process shopping lists."""

    def __init__(self):
        # Initialize model instance
        self.model = None
        self.model_id = settings.llm_model

        # Only proceed if a model is specified
        if not self.model_id:
            logger.error("No LLM model specified in settings")
            return

        try:
            # Get the specified model directly
            logger.info(f"Initializing LLM model: {self.model_id}")
            self.model = llm.get_model(self.model_id)

            # Set the API key directly on the model
            if settings.llm_api_key:
                self.model.key = settings.llm_api_key
                logger.info(f"API key set for model: {self.model_id}")
            else:
                logger.warning(
                    f"No API key provided for model: {self.model_id}"
                )

        except Exception as e:
            logger.exception(f"Error initializing LLM model: {str(e)}")
            # Log available models to help troubleshoot
            try:
                available_models = [m.model_id for m in llm.get_models()]
                logger.info(f"Available models: {available_models}")
            except:
                pass

    async def process_shopping_list(
        self, items: List[Dict[str, Any]], store_name: Optional[str] = None
    ) -> str:
        """
        Process a shopping list through LLM.

        Args:
            items: List of items from the list provider
            store_name: Name of the store for context (optional)

        Returns:
            Processed list formatted for receipt paper
        """
        # Use default store if none provided
        store = store_name or settings.default_store

        # Convert items to a simple text list
        raw_list = "\n".join(
            [item.get("name", "") for item in items if item.get("name")]
        )

        # Build the prompt for the LLM
        prompt = self._build_prompt(raw_list, store)

        try:
            # Check if we have the required configuration
            if not settings.llm_api_key:
                logger.error("LLM API key not configured")
                return "Error: LLM API key not configured"

            if not self.model:
                logger.error("LLM model not configured properly")
                return "Error: LLM model not configured properly"

            # Process through the LLM library
            logger.info(f"Processing shopping list with {self.model_id}")

            # Add system prompt for better context
            system_prompt = (
                "You are a helpful shopping list organizer assistant."
            )

            # Use the LLM package to make the request in a thread to keep our interface async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.prompt(
                    prompt,
                    system=system_prompt,
                    temperature=0.3,
                    max_tokens=1000,
                ),
            )

            return response.text().strip()

        except Exception as e:
            logger.exception(f"Error processing with LLM: {str(e)}")
            return f"Error processing list: {str(e)}"

    def _build_prompt(self, raw_list: str, store_name: str) -> str:
        """Build the prompt for the LLM with store-specific sections."""
        # Get the sections for the specified store
        store_sections = self._get_store_sections(store_name)
        sections_text = ", ".join(store_sections)

        return f"""
Process this shopping list for {store_name}:
{raw_list}

Tasks:
1. Remove duplicates (combine quantities)
2. Sort into store sections: {sections_text}
3. Format for {settings.receipt_width} character width receipt paper

<example>
Produce
 - Carrots
 - Onions
 - Lemons

Bakery
 - Bread
 - Croissants

Toiletries
 - Hand soap
</example>

Output as structured text ready for printing with clear section headers.
Do not include any explanations or notes, just the formatted list.
"""

    def _get_store_sections(self, store_name: str) -> List[str]:
        """Get the sections for a specific store from settings."""
        # Find the store in the settings
        for store in settings.stores:
            if store["name"].lower() == store_name.lower():
                return store["sections"]

        # If not found, return the sections from the default store
        for store in settings.stores:
            if store["name"].lower() == settings.default_store.lower():
                return store["sections"]

        # Fallback to a basic set of sections
        return ["Produce", "Dairy", "Meat", "Pantry", "Frozen", "Household"]

    async def close(self):
        """No need to close anything with the LLM package."""
        pass


# Factory function for getting the LLM service
def get_llm_service():
    return LLMService()
