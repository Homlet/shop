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
        # Initialize models based on configuration
        # FIXME: not sure the named model here will always be used
        self.model_name = None
        if settings.llm_provider.lower() == "anthropic":
            self.model_name = "anthropic/claude-3-sonnet-20240229"
        else:
            self.model_name = "openai/gpt-3.5-turbo"

        # Configure the model instance
        self.model = None

        try:
            # Try to get the appropriate model
            if settings.llm_api_key:
                # First, try to get all available models
                llm_models = llm.get_models()
                logger.info(
                    f"Available models: {[m.model_id for m in llm_models]}"
                )

                # Find a model matching our provider
                for model in llm_models:
                    if settings.llm_provider.lower() in model.model_id:
                        self.model = model
                        logger.info(f"Found matching model: {model.model_id}")
                        # Set the API key
                        if settings.llm_provider.lower() == "anthropic":
                            model.key = settings.llm_api_key
                        elif settings.llm_provider.lower() == "openai":
                            model.key = settings.llm_api_key
                        break

                # If no model was found by provider match, try to get it directly
                if not self.model:
                    logger.info(
                        f"No matching model found, trying direct lookup: {self.model_name}"
                    )
                    self.model = llm.get_model(self.model_name)

                    # Set API key directly
                    if settings.llm_provider.lower() == "anthropic":
                        self.model.key = settings.llm_api_key
                    elif settings.llm_provider.lower() == "openai":
                        self.model.key = settings.llm_api_key

            if not self.model:
                logger.error(
                    f"Failed to initialize LLM model for {settings.llm_provider}"
                )
        except Exception as e:
            logger.exception(f"Error initializing LLM model: {str(e)}")

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
                logger.error(f"{settings.llm_provider} API key not configured")
                return "Error: LLM API key not configured"

            if not self.model:
                logger.error(f"No {settings.llm_provider} model is configured")
                return "Error: LLM model not configured properly"

            # Process through the LLM library
            logger.info(f"Processing shopping list with {self.model_name}")

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
            logger.exception(
                f"Error processing with {settings.llm_provider}: {str(e)}"
            )
            return f"Error processing list: {str(e)}"

    def _build_prompt(self, raw_list: str, store_name: str) -> str:
        """Build the prompt for the LLM."""
        return f"""
Process this shopping list for {store_name}:
{raw_list}

Tasks:
1. Remove duplicates (combine quantities)
2. Sort into store sections: Produce, Dairy, Meat, Pantry, Frozen, Household
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

    async def close(self):
        """No need to close anything with the LLM package."""
        pass


# Factory function for getting the LLM service
def get_llm_service():
    return LLMService()
