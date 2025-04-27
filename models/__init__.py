from sqlmodel import SQLModel

from .agent import Agent, LLMProviderEnum
from .base import create_db_and_tables, engine, get_session
from .chat import ChatMessage, ChatSession, MessageTypeEnum
from .user import PasswordReset, RoleEnum, User
from .vector_db import (
    DBTypeEnum,
    EmbeddingModel,
    FaissDB,
    FileUpload,
    PineconeDB,
    VectorDB,
)

__all__ = [
    "engine",
    "get_session",
    "create_db_and_tables",
    "User",
    "PasswordReset",
    "RoleEnum",
    "Agent",
    "LLMProviderEnum",
    "VectorDB",
    "PineconeDB",
    "FaissDB",
    "DBTypeEnum",
    "EmbeddingModel",
    "FileUpload",
    "ChatSession",
    "ChatMessage",
    "MessageTypeEnum",
]


# Function to create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
