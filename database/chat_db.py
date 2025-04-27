import logging
from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime

from models.base import engine
from models import User, Agent, ChatSession, ChatMessage, MessageTypeEnum
from fastapi import HTTPException

# Configure logger
logger = logging.getLogger(__name__)

def get_chat_sessions(user_id: int, agent_id: int) -> List[ChatSession]:
    """Retrieve all chat sessions for a specific user and agent."""
    with Session(engine) as session:
        statement = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.agent_id == agent_id
        ).order_by(ChatSession.created_at.desc())
        sessions = session.exec(statement).all()
        logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}, agent {agent_id}")
        return sessions

def get_chat_messages(session_id: int, user_id: int) -> List[ChatMessage]:
    """Retrieve all messages for a specific chat session, ensuring user owns it."""
    with Session(engine) as session:
        # First verify the session belongs to the user
        session_check = session.get(ChatSession, session_id)
        if not session_check:
             logger.warning(f"Attempt to access non-existent session {session_id}")
             raise HTTPException(status_code=404, detail="Chat session not found")
        if session_check.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access session {session_id} owned by user {session_check.user_id}")
            raise HTTPException(status_code=403, detail="Access denied to chat session")
            
        statement = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())
        messages = session.exec(statement).all()
        logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages

def create_chat_session(user_id: int, agent_id: int, first_message: str) -> ChatSession:
    """Create a new chat session."""
    with Session(engine) as session:
        # Check if user and agent exist
        user = session.get(User, user_id)
        if not user:
            logger.error(f"User with id {user_id} not found during session creation.")
            raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
        agent = session.get(Agent, agent_id)
        if not agent:
             logger.error(f"Agent with id {agent_id} not found during session creation.")
             raise HTTPException(status_code=404, detail=f"Agent with id {agent_id} not found")

        # Create the session
        title = (first_message[:50] + '...') if len(first_message) > 50 else first_message
        if not title:
            title = "New Chat"
            
        new_session = ChatSession(
            user_id=user_id,
            agent_id=agent_id,
            title=title
        )
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        logger.info(f"Created new chat session {new_session.id} for user {user_id}, agent {agent_id}")
        return new_session

def add_chat_message(session_id: int, message_type: MessageTypeEnum, content: str) -> ChatMessage:
    """Add a new message to a chat session."""
    with Session(engine) as session:
        session_check = session.get(ChatSession, session_id)
        if not session_check:
            logger.error(f"Attempted to add message to non-existent session {session_id}")
            raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")
            
        new_message = ChatMessage(
            session_id=session_id,
            message_type=message_type,
            content=content
        )
        session.add(new_message)
        session.commit()
        session.refresh(new_message)
        logger.debug(f"Added {message_type.value} message to session {session_id}")
        return new_message

def delete_chat_session(session_id: int, user_id: int) -> bool:
    """Delete a chat session and its messages, ensuring user owns it."""
    with Session(engine) as session:
        session_to_delete = session.get(ChatSession, session_id)
        if not session_to_delete:
             logger.warning(f"Attempt to delete non-existent session {session_id}")
             raise HTTPException(status_code=404, detail="Chat session not found")
        if session_to_delete.user_id != user_id:
            logger.warning(f"User {user_id} attempted to delete session {session_id} owned by user {session_to_delete.user_id}")
            raise HTTPException(status_code=403, detail="Access denied to delete chat session")
        
        session.delete(session_to_delete)
        session.commit()
        logger.info(f"Deleted chat session {session_id} for user {user_id}")
        return True 