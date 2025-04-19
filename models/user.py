from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum
from pydantic import EmailStr

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
    
    # Relationships - use string references to avoid circular imports
    agents: List["Agent"] = Relationship(back_populates="user")
    vector_dbs: List["VectorDB"] = Relationship(back_populates="user")

class PasswordReset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    is_used: bool = Field(default=False) 