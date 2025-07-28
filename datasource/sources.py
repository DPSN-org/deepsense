"""
Data Sources Module for LangGraph Assistant
Imports and provides access to all specialized data sources.
"""

# Import all data source classes from their respective modules
from .crypto_source import CoinGeckoDataSource, create_coingecko_source
from .news_source import NewsDataSource, create_news_source
from .github_source import GitHubDataSource, create_github_source
from .helius_source import HeliusDataSource, create_helius_source

# Export all data source classes and factory functions
__all__ = [
    # Cryptocurrency data sources
    "CoinGeckoDataSource", 
    "create_coingecko_source",
    
    # News data sources
    "NewsDataSource",
    "create_news_source",
    
    # GitHub data sources
    "GitHubDataSource",
    "create_github_source",
    
    # Solana/Helius data sources
    "HeliusDataSource",
    "create_helius_source",
]

# Convenience function to create all data sources with environment variables
def create_all_sources():
    """Create instances of all available data sources using environment variables.
    
    Returns:
        Dict: Dictionary containing all configured data sources
    """
    import os
    
    sources = {}
    
    # Cryptocurrency (CoinGecko is free, no API key needed)
    sources["crypto"] = create_coingecko_source()
    
    # News
    news_key = os.getenv("NEWS_API_KEY")
    if news_key:
        sources["news"] = create_news_source(news_key)
    
    # GitHub (optional API key for higher rate limits)
    github_key = os.getenv("GITHUB_API_KEY")
    sources["github"] = create_github_source(github_key)
    
    # Solana/Helius
    helius_key = os.getenv("HELIUS_API_KEY")
    if helius_key:
        sources["helius"] = create_helius_source(helius_key)
    
    return sources

# Data source registry for easy access
DATA_SOURCE_REGISTRY = {
    "crypto": {
        "class": CoinGeckoDataSource,
        "factory": create_coingecko_source,
        "env_key": None,  # No API key required
        "description": "Cryptocurrency market data via CoinGecko API"
    },
    "news": {
        "class": NewsDataSource,
        "factory": create_news_source,
        "env_key": "NEWS_API_KEY",
        "description": "News articles via NewsAPI"
    },
    "github": {
        "class": GitHubDataSource,
        "factory": create_github_source,
        "env_key": "GITHUB_API_KEY",  # Optional
        "description": "GitHub repository and user data via GitHub API"
    },
    "helius": {
        "class": HeliusDataSource,
        "factory": create_helius_source,
        "env_key": "HELIUS_API_KEY",
        "description": "Solana blockchain data via Helius API"
    }
}

def get_available_sources():
    """Get information about all available data sources.
    
    Returns:
        Dict: Information about all data sources and their requirements
    """
    return DATA_SOURCE_REGISTRY.copy()

def create_source_by_name(name: str, api_key: str = None):
    """Create a specific data source by name.
    
    Args:
        name (str): Name of the data source
        api_key (str, optional): API key for the data source
        
    Returns:
        DataSource: Configured data source instance
        
    Raises:
        ValueError: If the data source name is not found
    """
    if name not in DATA_SOURCE_REGISTRY:
        available = ", ".join(DATA_SOURCE_REGISTRY.keys())
        raise ValueError(f"Unknown data source '{name}'. Available: {available}")
    
    source_info = DATA_SOURCE_REGISTRY[name]
    factory = source_info["factory"]
    
    if source_info["env_key"] and not api_key:
        import os
        api_key = os.getenv(source_info["env_key"])
        if not api_key:
            raise ValueError(f"API key required for {name}. Set {source_info['env_key']} environment variable.")
    
    return factory(api_key) if api_key else factory() 