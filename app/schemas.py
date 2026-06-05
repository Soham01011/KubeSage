from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import TransportType

# User Schemas
class UserBase(BaseModel):
    username: str
    usergroup: str = "dev"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Settings Schemas
class UserSettingBase(BaseModel):
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    mcp_transport: Optional[TransportType] = None
    mcp_command: Optional[str] = None
    mcp_url: Optional[str] = None

class UserSettingResponse(UserSettingBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class ModelListResponse(BaseModel):
    models: List[str]

# Chat Schemas
class ChatMessageBase(BaseModel):
    role: str
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    title: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    messages: List[ChatMessageResponse] = []
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
