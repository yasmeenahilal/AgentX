from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum

# Forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .vector_db import VectorDB
    from .chat import ChatSession

class LLMProviderEnum(str, Enum):
    huggingface = "huggingface"
    openai = "openai"
    gemini = "gemini"

class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_name: str = Field(index=True)
    llm_provider: LLMProviderEnum
    llm_model_name: str
    llm_api_key: str
    prompt_template: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    vector_db_id: Optional[int] = Field(default=None, foreign_key="vectordb.id", nullable=True)
    
    # Relationships - use string references to avoid circular imports
    user: "User" = Relationship(back_populates="agents")
    vector_db: Optional["VectorDB"] = Relationship()
    chat_sessions: List["ChatSession"] = Relationship(back_populates="agent")
    
    class Config:
        table_name = "agent" 