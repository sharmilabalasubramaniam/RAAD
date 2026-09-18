import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.config import settings
from client.backend_client import backend_client
from workflows.chat_agent import ChatAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agent_service")

app = FastAPI(
    title="ResourcePulse AI Workforce Agent",
    version="1.0.0",
    description="Autonomous Agent service for workforce allocation, conflict resolution, and staffing decisions."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    role: str = "assistant"
    message: str
    tool_calls: List[Dict[str, Any]] = []
    actions_taken: List[Dict[str, Any]] = []

@app.get("/")
async def root():
    return {
        "service": "ResourcePulse AI Workforce Agent",
        "status": "online",
        "backend_url": settings.BACKEND_URL,
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verify agent health and backend connectivity."""
    backend_status = await backend_client.check_health()
    return {
        "status": "healthy",
        "service": "workforce-agent-service",
        "backend_url": settings.BACKEND_URL,
        "backend_connected": backend_status.get("connected", False),
        "backend_details": backend_status.get("data") or backend_status.get("error")
    }

@app.post("/api/v1/agent/chat", response_model=ChatResponse)
async def agent_chat(payload: ChatRequest):
    """
    Primary endpoint for manager interaction with the AI Workforce Agent.
    Executes backend domain tools and returns synthesized analysis.
    """
    try:
        res = await ChatAgent.handle_message(
            message=payload.message,
            conversation_id=payload.conversation_id
        )
        return res
    except Exception as e:
        logger.error(f"Error handling agent chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}")

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", settings.AGENT_PORT))
    uvicorn.run(
        "main:app",
        host=settings.AGENT_HOST,
        port=port,
        reload=False
    )
