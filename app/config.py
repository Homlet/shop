import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables or HA addon config."""
    
    # API keys and credentials
    anylist_email: str = Field("", env="ANYLIST_EMAIL")
    anylist_password: str = Field("", env="ANYLIST_PASSWORD")
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