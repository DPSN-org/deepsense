#!/usr/bin/env python3
"""
Test cases for database utilities.
Tests all database functions for session management.
"""

import unittest
import uuid
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db_utils import (
    create_session,
    get_session_info,
    save_message,
    get_session_messages,
    delete_session,
    get_user_sessions,
    cleanup_old_sessions,
    init_database
)

class TestDatabaseUtils(unittest.TestCase):
    """Test cases for database utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_session_id = str(uuid.uuid4())
        self.test_user_id = "test_user_123"
        self.test_message_content = {
            "content": "Hello, this is a test message",
            "type": "human"
        }
        self.test_metadata = {
            "source": "test",
            "timestamp": "2024-01-01T12:00:00"
        }
    
    @patch('utils.db_utils.get_connection')
    def test_create_session(self, mock_get_connection):
        """Test creating a new session."""
        # Mock the database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [self.test_session_id]
        mock_get_connection.return_value = mock_conn
        
        # Test creating session with user_id
        result = create_session(self.test_user_id)
        
        # Verify the result
        self.assertEqual(result, self.test_session_id)
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_create_session_without_user_id(self, mock_get_connection):
        """Test creating a session without user_id."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [self.test_session_id]
        mock_get_connection.return_value = mock_conn
        
        result = create_session()
        
        self.assertEqual(result, self.test_session_id)
        mock_cursor.execute.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_get_session_info(self, mock_get_connection):
        """Test getting session information."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock the result as a dictionary-like object (RealDictCursor returns dict-like)
        mock_result = {
            'session_id': self.test_session_id,
            'user_id': self.test_user_id,
            'created_at': "2024-01-01T12:00:00",
            'updated_at': "2024-01-01T12:00:00",
            'status': "active"
        }
        mock_cursor.fetchone.return_value = mock_result
        mock_get_connection.return_value = mock_conn
        
        result = get_session_info(self.test_session_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['session_id'], self.test_session_id)
        self.assertEqual(result['user_id'], self.test_user_id)
        self.assertEqual(result['status'], "active")
    
    @patch('utils.db_utils.get_connection')
    def test_get_session_info_not_found(self, mock_get_connection):
        """Test getting session info for non-existent session."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_get_connection.return_value = mock_conn
        
        result = get_session_info(self.test_session_id)
        
        self.assertIsNone(result)
    
    @patch('utils.db_utils.get_connection')
    def test_save_message(self, mock_get_connection):
        """Test saving a message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock sequence order query
        mock_cursor.fetchone.side_effect = [[1], [str(uuid.uuid4())]]
        mock_get_connection.return_value = mock_conn
        
        message_id = save_message(
            self.test_session_id,
            "HumanMessage",
            self.test_message_content,
            self.test_metadata
        )
        
        self.assertIsNotNone(message_id)
        self.assertEqual(mock_cursor.execute.call_count, 3)  # sequence, insert, update
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_save_message_without_metadata(self, mock_get_connection):
        """Test saving a message without metadata."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [[1], [str(uuid.uuid4())]]
        mock_get_connection.return_value = mock_conn
        
        message_id = save_message(
            self.test_session_id,
            "AIMessage",
            self.test_message_content
        )
        
        self.assertIsNotNone(message_id)
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_get_session_messages(self, mock_get_connection):
        """Test getting session messages."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock the results with simple dictionaries
        mock_messages = [
            {
                'message_id': str(uuid.uuid4()),
                'session_id': self.test_session_id,
                'message_type': 'HumanMessage',
                'content': self.test_message_content,
                'timestamp': "2024-01-01T12:00:00",
                'sequence_order': 1,
                'metadata': {}
            },
            {
                'message_id': str(uuid.uuid4()),
                'session_id': self.test_session_id,
                'message_type': 'AIMessage',
                'content': {"content": "Response message"},
                'timestamp': "2024-01-01T12:01:00",
                'sequence_order': 2,
                'metadata': {}
            }
        ]
        mock_cursor.fetchall.return_value = mock_messages
        mock_get_connection.return_value = mock_conn
        
        messages = get_session_messages(self.test_session_id)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['message_type'], "HumanMessage")
        self.assertEqual(messages[1]['message_type'], "AIMessage")
        self.assertEqual(messages[0]['sequence_order'], 1)
        self.assertEqual(messages[1]['sequence_order'], 2)
    
    @patch('utils.db_utils.get_connection')
    def test_get_session_messages_with_limit(self, mock_get_connection):
        """Test getting session messages with limit."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_get_connection.return_value = mock_conn
        
        messages = get_session_messages(self.test_session_id, limit=5)
        
        self.assertEqual(len(messages), 0)
        # Verify the query included LIMIT
        execute_calls = mock_cursor.execute.call_args_list
        self.assertTrue(any('LIMIT' in str(call) for call in execute_calls))
    
    @patch('utils.db_utils.get_connection')
    def test_delete_session(self, mock_get_connection):
        """Test deleting a session."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 1  # One row affected
        mock_get_connection.return_value = mock_conn
        
        result = delete_session(self.test_session_id)
        
        self.assertTrue(result)
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_delete_session_not_found(self, mock_get_connection):
        """Test deleting a non-existent session."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 0  # No rows affected
        mock_get_connection.return_value = mock_conn
        
        result = delete_session(self.test_session_id)
        
        self.assertFalse(result)
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_get_user_sessions(self, mock_get_connection):
        """Test getting user sessions."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock the results as dictionary-like objects (RealDictCursor returns dict-like)
        mock_sessions = [
            {
                'session_id': self.test_session_id,
                'user_id': self.test_user_id,
                'created_at': "2024-01-01T12:00:00",
                'updated_at': "2024-01-01T12:00:00",
                'status': "active"
            }
        ]
        mock_cursor.fetchall.return_value = mock_sessions
        mock_get_connection.return_value = mock_conn
        
        sessions = get_user_sessions(self.test_user_id)
        
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['user_id'], self.test_user_id)
        self.assertEqual(sessions[0]['session_id'], self.test_session_id)
    
    @patch('utils.db_utils.get_connection')
    def test_cleanup_old_sessions(self, mock_get_connection):
        """Test cleaning up old sessions."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 5  # Five sessions deleted
        mock_get_connection.return_value = mock_conn
        
        deleted_count = cleanup_old_sessions(days_old=30)
        
        self.assertEqual(deleted_count, 5)
        mock_conn.commit.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_database_error_handling(self, mock_get_connection):
        """Test error handling in database operations."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        mock_get_connection.return_value = mock_conn
        
        # Test that exceptions are raised
        with self.assertRaises(Exception):
            create_session(self.test_user_id)
        
        mock_conn.rollback.assert_called()
    
    @patch('utils.db_utils.get_connection')
    def test_init_database(self, mock_get_connection):
        """Test database initialization."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        # This should not raise an exception
        init_database()
        
        # Verify that CREATE TABLE statements were executed
        execute_calls = mock_cursor.execute.call_args_list
        create_table_calls = [call for call in execute_calls if 'CREATE TABLE' in str(call)]
        self.assertGreater(len(create_table_calls), 0)
        
        mock_conn.commit.assert_called()

def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDatabaseUtils))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 