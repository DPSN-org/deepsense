# Sandbox Server Test Suite

This directory contains comprehensive test cases for the sandbox server's `/run` API.

## Prerequisites

Before running the tests, make sure you have:

1. **Docker installed and running**
2. **Docker images built**:
   ```bash
   docker build -t sandbox-python -f Dockerfile.python .
   docker build -t sandbox-node -f Dockerfile.node .
   ```
3. **Sandbox server running**:
   ```bash
   uvicorn sandbox_server:app --reload
   ```

## Test Files

### 1. `test_sandbox_quick.py` - Quick Basic Test
A simple test to verify basic functionality.

**Run with:**
```bash
python test_sandbox_quick.py
```

**What it tests:**
- Basic Python code execution
- Basic Node.js code execution
- Simple arithmetic operations

### 2. `test_sandbox_server.py` - Comprehensive Test Suite
A full test suite covering various scenarios.

**Run with:**
```bash
python test_sandbox_server.py
```

**What it tests:**

#### Python Tests:
- ✅ Simple arithmetic operations
- ✅ Code with external requirements (pip packages)
- ✅ Error handling (NameError, etc.)

#### Node.js Tests:
- ✅ Simple arithmetic operations  
- ✅ Code with npm packages
- ✅ Error handling (ReferenceError, etc.)

#### Security & Isolation Tests:
- ✅ Infinite loop protection
- ✅ File system isolation
- ✅ Memory usage limits
- ✅ Network isolation

## Test Scenarios Explained

### 1. Basic Functionality Tests
- **Purpose**: Verify that simple code execution works
- **Example**: `print("Hello")` and basic arithmetic
- **Expected**: Correct output in stdout

### 2. Package Installation Tests
- **Purpose**: Verify that external dependencies can be installed
- **Example**: Python with `requests`, Node.js with `axios`
- **Expected**: Packages install successfully and code runs

### 3. Error Handling Tests
- **Purpose**: Verify that errors are properly captured
- **Example**: Undefined variables, syntax errors
- **Expected**: Errors appear in stderr

### 4. Security Tests
- **Purpose**: Verify sandbox isolation and security
- **Examples**:
  - File system access restrictions
  - Network access blocking
  - Memory limits enforcement
  - Infinite loop timeout

## Expected Test Results

### Successful Test Output:
```
🚀 Starting Sandbox Server Tests

✅ Sandbox server is running

=== Python Simple Arithmetic Test ===
Status Code: 200
Response: {'stdout': 'Hello from Python!\nResult: 14\n', 'stderr': ''}
✅ Python simple arithmetic test passed

=== Node.js Simple Arithmetic Test ===
Status Code: 200
Response: {'stdout': 'Hello from Node.js!\nResult: 14\n', 'stderr': ''}
✅ Node.js simple arithmetic test passed

📊 Test Results: 10 passed, 0 failed
🎉 All tests passed!
```

### Common Issues and Solutions

#### 1. "Sandbox server is not running"
**Solution**: Start the server
```bash
uvicorn sandbox_server:app --reload
```

#### 2. "Docker daemon not running"
**Solution**: Start Docker
```bash
sudo service docker start
```

#### 3. "Image not found" errors
**Solution**: Build the Docker images
```bash
docker build -t sandbox-python -f Dockerfile.python .
docker build -t sandbox-node -f Dockerfile.node .
```

#### 4. Network isolation test fails
**Expected**: The test should show "Network access blocked" - this is correct behavior for a secure sandbox.

#### 5. Memory test shows allocation successful
**Note**: This might happen if your system has enough memory. The test verifies the sandbox doesn't crash.

## API Endpoint Details

### POST `/run`

**Request Body:**
```json
{
  "code": "print('Hello World')",
  "requirements": ["requests"],
  "language": "python"
}
```

**Response:**
```json
{
  "stdout": "Hello World\n",
  "stderr": ""
}
```

**Parameters:**
- `code` (string): The source code to execute
- `requirements` (array): List of packages to install
- `language` (string): Either "python" or "node"

## Security Features Tested

1. **Container Isolation**: Each execution runs in a separate Docker container
2. **Network Isolation**: Containers run with `--network=none`
3. **Resource Limits**: 256MB memory, 0.5 CPU cores
4. **File System Isolation**: Only `/home/sandbox` is accessible
5. **User Isolation**: Runs as non-root `sandbox` user
6. **Automatic Cleanup**: Containers are removed after execution

## Performance Notes

- **Timeout**: Tests have a 30-second timeout
- **Memory**: Each container limited to 256MB
- **CPU**: Each container limited to 0.5 cores
- **Cleanup**: Containers are automatically removed after execution

## Troubleshooting

### Test Hangs or Times Out
- Check if Docker containers are stuck: `docker ps -a`
- Clean up stuck containers: `docker rm -f $(docker ps -aq)`
- Restart Docker: `sudo service docker restart`

### Permission Denied Errors
- Ensure Docker is running: `sudo service docker status`
- Add user to docker group: `sudo usermod -aG docker $USER`
- Log out and back in, or run: `newgrp docker`

### Package Installation Fails
- Check internet connectivity in containers
- Verify package names are correct
- Check if packages are available in the base images

## Contributing

To add new tests:

1. Create a new test function in `test_sandbox_server.py`
2. Follow the naming convention: `test_<description>()`
3. Add assertions to verify expected behavior
4. Add the test to the `tests` list in `run_all_tests()`
5. Update this README with test description 