import httpx
import logging
import json
from typing import List, Dict, Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs to process shopping lists."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0
        )  # Longer timeout for LLM APIs

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

        # Process with the configured LLM provider
        if settings.llm_provider.lower() == "anthropic":
            return await self._process_with_anthropic(prompt)
        else:
            # Default to OpenAI
            return await self._process_with_openai(prompt)

    def _build_prompt(self, raw_list: str, store_name: str) -> str:
        """Build the prompt for the LLM."""
        return f"""
Process this shopping list for {store_name}:
{raw_list}

Tasks:
1. Remove duplicates (combine quantities)
2. Sort into store sections: Produce, Dairy, Meat, Pantry, Frozen, Household
3. Format for {settings.receipt_width} character width receipt paper

Output as structured text ready for printing with clear section headers.
Do not include any explanations or notes, just the formatted list.
"""

    async def _process_with_openai(self, prompt: str) -> str:
        """Process the list using OpenAI API."""
        if not settings.llm_api_key:
            logger.error("OpenAI API key not configured")
            return "Error: LLM API key not configured"

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.llm_api_key}",
            }

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful shopping list organizer assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
            }

            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                return (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error processing list: {error_msg}"

        except Exception as e:
            logger.exception(f"Error processing with OpenAI: {str(e)}")
            return f"Error processing list: {str(e)}"

    async def _process_with_anthropic(self, prompt: str) -> str:
        """Process the list using Anthropic Claude API."""
        if not settings.llm_api_key:
            logger.error("Anthropic API key not configured")
            return "Error: LLM API key not configured"

        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": settings.llm_api_key,
                "anthropic-version": "2023-06-01",
            }

            payload = {
                "model": "claude-2",
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 1000,
                "temperature": 0.3,
            }

            response = await self.client.post(
                "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("completion", "").strip()
            else:
                error_msg = f"Anthropic API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error processing list: {error_msg}"

        except Exception as e:
            logger.exception(f"Error processing with Anthropic: {str(e)}")
            return f"Error processing list: {str(e)}"

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()


# Factory function for getting the LLM service
def get_llm_service():
    return LLMService()
