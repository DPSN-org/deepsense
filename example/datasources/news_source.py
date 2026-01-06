"""
News DataSource implementation for example
"""

import os
from deepsense import DataSource, DataSourceConfig
from typing import Dict, Any, Optional

class NewsDataSource(DataSource):
    """News data source using NewsAPI."""
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("NEWS_API_KEY")
        config = DataSourceConfig(
            name="news",
            rest_url="https://newsapi.org/v2",
            params={"apiKey": api_key} if api_key else {},
            headers={"Accept": "application/json"}
        )
        super().__init__(config)
        self.api_key = api_key
    
    def get_top_headlines(self, country: str = "us", category: Optional[str] = None, 
                         page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get top headlines."""
        params = {"country": country, "pageSize": page_size, "page": page}
        if category:
            params["category"] = category
        return self.get("/top-headlines", params)
    
    def search_news(self, query: str, language: str = "en", sort_by: str = "publishedAt",
                   from_date: Optional[str] = None, to_date: Optional[str] = None,
                   page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Search news."""
        params = {"q": query, "language": language, "sortBy": sort_by, 
                 "pageSize": page_size, "page": page}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self.get("/everything", params)
    
    def get_news_by_domain(self, domain: str, language: str = "en", sort_by: str = "publishedAt",
                          page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get news by domain."""
        params = {"domains": domain, "language": language, "sortBy": sort_by, 
                 "pageSize": page_size, "page": page}
        return self.get("/everything", params)
    
    def get_news_sources(self, category: Optional[str] = None, language: Optional[str] = None,
                        country: Optional[str] = None) -> Dict[str, Any]:
        """Get news sources."""
        params = {}
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country
        return self.get("/sources", params)
    
    def get_news_by_topic(self, topic: str, language: str = "en", sort_by: str = "publishedAt",
                         page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get news by topic."""
        return self.search_news(topic, language, sort_by, None, None, page_size, page)
    
    def get_breaking_news(self, country: str = "us", page_size: int = 10) -> Dict[str, Any]:
        """Get breaking news."""
        return self.get_top_headlines(country, None, page_size, 1)
    
    def get_news_analysis(self, query: str, language: str = "en", page_size: int = 10) -> Dict[str, Any]:
        """Get news analysis."""
        return self.search_news(query, language, "popularity", None, None, page_size, 1)
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            if not self.api_key:
                return False
            result = self.get_top_headlines("us", None, 1, 1)
            return "error" not in result
        except:
            return False

