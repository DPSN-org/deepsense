# DPSN-AGENTIC-FRAMEWORK 

An agentic LLM orchestration framework built on DPSN  giving your AI agents a real-time edge. DPSN enables agents to access, stream, and act on live or most recent data for answering user queries, executing tasks, or chaining actions with awareness of up-to-date context.

## Prerequisites

- Ubuntu 20.04 or later
- Python 3.8 or later
- Git
- Docker (optional, for containerized deployment)

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd dpsn-agentic-framework
```

### 2. Set Up Virtual Environment (Ubuntu)

#### Install Python and pip (if not already installed)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Create and activate virtual environment
```bash
# Create virtual environment
python3 -m venv test

# Activate virtual environment
source env/bin/activate

# Verify activation (you should see (test) in your prompt)
which python
# Should show: /path/to/langgraph-sample/env/bin/python
```

### 3. Install Dependencies

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all packages from requirements.txt
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL 16 Database

The application requires PostgreSQL 16 for session management and message persistence. Follow these steps to set up the database:

#### Install PostgreSQL 16 on Ubuntu

```bash
# Update package list
sudo apt update

# Install PostgreSQL 16
sudo apt install postgresql-16 postgresql-contrib-16

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

#### Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database user (replace 'your_username' and 'your_password' with your desired credentials)
CREATE USER your_username WITH PASSWORD 'your_password';

# Create database
CREATE DATABASE agentic_db OWNER your_username;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agentic_db TO your_username;

# Exit PostgreSQL
\q
```

#### Test Database Connection

```bash
# Test connection with your credentials
psql -h localhost -U your_username -d agentic_db -p 5432

# You should see the PostgreSQL prompt. Type \q to exit.
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add your API keys and database configuration:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=your_s3_bucket_name

# Tool-specific keys
HELIUS_API_KEY=your_helius_key_here

# Weather API (optional)
OPENWEATHER_API_KEY=your_openweather_key

# Flight API (optional)
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

### 6. Install Docker

#### Install Docker on Ubuntu
```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
sudo apt update

# Install Docker Engine
sudo apt install docker-ce docker-ce-cli containerd.io

# Add your user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Log out and log back in for group changes to take effect
# Or run: newgrp docker
```

#### Verify Docker installation
```bash
docker --version
docker run hello-world
```

### 7. Build Docker Sandbox Images

The project includes Dockerfiles for sandbox environments that provide isolated execution environments for code.

#### Build Docker Sandbox Images

```bash
# Build Python sandbox image
docker build -f Dockerfile.python -t sandbox-python .

# Build Node.js sandbox image  
docker build -f Dockerfile.node -t sandbox-node .

# Verify images were created
docker images | grep sandbox
```




#### Remove images (optional)
```bash
docker rmi sandbox-python sandbox-node
```



### 8. Running the Application

#### Activate Virtual Environment
```bash
# Always activate virtual environment before running any commands
source env/bin/activate
```

#### Run Sandbox Tool with Uvicorn

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Run sandbox tool server
uvicorn sandbox_server:app --host 0.0.0.0 --port 8000 --reload
```

The sandbox tool will be available at `http://localhost:8001`

#### Run Test Workflow

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Run the test workflow
python test_workflow.py
```

This will test the main planner-react agent workflow with a sample query.

#### Run API Server

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Run the main API server
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

The API server will be available at `http://localhost:8001`

#### API Endpoints

Once the server is running, you can access:

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Available Tools**: `http://localhost:8000/tools`
- **Query Processing**: `POST http://localhost:8000/query`

### 9. Docker Deployment (Optional)

#### Build and Run with Docker

```bash
# Build the Python Docker image
docker build -f Dockerfile.python -t langgraph-api .

# Run the container
docker run -p 8000:8000 --env-file .env langgraph-api
```

#### Using Docker Compose (if you have a docker-compose.yml)

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d
```

### 10. Test LangGraph Workflow

#### Test Basic Workflow
```bash
# Run the test workflow
python test_workflow.py
```

#### Test Session Management
```bash
# Test complete session workflow with database
python test_session_workflow.py
```

This will test:
- Session creation via API
- Message persistence to database
- Session history retrieval
- Multiple queries in the same session
- Session cleanup



**Port Already in Use:**
```bash
# Check what's using the port
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

**Database Connection Issues:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Restart PostgreSQL if needed
sudo systemctl restart postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Test database connection
psql -h localhost -U your_username -d agentic_db -p 5432
```

**Database Schema Issues:**
```bash
# The application will automatically create tables on first run
# If you need to manually initialize the database:
python3 -c "from utils.db_utils import init_database; init_database()"
```



### 11. Project Structure

```
dpsn-agentic-framework/
├── api/                   # FastAPI server implementation
├── graph/                 # Main workflow definitions
├── tools/                 # Tool implementations
├── utils/                 # Utility modules
└── sanbox_runner.js            # This file
└── sanbox_runner.py            # This file
└── sanbox_server.py            # This file
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── Dockerfile.python      # Python Docker configuration
├── Dockerfile.node        # Node.js Docker configuration
└── README.md             # This file
```

