from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class TransportType(str, enum.Enum):
    stdio = "stdio"
    sse = "sse"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    usergroup = Column(String, default="dev") # e.g., 'dev', 'devops'
    created_at = Column(DateTime, default=datetime.utcnow)

    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    ai_provider = Column(String, default="ollama")
    model_name = Column(String, default="llama3")
    
    # MCP Configuration
    mcp_transport = Column(Enum(TransportType), default=TransportType.stdio)
    mcp_command = Column(String, default="../kubesage") # Command for stdio
    mcp_url = Column(String, nullable=True) # URL for SSE

    user = relationship("User", back_populates="settings")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String) # 'user', 'assistant', 'system', 'tool'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
