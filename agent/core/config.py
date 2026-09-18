import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BACKEND_URL: str = "http://127.0.0.1:8000/api/v1"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AGENT_PORT: int = 8001
    AGENT_HOST: str = "0.0.0.0"
    TIMEOUT_SECONDS: float = 15.0

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
