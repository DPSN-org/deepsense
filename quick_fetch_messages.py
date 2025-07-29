#!/usr/bin/env python3
"""
Quick script to fetch and print session messages from the database.
Edit the SESSION_ID variable below to fetch messages for a specific session.
"""

import sys
import json
from datetime import datetime

# Add the current directory to the path so we can import utils
sys.path.append('.')

from utils.db_utils import get_session_messages, get_session_info, test_connection

# Edit this variable to fetch messages for a specific session
SESSION_ID = "your-session-id-here"  # Replace with actual session ID

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for better readability."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def print_message(message):
    """Print a single message in a formatted way."""
    print(f"\n{'='*80}")
    print(f"Message ID: {message['message_id']}")
    print(f"Type: {message['message_type']}")
    print(f"Sequence: {message['sequence_order']}")
    print(f"Timestamp: {format_timestamp(message['timestamp'])}")
    
    # Print content
    content = message['content']
    if isinstance(content, dict):
        if 'content' in content:
            print(f"Content: {content['content']}")
        else:
            print(f"Content: {json.dumps(content, indent=2)}")
    else:
        print(f"Content: {content}")
    
    # Print metadata if present
    if message.get('metadata'):
        print(f"Metadata: {json.dumps(message['metadata'], indent=2)}")
    
    print(f"{'='*80}")

def main():
    print("🔧 Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your database configuration.")
        return
    
    print("✅ Database connection successful")
    
    if SESSION_ID == "your-session-id-here":
        print("❌ Please edit the SESSION_ID variable in this script with an actual session ID")
        return
    
    # Check if session exists
    session_info = get_session_info(SESSION_ID)
    if not session_info:
        print(f"❌ Session {SESSION_ID} not found")
        return
    
    print(f"📋 Session Info:")
    print(f"   Session ID: {session_info['session_id']}")
    print(f"   User ID: {session_info.get('user_id', 'N/A')}")
    print(f"   Created: {format_timestamp(session_info['created_at'])}")
    print(f"   Updated: {format_timestamp(session_info['updated_at'])}")
    print(f"   Status: {session_info['status']}")
    
    # Fetch messages
    messages = get_session_messages(SESSION_ID)
    
    if not messages:
        print(f"\n📭 No messages found for session {SESSION_ID}")
        return
    
    print(f"\n📨 Found {len(messages)} messages:")
    
    # Prepare data for JSON file
    log_data = {
        "session_info": {
            "session_id": session_info['session_id'],
            "user_id": session_info.get('user_id', 'N/A'),
            "created_at": session_info['created_at'],
            "updated_at": session_info['updated_at'],
            "status": session_info['status']
        },
        "messages": []
    }
    
    # Process each message
    for message in messages:
        # Print message to console
        print_message(message)
        
        # Add message to log data
        log_data["messages"].append({
            "message_id": message['message_id'],
            "session_id": message['session_id'],
            "message_type": message['message_type'],
            "content": message['content'],
            "timestamp": message['timestamp'],
            "sequence_order": message['sequence_order'],
            "metadata": message.get('metadata', {})
        })
    
    # Write to JSON file
    try:
        with open('message_log.json', 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Messages written to message_log.json")
        print(f"📊 Total messages logged: {len(log_data['messages'])}")
    except Exception as e:
        print(f"❌ Error writing to message_log.json: {e}")

if __name__ == "__main__":
    main() 