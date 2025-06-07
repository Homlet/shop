import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables or HA addon config."""
    
    # Home Assistant connection settings
    ha_url: str = Field("http://supervisor/core", env="HA_URL")  # Default URL when running as addon
    ha_token: str = Field("", env="HA_TOKEN")  # Long-lived access token
    
    # LLM settings
    llm_api_key: str = Field("", env="LLM_API_KEY")
    llm_provider: str = Field("openai", env="LLM_PROVIDER")  # "openai" or "anthropic"
    
    # Store settings
    default_store: str = Field("Grocery Store", env="DEFAULT_STORE")
    
    # Printer settings
    receipt_width: int = Field(32, env="RECEIPT_WIDTH")  # 32 chars for 58mm, ~48 for 80mm
    
    # App settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    port: int = Field(8080, env="PORT")
    host: str = Field("0.0.0.0", env="HOST")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings object
settings = Settings()