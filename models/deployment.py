from datetime import datetime
from enum import Enum

# Forward references
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Column, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .agent import Agent
    from .user import User


class DeploymentMethodEnum(str, Enum):
    api = "api"
    embed = "embed"
    both = "both"


class Deployment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    deployment_id: str = Field(unique=True, index=True)
    deployment_name: str
    deployment_description: Optional[str] = None
    deployment_method: DeploymentMethodEnum
    created_at: datetime = Field(default_factory=datetime.now)

    # API specific fields
    api_key: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    api_endpoint: Optional[str] = None

    # Embed specific fields
    embed_code: Optional[str] = None
    embed_settings: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # Security fields
    short_token: Optional[str] = Field(default=None, unique=True, index=True)
    allowed_domains: Optional[str] = Field(
        default="*"
    )  # Comma-separated list of allowed domains, * for all
    is_active: bool = Field(default=True)
    rate_limit: int = Field(default=100)  # Requests per day

    # Foreign Keys
    agent_id: int = Field(foreign_key="agent.id")
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    agent: "Agent" = Relationship(back_populates="deployments")
    user: "User" = Relationship(back_populates="deployments")

    class Config:
        table_name = "deployment"
