"""
DPSN Intelligence Tool for LangGraph Assistant
Provides AI-powered cryptocurrency investment analysis and market intelligence.
"""

import requests
import json
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import os

class DPSNIntelligenceInput(BaseModel):
    query: str = Field(
        description="Market analysis question or investment query. Examples: 'market analysis for Bitcoin', 'should I invest in Ethereum?', 'what's the trend for SOL?', 'price prediction for crypto tokens'"
    )
    
   

class DPSNIntelligenceTool(BaseTool):
    """AI-powered cryptocurrency price analysis tool."""
    
    name: str = "dpsn_intelligence"
    description: str = """
    AI-powered cryptocurrency market analysis and investment intelligence tool. Use this tool for:
    - Market analysis and price predictions
    - Investment advice and trading opportunities
    - Technical analysis and trend analysis
    - Market sentiment and community metrics
    - Token performance analysis
    - Trading volume and momentum analysis
    
    Perfect for questions like: "What's the market analysis for Bitcoin?", "Should I invest in Ethereum?", "What's the trend for SOL?", "Market analysis for crypto tokens"
    """
    args_schema: type = DPSNIntelligenceInput
    
    def _run(self, query: str, timeframe: str = "7d", token_symbol: str = None, market_context: str = None) -> str:
        """Run DPSN intelligence analysis."""
        try:
            # Get API configuration
            api_url = "https://data.streams.dpsn.org/api/intelligence/95a9d3d8-a3fe-4b34-825a-f43139f1f46a"
            api_token = os.getenv("DPSN_API_TOKEN")
            
            if not api_token:
                return "Error: DPSN_API_TOKEN environment variable not set"
            
            # Prepare request payload
            payload = {
                "query": query,
            }
          
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_token,
                "User-Agent": "DPSN-Agentic-Framework/1.0"
            }
            
            # Make API request
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=100
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                return result
            elif response.status_code == 401:
                return "Error: Invalid API token. Please check your DPSN_API_TOKEN."
            elif response.status_code == 429:
                return "Error: Rate limit exceeded. Please try again later."
            elif response.status_code == 500:
                return "Error: DPSN intelligence service temporarily unavailable."
            else:
                return f"Error: API request failed with status {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timeout. The DPSN intelligence service is taking too long to respond."
        except requests.exceptions.ConnectionError:
            return "Error: Connection failed. Please check your internet connection."
        except Exception as e:
            return f"Error: Unexpected error occurred: {str(e)}"
    
    
    async def _arun(self, query: str, timeframe: str = "7d", token_symbol: str = None, market_context: str = None) -> str:
        """Async version of the tool."""
        return self._run(query, timeframe, token_symbol, market_context)

# Create tool instance
dpsn_intelligence_tool = DPSNIntelligenceTool()

# Export for use in other modules
__all__ = ["dpsn_intelligence_tool", "DPSNIntelligenceTool"] 