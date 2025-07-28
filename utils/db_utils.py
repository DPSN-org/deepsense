"""
Database utilities for LangGraph session management with PostgreSQL.
Handles session creation, message storage, and retrieval.
"""

import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError, InterfaceError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5435'),
    'database': os.getenv('POSTGRES_DB', 'agentic_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
}

# Connection pool
connection_pool = None

def get_connection_pool():
    """Get or create connection pool."""
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **DB_CONFIG
            )
            print("✅ Database connection pool created successfully")
        except Exception as e:
            print(f"❌ Failed to create connection pool: {e}")
            raise
    return connection_pool

def get_connection():
    """Get a connection from the pool."""
    pool = get_connection_pool()
    try:
        conn = pool.getconn()
        # Test the connection to ensure it's valid
        conn.cursor().execute("SELECT 1")
        return conn
    except (OperationalError, InterfaceError) as e:
        print(f"⚠️ Invalid connection from pool, getting new one: {e}")
        # Try to get a fresh connection
        try:
            conn = pool.getconn()
            conn.cursor().execute("SELECT 1")
            return conn
        except Exception as e2:
            print(f"❌ Failed to get valid connection: {e2}")
            raise

def return_connection(conn):
    """Return a connection to the pool with proper error handling."""
    if conn is None:
        return
        
    pool = get_connection_pool()
    try:
        # Check if connection is still valid before returning
        if not conn.closed:
            # Reset the connection state
            conn.rollback()
            pool.putconn(conn)
        else:
            print("⚠️ Connection was closed, not returning to pool")
    except (OperationalError, InterfaceError) as e:
        print(f"⚠️ Connection error when returning to pool: {e}")
        # Don't return corrupted connections to the pool
        try:
            conn.close()
        except:
            pass
    except Exception as e:
        print(f"❌ Unexpected error returning connection to pool: {e}")
        # Close the connection to prevent pool corruption
        try:
            conn.close()
        except:
            pass

def execute_with_connection(func):
    """Decorator to handle connection management automatically."""
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_connection()
            return func(conn, *args, **kwargs)
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if conn:
                return_connection(conn)
    return wrapper

def test_connection():
    """Test database connection and print configuration."""
    print(f"🔍 Testing database connection...")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Port: {DB_CONFIG['port']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   User: {DB_CONFIG['user']}")
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL version: {version}")
        return_connection(conn)
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def init_database():
    """Initialize database tables if they don't exist."""
    print("🔧 Initializing database tables...")
    
    # Test connection first
    if not test_connection():
        raise Exception("Cannot connect to database")
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active'
                )
            """)
            
            # Create chat_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                    message_type VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sequence_order INTEGER NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    UNIQUE(session_id, sequence_order)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id 
                ON chat_messages(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp 
                ON chat_messages(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
                ON chat_sessions(user_id)
            """)
            
            conn.commit()
            print("✅ Database tables initialized successfully")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        return_connection(conn)

def create_session(user_id: Optional[str] = None) -> str:
    """
    Create a new chat session.
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        session_id: UUID of the created session
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_sessions (user_id, created_at, updated_at, status)
                VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'active')
                RETURNING session_id
            """, (user_id,))
            
            session_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ Created session: {session_id}")
            return str(session_id)
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create session: {e}")
        raise
    finally:
        return_connection(conn)

def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session information.
    
    Args:
        session_id: UUID of the session
        
    Returns:
        Session information dictionary or None if not found
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT session_id, user_id, created_at, updated_at, status
                FROM chat_sessions
                WHERE session_id = %s
            """, (session_id,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
            
    except Exception as e:
        print(f"❌ Failed to get session info: {e}")
        raise
    finally:
        return_connection(conn)

def save_message(session_id: str, message_type: str, content: Dict[str, Any], 
                metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Save a message to the database.
    
    Args:
        session_id: UUID of the session
        message_type: Type of message (SystemMessage, HumanMessage, AIMessage, ToolMessage)
        content: Message content as dictionary
        metadata: Optional metadata dictionary
        
    Returns:
        message_id: UUID of the saved message
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Get the next sequence order for this session
            cursor.execute("""
                SELECT COALESCE(MAX(sequence_order), 0) + 1
                FROM chat_messages
                WHERE session_id = %s
            """, (session_id,))
            
            sequence_order = cursor.fetchone()[0]
            
            # Insert the message
            cursor.execute("""
                INSERT INTO chat_messages (session_id, message_type, content, sequence_order, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING message_id
            """, (
                session_id,
                message_type,
                Json(content),
                sequence_order,
                Json(metadata or {})
            ))
            
            message_id = cursor.fetchone()[0]
            
            # Update session timestamp
            cursor.execute("""
                UPDATE chat_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """, (session_id,))
            
            conn.commit()
            print(f"✅ Saved message {message_id} to session {session_id}")
            return str(message_id)
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to save message: {e}")
        raise
    finally:
        return_connection(conn)

def get_session_messages(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all messages for a session in ascending order.
    
    Args:
        session_id: UUID of the session
        limit: Optional limit on number of messages to return
        
    Returns:
        List of message dictionaries
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT message_id, session_id, message_type, content, 
                       timestamp, sequence_order, metadata
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY sequence_order ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (session_id,))
            results = cursor.fetchall()
            
            messages = []
            for row in results:
                message_dict = dict(row)
                # Convert UUID to string for JSON serialization
                message_dict['message_id'] = str(message_dict['message_id'])
                message_dict['session_id'] = str(message_dict['session_id'])
                messages.append(message_dict)
            
            print(f"✅ Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
    except Exception as e:
        print(f"❌ Failed to get session messages: {e}")
        raise
    finally:
        return_connection(conn)

def delete_session(session_id: str) -> bool:
    """
    Delete a session and all its messages.
    
    Args:
        session_id: UUID of the session
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM chat_sessions
                WHERE session_id = %s
            """, (session_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"✅ Deleted session {session_id}")
                return True
            else:
                print(f"⚠️ Session {session_id} not found")
                return False
                
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to delete session: {e}")
        raise
    finally:
        return_connection(conn)

def get_user_sessions(user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all sessions for a user.
    
    Args:
        user_id: User identifier
        limit: Optional limit on number of sessions to return
        
    Returns:
        List of session dictionaries
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT session_id, user_id, created_at, updated_at, status
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY updated_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            
            sessions = []
            for row in results:
                session_dict = dict(row)
                # Convert UUID to string for JSON serialization
                session_dict['session_id'] = str(session_dict['session_id'])
                sessions.append(session_dict)
            
            print(f"✅ Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions
            
    except Exception as e:
        print(f"❌ Failed to get user sessions: {e}")
        raise
    finally:
        return_connection(conn)

def cleanup_old_sessions(days_old: int = 30) -> int:
    """
    Clean up old sessions and their messages.
    
    Args:
        days_old: Number of days after which sessions are considered old
        
    Returns:
        Number of sessions deleted
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM chat_sessions
                WHERE updated_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND status = 'archived'
            """, (days_old,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Cleaned up {deleted_count} old sessions")
            return deleted_count
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to cleanup old sessions: {e}")
        raise
    finally:
        return_connection(conn)

# Initialize database tables when module is imported
try:
    init_database()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("Make sure PostgreSQL is running and configured correctly") 