from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum
from pydantic import EmailStr

# Forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .agent import Agent
    from .vector_db import VectorDB
    from .chat import ChatSession
    from .deployment import Deployment

class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: RoleEnum = Field(default=RoleEnum.user)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)
    
    # Relationships
    agents: List["Agent"] = Relationship(back_populates="user")
    vector_dbs: List["VectorDB"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    deployments: List["Deployment"] = Relationship(back_populates="user")

    class Config:
        table_name = "user"

class PasswordReset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    is_used: bool = Field(default=False) 