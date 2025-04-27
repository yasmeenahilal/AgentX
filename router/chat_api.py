import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

import database.chat_db as chat_db
from models import ChatMessage, ChatSession, User
from schemas.chat_schemas import (  # Need to create these schemas
    ChatMessageResponse,
    ChatSessionResponse,
)
from user.auth import get_current_active_user

chat_router = APIRouter(tags=["Chat History"])
logger = logging.getLogger(__name__)


@chat_router.get("/sessions/{agent_id}", response_model=List[ChatSessionResponse])
async def get_sessions_for_agent(
    agent_id: int, current_user: User = Depends(get_current_active_user)
):
    """Get all chat session titles for the current user and a specific agent."""
    logger.info(
        f"API endpoint /chat/sessions/{agent_id} called for user {current_user.id}"
    )
    try:
        sessions = chat_db.get_chat_sessions(user_id=current_user.id, agent_id=agent_id)
        logger.info(
            f"Retrieved {len(sessions)} sessions from DB function for agent {agent_id}"
        )
        return sessions
    except Exception as e:
        logger.error(
            f"Error retrieving sessions for agent {agent_id}, user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")


@chat_router.get("/messages/{session_id}", response_model=List[ChatMessageResponse])
async def get_messages_for_session(
    session_id: int, current_user: User = Depends(get_current_active_user)
):
    """Get all messages for a specific chat session owned by the current user."""
    try:
        messages = chat_db.get_chat_messages(
            session_id=session_id, user_id=current_user.id
        )
        return messages
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Error retrieving messages for session {session_id}, user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve chat messages")


@chat_router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int, current_user: User = Depends(get_current_active_user)
):
    """Delete a specific chat session and its messages."""
    try:
        success = chat_db.delete_chat_session(
            session_id=session_id, user_id=current_user.id
        )
        if success:
            return
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Error deleting session {session_id} for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to delete chat session")
