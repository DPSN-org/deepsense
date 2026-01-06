"""
Example workflow instance implementing planner_react_agent using deepsense/workflow.py
All tools are created from datasources using deepsense/datasource.py
"""

import os
from deepsense import Workflow, MongoDBCheckpointer
from deepsense.datasource import DataSourceManager
from typing import List, Dict, Any

# Import all datasources
from example.datasources import (
    CryptoDataSource, GitHubDataSource, HeliusDataSource, JupiterDataSource,
    WeatherDataSource, FlightDataSource, LocationDataSource, DPSNDataSource,
    CoinGeckoDataSource, NewsDataSource
)

# Import system prompt
from deepsense import get_system_prompt

# Create datasource manager
datasource_manager = DataSourceManager()

# Register all datasources
try:
    if os.getenv("HELIUS_API_KEY"):
        helius_source = HeliusDataSource(api_key=os.getenv("HELIUS_API_KEY"))
        datasource_manager.register_source("helius", helius_source)
except Exception as e:
    print(f"Warning: Could not register Helius datasource: {e}")

jupiter_source = JupiterDataSource()
datasource_manager.register_source("jupiter", jupiter_source)

coingecko_source = CoinGeckoDataSource()
datasource_manager.register_source("coingecko", coingecko_source)

try:
    if os.getenv("NEWS_API_KEY"):
        news_source = NewsDataSource(api_key=os.getenv("NEWS_API_KEY"))
        datasource_manager.register_source("news", news_source)
except Exception as e:
    print(f"Warning: Could not register News datasource: {e}")

github_source = GitHubDataSource(api_key=os.getenv("GITHUB_API_KEY"))
datasource_manager.register_source("github", github_source)

try:
    if os.getenv("OPENWEATHER_API_KEY"):
        weather_source = WeatherDataSource(api_key=os.getenv("OPENWEATHER_API_KEY"))
        datasource_manager.register_source("weather", weather_source)
except Exception as e:
    print(f"Warning: Could not register Weather datasource: {e}")

try:
    if os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET"):
        flight_source = FlightDataSource(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
        )
        location_source = LocationDataSource(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
        )
        datasource_manager.register_source("flight", flight_source)
        datasource_manager.register_source("location", location_source)
except Exception as e:
    print(f"Warning: Could not register Flight/Location datasources: {e}")

try:
    if os.getenv("DPSN_API_TOKEN"):
        dpsn_source = DPSNDataSource(api_token=os.getenv("DPSN_API_TOKEN"))
        datasource_manager.register_source("dpsn", dpsn_source)
except Exception as e:
    print(f"Warning: Could not register DPSN datasource: {e}")

# Automatically create tools from all registered datasources using @tool decorator
all_tools = []
for source_name in datasource_manager.list_sources():
    source = datasource_manager.get_source(source_name)
    if source:
        try:
            tools = source.get_tools()
            all_tools.extend(tools)
            print(f"✅ Created {len(tools)} tool(s) from {source_name} datasource")
        except Exception as e:
            print(f"⚠️  Warning: Could not create tools from {source_name}: {e}")

# Note: sandbox tool is already included in Workflow by default

# Initialize MongoDB checkpointer
checkpointer = MongoDBCheckpointer(
    connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
    database_name="deepsense_example"
)

# Create workflow instance matching planner_react_agent
# Uses deepsense/workflow.py with all datasource tools
workflow = Workflow(
    checkpointer=checkpointer,
    llm_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),  # "openai", "anthropic", "google"
    api_key=os.getenv("OPENAI_API_KEY"),
    system_prompt=get_system_prompt(),  # Use planner_react_agent system prompt
    custom_tools=all_tools,
    chunking_threshold=15000  # Token threshold for chunking
)

def invoke_workflow(query: str, session_id: str = None) -> Dict[str, Any]:
    """
    Invoke the workflow with a query.
    This replicates planner_react_agent functionality using deepsense/workflow.py
    
    Args:
        query: User query
        session_id: Optional session ID
        
    Returns:
        Workflow result with user_actions if any
    """
    return workflow.invoke(query, session_id=session_id)
