import uuid
import logging
from typing import Dict, Any, Optional
from core.llm import LLMService

logger = logging.getLogger("agent.workflows.chat_agent")

class ChatAgent:
    """
    Primary workflow agent for single-turn and multi-turn manager commands.
    Orchestrates backend API queries via domain tools and synthesizes responses.
    """

    @classmethod
    async def handle_message(cls, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        cid = conversation_id or f"conv_{str(uuid.uuid4())[:8]}"

        if not message or not message.strip():
            return {
                "conversation_id": cid,
                "role": "assistant",
                "message": "Please provide a valid manager prompt or question.",
                "tool_calls": [],
                "actions_taken": []
            }

        logger.info(f"Processing chat message for conversation '{cid}': {message}")
        result = await LLMService.process_chat(user_message=message, conversation_id=cid)

        return {
            "conversation_id": cid,
            "role": result.get("role", "assistant"),
            "message": result.get("message", ""),
            "tool_calls": result.get("tool_calls", []),
            "actions_taken": result.get("actions_taken", [])
        }
