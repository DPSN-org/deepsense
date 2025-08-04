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
    rest_url: Optional[str] = None
    rpc_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None  # requests per minute
    timeout: int = 30

class DataSource(ABC):
    """Base class for data sources."""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = requests.Session()
        if config.headers:
            self.session.headers.update(config.headers)
        if config.params:
            self.session.params.update(config.params)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the data source."""
        if not self.config.rest_url:
            return {"error": f"No REST URL configured for {self.config.name}"}
        
        url = f"{self.config.rest_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Combine config params with user params
        request_params = {}
        if self.config.params:
            request_params.update(self.config.params)
        if params:
            request_params.update(params)
        
        try:
            response = self.session.get(url, params=request_params, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed for {self.config.name}: {e}")
            return {"error": str(e), "source": self.config.name}
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request to the data source."""
        if not self.config.rest_url:
            return {"error": f"No REST URL configured for {self.config.name}"}
        
        url = f"{self.config.rest_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Combine config params with user params
        request_params = {}
        if self.config.params:
            request_params.update(self.config.params)
        if params:
            request_params.update(params)
        
        try:
            response = self.session.post(url, json=data, params=request_params, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed for {self.config.name}: {e}")
            return {"error": str(e), "source": self.config.name}
    
    def rpc_post(self, method: str, params: Any, rpc_url: Optional[str] = None) -> Dict[str, Any]:
        """Make a JSON-RPC POST request to the data source."""
        url = rpc_url or self.config.rpc_url
        if not url:
            return {"error": f"No RPC URL configured for {self.config.name}"}
        
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"RPC POST request failed for {self.config.name}: {e}")
            return {"error": str(e), "source": self.config.name}
    
    def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve data from the data source."""
        # Default implementation - can be overridden by subclasses
        return self.get(endpoint, params)
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        pass

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