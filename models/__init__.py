from sqlmodel import SQLModel

from .base import engine, get_session, create_db_and_tables
from .user import User, RoleEnum, PasswordReset
from .agent import Agent, LLMProviderEnum
from .vector_db import VectorDB, PineconeDB, FaissDB, DBTypeEnum, EmbeddingModel, FileUpload
from .chat import ChatSession, ChatMessage, MessageTypeEnum

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