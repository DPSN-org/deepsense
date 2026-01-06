"""
Helius DataSource implementation for example
"""

import os
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any, List, Optional

class HeliusDataSource(DataSource):
    """Helius blockchain data source."""
    
    def __init__(self, api_key: str = None, network: str = "mainnet-beta"):
        api_key = api_key or os.getenv("HELIUS_API_KEY")
        if not api_key:
            raise ValueError("HELIUS_API_KEY is required")
        
        config = DataSourceConfig(
            name="helius",
            rest_url="https://api.helius.xyz/v0",
            rpc_url="https://mainnet.helius-rpc.com",
            params={"api-key": api_key},
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
        self.api_key = api_key
        self.network = network
    
    @tool(name="solana_blockchain_data", description="Comprehensive Solana blockchain data access tool powered by Helius API.")
    def get_account_info(self, address: str) -> Dict[str, Any]:
        """Get comprehensive account information for a wallet address."""
        return self.rpc_post("getAccountInfo", [address, {"encoding": "jsonParsed"}])
    
    @tool(name="solana_blockchain_data")
    def get_balance(self, address: str) -> Dict[str, Any]:
        """Get SOL (native token) balance for a wallet address."""
        return self.rpc_post("getBalance", [address])
    
    @tool(name="solana_blockchain_data")
    def get_token_accounts(self, address: str) -> Dict[str, Any]:
        """Get all SPL token accounts owned by a wallet."""
        return self.rpc_post("getTokenAccountsByOwner", [
            address, 
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, 
            {"encoding": "jsonParsed"}
        ])
    
    @tool(name="solana_blockchain_data")
    def get_nft_accounts(self, address: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get all NFT accounts owned by a wallet."""
        params = {
            "ownerAddress": address,
            "page": page,
            "limit": limit
        }
        return self.rpc_post("getAssetsByOwner", params)
    
    @tool(name="solana_blockchain_data")
    def get_enhanced_transactions_by_address(self, address: str, limit: int = 100, 
                                            before: Optional[str] = None, 
                                            until: Optional[str] = None, 
                                            commitment: Optional[str] = None) -> Dict[str, Any]:
        """Get enhanced transaction history for a wallet address (MAXIMUM 100 transactions per call)."""
        endpoint = f"addresses/{address}/transactions"
        params = {"limit": limit}
        if before:
            params["before"] = before
        if until:
            params["until"] = until
        if commitment:
            params["commitment"] = commitment
        return self.get(endpoint, params)
    
    @tool(name="solana_blockchain_data")
    def get_parsed_transactions(self, transactions: List[str]) -> Dict[str, Any]:
        """Get detailed parsed transaction data by signature."""
        data = {"transactions": transactions}
        return self.post("transactions", data)
    
    @tool(name="solana_blockchain_data")
    def get_token_metadata(self, mint_address: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a specific SPL token."""
        return self.rpc_post("getAsset", {"id": mint_address})
    
    @tool(name="solana_blockchain_data")
    def get_nft_metadata(self, mint_address: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a specific NFT."""
        return self.rpc_post("getAsset", {"id": mint_address})
    
    @tool(name="solana_blockchain_data")
    def get_asset_by_id(self, asset_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific digital asset."""
        return self.rpc_post("getAsset", {"id": asset_id})
    
    @tool(name="solana_blockchain_data")
    def get_assets_by_owner(self, owner_address: str, page: int = 1) -> Dict[str, Any]:
        """Get all digital assets owned by a wallet address."""
        return self.rpc_post("getAssetsByOwner", {"ownerAddress": owner_address, "page": page})
    
    @tool(name="solana_blockchain_data")
    def get_asset_search(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search for digital assets by name, symbol, or description."""
        return self.rpc_post("searchAssets", {"query": query, "page": page})
    
    @tool(name="solana_blockchain_data")
    def get_das_search(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Advanced digital asset search using DAS (Digital Asset Standard)."""
        return self.rpc_post("searchAssets", {"query": query, "limit": limit})
    
    @tool(name="solana_blockchain_data")
    def rpc_method(self, method_name: str, params: List[Any]) -> Dict[str, Any]:
        """Make custom Solana RPC method calls for advanced operations."""
        return self.rpc_post(method_name, params)
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get("addresses/11111111111111111111111111111112/transactions", {"limit": 1})
            return "error" not in result
        except:
            return False

