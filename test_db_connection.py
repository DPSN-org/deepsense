#!/usr/bin/env python3
"""
Simple database connection test script.
Use this to debug connection pooling issues.
"""

import sys
import os
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_basic_connection():
    """Test basic database connection without pooling."""
    print("🔍 Testing basic connection...")
    
    import psycopg2
    
    # Database configuration
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5435'),
        'database': os.getenv('POSTGRES_DB', 'agentic_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    }
    
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Basic connection successful!")
            print(f"   PostgreSQL version: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False

def test_pool_connection():
    """Test connection pooling."""
    print("\n🔍 Testing connection pooling...")
    
    try:
        from utils.db_utils import test_connection, get_connection, return_connection
        
        # Test the connection
        if test_connection():
            print("✅ Pool connection test successful!")
            
            # Test getting and returning connections
            print("🔍 Testing connection get/return cycle...")
            for i in range(5):
                conn = get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT %s", (i,))
                    result = cursor.fetchone()[0]
                    print(f"   Test {i}: {result}")
                return_connection(conn)
                print(f"   ✅ Connection {i} returned successfully")
            
            return True
        else:
            print("❌ Pool connection test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Pool connection test failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    print("\n🔍 Testing database operations...")
    
    try:
        from utils.db_utils import create_session, get_session_info, delete_session
        
        # Create a test session
        session_id = create_session("test_user")
        print(f"✅ Created session: {session_id}")
        
        # Get session info
        session_info = get_session_info(session_id)
        print(f"✅ Session info: {session_info}")
        
        # Delete the session
        result = delete_session(session_id)
        print(f"✅ Deleted session: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting database connection tests...\n")
    
    # Test 1: Basic connection
    basic_ok = test_basic_connection()
    
    # Test 2: Pool connection
    pool_ok = test_pool_connection()
    
    # Test 3: Database operations
    ops_ok = test_database_operations()
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results:")
    print(f"   Basic Connection: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"   Pool Connection:  {'✅ PASS' if pool_ok else '❌ FAIL'}")
    print(f"   Database Ops:     {'✅ PASS' if ops_ok else '❌ FAIL'}")
    print("="*50)
    
    if basic_ok and pool_ok and ops_ok:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 