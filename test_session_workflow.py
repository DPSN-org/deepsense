#!/usr/bin/env python3
"""
Test case for complete session workflow:
1. Create user session via API server
2. Process user query (first call)
3. Process user query again (second call) with same session ID
"""

import sys
import os
import json
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SessionWorkflowTester:
    """Test class for session workflow testing."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session_id = None
        self.user_id = "test_user_workflow"
        
    def test_create_session(self) -> bool:
        """Test creating a new user session via API."""
        print("🔍 Testing session creation...")
        
        try:
            # Create session via API
            response = requests.post(
                f"{self.base_url}/sessions",
                json={"user_id": self.user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                print(f"✅ Session created successfully: {self.session_id}")
                print(f"   User ID: {data.get('user_id')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Failed to create session: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False
    
    def test_get_session_info(self) -> bool:
        """Test getting session information."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
            
        print(f"🔍 Testing get session info for {self.session_id}...")
        
        try:
            response = requests.get(f"{self.base_url}/sessions/{self.session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session info retrieved:")
                print(f"   Session ID: {data.get('session_id')}")
                print(f"   User ID: {data.get('user_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Created: {data.get('created_at')}")
                return True
            else:
                print(f"❌ Failed to get session info: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting session info: {e}")
            return False
    
    def test_process_user_query(self, query: str, query_number: int) -> bool:
        """Test processing a user query."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
            
        print(f"🔍 Testing process user query #{query_number}...")
        print(f"   Query: {query}")
        print(f"   Session ID: {self.session_id}")
        
        try:
            # Process query via API
            response = requests.post(
                f"{self.base_url}/query",
                json={
                    "query": query,
                    "session_id": self.session_id,
                    "user_id": self.user_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Query #{query_number} processed successfully")
                print(f"   Response session ID: {data.get('session_id')}")
                print(f"   Response: {data.get('response', '')[:200]}...")
                return True
            else:
                print(f"❌ Failed to process query #{query_number}: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing query #{query_number}: {e}")
            return False
    
    def test_get_session_messages(self, expected_count: int = None) -> bool:
        """Test getting session messages."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
            
        print(f"🔍 Testing get session messages for {self.session_id}...")
        
        try:
            response = requests.get(f"{self.base_url}/sessions/{self.session_id}/messages")
            
            if response.status_code == 200:
                messages = response.json()  # API returns list directly
                print(f"✅ Retrieved {len(messages)} messages:")
                
                for i, msg in enumerate(messages):
                    msg_type = msg.get("message_type", "Unknown")
                    content = msg.get("content", {}).get("content", "No content")
                    print(f"   {i+1}. {msg_type}: {content[:100]}...")
                
                return True
            else:
                print(f"❌ Failed to get session messages: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting session messages: {e}")
            return False
    
    def test_get_session_messages_full(self) -> bool:
        """Test getting all session messages including nested subgraphs."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
            
        print(f"🔍 Testing get full session messages for {self.session_id}...")
        
        try:
            response = requests.get(f"{self.base_url}/sessions/{self.session_id}/messages/full")
            
            if response.status_code == 200:
                messages = response.json()  # API returns list directly
                print(f"✅ Retrieved {len(messages)} full messages (including nested subgraphs):")
                
                for i, msg in enumerate(messages):
                    msg_type = msg.get("message_type", "Unknown")
                    content = msg.get("content", {}).get("content", "No content")
                    metadata = msg.get("metadata", {})
                    nested = metadata.get("nested_subgraph", False)
                    nested_indicator = " [NESTED]" if nested else ""
                    print(f"   {i+1}. {msg_type}{nested_indicator}: {content[:100]}...")
                
                return True
            else:
                print(f"❌ Failed to get full session messages: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting full session messages: {e}")
            return False
    
    def test_delete_session(self) -> bool:
        """Test deleting the session."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
            
        print(f"🔍 Testing delete session {self.session_id}...")
        
        try:
            response = requests.delete(f"{self.base_url}/sessions/{self.session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session deleted successfully")
                print(f"   Deleted session ID: {data.get('session_id')}")
                return True
            else:
                print(f"❌ Failed to delete session: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting session: {e}")
            return False
    
    def run_complete_workflow_test(self) -> bool:
        """Run the complete session workflow test."""
        print("🚀 Starting complete session workflow test...")
        print("=" * 60)
        
        test_results = []
        
        # Step 1: Create session
        print("\n📋 Step 1: Create User Session")
        print("-" * 40)
        result1 = self.test_create_session()
        test_results.append(("Create Session", result1))
        
        if not result1:
            print("❌ Cannot proceed without session creation")
            return False
        
        # Step 2: Get session info
        print("\n📋 Step 2: Get Session Info")
        print("-" * 40)
        result2 = self.test_get_session_info()
        test_results.append(("Get Session Info", result2))
        
        # Step 3: First query
        print("\n📋 Step 3: First User Query")
        print("-" * 40)
        query1 = "what is the account balance for Solana wallet xyz"
        result3 = self.test_process_user_query(query1, 1)
        test_results.append(("First Query", result3))
        
        # Step 4: Check messages after first query
        print("\n📋 Step 4: Check Messages After First Query")
        print("-" * 40)
        result4 = self.test_get_session_messages()
        test_results.append(("Messages After Query 1", result4))
        
        # Step 5: Second query (same session)
        print("\n📋 Step 5: Second User Query (Same Session)")
        print("-" * 40)
        query2 = "I meant for all tokens in the wallet"
        result5 = self.test_process_user_query(query2, 2)
        test_results.append(("Second Query", result5))
        
        # Step 6: Check messages after second query
        print("\n📋 Step 6: Check Messages After Second Query")
        print("-" * 40)
        result6 = self.test_get_session_messages()
        test_results.append(("Messages After Query 2", result6))
        
        # Step 7: Check full messages (including nested subgraphs)
        print("\n📋 Step 7: Check Full Messages (Including Nested Subgraphs)")
        print("-" * 40)
        result7 = self.test_get_session_messages_full()
        test_results.append(("Full Messages", result7))
        
        # Step 8: Cleanup - Delete session
        print("\n📋 Step 8: Cleanup - Delete Session")
        print("-" * 40)
        result8 = self.test_delete_session()
        test_results.append(("Delete Session", result8))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Session workflow is working correctly.")
            return True
        else:
            print("💥 Some tests failed. Check the output above for details.")
            return False

def main():
    """Main test runner."""
    print("🧪 Session Workflow Test Suite")
    print("=" * 60)
    
    # Check if API server is running
   
    
    # Run the test
    tester = SessionWorkflowTester()
    success = tester.run_complete_workflow_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 