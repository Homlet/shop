import os
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Configure logging for the config module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables or HA addon config."""
    
    # Home Assistant connection settings
    ha_url: str = Field("http://supervisor/core", env="HA_URL")  # Default URL when running as addon
    ha_token: str = Field("", env="HA_TOKEN")  # Long-lived access token
    todo_list_entity_id: str = Field("todo.shopping", env="TODO_LIST_ENTITY_ID")  # Entity ID of the shopping list to use
    
    # LLM settings
    llm_api_key: str = Field("", env="LLM_API_KEY")  # API key for the selected model
    llm_model: str = Field("", env="LLM_MODEL")  # Model ID (e.g., gpt-3.5-turbo or anthropic/claude-3-sonnet-20240229)
    
    # Store settings
    default_store: str = Field("Grocery Store", env="DEFAULT_STORE")
    
    # Store configurations with sections
    stores: List[Dict[str, Any]] = Field(
        [
            {
                "name": "Grocery Store",
                "sections": ["Produce", "Dairy", "Meat", "Pantry", "Frozen", "Household"]
            },
            {
                "name": "Supermarket",
                "sections": ["Fruits & Vegetables", "Dairy & Eggs", "Meat & Seafood", 
                            "Bakery", "Canned Goods", "Frozen Foods", "Cleaning Supplies"]
            },
            {
                "name": "Convenience Store",
                "sections": ["Snacks", "Beverages", "Quick Meals", "Essentials"]
            }
        ],
        env="STORES"
    )
    
    # Printer settings
    receipt_width: int = Field(32, env="RECEIPT_WIDTH")  # 32 chars for 58mm, ~48 for 80mm
    
    # App settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    port: int = Field(8080, env="PORT")
    host: str = Field("0.0.0.0", env="HOST")

    @field_validator('stores', mode='before')
    @classmethod
    def parse_stores(cls, value):
        """Parse the STORES environment variable if it's a string."""
        if isinstance(value, str):
            try:
                logger.info(f"Parsing STORES from string: {value}")
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing STORES JSON: {e}")
                logger.error(f"Invalid JSON: {value}")
                # Return default value on error
                return [
                    {
                        "name": "Grocery Store",
                        "sections": ["Produce", "Dairy", "Meat", "Pantry", "Frozen", "Household"]
                    },
                    {
                        "name": "Supermarket",
                        "sections": ["Fruits & Vegetables", "Dairy & Eggs", "Meat & Seafood", 
                                    "Bakery", "Canned Goods", "Frozen Foods", "Cleaning Supplies"]
                    },
                    {
                        "name": "Convenience Store",
                        "sections": ["Snacks", "Beverages", "Quick Meals", "Essentials"]
                    }
                ]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Log environment variables for debugging
logger.info("Environment variables:")
for key, value in os.environ.items():
    if key in ["LLM_API_KEY", "HA_TOKEN"]:
        # Don't log sensitive values
        logger.info(f"{key}: [REDACTED]")
    elif key == "STORES":
        logger.info(f"{key}: {value[:50]}..." if len(str(value)) > 50 else f"{key}: {value}")
    else:
        logger.info(f"{key}: {value}")

# Global settings object
settings = Settings()

# Log loaded settings
logger.info(f"Loaded settings:")
logger.info(f"TODO_LIST_ENTITY_ID: {settings.todo_list_entity_id}")
logger.info(f"LLM_MODEL: {settings.llm_model}")
logger.info(f"DEFAULT_STORE: {settings.default_store}")
logger.info(f"RECEIPT_WIDTH: {settings.receipt_width}")
logger.info(f"LOG_LEVEL: {settings.log_level}")
logger.info(f"Number of stores configured: {len(settings.stores)}")