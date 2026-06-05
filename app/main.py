import os
from dotenv import load_dotenv
load_dotenv() # Load variables from .env if present

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import settings, chat, users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KubeSage AI API",
    description="FastAPI backend connecting AI models to Kubernetes via MCP",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(settings.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "KubeSage AI API is running. Check /docs for endpoints."}
