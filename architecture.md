# DeepSense Architecture

## Overview

DeepSense is an agentic LLM orchestration framework that enables developers to build AI agents capable of interacting with multiple data sources, executing code securely, and maintaining conversational context. The framework is designed with a clear separation between the reusable core framework and user-specific implementations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Application                         │
│                      (example/server.py)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP API
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Example Implementation                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         workflow_instance.py                              │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Workflow (deepsense/workflow.py)                   │ │  │
│  │  │  ┌──────────────┐  ┌──────────────┐                │ │  │
│  │  │  │   LLM        │  │    Tools     │                │ │  │
│  │  │  │  (OpenAI/    │  │  - Sandbox   │                │ │  │
│  │  │  │  Anthropic/  │  │  - Datasource│                │ │  │
│  │  │  │  Google)     │  │    Tools    │                │ │  │
│  │  │  └──────────────┘  └──────────────┘                │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         DataSourceManager                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Helius      │  │ Jupiter      │  │ CoinGecko    │   │  │
│  │  │ DataSource  │  │ DataSource   │  │ DataSource   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ... (other datasources)                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Uses
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    DeepSense Framework                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Components                                          │  │
│  │  - workflow.py (LangGraph orchestration)                 │  │
│  │  - datasource.py (Base classes & tool decorator)         │  │
│  │  - checkpointer.py (MongoDB state persistence)          │  │
│  │  - summarizer_graph.py (Chunking & schema discovery)    │  │
│  │  - sandbox/ (Code execution server)                      │  │
│  │  - utils/ (Token counting, S3 utilities)                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Persists to / Reads from
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    External Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   MongoDB    │  │   Sandbox    │  │   AWS S3     │          │
│  │ (Checkpoint  │  │   Server     │  │  (Optional)  │          │
│  │   Storage)   │  │  (Docker)    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

## Framework Core Architecture

### 1. Workflow Engine (`deepsense/workflow.py`)

The workflow engine is built on LangGraph and implements a planner-react agent pattern with dynamic tool binding.

**Key Components:**
- **Workflow Class**: Main orchestration engine
- **AgentState**: TypedDict defining workflow state
- **Graph Nodes**:
  - `tool_selection`: Binds tools to LLM
  - `model`: LLM inference node
  - `router`: Routes to tools or end
  - `tools`: Executes tool calls
  - `select_tool_output`: Processes tool outputs
  - `discover_schema`: Handles large outputs via summarizer_graph
  - `add_tool_messages`: Adds tool results to conversation

**Flow:**
```
tool_selection → model → router → [tools | end]
                                    ↓
                            select_tool_output
                                    ↓
                    [model | discover_schema | add_tool_messages]
                                    ↓
                            (loop back or end)
```

**Features:**
- Dynamic LLM provider support (OpenAI, Anthropic, Google)
- Automatic tool binding
- Chunking for large outputs (mandatory summarizer_graph)
- User action detection and collection
- Session-based state management

### 2. DataSource System (`deepsense/datasource.py`)

The datasource system provides a unified interface for accessing external APIs and data sources.

**Components:**
- **DataSource**: Abstract base class for all datasources
- **DataSourceConfig**: Configuration dataclass
- **DataSourceManager**: Manages multiple datasources
- **@tool Decorator**: Declarative tool creation from methods

**Tool Creation System:**
- Methods decorated with `@tool` are automatically converted to LangChain tools
- Unified tools: Multiple methods with same `tool_name` become a single tool with `action` parameter
- Simple tools: Single method becomes a standalone tool
- Auto-generated schemas: Input schemas generated from method signatures
- User action support: Tools can mark outputs with `user_action: True`

**Example:**
```python
class MyDataSource(DataSource):
    @tool(name="my_api", description="Access my API")
    def get_data(self, param: str) -> Dict[str, Any]:
        return self.get("/endpoint", {"param": param})
```

### 3. Checkpointer (`deepsense/checkpointer.py`)

The checkpointer provides persistent state management for workflows using MongoDB.

**Features:**
- Implements LangGraph's checkpointer interface
- Stores complete workflow state (not just messages)
- Session-based isolation
- Automatic state restoration on workflow resumption
- Uses `langgraph.checkpoint.mongodb.MongoDBSaver`

**Separation of Concerns:**
- **Checkpointer**: Stores LangGraph workflow state (internal state, tool calls, intermediate results)
- **Message History** (in example/server.py): Stores user/agent messages for display/retrieval

### 4. Summarizer Graph (`deepsense/summarizer_graph.py`)

Handles large tool outputs through schema discovery and summarization.

**Features:**
- Mandatory for chunking functionality
- Schema discovery mode: Extracts structured schemas from large JSON outputs
- Summarization mode: Creates concise summaries
- Parallel processing: Processes chunks concurrently
- S3 integration: Optionally stores large outputs to S3

**Processing Flow:**
```
Large Output → Token Count Check → Chunking → Parallel Processing
                                                      ↓
                                            Schema Discovery / Summarization
                                                      ↓
                                            Final Schema / Summary
```

