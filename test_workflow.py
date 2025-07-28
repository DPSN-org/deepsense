import sys
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.assistant_graph import process_query
from graph.planner_react_agent import run_planner_react_agent
from utils.db_utils import create_session, get_session_info, get_session_messages, save_message

SOLANA_WALLET = ""

def setup_test_session():
    """Create a test session for workflow testing."""
    try:
        # Create a new session for testing
        session_id = create_session("test_user_workflow")
        print(f"✅ Created test session: {session_id}")
        
        # Verify session was created
        session_info = get_session_info(session_id)
        if session_info:
            print(f"✅ Session info: {session_info}")
        else:
            print("❌ Failed to get session info")
            return None
            
        return session_id
    except Exception as e:
        print(f"❌ Failed to create test session: {e}")
        return None

def cleanup_test_session(session_id):
    """Clean up test session after testing."""
    if session_id:
        try:
            from utils.db_utils import delete_session
            result = delete_session(session_id)
            if result:
                print(f"✅ Cleaned up test session: {session_id}")
            else:
                print(f"⚠️ Failed to clean up test session: {session_id}")
        except Exception as e:
            print(f"❌ Error cleaning up test session: {e}")

def save_query_as_human_message(session_id: str, query: str) -> bool:
    """Save the query as a human message to the database."""
    try:
        # Save the query as a HumanMessage
        message_id = save_message(
            session_id=session_id,
            message_type="HumanMessage",
            content={"content": query},
            metadata={"source": "test_workflow", "test_type": "manual_save"}
        )
        print(f"✅ Saved query as HumanMessage: {message_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save query as HumanMessage: {e}")
        return False

def run_tests():
    """Run workflow tests with session management."""
    print("🚀 Starting workflow tests with session management...")
    
    # Setup test session
    session_id = setup_test_session()
    if not session_id:
        print("❌ Cannot proceed without valid session")
        return
    
    try:
        # Test 1: Simple query to test message cleanup
        query = f"what is the account balance for Solana wallet {SOLANA_WALLET}"
        # query ="Execute Python code that prints numbers 1 to 5."
        print(f"\n📝 Query: {query}")
        print(f"🆔 Session ID: {session_id}")
        
        # Save query as human message before running planner agent
        print(f"\n💾 Saving query as HumanMessage...")
        if not save_query_as_human_message(session_id, query):
            print("❌ Failed to save query, but continuing with test...")
        
        # Show messages after saving query
        print(f"\n📋 Messages after saving query:")
        
        # Run planner agent with session
        print(f"\n🤖 Running planner agent...")
        result = run_planner_react_agent(query, session_id=session_id)
        
        # Display result
        if result and 'messages' in result and result['messages']:
            last_message = result['messages'][-1]
            print(f"✅ Result: {last_message.content}")
        else:
            print("❌ No result or messages found")
        
        # Show session messages after planner agent
        print(f"\n📋 Session messages after planner agent:")
         
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Cleanup test session
        cleanup_test_session(session_id)

if __name__ == "__main__":
    run_tests() 