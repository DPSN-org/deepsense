"""
Example GitHub DataSource implementation
"""

import os
from deepsense import DataSource, DataSourceConfig
from typing import Dict, Any

class GitHubDataSource(DataSource):
    """Example GitHub data source."""
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("GITHUB_API_KEY")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if api_key:
            headers["Authorization"] = f"token {api_key}"
        
        config = DataSourceConfig(
            name="github",
            rest_url="https://api.github.com",
            headers=headers
        )
        super().__init__(config)
    
    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        return self.get(f"/repos/{owner}/{repo}")
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get("/")
            return "current_user_url" in str(result) or "rate_limit_url" in str(result)
        except:
            return False