### 5. Sandbox (`deepsense/sandbox/`)

Secure code execution environment for LLM-generated code.

**Components:**
- **server.py**: FastAPI server for code execution requests
- **runner.py**: Python code execution runner
- **runner.js**: Node.js code execution runner
- **Dockerfile.python**: Python 3.11 Docker image
- **Dockerfile.node**: Node.js 20 Docker image

**Features:**
- Isolated Docker containers per execution
- Support for Python and Node.js
- Automatic dependency installation
- Matplotlib image generation with base64 encoding
- File download support from URLs

### 6. Utilities (`deepsense/utils/`)

**token_utils.py:**
- Token counting for various models (OpenAI, Anthropic)
- Chunking utilities for large data

**s3_utils.py:**
- JSON upload to AWS S3
- Configurable credentials and regions

## Example Implementation Architecture

### Structure

```
example/
├── datasources/              # User-defined datasources
│   ├── helius_source.py     # Solana blockchain data
│   ├── jupiter_source.py    # Token swap quotes
│   ├── coingecko_source.py  # Cryptocurrency prices
│   ├── github_source.py     # GitHub API
│   ├── weather_source.py    # Weather data
│   ├── flight_source.py     # Flight information
│   ├── location_source.py   # Location data
│   ├── news_source.py       # News articles
│   └── dpsn_source.py       # DPSN Intelligence
├── workflow_instance.py     # Workflow configuration
└── server.py                # FastAPI API server
```

### Workflow Instance (`example/workflow_instance.py`)

**Responsibilities:**
1. Register all datasources with DataSourceManager
2. Automatically create tools from datasources using `@tool` decorator
3. Initialize MongoDB checkpointer
4. Create Workflow instance with:
   - Custom datasource tools
   - System prompt
   - LLM configuration
   - Chunking threshold
5. Provide `invoke_workflow()` function for server use

### API Server (`example/server.py`)

**Components:**
- **FastAPI Application**: REST API endpoints
- **MessageHistory Class**: Manages user/agent message history (separate from checkpointer)
- **Endpoints**:
  - `POST /query`: Process user queries
  - `POST /sessions`: Create new sessions
  - `GET /sessions/{session_id}/messages`: Retrieve message history
  - `GET /health`: Health check

**Message Flow:**
```
User Request → Server → Workflow → LLM + Tools → Response
                     ↓                              ↓
              MessageHistory                  Checkpointer
              (Conversation)                  (State)
```

## Data Flow

### Query Processing Flow

```
1. User sends query via API
   ↓
2. Server saves user message to MessageHistory
   ↓
3. Server invokes workflow with query and session_id
   ↓
4. Workflow loads state from checkpointer (if session exists)
   ↓
5. Workflow processes through graph:
   - tool_selection: Binds tools to LLM
   - model: LLM generates response/tool calls
   - router: Routes to tools or returns final answer
   - tools: Executes tool calls (datasources, sandbox)
   - select_tool_output: Processes tool results
     - If large output → discover_schema (chunking)
     - If user_action → Collect for response
     - Otherwise → Continue to model
   ↓
6. Workflow saves state to checkpointer
   ↓
7. Server extracts final response and user_actions
   ↓
8. Server saves agent message to MessageHistory
   ↓
9. Server returns response to user
```

### Tool Execution Flow

```
LLM decides to use tool
   ↓
Tool call routed to tools node
   ↓
Tool executed (datasource method or sandbox)
   ↓
Output returned
   ↓
select_tool_output node:
   - Check token count
   - If > threshold → discover_schema (chunking)
   - If user_action → Add to user_actions list
   - Otherwise → Add to messages
   ↓
Continue workflow (back to model or end)
```

### Chunking Flow

```
Large tool output detected
   ↓
Token count exceeds threshold
   ↓
Route to discover_schema node
   ↓
summarizer_graph processes:
   - Chunk data by tokens
   - Process chunks in parallel
   - Discover schema or summarize
   ↓
Final schema/summary returned
   ↓
Continue workflow with processed output
```

## Component Interactions

### Workflow ↔ Checkpointer
- **Workflow** saves/loads state via LangGraph's checkpointer interface
- **Checkpointer** provides MongoDB persistence layer
- State includes: messages, tool calls, intermediate results, user_actions

### Workflow ↔ DataSources
- **Workflow** receives tools created from datasources
- **DataSources** provide methods decorated with `@tool`
- **DataSourceManager** registers and manages datasources
- Tools are automatically generated via `get_tools()` method

### Workflow ↔ Summarizer Graph
- **Workflow** calls `schema_discovery_wrapper` when chunking needed
- **Summarizer Graph** processes large outputs
- **Summarizer Graph** uses token_utils for chunking
- **Summarizer Graph** optionally uses s3_utils for storage

### Server ↔ Workflow
- **Server** invokes workflow with queries
- **Server** extracts responses and user_actions
- **Server** manages message history separately from workflow state

