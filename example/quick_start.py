"""
Quick start example showing how to use DeepSense Framework
"""

import os
from deepsense import Workflow, MongoDBCheckpointer
from example.workflow_instance import invoke_workflow

# Example 1: Simple workflow invocation
def example_simple_query():
    """Simple example of invoking the workflow."""
    print("Example 1: Simple Query")
    print("-" * 50)
    
    result = invoke_workflow("What is the current price of bitcoin?")
    
    if result and 'messages' in result:
        last_message = result['messages'][-1]
        print(f"Response: {last_message.content}")
    print()

# Example 2: Workflow with session
def example_with_session():
    """Example with session management."""
    print("Example 2: Query with Session")
    print("-" * 50)
    
    # Create checkpointer
    checkpointer = MongoDBCheckpointer(
        connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        database_name="deepsense_example"
    )
    
    # Create session
    session_id = checkpointer.create_session(user_id="demo_user")
    print(f"Created session: {session_id}")
    
    # First query
    result1 = invoke_workflow("What is bitcoin?", session_id=session_id)
    print(f"First response: {result1['messages'][-1].content[:100]}...")
    
    # Second query (with context)
    result2 = invoke_workflow("What about ethereum?", session_id=session_id)
    print(f"Second response: {result2['messages'][-1].content[:100]}...")
    
    # Get all messages
    messages = checkpointer.get_messages(session_id)
    print(f"\nTotal messages in session: {len(messages)}")
    print()

# Example 3: Custom workflow
def example_custom_workflow():
    """Example of creating a custom workflow."""
    print("Example 3: Custom Workflow")
    print("-" * 50)
    
    from langchain_core.tools import Tool
    
    # Create a simple custom tool
    def hello_tool(name: str) -> str:
        """Say hello to someone."""
        return f"Hello, {name}!"
    
    custom_tool = Tool(
        name="hello",
        description="Say hello to someone",
        func=hello_tool
    )
    
    # Create workflow with custom tool
    checkpointer = MongoDBCheckpointer(
        connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        database_name="deepsense_example"
    )
    
    workflow = Workflow(
        checkpointer=checkpointer,
        custom_tools=[custom_tool]
    )
    
    result = workflow.invoke("Use the hello tool to greet Alice")
    print(f"Response: {result['messages'][-1].content}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("DeepSense Framework - Quick Start Examples")
    print("=" * 50)
    print()
    
    # Make sure MongoDB is running and env vars are set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print()
    
    try:
        example_simple_query()
        example_with_session()
        example_custom_workflow()
        
        print("=" * 50)
        print("✅ Examples completed!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. MongoDB is running (mongodb://localhost:27017/)")
        print("2. OPENAI_API_KEY is set")
        print("3. All dependencies are installed")

