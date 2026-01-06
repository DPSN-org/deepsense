# DeepSense Framework

An agentic LLM orchestration framework designed to provide analytical insights from connected datasources through human queries. DeepSense enables developers to build AI agents that can query multiple data sources, analyze data, execute code securely, and deliver actionable insights in natural language.

## Purpose

DeepSense is designed to transform human queries into analytical insights by:

- **Connecting Multiple Data Sources**: Unified interface for accessing REST APIs, RPC endpoints, blockchain data, financial APIs, and external services
- **Providing Analytical Insights**: AI agents analyze data from connected datasources to answer questions, generate reports, and provide insights
- **Processing Human Queries**: Natural language queries are interpreted and executed across multiple datasources to deliver comprehensive answers
- **Executing Code Securely**: Built-in sandbox tool for running LLM-generated Python and Node.js code for data analysis and visualization
- **Maintaining Context**: MongoDB-based checkpointing for session state persistence and workflow resumption across conversations
- **Handling Large Outputs**: Automatic chunking and schema discovery for processing large datasets and tool outputs
- **Supporting Multiple LLMs**: Dynamic configuration for OpenAI, Anthropic, and Google Gemini models
- **Extending Easily**: Declarative tool creation from datasource methods using `@tool` decorator

## Key Features

### 🎯 Core Capabilities

- **Workflow Orchestration**: LangGraph-based workflow engine 
- **Declarative Tool Creation**: Define tools directly in datasource methods using `@tool` decorator
- **Unified Tool System**: Multiple datasource methods can be grouped into unified tools with action parameters
- **Automatic Schema Generation**: Input schemas auto-generated from method signatures
- **Sandbox Tool**: Pre-configured secure code execution environment (Python 3.11, Node.js 20)
- **MongoDB Checkpointing**: Persistent workflow state for session management and resumption
- **Chunking & Summarization**: Mandatory summarizer graph for handling large outputs
- **User Action Detection**: Automatic collection of user actions from tool outputs
- **Dynamic LLM Support**: Configurable LLM providers (OpenAI, Anthropic, Google)
- **Environment Auto-loading**: Automatic `.env` file loading on import

For detailed architecture and component documentation, see [architecture.md](architecture.md).

## Framework Structure

```
deepsense/
├── __init__.py              # Framework exports and .env auto-loading
├── datasource.py            # DataSource base class, @tool decorator, DataSourceManager
├── workflow.py              # Workflow orchestration engine
├── checkpointer.py          # MongoDB checkpointer for state persistence
├── summarizer_graph.py      # Chunking and schema discovery
├── system_prompt.py         # Default system prompt
├── agents.py                # Base agent class
├── sandbox/                 # Secure code execution
│   ├── server.py            # FastAPI sandbox server
│   ├── runner.py            # Python code runner
│   ├── runner.js            # Node.js code runner
│   ├── Dockerfile.python    # Python 3.11 Docker image
│   └── Dockerfile.node      # Node.js 20 Docker image
└── utils/                   # Framework utilities
    ├── token_utils.py       # Token counting and chunking
    └── s3_utils.py          # AWS S3 integration
```

See [architecture.md](architecture.md) for detailed component architecture and interactions.

## Installation

### Prerequisites

- Python 3.8 or later
- MongoDB (for checkpointing)
- Docker (optional, for sandbox tool)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root (automatically loaded on import):

```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai  # or "anthropic", "google"

# MongoDB
MONGODB_URI=mongodb://localhost:27017/

# Sandbox (optional)
SANDBOX_URL=http://localhost:8000/run

# AWS S3 (optional, for large output storage)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_BUCKET=your_bucket_name
AWS_REGION=us-east-1
```

## Quick Start

### 1. Create a Datasource

```python
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any

class CryptoDataSource(DataSource):
    """Example datasource for cryptocurrency price data."""
    def __init__(self):
        config = DataSourceConfig(
            name="crypto_api",
            rest_url="https://api.coingecko.com/api/v3",
            headers={"Accept": "application/json"}
        )
        super().__init__(config)
    
    @tool(name="crypto_data", description="Get cryptocurrency price and market data")
    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price and market data for a cryptocurrency."""
        return self.get("/simple/price", {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        })
    
    def health_check(self) -> bool:
        return True
```

### 2. Create a Workflow Instance

```python
from deepsense import Workflow, MongoDBCheckpointer
from deepsense.datasource import DataSourceManager

# Register datasource
datasource_manager = DataSourceManager()
crypto_source = CryptoDataSource()
datasource_manager.register_source("crypto_api", crypto_source)

# Create tools from datasource
tools = crypto_source.get_tools()  # Automatically creates LangChain tools

# Initialize checkpointer
checkpointer = MongoDBCheckpointer(
    connection_string="mongodb://localhost:27017/",
    database_name="deepsense"
)

# Create workflow
workflow = Workflow(
    checkpointer=checkpointer,
    llm_model="gpt-4o",
    llm_provider="openai",
    api_key="your-api-key",
    custom_tools=tools,
    chunking_threshold=15000
)
```

