"""
Jupiter DataSource implementation for example
"""

import os
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any, List, Optional
from datetime import datetime

class JupiterDataSource(DataSource):
    """Jupiter token swap data source."""
    
    def __init__(self):
        config = DataSourceConfig(
            name="jupiter",
            rest_url="https://lite-api.jup.ag",
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
    
    @tool(
        name="jupiter_ag_apis",
        description="Comprehensive Jupiter AG API access tool for Solana token swaps and discovery.",
        user_action=True
    )
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
        """Get the best possible quote for a token swap. This API aggregates liquidity from various DEXes on Solana to provide optimal routing for trades."""
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
        if dexes:
            params["dexes"] = ",".join(dexes)
        elif exclude_dexes:
            params["excludeDexes"] = ",".join(exclude_dexes)
        
        quote_data = self.get(endpoint, params)
        
        # Wrap with user_action flag for workflow detection
        return {
            "user_action": True,
            "data": quote_data,
            "timestamp": datetime.now().isoformat(),
            "source": self.config.name,
            "action_type": "swap_quote"
        }
    
    @tool(name="jupiter_ag_apis")
    def search_tokens(self, query: str) -> Dict[str, Any]:
        """Search for tokens by symbol, name, or mint address. Returns comprehensive token information including mint address, symbol, name, decimals, and metadata."""
        return self.get("tokens/v2/search", {"query": query})
    
    @tool(name="jupiter_ag_apis")
    def get_token_info(self, mint_address: str) -> List[Dict[str, Any]]:
        """Get token info - returns list (Jupiter tool expects list)."""
        # Use search with mint address - returns list
        result = self.search_tokens(mint_address)
        # Handle both list and dict responses
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "data" in result:
            return result["data"]
        elif isinstance(result, dict):
            return [result]
        return []
    
    @tool(name="jupiter_ag_apis")
    def get_verified_tokens(self, query: str) -> Dict[str, Any]:
        """Search for verified tokens only (filters out potential scam tokens)."""
        result = self.search_tokens(query)
        # Filter for verified tokens
        if isinstance(result, list):
            verified = [token for token in result if token.get("isVerified", False)]
            return {"data": verified}
        elif isinstance(result, dict) and "data" in result:
            verified = [token for token in result["data"] if token.get("isVerified", False)]
            return {"data": verified}
        return {"data": []}
    
    @tool(name="jupiter_ag_apis")
    def get_token_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Get token information by symbol (e.g., 'USDC', 'SOL')."""
        return self.search_tokens(symbol)
    
    @tool(name="jupiter_ag_apis")
    def get_token_by_name(self, name: str) -> Dict[str, Any]:
        """Get token information by name (e.g., 'Wrapped Solana')."""
        return self.search_tokens(name)
    
    @tool(name="jupiter_ag_apis")
    def get_multiple_tokens(self, mint_addresses: List[str]) -> Dict[str, Any]:
        """Get information for multiple tokens by their mint addresses (max 100)."""
        if len(mint_addresses) > 100:
            raise ValueError("Maximum 100 mint addresses allowed")
        # Search with comma-separated mints
        query = ",".join(mint_addresses)
        return self.search_tokens(query)
    
    @tool(name="jupiter_ag_apis")
    def get_popular_tokens(self) -> Dict[str, Any]:
        """Get a list of popular/verified tokens."""
        # Search for common tokens
        popular_symbols = ["SOL", "USDC", "USDT", "BTC", "ETH"]
        return self.search_tokens(",".join(popular_symbols))
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get("tokens/v2/search", {"query": "SOL"})
            return "error" not in result
        except:
            return False