### Server ↔ MessageHistory
- **Server** saves user messages before workflow invocation
- **Server** saves agent messages after workflow completion
- **MessageHistory** provides conversation retrieval API

## Design Decisions

### 1. Separation of Framework and Example
- **Rationale**: Framework is reusable, example shows usage
- **Benefit**: Clear separation of concerns, easier maintenance

### 2. Declarative Tool Creation
- **Rationale**: Reduces boilerplate, improves developer experience
- **Benefit**: Users define tools directly in datasource methods using `@tool` decorator

### 3. Mandatory Summarizer Graph
- **Rationale**: Ensures consistent handling of large outputs
- **Benefit**: No fallback complexity, predictable behavior

### 4. Checkpointer vs Message History Separation
- **Rationale**: Different purposes - state vs conversation
- **Benefit**: Flexibility, can use different storage backends

### 5. Dynamic LLM Configuration
- **Rationale**: Support multiple providers, flexible deployment
- **Benefit**: Users can choose LLM provider and model

### 6. Sandbox Tool Predefined
- **Rationale**: Code execution is common use case
- **Benefit**: Always available, no need to configure

### 7. Unified Tools for Multiple Actions
- **Rationale**: Group related operations under single tool
- **Benefit**: Cleaner tool list, better LLM understanding

## Technology Stack

### Core Framework
- **LangGraph**: Workflow orchestration
- **LangChain**: LLM integration and tool framework
- **Pydantic**: Data validation and schema generation
- **Python 3.8+**: Runtime

### LLM Providers
- **OpenAI**: GPT models (via langchain-openai)
- **Anthropic**: Claude models (via langchain-anthropic)
- **Google**: Gemini models (via langchain-google-genai)

### Data Storage
- **MongoDB**: Workflow state persistence (via pymongo)
- **AWS S3**: Optional large output storage (via boto3)

### Web Framework
- **FastAPI**: API server (example/server.py, sandbox/server.py)
- **Uvicorn**: ASGI server

### Code Execution
- **Docker**: Container isolation for sandbox
- **Python 3.11**: Sandbox Python runtime
- **Node.js 20**: Sandbox JavaScript runtime

### Utilities
- **tiktoken**: Token counting
- **requests**: HTTP client for datasources
- **python-dotenv**: Environment variable management

## Deployment Architecture

### Development
```
┌─────────────┐
│   Python    │
│  Process    │
│             │
│  - Server   │
│  - Workflow │
└──────┬──────┘
       │
       ├──→ MongoDB (local)
       ├──→ Sandbox Server (local Docker)
       └──→ External APIs
```

### Production
```
┌─────────────┐      ┌─────────────┐
│   FastAPI   │      │   MongoDB   │
│   Server    │◄────►│   Cluster   │
└──────┬──────┘      └─────────────┘
       │
       ├──→ Sandbox Server (Docker)
       │
       ├──→ AWS S3 (optional)
       │
       └──→ External APIs
            - Helius
            - Jupiter
            - CoinGecko
            - GitHub
            - etc.
```

### Environment Variables
- **MONGODB_URI**: MongoDB connection string
- **OPENAI_API_KEY**: OpenAI API key
- **OPENAI_MODEL**: OpenAI model name
- **LLM_PROVIDER**: LLM provider ("openai", "anthropic", "google")
- **SANDBOX_URL**: Sandbox server URL
- **AWS_ACCESS_KEY_ID**: AWS credentials (optional)
- **AWS_SECRET_ACCESS_KEY**: AWS credentials (optional)
- **AWS_BUCKET**: S3 bucket name (optional)
- **Datasource API keys**: Various datasource-specific keys

## Security Considerations

1. **Sandbox Isolation**: Code execution in isolated Docker containers
2. **API Key Management**: Environment variables, never hardcoded
3. **Input Validation**: Pydantic schemas validate all inputs
4. **State Isolation**: Session-based state prevents cross-contamination
5. **Error Handling**: Graceful degradation, no sensitive data in errors

## Scalability Considerations

1. **Stateless Workflow**: State stored in MongoDB, server can scale horizontally
2. **Async Operations**: FastAPI supports async/await
3. **Parallel Processing**: Summarizer graph processes chunks in parallel
4. **Caching**: DataSourceManager supports optional caching
5. **Connection Pooling**: MongoDB connection pooling via pymongo

## Extension Points

1. **Custom Datasources**: Inherit from `DataSource`, use `@tool` decorator
2. **Custom Tools**: Add LangChain tools to `custom_tools` parameter
3. **Custom System Prompts**: Pass to `Workflow` constructor
4. **Custom LLM Providers**: Extend `_create_llm()` method
5. **Custom Checkpointers**: Implement LangGraph checkpointer interface

## Future Enhancements

- [ ] Support for additional LLM providers
- [ ] GraphQL API option
- [ ] WebSocket support for streaming
- [ ] Advanced caching strategies
- [ ] Multi-tenant support
- [ ] Plugin system for datasources
- [ ] Workflow versioning
- [ ] Analytics and monitoring

