"""
DPSN Intelligence DataSource implementation for example
"""

import os
import requests
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any

class DPSNDataSource(DataSource):
    """DPSN Intelligence data source."""
    
    def __init__(self, api_token: str = None):
        api_token = api_token or os.getenv("DPSN_API_TOKEN")
        if not api_token:
            raise ValueError("DPSN_API_TOKEN is required")
        
        config = DataSourceConfig(
            name="dpsn",
            rest_url="https://data.streams.dpsn.org/api/intelligence/95a9d3d8-a3fe-4b34-825a-f43139f1f46a",
            headers={
                "Content-Type": "application/json",
                "Authorization": api_token,
                "User-Agent": "DeepSense/1.0"
            }
        )
        super().__init__(config)
        self.api_token = api_token
    
    @tool(name="dpsn_intelligence", description="AI-powered cryptocurrency market analysis and investment intelligence tool")
    def get_intelligence(self, query: str) -> Dict[str, Any]:
        """Get DPSN intelligence analysis."""
        try:
            payload = {"query": query}
            result = self.post("", payload)  # POST to base URL
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get_intelligence("test")
            return "error" not in result
        except:
            return False

