from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# Import the enum from the correct location
from models.chat import MessageTypeEnum


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    user_id: int
    agent_id: int

    class Config:
        orm_mode = True  # Enable ORM mode for SQLModel compatibility


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    message_type: MessageTypeEnum  # Use the imported enum
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


# Add schemas for request bodies if needed later, e.g.:
# class ChatMessageCreate(BaseModel):
#     content: str
