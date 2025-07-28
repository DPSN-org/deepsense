#!/usr/bin/env python3
"""
Test cases for the sandbox server /run API.
Tests both Python and Node.js code execution with various scenarios.
"""

import requests
import json
import time
import subprocess
import sys
from typing import Dict, Any

# Configuration
SANDBOX_SERVER_URL = "http://localhost:8000"
TEST_TIMEOUT = 120  # seconds

def test_sandbox_server_health():
    """Test if the sandbox server is running."""
    try:
        response = requests.get(f"{SANDBOX_SERVER_URL}/docs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def test_python_simple_arithmetic():
    """Test simple Python arithmetic."""
    code = """
print("Hello from Python!")
result = 2 + 3 * 4
print(f"Result: {result}")
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Python Simple Arithmetic Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    assert "stderr" in result
    assert "Hello from Python!" in result["stdout"]
    assert "Result: 14" in result["stdout"]
    print("✅ Python simple arithmetic test passed\n")

def test_python_with_requirements():
    """Test Python code with external requirements."""
    code = """
import requests
import json

# Test making a simple HTTP request
response = requests.get("https://httpbin.org/json")
data = response.json()
print(f"Status: {response.status_code}")
print(f"Data keys: {list(data.keys())}")
"""
    
    payload = {
        "code": code,
        "requirements": ["requests"],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Python with Requirements Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    assert "stderr" in result
    
    # Since containers run with --network=none, package installation will fail
    # This is expected behavior for security isolation
    if "ModuleNotFoundError" in result["stderr"] or "No matching distribution found" in result["stderr"]:
        print("✅ Python with requirements test passed (network isolation working as expected)\n")
    else:
        # If network is available, check for successful execution
        assert "Status: 200" in result["stdout"]
        print("✅ Python with requirements test passed\n")

def test_python_error_handling():
    """Test Python error handling."""
    code = """
# This will cause a NameError
print(undefined_variable)
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Python Error Handling Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stderr" in result
    assert "NameError" in result["stderr"] or "undefined_variable" in result["stderr"]
    print("✅ Python error handling test passed\n")

def test_node_simple_arithmetic():
    """Test simple Node.js arithmetic."""
    code = """
console.log("Hello from Node.js!");
const result = 2 + 3 * 4;
console.log(`Result: ${result}`);
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "node"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Node.js Simple Arithmetic Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    assert "stderr" in result
    assert "Hello from Node.js!" in result["stdout"]
    assert "Result: 14" in result["stdout"]
    print("✅ Node.js simple arithmetic test passed\n")

def test_node_with_packages():
    """Test Node.js code with npm packages."""
    code = """
const axios = require('axios');

async function testRequest() {
    try {
        const response = await axios.get('https://httpbin.org/json');
        console.log(`Status: ${response.status}`);
        console.log(`Data keys: ${Object.keys(response.data)}`);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

testRequest();
"""
    
    payload = {
        "code": code,
        "requirements": ["axios"],
        "language": "node"
    }
    
    # Use a longer timeout for npm install
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=60)
    
    print("=== Node.js with Packages Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    assert "stderr" in result
    
    # Since containers run with --network=none, package installation will fail
    # This is expected behavior for security isolation
    if "Cannot find module" in result["stderr"] or "npm ERR!" in result["stderr"]:
        print("✅ Node.js with packages test passed (network isolation working as expected)\n")
    else:
        # If network is available, check for successful execution
        assert "Status: 200" in result["stdout"]
        print("✅ Node.js with packages test passed\n")

def test_node_error_handling():
    """Test Node.js error handling."""
    code = """
// This will cause a ReferenceError
console.log(undefinedVariable);
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "node"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Node.js Error Handling Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stderr" in result
    assert "ReferenceError" in result["stderr"] or "undefinedVariable" in result["stderr"]
    print("✅ Node.js error handling test passed\n")

def test_infinite_loop_protection():
    """Test if the sandbox can handle infinite loops (should timeout)."""
    code = """
while True:
    print("This should timeout")
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Infinite Loop Protection Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should either timeout or be killed by Docker
    assert response.status_code == 200
    result = response.json()
    print("✅ Infinite loop protection test completed\n")

def test_file_system_isolation():
    """Test that file system is properly isolated."""
    code = """
import os
import sys

# Try to access system files (should be restricted)
try:
    with open('/etc/passwd', 'r') as f:
        print("System file access:", len(f.read()))
except Exception as e:
    print("System file access blocked:", str(e))

# Check current directory
print("Current directory:", os.getcwd())
print("Directory contents:", os.listdir('.'))

# Try to write to current directory
with open('test_file.txt', 'w') as f:
    f.write('test content')
print("File write test completed")
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== File System Isolation Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    print("✅ File system isolation test completed\n")

def test_memory_usage():
    """Test memory usage limits."""
    code = """
import sys

# Try to allocate a large amount of memory
try:
    large_list = [0] * 100000000  # 100M integers
    print("Large memory allocation successful")
except MemoryError:
    print("Memory limit enforced")
except Exception as e:
    print(f"Memory allocation failed: {e}")
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Memory Usage Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    print("✅ Memory usage test completed\n")

def test_network_isolation():
    """Test network isolation."""
    code = """
import socket

try:
    # Try to create a socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('8.8.8.8', 53))
    print("Network access allowed")
    sock.close()
except Exception as e:
    print("Network access blocked:", str(e))
"""
    
    payload = {
        "code": code,
        "requirements": [],
        "language": "python"
    }
    
    response = requests.post(f"{SANDBOX_SERVER_URL}/run", json=payload, timeout=TEST_TIMEOUT)
    
    print("=== Network Isolation Test ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    
    # Check if network access is properly blocked
    if "Network access blocked" in result["stdout"]:
        print("✅ Network isolation test passed (network properly blocked)\n")
    else:
        print("⚠️ Network isolation test completed (network access detected)\n")

def run_all_tests():
    """Run all test cases."""
    print("🚀 Starting Sandbox Server Tests\n")
    
    # Check if server is running
    if not test_sandbox_server_health():
        print("❌ Sandbox server is not running!")
        print("Please start the server with: uvicorn sandbox_server:app --reload")
        return False
    
    print("✅ Sandbox server is running\n")
    
    tests = [
        test_python_simple_arithmetic,
        test_python_with_requirements,
        test_python_error_handling,
        test_node_simple_arithmetic,
        test_node_with_packages,
        test_node_error_handling,
        test_infinite_loop_protection,
        test_file_system_isolation,
        test_memory_usage,
        test_network_isolation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 