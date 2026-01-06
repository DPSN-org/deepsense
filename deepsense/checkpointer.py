"""
MongoDB Checkpointer for DeepSense Framework
Implements LangGraph checkpointer interface to store workflow state in MongoDB.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

try:
    from langgraph.checkpoint.mongodb import MongoDBSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph.checkpoint.mongodb not available. Using fallback implementation.")

class MongoDBCheckpointer:
    """
    MongoDB-based checkpointer for LangGraph workflow state persistence.
    
    This checkpointer stores the complete LangGraph workflow state for each session,
    allowing workflows to be resumed from checkpoints.
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "deepsense",
        collection_name: str = "checkpoints"
    ):
        """
        Initialize MongoDB checkpointer.
        
        Args:
            connection_string: MongoDB connection string (defaults to MONGODB_URI env var)
            database_name: Name of the database
            collection_name: Name of the collection for checkpoints
        """
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = database_name
        self.collection_name = collection_name
        
        try:
            self.client = MongoClient(self.connection_string)
            
            # Use LangGraph's MongoDBSaver if available
            if LANGGRAPH_AVAILABLE:
                self.saver = MongoDBSaver(self.client, db_name=database_name, collection_name=collection_name)
                logger.info(f"✅ Initialized LangGraph MongoDBSaver: {database_name}.{collection_name}")
            else:
                # Fallback: create our own collection
                self.db = self.client[database_name]
                self.collection = self.db[collection_name]
                self.collection.create_index([("thread_id", 1), ("checkpoint_ns", 1)])
                self.saver = None
                logger.info(f"✅ Initialized MongoDB checkpointer (fallback): {database_name}.{collection_name}")
            
            # Additional collection for session metadata
            self.db = self.client[database_name]
            self.sessions_collection = self.db["sessions"]
            
            # Create indexes
            self.sessions_collection.create_index("session_id", unique=True)
            self.sessions_collection.create_index("user_id")
            
            logger.info(f"✅ Connected to MongoDB: {database_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def create_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """
        Create a new session (thread_id for LangGraph).
        
        Args:
            user_id: Optional user identifier
            session_id: Optional session ID to use (thread_id)
            
        Returns:
            session_id: The session/thread ID
        """
        import uuid
        
        if session_id:
            # Check if session exists
            existing = self.sessions_collection.find_one({"session_id": session_id})
            if existing:
                logger.info(f"✅ Session already exists: {session_id}")
                return session_id
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        
        try:
            self.sessions_collection.insert_one(session_doc)
            logger.info(f"✅ Created session: {session_id}")
        except Exception as e:
            # If duplicate key error, session already exists
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                logger.info(f"✅ Session already exists (duplicate): {session_id}")
            else:
                logger.error(f"❌ Failed to create session: {e}")
                raise
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        session = self.sessions_collection.find_one({"session_id": session_id})
        if session:
            session["_id"] = str(session["_id"])
            return session
        return None
    
    def get_saver(self):
        """
        Get the LangGraph checkpointer saver.
        This is used by LangGraph to save/load workflow state.
        
        Returns:
            MongoDBSaver instance (or None if not available)
        """
        return self.saver if LANGGRAPH_AVAILABLE else None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its checkpoints.
        Note: Message history is managed separately by the server.
        
        Args:
            session_id: Session/thread ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        result = self.sessions_collection.delete_one({"session_id": session_id})
        
        # Delete checkpoints for this thread_id
        if LANGGRAPH_AVAILABLE and self.saver:
            # Use LangGraph's saver to delete checkpoints
            try:
                # Delete all checkpoints for this thread
                self.db[self.collection_name].delete_many({"thread_id": session_id})
            except Exception as e:
                logger.warning(f"Failed to delete checkpoints: {e}")
        else:
            # Fallback: delete from our collection
            if hasattr(self, 'collection'):
                self.collection.delete_many({"thread_id": session_id})
        
        if result.deleted_count > 0:
            logger.info(f"✅ Deleted session {session_id} (including checkpoints)")
            return True
        else:
            logger.warning(f"⚠️ Session {session_id} not found")
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

