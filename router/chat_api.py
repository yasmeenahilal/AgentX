from fastapi import APIRouter, Depends, HTTPException
from typing import List

from models import User, ChatSession, ChatMessage
from schemas.chat_schemas import ChatSessionResponse, ChatMessageResponse # Need to create these schemas
from user.auth import get_current_active_user
import database.chat_db as chat_db

chat_router = APIRouter(prefix="/chat", tags=["Chat History"])

@chat_router.get("/sessions/{agent_id}", response_model=List[ChatSessionResponse])
async def get_sessions_for_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get all chat session titles for the current user and a specific agent."""
    try:
        sessions = chat_db.get_chat_sessions(user_id=current_user.id, agent_id=agent_id)
        # Convert to response model (assuming ChatSessionResponse has id, title, created_at)
        return sessions 
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")

@chat_router.get("/messages/{session_id}", response_model=List[ChatMessageResponse])
async def get_messages_for_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get all messages for a specific chat session owned by the current user."""
    try:
        messages = chat_db.get_chat_messages(session_id=session_id, user_id=current_user.id)
        # Convert to response model (assuming ChatMessageResponse has id, type, content, created_at)
        return messages
    except HTTPException as http_exc:
        raise http_exc # Re-raise specific errors (like 404)
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="Failed to retrieve chat messages")

@chat_router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a specific chat session and its messages."""
    try:
        success = chat_db.delete_chat_session(session_id=session_id, user_id=current_user.id)
        if success:
            return # Return 204 No Content on success
        else:
             # Should not happen if delete_chat_session raises exceptions on failure
             raise HTTPException(status_code=500, detail="Failed to delete session")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

# Note: Session creation will be handled implicitly by the query endpoint when no session_id is provided. 