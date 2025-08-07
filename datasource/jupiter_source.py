"""
Jupiter Data Source for LangGraph Assistant
Provides access to Jupiter AG APIs for token swaps and discovery.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
from .core import DataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class JupiterDataSource(DataSource):
    """Data source for Jupiter AG APIs - token swaps and discovery."""
    
    def __init__(self):
        config = DataSourceConfig(
            name="jupiter",
            rest_url="https://lite-api.jup.ag",
            params={},
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
    
    def health_check(self) -> bool:
        """Check if the Jupiter API is accessible."""
        try:
            # Test with a simple search query
            response = self.session.get("https://lite-api.jup.ag/tokens/v2/search?query=SOL", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    # --- Swap API Methods ---
    def get_quote(self, 
                  input_mint: str, 
                  output_mint: str, 
                  amount: int,
                  slippage_bps: Optional[int] = None,
                  swap_mode: Optional[str] = "ExactIn",
                  dexes: Optional[List[str]] = None,
                  exclude_dexes: Optional[List[str]] = None,
                  restrict_intermediate_tokens: Optional[bool] = True,
                  only_direct_routes: Optional[bool] = False,
                  as_legacy_transaction: Optional[bool] = False,
                  platform_fee_bps: Optional[int] = None,
                  max_accounts: Optional[int] = 64,
                  dynamic_slippage: Optional[bool] = False) -> Dict[str, Any]:
        """
        Get the best possible quote for a token swap.
        
        Args:
            input_mint: The mint address of the token to sell
            output_mint: The mint address of the token to buy
            amount: The amount of input token to swap (in smallest unit)
            slippage_bps: Maximum acceptable slippage in basis points
            swap_mode: 'ExactIn' or 'ExactOut'
            dexes: List of DEXes to exclusively use
            exclude_dexes: List of DEXes to exclude
            restrict_intermediate_tokens: Restrict to stable intermediate tokens
            only_direct_routes: Limit to single-hop routes only
            as_legacy_transaction: Use legacy transaction format
            platform_fee_bps: Platform fees in basis points
            max_accounts: Maximum number of accounts for the quote
            dynamic_slippage: Use dynamic slippage estimation
        """
        endpoint = "swap/v1/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "swapMode": swap_mode,
            "restrictIntermediateTokens": str(restrict_intermediate_tokens).lower(),
            "onlyDirectRoutes": str(only_direct_routes).lower(),
            "asLegacyTransaction": str(as_legacy_transaction).lower(),
            "maxAccounts": max_accounts,
            "dynamicSlippage": str(dynamic_slippage).lower()
        }
        
        if slippage_bps is not None:
            params["slippageBps"] = slippage_bps
        if platform_fee_bps is not None:
            params["platformFeeBps"] = platform_fee_bps
            
        # Handle DEX parameters - only send one of dexes or excludeDexes, not both
        if dexes and exclude_dexes:
            # If both are specified, prioritize dexes (inclusion) over exclusion
            print("Warning: Both dexes and excludeDexes specified. Using dexes (inclusion) only.")
            params["dexes"] = ",".join(dexes)
        elif dexes:
            params["dexes"] = ",".join(dexes)
        elif exclude_dexes:
            params["excludeDexes"] = ",".join(exclude_dexes)
            
        return self.get(endpoint, params)
    
    # --- Token API V2 Methods ---
    def search_tokens(self, query: str) -> Dict[str, Any]:
        """
        Search for tokens by symbol, name, or mint address.
        
        Args:
            query: Search query (symbol, name, or mint address)
        """
        endpoint = "tokens/v2/search"
        params = {"query": query}
        return self.get(endpoint, params)
    
    def get_token_info(self, mint_address: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific token.
        
        Args:
            mint_address: The token's mint address
        """
        # Use search with specific mint address
        return self.search_tokens(mint_address)
    
    def get_verified_tokens(self, query: str) -> Dict[str, Any]:
        """
        Search for verified tokens only.
        
        Args:
            query: Search query for verified tokens
        """
        result = self.search_tokens(query)
        # Handle both list and dict responses
        if isinstance(result, list):
            # Filter for verified tokens
            verified_tokens = [token for token in result if token.get("isVerified", False)]
            return {"data": verified_tokens}
        elif isinstance(result, dict) and "data" in result:
            # Filter for verified tokens
            verified_tokens = [token for token in result["data"] if token.get("isVerified", False)]
            result["data"] = verified_tokens
            return result
        else:
            return {"data": []}
    
    def get_token_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get token information by symbol.
        
        Args:
            symbol: Token symbol (e.g., 'USDC', 'SOL')
        """
        return self.search_tokens(symbol)
    
    def get_token_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get token information by name.
        
        Args:
            name: Token name (e.g., 'Wrapped Solana', 'USD Coin')
        """
        return self.search_tokens(name)
    
    def get_multiple_tokens(self, mint_addresses: List[str]) -> Dict[str, Any]:
        """
        Get information for multiple tokens by their mint addresses.
        
        Args:
            mint_addresses: List of mint addresses (max 100)
        """
        if len(mint_addresses) > 100:
            raise ValueError("Maximum 100 mint addresses allowed per query")
        
        query = ",".join(mint_addresses)
        return self.search_tokens(query)
    
    def get_popular_tokens(self) -> Dict[str, Any]:
        """
        Get a list of popular/verified tokens.
        """
        # Search for common tokens to get popular ones
        popular_symbols = ["SOL", "USDC", "USDT", "BTC", "ETH", "RAY", "SRM", "ORCA"]
        return self.search_tokens(",".join(popular_symbols))

def create_jupiter_source() -> JupiterDataSource:
    """Create a Jupiter data source instance."""
    return JupiterDataSource() 