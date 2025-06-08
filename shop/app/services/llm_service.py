import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs to process shopping lists."""

    def __init__(self):
        # Initialize httpx client
        self.client = httpx.AsyncClient(timeout=60.0)
        self.model_id = settings.llm_model
        self.api_key = settings.llm_api_key

        # Log initialization
        if not self.model_id:
            logger.error("No LLM model specified in settings")
        elif not self.api_key:
            logger.warning(f"No API key provided for model: {self.model_id}")
        else:
            logger.info(f"Initialized LLM service with model: {self.model_id}")

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
        system_prompt = "You are a helpful shopping list organizer assistant."

        try:
            # Check if we have the required configuration
            if not self.api_key:
                logger.error("LLM API key not configured")
                return "Error: LLM API key not configured"

            # Process through the appropriate API based on model ID
            if "gpt" in self.model_id.lower():
                return await self._call_openai_api(prompt, system_prompt)
            elif "claude" in self.model_id.lower() or "anthropic" in self.model_id.lower():
                return await self._call_anthropic_api(prompt, system_prompt)
            else:
                logger.error(f"Unsupported model type: {self.model_id}")
                return f"Error: Unsupported model type: {self.model_id}"

        except Exception as e:
            logger.exception(f"Error processing with LLM: {str(e)}")
            return f"Error processing list: {str(e)}"

    async def _call_openai_api(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI API with the given prompt."""
        try:
            payload = {
                "model": self.model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"Error calling OpenAI API: {response.status_code}"
                
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.exception(f"Error calling OpenAI API: {str(e)}")
            return f"Error calling OpenAI API: {str(e)}"

    async def _call_anthropic_api(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic API with the given prompt."""
        try:
            # Handle both full model names and simplified names
            model_id = self.model_id
            if "/" not in model_id and "claude" in model_id.lower():
                model_id = f"anthropic/{model_id}"
            
            payload = {
                "model": model_id,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return f"Error calling Anthropic API: {response.status_code}"
                
            result = response.json()
            return result["content"][0]["text"].strip()
            
        except Exception as e:
            logger.exception(f"Error calling Anthropic API: {str(e)}")
            return f"Error calling Anthropic API: {str(e)}"

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
        """Close the HTTP client."""
        await self.client.aclose()


# Factory function for getting the LLM service
def get_llm_service():
    return LLMService()