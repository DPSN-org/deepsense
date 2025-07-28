"""
News Data Source for LangGraph Assistant
Provides news articles via NewsAPI.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from .core import RESTDataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class NewsDataSource(RESTDataSource):
    """Data source for news articles via NewsAPI.
    
    This data source provides comprehensive access to news articles through
    NewsAPI's services. It supports top headlines, article search, and news
    categorization.
    
    Key Features:
    - Top headlines by country and category
    - News article search and filtering
    - News categorization and topics
    - Article metadata and content
    - Source information and credibility
    - News sentiment and analysis
    
    Supported Categories:
    - Business, Technology, Entertainment
    - Health, Science, Sports
    - General, Politics, World
    
    API Documentation: https://newsapi.org/docs
    """
    
    def __init__(self, api_key: str):
        config = DataSourceConfig(
            name="news",
            base_url="https://newsapi.org/v2",
            api_key=api_key
        )
        super().__init__(config)
        self.api_key = api_key
    
    def get_top_headlines(self, country: str = "us", category: Optional[str] = None, 
                         page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get top headlines by country and optional category.
        
        Args:
            country (str): Country code (e.g., 'us', 'gb', 'in', 'au')
            category (str, optional): News category (business, technology, entertainment, etc.)
            page_size (int): Number of articles per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing top headlines with:
            - Article titles and descriptions
            - Source names and URLs
            - Publication dates and timestamps
            - Article URLs and content
            - Author information
            - News category and tags
        """
        params = {
            "country": country,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.config.api_key
        }
        if category:
            params["category"] = category
        return self.get_data("top-headlines", params)
    
    def search_news(self, query: str, language: str = "en", sort_by: str = "publishedAt",
                   from_date: Optional[str] = None, to_date: Optional[str] = None,
                   page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Search for news articles by query.
        
        Args:
            query (str): Search query (keywords, phrases, topics)
            language (str): Language code (en, es, fr, de, etc.)
            sort_by (str): Sort order (relevancy, popularity, publishedAt)
            from_date (str): Start date in YYYY-MM-DD format
            to_date (str): End date in YYYY-MM-DD format
            page_size (int): Number of articles per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing search results with:
            - Matching articles and metadata
            - Source information and URLs
            - Publication dates and content
            - Relevance scores and ranking
            - Total results count
            - Pagination information
        """
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.config.api_key
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self.get_data("everything", params)
    
    def get_news_by_domain(self, domain: str, language: str = "en", sort_by: str = "publishedAt",
                          page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get news articles from a specific domain.
        
        Args:
            domain (str): News domain (e.g., 'bbc.com', 'cnn.com')
            language (str): Language code (en, es, fr, de, etc.)
            sort_by (str): Sort order (relevancy, popularity, publishedAt)
            page_size (int): Number of articles per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing domain-specific news with:
            - Articles from the specified domain
            - Article metadata and content
            - Publication dates and URLs
            - Source information
            - Total results and pagination
        """
        params = {
            "domains": domain,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.config.api_key
        }
        return self.get_data("everything", params)
    
    def get_news_sources(self, category: Optional[str] = None, language: Optional[str] = None,
                        country: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available news sources.
        
        Args:
            category (str, optional): Filter by category (business, technology, etc.)
            language (str, optional): Filter by language (en, es, fr, etc.)
            country (str, optional): Filter by country (us, gb, in, etc.)
            
        Returns:
            Dict containing news sources with:
            - Source names and IDs
            - Source descriptions and URLs
            - Categories and languages
            - Countries and credibility info
            - Source metadata and status
        """
        params = {"apiKey": self.config.api_key}
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country
        return self.get_data("sources", params)
    
    def get_news_by_topic(self, topic: str, language: str = "en", sort_by: str = "publishedAt",
                         page_size: int = 20, page: int = 1) -> Dict[str, Any]:
        """Get news articles by specific topic or keyword.
        
        Args:
            topic (str): News topic (e.g., 'technology', 'politics', 'sports')
            language (str): Language code (en, es, fr, de, etc.)
            sort_by (str): Sort order (relevancy, popularity, publishedAt)
            page_size (int): Number of articles per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing topic-specific news with:
            - Articles related to the topic
            - Article metadata and content
            - Source information and URLs
            - Publication dates and relevance
            - Topic categorization
        """
        params = {
            "q": topic,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
            "apiKey": self.config.api_key
        }
        return self.get_data("everything", params)
    
    def get_breaking_news(self, country: str = "us", page_size: int = 20) -> Dict[str, Any]:
        """Get breaking news and latest headlines.
        
        Args:
            country (str): Country code (e.g., 'us', 'gb', 'in', 'au')
            page_size (int): Number of articles per page (max: 100)
            
        Returns:
            Dict containing breaking news with:
            - Latest headlines and updates
            - Breaking news articles
            - Urgent news notifications
            - Real-time updates
            - News priority and urgency
        """
        params = {
            "country": country,
            "pageSize": page_size,
            "apiKey": self.config.api_key
        }
        return self.get_data("top-headlines", params)
    
    def get_news_analysis(self, query: str, language: str = "en", 
                         page_size: int = 20) -> Dict[str, Any]:
        """Get news articles for analysis and sentiment.
        
        Args:
            query (str): Analysis query or topic
            language (str): Language code (en, es, fr, de, etc.)
            page_size (int): Number of articles per page (max: 100)
            
        Returns:
            Dict containing news for analysis with:
            - Articles suitable for analysis
            - Diverse source coverage
            - Balanced viewpoints
            - Detailed content for analysis
            - Metadata for sentiment analysis
        """
        params = {
            "q": query,
            "language": language,
            "sortBy": "relevancy",
            "pageSize": page_size,
            "apiKey": self.config.api_key
        }
        return self.get_data("everything", params)

# Factory function for News data source
def create_news_source(api_key: str) -> NewsDataSource:
    """Create a News data source instance.
    
    Args:
        api_key (str): NewsAPI key
        
    Returns:
        NewsDataSource: Configured News data source instance
    """
    return NewsDataSource(api_key) 