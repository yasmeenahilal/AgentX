# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    role: RoleEnum = RoleEnum.user

class UserResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
