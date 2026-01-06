# DeepSense Example

This is an example implementation using the DeepSense Framework with a complete frontend and backend setup.

## Structure

```
example/
├── datasources/          # User-defined datasources
│   ├── crypto_source.py  # Example cryptocurrency datasource
│   └── github_source.py  # Example GitHub datasource
├── workflow_instance.py  # Workflow instance with custom datasources
└── server.py            # FastAPI server using the workflow
```

## Setup

### 1. Install Backend Dependencies

From the project root directory:
```bash
pip install -r requirements.txt
```

### 2. Install Chat UI Dependencies

```bash
cd chat-ui
npm install
# or if using bun
bun install
```

### 3. Environment Configuration

**Backend (.env in project root):**
```bash
# Required
OPENAI_API_KEY=your_openai_key
MONGODB_URI=mongodb://localhost:27017/

# Optional
OPENAI_MODEL=gpt-4o
LLM_PROVIDER=openai
SERVER_PORT=8001  # Backend server port
SANDBOX_URL=http://localhost:8000/run
```

**Chat UI (.env in chat-ui/ directory):**
```bash
# Backend API URL (default: http://localhost:8001)
VITE_API_BASE_URL=http://localhost:8001
```

### 4. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Running the Application

### Option 1: Run Backend and Frontend Separately

**Terminal 1 - Backend:**
```bash
# From project root
python example/server.py
```

The backend will start on `http://localhost:8001`

**Terminal 2 - Chat UI:**
```bash
# From chat-ui directory
cd chat-ui
npm run dev
# or
bun run dev
```

The chat UI will start on `http://localhost:8080`

### Option 2: Use npm scripts (if configured)

```bash
# From project root
npm run start:backend  # Start backend
npm run start:chat-ui # Start chat UI
```

## API Endpoints

The backend provides these endpoints:

- `POST /query` - Process a query through the workflow
  ```json
  {
    "query": "What is the current price of bitcoin?",
    "session_id": "optional-session-id",
    "user_id": "user123",
    "remarks": ["optional context"]
  }
  ```

- `POST /sessions` - Create a new session
- `GET /sessions/{session_id}/messages` - Get messages for a session
- `GET /health` - Health check

## Chat UI Features

The chat UI (`chat-ui/`) provides:

- 💬 Real-time chat interface
- 📂 Session management
- 💾 Persistent chat history (localStorage)
- 🎨 Clean, modern UI with dark/light mode
- 🔗 Wallet connection (Solana)
- 📊 User actions support (e.g., token swaps)

## Example Query

Open the chat UI at `http://localhost:8080` and try:

- "What is the current price of bitcoin?"
- "Get info about the langchain-ai/langchain repository"
- "What's the weather in New York?"

## Customizing

### Adding Custom Datasources

1. Create a new datasource class in `datasources/`:
```python
from deepsense import DataSource, DataSourceConfig, tool

class MyDataSource(DataSource):
    def __init__(self):
        config = DataSourceConfig(
            name="my_source",
            rest_url="https://api.example.com"
        )
        super().__init__(config)
    
    @tool(name="my_api", description="Access my API")
    def get_data(self, param: str) -> Dict[str, Any]:
        """Get data from the API."""
        return self.get("/endpoint", {"param": param})
    
    def health_check(self) -> bool:
        return True
```

2. Register it in `workflow_instance.py`:
```python
from example.datasources import MyDataSource

my_source = MyDataSource()
datasource_manager.register_source("my_source", my_source)
```

3. The tool will be automatically available to the workflow!

### Customizing the Workflow

Modify `workflow_instance.py` to:
- Change the system prompt
- Add more tools
- Customize the LLM model
- Adjust workflow behavior

### Chat UI Configuration

Edit `chat-ui/.env` to change:
- Backend API URL (`VITE_API_BASE_URL`)
- Other frontend-specific settings

## Troubleshooting

### Backend not responding
- Check if MongoDB is running: `docker ps | grep mongo`
- Verify backend is running on port 8001: `curl http://localhost:8001/health`
- Check CORS settings in `server.py`

### Chat UI can't connect to backend
- Verify `VITE_API_BASE_URL` in `chat-ui/.env` matches backend URL
- Check browser console for CORS errors
- Ensure backend CORS allows chat UI origin (http://localhost:8080)

### Session issues
- Check MongoDB connection
- Verify `MONGODB_URI` in `.env`
- Check backend logs for errors
