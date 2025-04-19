from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum

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
    
    class Config:
        table_name = "agent" 