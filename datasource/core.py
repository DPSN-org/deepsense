"""
Core Datasource Module for LangGraph Assistant
Handles API client management and data retrieval for various data sources.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    param_api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    rate_limit: Optional[int] = None  # requests per minute
    timeout: int = 30

class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = requests.Session()
        if config.headers:
            self.session.headers.update(config.headers)
        if config.param_api_key:
            self.session.params.update({"api-key": config.param_api_key})
    @abstractmethod
    def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve data from the data source."""
        pass
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            response = self.session.get(self.config.base_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False

class RESTDataSource(DataSource):
    """Standard REST API data source."""
    
    def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve data from REST API endpoint."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            print(response.json())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {self.config.name}: {e}")
            return {"error": str(e), "source": self.config.name}

class DataSourceManager:
    """Manages multiple data sources and provides unified access."""
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
    
    def register_source(self, name: str, source: DataSource) -> None:
        """Register a new data source."""
        self.sources[name] = source
        logger.info(f"Registered data source: {name}")
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """Get a registered data source by name."""
        return self.sources.get(name)
    
    def list_sources(self) -> List[str]:
        """List all registered data sources."""
        return list(self.sources.keys())
    
    def get_data(self, source_name: str, endpoint: str, 
                 params: Optional[Dict[str, Any]] = None, 
                 use_cache: bool = True, 
                 cache_ttl: int = 300) -> Dict[str, Any]:
        """Get data from a specific source with optional caching."""
        
        # Check cache first
        cache_key = f"{source_name}:{endpoint}:{hash(str(params))}"
        if use_cache and cache_key in self.cache:
            if datetime.now().timestamp() - self.cache_ttl[cache_key].timestamp() < cache_ttl:
                logger.info(f"Returning cached data for {cache_key}")
                return self.cache[cache_key]
        
        # Get data from source
        source = self.get_source(source_name)
        if not source:
            return {"error": f"Data source '{source_name}' not found"}
        
        data = source.get_data(endpoint, params)
        
        # Cache the result
        if use_cache and "error" not in data:
            self.cache[cache_key] = data
            self.cache_ttl[cache_key] = datetime.now()
        
        return data
    
    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered data sources."""
        results = {}
        for name, source in self.sources.items():
            results[name] = source.health_check()
        return results

# Global datasource manager instance
datasource_manager = DataSourceManager() 