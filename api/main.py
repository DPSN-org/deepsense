from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from graph.planner_react_agent import run_planner_react_agent
from utils.db_utils import (
    create_session,
    get_session_info,
    save_message,
    get_session_messages,
    delete_session,
    get_user_sessions
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import uuid
from datetime import datetime
from collections import OrderedDict

# Create FastAPI app
app = FastAPI(
    title="LangGraph Assistant API",
    description="A LangGraph-powered assistant with session management and advanced processing capabilities",
    version="1.0.0"
)

# Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# In-memory cache for agent states (limited to 10 sessions)
agent_states_cache = OrderedDict()
MAX_CACHE_SIZE = 10

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ToolResult(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    result: Dict[str, Any]

class QueryResponse(BaseModel):
    query: str
    response: str
    session_id: str
    tool_results: List[ToolResult]
    conversation_length: int
    success: bool = True
    error: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    user_id: Optional[str]
    created_at: str
    updated_at: str
    status: str

class SessionMessage(BaseModel):
    message_id: str
    session_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    sequence_order: int
    metadata: Dict[str, Any]

def manage_cache_size():
    """Manage cache size by removing least recently used items."""
    while len(agent_states_cache) > MAX_CACHE_SIZE:
        agent_states_cache.popitem(last=False)

def convert_db_message_to_langgraph(db_message: Dict[str, Any], include_nested_subgraphs: bool = False):
    """Convert database message to LangGraph message object."""
    message_type = db_message['message_type']
    content = db_message['content']
    metadata = db_message.get('metadata', {})
    
    # Skip nested subgraph messages unless explicitly requested
    if not include_nested_subgraphs and metadata.get('nested_subgraph', False):
        return None
    
    if message_type == 'SystemMessage':
        return SystemMessage(content=content.get('content', ''))
    elif message_type == 'HumanMessage':
        return HumanMessage(content=content.get('content', ''))
    elif message_type == 'AIMessage':
        return AIMessage(content=content.get('content', ''))
    elif message_type == 'ToolMessage':
        return ToolMessage(
            content=content.get('content', ''),
            tool_call_id=content.get('tool_call_id', '')
        )
    else:
        # Fallback to HumanMessage for unknown types
        return HumanMessage(content=str(content))

def save_langgraph_message_to_db(session_id: str, message, metadata: Dict[str, Any] = None):
    """Save a LangGraph message to the database."""
    if isinstance(message, SystemMessage):
        message_type = 'SystemMessage'
        content = {'content': message.content}
    elif isinstance(message, HumanMessage):
        message_type = 'HumanMessage'
        content = {'content': message.content}
    elif isinstance(message, AIMessage):
        message_type = 'AIMessage'
        content = {'content': message.content}
    elif isinstance(message, ToolMessage):
        message_type = 'ToolMessage'
        content = {
            'content': message.content,
            'tool_call_id': getattr(message, 'tool_call_id', '')
        }
    else:
        message_type = 'UnknownMessage'
        content = {'content': str(message)}
    
    return save_message(session_id, message_type, content, metadata)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LangGraph Assistant API",
        "version": "1.0.0",
        "description": "A LangGraph-powered assistant with session management and advanced processing capabilities",
        "endpoints": {
            "/query": "POST - Process a natural language query",
            "/sessions": "POST - Create a new session",
            "/sessions/{session_id}": "GET - Get session information",
            "/sessions/{session_id}/messages": "GET - Get session messages (excludes nested subgraphs)",
            "/sessions/{session_id}/messages/full": "GET - Get all session messages (includes nested subgraphs)",
            "/sessions/{session_id}": "DELETE - Delete a session",
            "/users/{user_id}/sessions": "GET - Get user sessions",
            "/health": "GET - Health check endpoint"
        }
    }



@app.post("/query", response_model=QueryResponse)
async def process_user_query(request: QueryRequest):
    """
    Process a natural language query using the LangGraph workflow with session management.
    
    Examples:
    - "What's the weather in Tokyo?"
    - "Find me a flight from Delhi to Dubai on July 22"
    - "How's the weather in New York and what flights are available to London tomorrow?"
    """
    try:
        # Validate configuration
        if not config.validate():
            raise HTTPException(
                status_code=500,
                detail="Missing required configuration. Please check your environment variables."
            )
        
        # Handle session management
        session_id = request.session_id
        if not session_id:
            # Create new session if none provided
            session_id = create_session(request.user_id)
        else:
            # If session_id is provided, ensure it exists in database
            session_id = create_session(request.user_id, session_id=session_id)
        
        # Check if session exists in cache
        existing_messages = None
        if session_id in agent_states_cache:
            # Use cached state
            cached_state = agent_states_cache[session_id]
            existing_messages = cached_state.get('messages', [])
            # Move to end (most recently used)
            agent_states_cache.move_to_end(session_id)
        else:
            # Fetch session history from database
            db_messages = get_session_messages(session_id)
            if db_messages:
                existing_messages = [
                    convert_db_message_to_langgraph(msg, include_nested_subgraphs=False) 
                    for msg in db_messages
                ]
                # Filter out None values (nested subgraph messages)
                existing_messages = [msg for msg in existing_messages if msg is not None]
        
        # Save the human message to database
        try:
            save_langgraph_message_to_db(
                session_id, 
                HumanMessage(content=request.query),
                metadata={"source": "api_query", "timestamp": str(datetime.now())}
            )
        except Exception as e:
            print(f"[API] Failed to save human message: {e}")
        
        # Process the query with session context
        result = run_planner_react_agent(
            user_input=request.query,
            session_id=session_id,
            existing_messages=existing_messages
        )
        
        # Save new messages to database (this is now handled within the workflow nodes)
        # The workflow nodes now save messages as they are created
        
        # Update cache
        if result:
            agent_states_cache[session_id] = result
            manage_cache_size()
        
        # Convert tool results to Pydantic models
        tool_results = []
        if result and 'tool_results' in result:
            for tr in result['tool_results']:
                tool_results.append(ToolResult(
                    tool_name=tr["tool_name"],
                    args=tr["args"],
                    result=tr["result"]
                ))
        
        # Get the final response
        final_response = ""
        if result and 'messages' in result and result['messages']:
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                final_response = last_message.content
        
        return QueryResponse(
            query=request.query,
            response=final_response,
            session_id=session_id,
            tool_results=tool_results,
            conversation_length=len(result.get('messages', [])) if result else 0
        )
        
    except Exception as e:
        return QueryResponse(
            query=request.query,
            response="",
            session_id=session_id or "",
            tool_results=[],
            conversation_length=0,
            success=False,
            error=str(e)
        )

@app.post("/sessions", response_model=SessionInfo)
async def create_new_session(user_id: Optional[str] = None):
    """Create a new chat session."""
    try:
        session_id = create_session(user_id)
        session_info = get_session_info(session_id)
        
        if session_info:
            return SessionInfo(
                session_id=session_info['session_id'],
                user_id=session_info['user_id'],
                created_at=session_info['created_at'].isoformat(),
                updated_at=session_info['updated_at'].isoformat(),
                status=session_info['status']
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create session")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_information(session_id: str):
    """Get information about a specific session."""
    try:
        session_info = get_session_info(session_id)
        
        if session_info:
            return SessionInfo(
                session_id=session_info['session_id'],
                user_id=session_info['user_id'],
                created_at=session_info['created_at'].isoformat(),
                updated_at=session_info['updated_at'].isoformat(),
                status=session_info['status']
            )
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

@app.get("/sessions/{session_id}/messages", response_model=List[SessionMessage])
async def get_session_messages_endpoint(session_id: str, limit: Optional[int] = 100, include_nested: bool = False):
    """Get all messages for a session."""
    try:
        # Verify session exists
        session_info = get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        db_messages = get_session_messages(session_id, limit=limit)
        
        # Convert to response model
        messages = []
        for msg in db_messages:
            # Filter nested subgraph messages unless explicitly requested
            metadata = msg.get('metadata', {})
            if not include_nested and metadata.get('nested_subgraph', False):
                continue
                
            messages.append(SessionMessage(
                message_id=msg['message_id'],
                session_id=msg['session_id'],
                message_type=msg['message_type'],
                content=msg['content'],
                timestamp=msg['timestamp'].isoformat(),
                sequence_order=msg['sequence_order'],
                metadata=msg['metadata']
            ))
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.get("/sessions/{session_id}/messages/full", response_model=List[SessionMessage])
async def get_session_messages_full_endpoint(session_id: str, limit: Optional[int] = 100):
    """Get all messages for a session including nested subgraph messages."""
    try:
        # Verify session exists
        session_info = get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        db_messages = get_session_messages(session_id, limit=limit)
        
        # Convert to response model (include all messages)
        messages = []
        for msg in db_messages:
            messages.append(SessionMessage(
                message_id=msg['message_id'],
                session_id=msg['session_id'],
                message_type=msg['message_type'],
                content=msg['content'],
                timestamp=msg['timestamp'].isoformat(),
                sequence_order=msg['sequence_order'],
                metadata=msg['metadata']
            ))
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete a session and all its messages."""
    try:
        # Remove from cache if present
        if session_id in agent_states_cache:
            del agent_states_cache[session_id]
        
        # Delete from database
        success = delete_session(session_id)
        
        if success:
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@app.get("/users/{user_id}/sessions", response_model=List[SessionInfo])
async def get_user_sessions_endpoint(user_id: str, limit: Optional[int] = 50):
    """Get all sessions for a user."""
    try:
        db_sessions = get_user_sessions(user_id, limit=limit)
        
        sessions = []
        for session in db_sessions:
            sessions.append(SessionInfo(
                session_id=session['session_id'],
                user_id=session['user_id'],
                created_at=session['created_at'].isoformat(),
                updated_at=session['updated_at'].isoformat(),
                status=session['status']
            ))
        
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user sessions: {str(e)}")

      

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 