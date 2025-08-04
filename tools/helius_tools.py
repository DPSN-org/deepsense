"""
Helius Tools for LangGraph Assistant
Unified tool for accessing multiple blockchain networks and data types.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime
# Import Helius data source
from datasource.helius_source import create_helius_source

class HeliusToolInput(BaseModel):
    action: str = Field(
        description="""
        Action to perform on Solana blockchain data:
        
        ACCOUNT & BALANCE ACTIONS:
        - 'account_info': Get comprehensive account information for a wallet address
        - 'balance': Get SOL (native token) balance for a wallet address
        - 'token_accounts': Get all SPL token accounts owned by a wallet
        - 'nft_accounts': Get all NFT accounts owned by a wallet
        
        TRANSACTION ACTIONS:
        - 'transactions': Get enhanced transaction history for a wallet address (MAXIMUM 100 transactions per call). This API provides human-readable interpretations of transactions, including decoded instructions and categorized events like NFT activities, token swaps, and DeFi interactions. It can be filtered by 'before', 'until' transaction signatures and 'commitment' level.
        - 'parsed_transaction': Get detailed parsed transaction data by signature
        
        METADATA ACTIONS:
        - 'token_metadata': Get comprehensive metadata for a specific SPL token
        - 'nft_metadata': Get comprehensive metadata for a specific NFT
        
        ASSET DISCOVERY ACTIONS:
        - 'asset_by_id': Get detailed information for a specific digital asset
        - 'assets_by_owner': Get all digital assets owned by a wallet address
        - 'asset_search': Search for digital assets by name, symbol, or description
        - 'das_search': Advanced digital asset search using DAS (Digital Asset Standard)
        
        ADVANCED ACTIONS:
        - 'rpc_method': Make custom Solana RPC method calls for advanced operations
        """
    )
    address: Optional[str] = Field(default=None, description="Solana wallet address (base58 encoded public key)")
    mint_address: Optional[str] = Field(default=None, description="Token or NFT mint address")
    asset_id: Optional[str] = Field(default=None, description="Digital asset ID (usually the mint address)")
    signature: Optional[str] = Field(default=None, description="Solana transaction signature (base58 encoded)")
    query: Optional[str] = Field(default=None, description="Search query for assets or DAS search")
    owner_address: Optional[str] = Field(default=None, description="Owner wallet address for asset searches")
    group_key: Optional[str] = Field(default=None, description="Group key for asset filtering (e.g., 'collection')")
    group_value: Optional[str] = Field(default=None, description="Group value for asset filtering (e.g., collection address)")
    limit: Optional[int] = Field(default=100, description="Maximum number of results to return (1-100)")
    page: Optional[int] = Field(default=1, description="Page number for paginated results")
    before: Optional[str] = Field(default=None, description="For 'transactions' action, start searching backwards from this transaction signature.")
    until: Optional[str] = Field(default=None, description="For 'transactions' action, search until this transaction signature.")
    commitment: Optional[str] = Field(default=None, description="For 'transactions' action, how finalized a block must be to be included in the search (e.g., 'finalized', 'confirmed', 'processed').")
    rpc_method_name: Optional[str] = Field(default=None, description="Solana RPC method name (e.g., 'getAccountInfo', 'getBalance')")
    rpc_method_params: Optional[List[Any]] = Field(default=None, description="Parameters array for the RPC method")

class HeliusTool(BaseTool):
    """Unified tool for Helius blockchain data access."""
    name: str = "solana_blockchain_data"
    description: str = """
    Comprehensive Solana blockchain data access tool powered by Helius API.
    
    This tool provides access to:
    - Wallet account information and balances (SOL and SPL tokens)
    - NFT collections and metadata with images and attributes
    - Enhanced transaction history with human-readable descriptions
    - Token transfers, swaps, and DeFi activities
    - Digital asset searches and discovery
    - Custom RPC calls for advanced blockchain operations
    
    Enhanced transactions include decoded instructions and categorized events like:
    - NFT minting, trading, and marketplace activities
    - Token swaps and DeFi protocol interactions
    - Staking, governance, and program interactions
    - Compressed NFT operations
    
    Perfect for analyzing wallet activity, tracking asset ownership, 
    understanding transaction patterns, and building Solana applications.
    """
    args_schema: type = HeliusToolInput
    
    def __init__(self):
        super().__init__()
        self._helius_source = None
    
    def _get_helius_source(self):
        """Get or create Helius data source."""
        if self._helius_source is None:
            api_key = os.getenv("HELIUS_API_KEY")
            if not api_key:
                raise ValueError("HELIUS_API_KEY environment variable not set")
            self._helius_source = create_helius_source(api_key)
        return self._helius_source
    
    def _run(self, action: str, **kwargs) -> str:
        """Run Helius blockchain data query."""
        try:
            # Get Helius data source
            helius_source = self._get_helius_source()
            
            # Execute the requested action
            if action == "account_info":
                if not kwargs.get("address"):
                    return "Error: 'address' parameter is required for account_info action"
                result = helius_source.get_account_info(kwargs["address"])
            
            elif action == "balance":
                if not kwargs.get("address"):
                    return "Error: 'address' parameter is required for balance action"
                result = helius_source.get_balance(kwargs["address"])
            
            elif action == "token_accounts":
                if not kwargs.get("address"):
                    return "Error: 'address' parameter is required for token_accounts action"
                result = helius_source.get_token_accounts(kwargs["address"])
            
            elif action == "nft_accounts":
                if not kwargs.get("address"):
                    return "Error: 'address' parameter is required for nft_accounts action"
                result = helius_source.get_nft_accounts(
                    kwargs["address"],
                    kwargs.get("page", 1),
                    kwargs.get("limit", 50)
                )
            
            # Transaction Actions
            elif action == "transactions":
                if not kwargs.get("address"):
                    return "Error: 'address' parameter is required for transactions action"
                
                # Enforce limit constraint (max 100)
                limit = kwargs.get("limit", 100)
                if limit > 100:
                    limit = 100
                    print(f"Warning: Limit {kwargs.get('limit')} exceeds maximum of 100. Using limit=100.")
                
                result = helius_source.get_enhanced_transactions_by_address(
                    kwargs["address"], 
                    limit,
                    kwargs.get("before"),
                    kwargs.get("until"),
                    kwargs.get("commitment")
                )
            
            elif action == "parsed_transaction":
                if not kwargs.get("signature"):
                    return "Error: 'signature' parameter is required for parsed_transaction action"
                result = helius_source.get_parsed_transactions([kwargs["signature"]])
            
            # Metadata Actions
            elif action == "token_metadata":
                if not kwargs.get("mint_address"):
                    return "Error: 'mint_address' parameter is required for token_metadata action"
                result = helius_source.get_token_metadata(kwargs["mint_address"])
            
            elif action == "nft_metadata":
                if not kwargs.get("mint_address"):
                    return "Error: 'mint_address' parameter is required for nft_metadata action"
                result = helius_source.get_nft_metadata(kwargs["mint_address"])
            
            # Asset Discovery Actions
            elif action == "asset_by_id":
                if not kwargs.get("asset_id"):
                    return "Error: 'asset_id' parameter is required for asset_by_id action"
                result = helius_source.get_asset_by_id(kwargs["asset_id"])
            
            elif action == "assets_by_owner":
                if not kwargs.get("owner_address"):
                    return "Error: 'owner_address' parameter is required for assets_by_owner action"
                result = helius_source.get_assets_by_owner(
                    kwargs["owner_address"], 
                    kwargs.get("page", 1)
                )
            
            elif action == "asset_search":
                if not kwargs.get("query"):
                    return "Error: 'query' parameter is required for asset_search action"
                result = helius_source.get_asset_search(
                    kwargs["query"], 
                    kwargs.get("page", 1)
                )
            
            elif action == "das_search":
                if not kwargs.get("query"):
                    return "Error: 'query' parameter is required for das_search action"
                result = helius_source.get_das_search(
                    kwargs["query"], 
                    kwargs.get("limit", 100)
                )
            
            # Advanced Actions
            # elif action == "rpc_method":
            #     if not kwargs.get("rpc_method_name") or not kwargs.get("rpc_method_params"):
            #         return "Error: 'rpc_method_name' and 'rpc_method_params' are required for rpc_method action"
            #     result = helius_source.get_rpc_method(
            #         kwargs["rpc_method_name"], 
            #         kwargs["rpc_method_params"]
            #     )
            
            else:
                available_actions = [
                    "account_info", "balance", "token_accounts", "nft_accounts",
                    "transactions", "parsed_transaction", "token_metadata", "nft_metadata",
                    "asset_by_id", "assets_by_owner", "asset_search", "das_search", "rpc_method"
                ]
                return f"Error: Unknown action '{action}'. Available actions: {', '.join(available_actions)}"

            return self._format_response(action, result, **kwargs)

        except Exception as e:
            error_response = {
                "action": action,
                "network": "mainnet-beta",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "parameters": kwargs
            }
            return json.dumps(error_response, indent=2)
            
       
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async run Helius blockchain data query."""
        return self._run(action, **kwargs)

    def _format_response(self, action: str, result: Dict[str, Any], **kwargs) -> str:
        """Format the API response with LLM-friendly context and summaries."""
        if "error" in result:
            return f"Error executing {action}: {result['error']}"
        
        # Only include action, network, timestamp, and data
        formatted_response = result
        
        return formatted_response

# List of Helius tools
helius_tools = [
    HeliusTool()
]