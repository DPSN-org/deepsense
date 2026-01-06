"""
DeepSense Framework - An agentic LLM orchestration framework.
"""

__version__ = "1.0.0"

# Automatically load environment variables from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    import os
    from pathlib import Path
    
    # Try to find .env file in project root (going up from deepsense package)
    current_dir = Path(__file__).parent.parent
    env_file = current_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Also try loading from current working directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception:
    # Silently fail if .env loading fails
    pass

from .datasource import DataSource, DataSourceConfig, DataSourceManager, tool
from .workflow import Workflow
from .checkpointer import MongoDBCheckpointer
from .summarizer_graph import schema_discovery_wrapper, SchemaDiscoveryState
from .system_prompt import get_system_prompt
from .utils.token_utils import estimate_token_count, chunk_data_by_tokens
from .utils.s3_utils import upload_json_to_s3

# Sandbox server can be imported as: from deepsense.sandbox.server import app
# Run with: uvicorn deepsense.sandbox.server:app --reload

__all__ = [
    "DataSource",
    "DataSourceConfig",
    "DataSourceManager",
    "tool",
    "Workflow",
    "MongoDBCheckpointer",
    "schema_discovery_wrapper",
    "SchemaDiscoveryState",
    "get_system_prompt",
    "estimate_token_count",
    "chunk_data_by_tokens",
    "upload_json_to_s3",
]

