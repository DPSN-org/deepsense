"""
FastAPI server that uses the example workflow
Maintains its own message history separate from LangGraph checkpointer
"""

import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import logging

from example.workflow_instance import invoke_workflow, checkpointer

logger = logging.getLogger(__name__)

# Message History Manager - separate from checkpointer
class MessageHistory:
    """Manages message history for the server, separate from LangGraph checkpointer."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "deepsense",
        collection_name: str = "messages"
    ):
        """Initialize message history manager."""
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = database_name
        self.collection_name = collection_name
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db: Database = self.client[database_name]
            self.collection: Collection = self.db[collection_name]
            
            # Create indexes
            self.collection.create_index("session_id")
            self.collection.create_index([("session_id", 1), ("sequence_order", 1)])
            self.collection.create_index("timestamp")
            
            logger.info(f"✅ Initialized MessageHistory: {database_name}.{collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MessageHistory: {e}")
            raise
    
    def save_message(
        self,
        session_id: str,
        message_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a user or agent message to message history.
        
        Args:
            session_id: Session ID
            message_type: Type of message ('user' or 'agent')
            content: Message content as dictionary
            metadata: Optional metadata dictionary
            
        Returns:
            message_id: The message ID
        """
        # Get the next sequence order
        last_message = self.collection.find_one(
            {"session_id": session_id},
            sort=[("sequence_order", -1)]
        )
        sequence_order = (last_message["sequence_order"] + 1) if last_message else 1
        
        message_doc = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "message_type": message_type,  # 'user' or 'agent'
            "content": content,
            "timestamp": datetime.utcnow(),
            "sequence_order": sequence_order,
            "metadata": metadata or {}
        }
        
        self.collection.insert_one(message_doc)
        
        logger.info(f"✅ Saved {message_type} message {message_doc['message_id']} to session {session_id}")
        return message_doc["message_id"]
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get message history for a session.
        
        Args:
            session_id: Session ID
            limit: Optional limit on number of messages
            message_type: Optional filter by message type ('user' or 'agent')
            
        Returns:
            List of message dictionaries
        """
        query = {"session_id": session_id}
        
        if message_type:
            query["message_type"] = message_type
        
        cursor = self.collection.find(query).sort("sequence_order", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        messages = []
        for msg in cursor:
            msg["_id"] = str(msg["_id"])
            messages.append(msg)
        
        logger.info(f"✅ Retrieved {len(messages)} messages for session {session_id}")
        return messages
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history (user and agent messages) for display.
        
        Args:
            session_id: Session ID
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries with 'user' and 'agent' messages
        """
        return self.get_messages(session_id, limit=limit)
    
    def delete_messages(self, session_id: str) -> int:
        """
        Delete all messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Number of messages deleted
        """
        result = self.collection.delete_many({"session_id": session_id})
        logger.info(f"✅ Deleted {result.deleted_count} messages for session {session_id}")
        return result.deleted_count
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MessageHistory MongoDB connection")

# Initialize message history manager
message_history = MessageHistory()

# Create FastAPI app
app = FastAPI(
    title="DeepSense Example API",
    description="Example API using DeepSense Framework",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    response: str
    session_id: str
    success: bool = True
    error: Optional[str] = None
    user_actions: Optional[List[Dict[str, Any]]] = []

class Message(BaseModel):
    message_id: str
    session_id: str
    message_type: str  # 'user' or 'agent'
    content: Dict[str, Any]
    timestamp: str
    sequence_order: int
    metadata: Optional[Dict[str, Any]] = None

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the workflow.
    
    This endpoint:
    1. Saves the user message to message history
    2. Invokes the workflow (which uses LangGraph checkpointer for state)
    3. Saves the agent response to message history
    
    Examples:
    - "What's the price of bitcoin?"
    - "Get info about the langchain-ai/langchain repository"
    """
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = checkpointer.create_session(user_id=request.user_id)
        else:
            session_id = checkpointer.create_session(user_id=request.user_id, session_id=session_id)
        
        # Save user message to message history (managed by server, separate from checkpointer)
        message_history.save_message(
            session_id=session_id,
            message_type="user",
            content={"text": request.query},
            metadata={"source": "api_query", "timestamp": str(datetime.now())}
        )
        
        # Invoke workflow (LangGraph checkpointer handles workflow state automatically)
        result = invoke_workflow(
            query=request.query,
            session_id=session_id
        )
        
        # Get final response
        final_response = ""
        if result and 'messages' in result and result['messages']:
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                final_response = last_message.content
        
        # Get user_actions from result (if any)
        user_actions = result.get('user_actions', []) if result else []
        
        # Save agent response to message history (managed by server, separate from checkpointer)
        message_history.save_message(
            session_id=session_id,
            message_type="agent",
            content={"text": final_response},
            metadata={"source": "workflow_response", "timestamp": str(datetime.now())}
        )
        
        return QueryResponse(
            query=request.query,
            response=final_response,
            session_id=session_id,
            success=True,
            user_actions=user_actions
        )
        
    except Exception as e:
        return QueryResponse(
            query=request.query,
            response="",
            session_id=session_id or "",
            success=False,
            error=str(e)
        )

@app.post("/sessions")
async def create_session(user_id: Optional[str] = None):
    """Create a new session."""
    try:
        session_id = checkpointer.create_session(user_id=user_id)
        session_info = checkpointer.get_session(session_id)
        
        if session_info:
            return {
                "session_id": session_info['session_id'],
                "user_id": session_info.get('user_id'),
                "created_at": session_info['created_at'].isoformat(),
                "status": session_info['status']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.get("/sessions/{session_id}/messages", response_model=List[Message])
async def get_messages(session_id: str, limit: Optional[int] = None):
    """
    Get message history for a session.
    This returns user and agent messages (managed by server, separate from LangGraph checkpoints).
    """
    try:
        messages = message_history.get_conversation_history(session_id, limit=limit)
        
        return [
            Message(
                message_id=msg['message_id'],
                session_id=msg['session_id'],
                message_type=msg['message_type'],
                content=msg['content'],
                timestamp=msg['timestamp'].isoformat(),
                sequence_order=msg['sequence_order'],
                metadata=msg.get('metadata')
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.get("/sessions/{session_id}/state")
async def get_state(session_id: str):
    """
    Get the current workflow state for a session.
    This retrieves the checkpoint stored by LangGraph (separate from message history).
    """
    try:
        # Get the latest checkpoint from LangGraph
        saver = checkpointer.get_saver()
        if saver:
            # Use LangGraph's saver to get checkpoint
            checkpoint = saver.get({"configurable": {"thread_id": session_id}})
            if checkpoint:
                return {
                    "session_id": session_id,
                    "state": checkpoint.get("channel_values", {}),
                    "checkpoint_id": checkpoint.get("id"),
                    "checkpoint_ns": checkpoint.get("checkpoint_ns")
                }
            else:
                return {"session_id": session_id, "state": None, "message": "No checkpoint found"}
        else:
            raise HTTPException(status_code=500, detail="LangGraph checkpointer not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving state: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "example.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

