# DeepSense Example

This is an example implementation using the DeepSense Framework.

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

1. Install dependencies (from project root):
```bash
# From the project root directory
pip install -r requirements.txt

# Or if you're in the example folder:
pip install -r ../requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export MONGODB_URI="mongodb://localhost:27017/"
export SANDBOX_URL="http://localhost:8000/run"  # Optional, for sandbox tool
```

3. Start MongoDB (if not already running):
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Usage

### Running the Server

```bash
python example/server.py
```

The server will start on `http://localhost:8000`

### API Endpoints

- `POST /query` - Process a query through the workflow
- `POST /sessions` - Create a new session
- `GET /sessions/{session_id}/messages` - Get messages for a session
- `GET /health` - Health check

### Example Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of bitcoin?",
    "user_id": "user123"
  }'
```

## Customizing

### Adding Custom Datasources

1. Create a new datasource class in `datasources/`:
```python
from deepsense import DataSource, DataSourceConfig

class MyDataSource(DataSource):
    def __init__(self):
        config = DataSourceConfig(
            name="my_source",
            rest_url="https://api.example.com"
        )
        super().__init__(config)
    
    def health_check(self) -> bool:
        # Implement health check
        return True
```

2. Register it in `workflow_instance.py`:
```python
from example.datasources import MyDataSource

my_source = MyDataSource()
datasource_manager.register_source("my_source", my_source)
```

3. Create a tool from the datasource and add it to `custom_tools`:
```python
def create_my_tool():
    def my_tool_function(param: str) -> str:
        source = datasource_manager.get_source("my_source")
        result = source.get_data("/endpoint", params={"param": param})
        return json.dumps(result, indent=2)
    
    return Tool(
        name="my_tool",
        description="Description of what the tool does",
        func=my_tool_function
    )

custom_tools.append(create_my_tool())
```

### Customizing the Workflow

Modify `workflow_instance.py` to:
- Change the system prompt
- Add more tools
- Customize the LLM model
- Adjust workflow behavior

