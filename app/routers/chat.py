import json
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ChatSession, ChatMessage, User
from ..schemas import ChatSessionResponse, ChatSessionCreate, ChatRequest
from .settings import get_current_user_settings
from ..ai.factory import get_ai_provider
from ..mcp_client.client import get_mcp_session, get_mcp_tools

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(session: ChatSessionCreate, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    db_session = ChatSession(title=session.title, user_id=x_user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(x_user_id: int = Header(...), db: Session = Depends(get_db)):
    return db.query(ChatSession).filter(ChatSession.user_id == x_user_id).all()

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: int, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == x_user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/sessions/{session_id}/message")
async def send_message(session_id: int, req: ChatRequest, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    # 1. Fetch Session and Settings scoped to user
    session = get_session(session_id, x_user_id, db)
    settings = get_current_user_settings(x_user_id, db)
    
    if not settings.ai_provider or not settings.model_name:
        raise HTTPException(status_code=400, detail="User must select an AI provider and model before chatting")
    
    # Initialize Provider via Factory
    provider = get_ai_provider(provider_name=settings.ai_provider, model_name=settings.model_name)
    
    # Save user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()
    
    # Reconstruct history for provider
    history = [{"role": m.role, "content": m.content} for m in session.messages]
    
    # 2. Connect to MCP Server and get tools
    async with get_mcp_session(settings) as mcp_session:
        tools = await get_mcp_tools(mcp_session)
        
        # 3. Call AI
        assistant_msg, tool_calls = await provider.chat(history, tools=tools)
        
        # Loop for tool execution
        while tool_calls:
            history.append({
                "role": "assistant",
                "content": assistant_msg.get("content", ""),
                "tool_calls": tool_calls
            })
            
            for call in tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                print(f"[Tool Call by User {x_user_id}] {tool_name}({args})")
                
                try:
                    result = await mcp_session.call_tool(tool_name, args)
                    tool_result_content = result.content[0].text if result.content else "Executed."
                except Exception as e:
                    tool_result_content = f"Error: {str(e)}"
                    
                tool_msg = provider.format_tool_result(call.id, tool_name, tool_result_content)
                history.append(tool_msg)
                
            # Call AI again with the new tool results
            assistant_msg, tool_calls = await provider.chat(history, tools=tools)
            
        # 4. Save Final Assistant Message
        assistant_db_msg = ChatMessage(
            session_id=session_id, 
            role=assistant_msg["role"], 
            content=assistant_msg["content"]
        )
        db.add(assistant_db_msg)
        db.commit()
        db.refresh(assistant_db_msg)
        
        return {"role": assistant_db_msg.role, "content": assistant_db_msg.content}
