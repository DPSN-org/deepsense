"""
Data Source Module for LangGraph Assistant
Provides unified access to various data sources for real-time information.
"""

# Core data source infrastructure
from .core import DataSource, DataSourceConfig, DataSourceManager

# Individual data source classes
from .crypto_source import CoinGeckoDataSource, create_coingecko_source
from .news_source import NewsDataSource, create_news_source
from .github_source import GitHubDataSource, create_github_source
from .helius_source import HeliusDataSource, create_helius_source

# Convenience functions and registry
from .sources import (
    create_all_sources,
    get_available_sources,
    create_source_by_name,
    DATA_SOURCE_REGISTRY
)

# Export a singleton datasource_manager for global use
datasource_manager = DataSourceManager()

# Export all public interfaces
__all__ = [
    # Core infrastructure
    "DataSource",
    "DataSourceConfig", 
    "DataSourceManager",
    
    # Individual data sources
    "CoinGeckoDataSource",
    "NewsDataSource",
    "GitHubDataSource",
    "HeliusDataSource",
    
    # Factory functions
    "create_coingecko_source",
    "create_news_source",
    "create_github_source",
    "create_helius_source",
    
    # Convenience functions
    "create_all_sources",
    "get_available_sources",
    "create_source_by_name",
    "DATA_SOURCE_REGISTRY",
]

# Version information
__version__ = "1.0.0"
__author__ = "LangGraph Assistant Team"
__description__ = "Comprehensive data source module for LangGraph Assistant" 