### 3. Invoke the Workflow

```python
# Invoke with an analytical query
result = workflow.invoke(
    query="What is the current price of bitcoin and how has it changed in the last 24 hours?",
    session_id="session-123"
)

# Extract response
if result and 'messages' in result:
    last_message = result['messages'][-1]
    print(last_message.content)

# Extract user actions (if any)
user_actions = result.get('user_actions', [])
```

## Framework Components

For detailed architecture, component interactions, and design decisions, see [architecture.md](architecture.md).

### DataSource System

The datasource system provides a unified interface for accessing external APIs:

**Features:**
- REST and RPC endpoint support
- Automatic session management
- Configurable headers, params, and timeouts
- Health check interface
- Declarative tool creation via `@tool` decorator

**Unified Tools:**
When multiple methods share the same `tool_name`, they become a unified tool with an `action` parameter:

```python
class MyDataSource(DataSource):
    @tool(name="my_api", description="Get user data")
    def get_user(self, user_id: str) -> Dict:
        """Get user by ID."""
        return self.get(f"/users/{user_id}")
    
    @tool(name="my_api", description="Get user posts")
    def get_posts(self, user_id: str) -> Dict:
        """Get posts by user."""
        return self.get(f"/users/{user_id}/posts")
    
    # Both methods become a single "my_api" tool with action parameter
```

### Workflow Engine

The workflow engine orchestrates LLM interactions with tools:

**Graph Flow:**
```
tool_selection → model → router → [tools | end]
                                    ↓
                            select_tool_output
                                    ↓
                    [model | discover_schema | add_tool_messages]
```

**Features:**
- Dynamic tool binding
- Conditional routing
- Automatic chunking for large outputs
- User action detection
- Session-based state management

See [architecture.md](architecture.md) for detailed workflow flow and data processing diagrams.

### Checkpointer

MongoDB-based state persistence:

**Features:**
- Stores complete workflow state (not just messages)
- Session-based isolation
- Automatic state restoration
- LangGraph checkpointer interface

**Note:** Message history for display/retrieval is separate and should be managed by your application (see `example/server.py`).

### Summarizer Graph

Handles large tool outputs:

**Features:**
- Schema discovery from large JSON outputs
- Summarization of verbose outputs
- Parallel chunk processing
- Optional S3 storage
- Mandatory for chunking (no fallback)

### Sandbox Tool

Secure code execution:

**Features:**
- Isolated Docker containers
- Python 3.11 and Node.js 20 support
- Automatic dependency installation
- Matplotlib image generation
- File download support

See [architecture.md](architecture.md) for deployment architecture and security considerations.

## Example Implementation

See the `example/` folder for a complete implementation including:

- Multiple datasource examples (Helius, Jupiter, CoinGecko, GitHub, etc.)
- Workflow instance configuration
- FastAPI server with message history management

### Quick Start - Backend API

```bash
# Run the example server
python example/server.py
# Server runs on http://localhost:8001
```

The backend API is now available at `http://localhost:8001`. You can test it with:

```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of bitcoin?",
    "user_id": "user123"
  }'
```

See `example/README.md` for detailed backend setup and usage instructions.

## Optional: Chat UI

For a complete frontend experience, an optional chat UI is available:

**Chat UI** - React/TypeScript chat interface (from [ai-agent-ui](https://github.com/DPSN-org/ai-agent-ui))

### Setup

```bash
# Install chat UI dependencies
cd chat-ui
npm install

# Start chat UI dev server
npm run dev
# Chat UI runs on http://localhost:8080
```

The chat UI connects to the backend API and provides a modern web interface for interacting with the DeepSense framework.

**Note:** The chat UI is optional. The backend API can be used directly or with any custom frontend. See `example/README.md` for complete setup instructions including chat UI.

## Documentation

- **[Architecture](architecture.md)**: Detailed system architecture and design decisions
- **[Example README](example/README.md)**: Example implementation guide (includes chat UI setup)

## Requirements

### Core Dependencies

- `langgraph>=0.2.0` - Workflow orchestration
- `langchain>=0.2.0` - LLM integration
- `langchain-core>=0.2.0` - Core LangChain components
- `langchain-openai>=0.1.0` - OpenAI integration
- `langchain-anthropic>=0.1.0` - Anthropic integration
- `langchain-google-genai>=0.1.0` - Google Gemini integration
- `pymongo>=4.6.0` - MongoDB driver
- `fastapi>=0.104.0` - Web framework (for sandbox server)
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variable management
- `tiktoken>=0.5.0` - Token counting
- `boto3>=1.34.0` - AWS S3 integration (optional)
- `requests>=2.31.0` - HTTP client

See `requirements.txt` for complete list.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](./LICENSE) file for details.
