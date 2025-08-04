"""
Cryptocurrency Data Source for LangGraph Assistant
Provides cryptocurrency market data via CoinGecko API.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from .core import DataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class CoinGeckoDataSource(DataSource):
    """Data source for cryptocurrency market data via CoinGecko API.
    
    This data source provides comprehensive access to cryptocurrency market data through
    CoinGecko's free APIs. It supports real-time prices, market data, trending coins,
    and historical information.
    
    Key Features:
    - Real-time cryptocurrency prices
    - Market cap and volume data
    - Trending coins and market trends
    - Historical price data
    - Token metadata and information
    - Exchange rates and conversions
    
    Supported Data:
    - 13,000+ cryptocurrencies
    - 800+ exchanges
    - Market data and analytics
    - NFT collections and data
    
    API Documentation: https://www.coingecko.com/en/api/documentation
    """
    
    def __init__(self):
        config = DataSourceConfig(
            name="coingecko",
            rest_url="https://api.coingecko.com/api/v3",
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
    
    def health_check(self) -> bool:
        """Check if the CoinGecko API is accessible."""
        try:
            response = self.session.get("https://api.coingecko.com/api/v3/ping", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    def get_coin_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price and market data for a specific cryptocurrency.
        
        Args:
            coin_id (str): Coin ID (e.g., 'bitcoin', 'ethereum', 'solana')
            vs_currency (str): Target currency (default: 'usd')
            
        Returns:
            Dict containing price information with:
            - Current price in target currency
            - Market cap and 24h volume
            - 24h price change percentage
            - Price change in 24h
            - Market cap rank and circulating supply
            - Total supply and max supply
        """
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        return self.get_data("simple/price", params)
    
    def get_coin_market_data(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get detailed market data for a specific cryptocurrency.
        
        Args:
            coin_id (str): Coin ID (e.g., 'bitcoin', 'ethereum', 'solana')
            vs_currency (str): Target currency (default: 'usd')
            
        Returns:
            Dict containing detailed market data with:
            - Current price and market cap
            - 24h volume and price change
            - Circulating and total supply
            - Market cap rank and dominance
            - Price change over different timeframes
            - All-time high and low prices
            - Price charts and sparkline data
        """
        params = {
            "vs_currency": vs_currency,
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": False
        }
        return self.get_data("coins/markets", params)
    
    def get_trending_coins(self) -> Dict[str, Any]:
        """Get trending coins in the last 24 hours.
        
        Returns:
            Dict containing trending coins with:
            - Top trending coins by market cap
            - Price change and volume data
            - Market cap and rank information
            - Trending score and social data
            - Coin metadata and descriptions
        """
        return self.get_data("search/trending")
    
    def get_coin_history(self, coin_id: str, date: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get historical price data for a specific date.
        
        Args:
            coin_id (str): Coin ID (e.g., 'bitcoin', 'ethereum')
            date (str): Date in DD-MM-YYYY format
            vs_currency (str): Target currency (default: 'usd')
            
        Returns:
            Dict containing historical data with:
            - Price data for the specified date
            - Market cap and volume information
            - Price change and percentage change
            - Market data and statistics
        """
        params = {
            "date": date,
            "localization": False
        }
        return self.get_data(f"coins/{coin_id}/history", params)
    
    def get_coin_market_chart(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> Dict[str, Any]:
        """Get market chart data for a cryptocurrency.
        
        Args:
            coin_id (str): Coin ID (e.g., 'bitcoin', 'ethereum')
            vs_currency (str): Target currency (default: 'usd')
            days (int): Number of days of data (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            Dict containing market chart data with:
            - Price data points over time
            - Market cap data over time
            - Volume data over time
            - Timestamp information
            - Price change statistics
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        return self.get_data(f"coins/{coin_id}/market_chart", params)
    
    def get_exchange_rates(self) -> Dict[str, Any]:
        """Get current exchange rates for supported currencies.
        
        Returns:
            Dict containing exchange rates with:
            - Rates for all supported currencies
            - Base currency information
            - Rate update timestamps
            - Currency metadata
        """
        return self.get_data("exchange_rates")
    
    def get_global_data(self) -> Dict[str, Any]:
        """Get global cryptocurrency market data.
        
        Returns:
            Dict containing global market data with:
            - Total market cap and volume
            - Market cap percentage change
            - Active cryptocurrencies count
            - Market dominance by currency
            - Market cap distribution
            - Trading volume statistics
        """
        return self.get_data("global")
    
    def search_coins(self, query: str) -> Dict[str, Any]:
        """Search for cryptocurrencies by name or symbol.
        
        Args:
            query (str): Search query (coin name or symbol)
            
        Returns:
            Dict containing search results with:
            - Matching coins and their IDs
            - Market cap ranks and symbols
            - Thumbnail images and names
            - API IDs for further queries
        """
        params = {"query": query}
        return self.get_data("search", params)
    
    def get_coin_info(self, coin_id: str) -> Dict[str, Any]:
        """Get comprehensive information about a cryptocurrency.
        
        Args:
            coin_id (str): Coin ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Dict containing comprehensive coin information with:
            - Basic coin information and metadata
            - Market data and statistics
            - Community data and social links
            - Developer information and GitHub stats
            - Public interest and sentiment data
            - Links and resources
        """
        params = {
            "localization": False,
            "tickers": False,
            "market_data": True,
            "community_data": True,
            "developer_data": True,
            "sparkline": False
        }
        return self.get_data(f"coins/{coin_id}", params)
    
    def get_top_coins(self, vs_currency: str = "usd", order: str = "market_cap_desc", per_page: int = 100) -> Dict[str, Any]:
        """Get top cryptocurrencies by market cap.
        
        Args:
            vs_currency (str): Target currency (default: 'usd')
            order (str): Sort order (market_cap_desc, volume_desc, price_desc, etc.)
            per_page (int): Number of results per page (max: 250)
            
        Returns:
            Dict containing top coins with:
            - List of top cryptocurrencies
            - Market data and statistics
            - Price and volume information
            - Market cap ranks and changes
            - Pagination information
        """
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": 1,
            "sparkline": False
        }
        return self.get_data("coins/markets", params)
    
    def get_exchanges(self, per_page: int = 100) -> Dict[str, Any]:
        """Get list of cryptocurrency exchanges.
        
        Args:
            per_page (int): Number of results per page (max: 250)
            
        Returns:
            Dict containing exchange information with:
            - List of cryptocurrency exchanges
            - Trading volume and trust scores
            - Exchange metadata and URLs
            - Country and year established
            - Description and features
        """
        params = {
            "per_page": per_page,
            "page": 1
        }
        return self.get_data("exchanges", params)

# Factory function for CoinGecko data source
def create_coingecko_source() -> CoinGeckoDataSource:
    """Create a CoinGecko data source instance.
    
    Returns:
        CoinGeckoDataSource: Configured CoinGecko data source instance
    """
    return CoinGeckoDataSource() 