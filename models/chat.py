from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum

# Forward references for relationships
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .agent import Agent

class MessageTypeEnum(str, Enum):
    HUMAN = "human"
    AI = "ai"

class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, default="New Chat") # Can be updated after first message
    created_at: datetime = Field(default_factory=datetime.now)
    total_tokens_in: int = Field(default=0)  # Total input tokens for this session
    total_tokens_out: int = Field(default=0)  # Total output tokens for this session
    
    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    agent_id: int = Field(foreign_key="agent.id") # Assuming Agent model has an ID
    
    # Relationships
    user: "User" = Relationship(back_populates="chat_sessions")
    agent: "Agent" = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    class Config:
        table_name = "chatsession"

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    message_type: MessageTypeEnum
    content: str
    token_count: int = Field(default=0)  # Token count for this message
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationship
    session: ChatSession = Relationship(back_populates="messages")

    class Config:
        table_name = "chatmessage" 