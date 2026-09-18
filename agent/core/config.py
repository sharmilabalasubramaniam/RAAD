import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    RAAD_BACKEND_URL: Optional[str] = None
    BACKEND_URL: str = "https://raad-5iv8.onrender.com/api/v1"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    PORT: Optional[int] = None
    AGENT_PORT: int = 8001
    AGENT_HOST: str = "0.0.0.0"
    TIMEOUT_SECONDS: float = 15.0

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Resolve RAAD_BACKEND_URL if specified in environment
        custom_backend = os.getenv("RAAD_BACKEND_URL") or self.RAAD_BACKEND_URL
        if custom_backend:
            custom_backend = custom_backend.rstrip("/")
            if not custom_backend.endswith("/api/v1"):
                custom_backend = f"{custom_backend}/api/v1"
            self.BACKEND_URL = custom_backend

        # Resolve Render PORT if specified
        render_port = os.getenv("PORT") or self.PORT
        if render_port:
            try:
                self.AGENT_PORT = int(render_port)
            except ValueError:
                pass

settings = Settings()
