"""
Jupiter Tools for LangGraph Assistant
Unified tool for accessing Jupiter AG APIs for token swaps and discovery.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime
# Import Jupiter data source
from datasource.jupiter_source import create_jupiter_source

class JupiterToolInput(BaseModel):
    action: str = Field(
        description="""
        Action to perform with Jupiter AG APIs on solana blockchain :
        
        SWAP QUOTE ACTIONS:
        - 'get_quote': Get the best possible quote for a token swap. This API aggregates liquidity from various DEXes on Solana to provide optimal routing for trades. Can also be used to check if a token pair is tradable.
        
        TOKEN DISCOVERY ACTIONS:
        - 'search_tokens': Search for tokens by symbol, name, or mint address. Returns comprehensive token information including mint address, symbol, name, decimals, and metadata.
        - 'get_token_info': Get detailed information for a specific token by mint address
        - 'get_verified_tokens': Search for verified tokens only (filters out potential scam tokens)
        - 'get_token_by_symbol': Get token information by symbol (e.g., 'USDC', 'SOL')
        - 'get_token_by_name': Get token information by name (e.g., 'Wrapped Solana')
        - 'get_multiple_tokens': Get information for multiple tokens by their mint addresses (max 100)
        - 'get_popular_tokens': Get a list of popular/verified tokens
        """
    )
    input_mint: Optional[str] = Field(default=None, description="The mint address of the token you intend to sell (for swap quotes)")
    output_mint: Optional[str] = Field(default=None, description="The mint address of the token you intend to buy (for swap quotes)")
    amount: Optional[int] = Field(default=None, description="The amount of input token to swap, expressed in its smallest unit (e.g., lamports for SOL which has 9 decimals)")
    slippage_bps: Optional[int] = Field(default=None, description="Maximum acceptable slippage in basis points (BPS). 1 BPS = 0.01%. Example: 50 for 0.5% slippage")
    swap_mode: Optional[str] = Field(default="ExactIn", description="Swap mode: 'ExactIn' (amount is exact input) or 'ExactOut' (amount is exact output desired)")
    dexes: Optional[List[str]] = Field(default=None, description="List of DEXes to exclusively use for the swap (e.g., ['Raydium', 'Orca+V2']). Cannot be used with exclude_dexes.")
    exclude_dexes: Optional[List[str]] = Field(default=None, description="List of DEXes to exclude from the swap (e.g., ['Aldrin', 'Saber']). Cannot be used with dexes.")
    restrict_intermediate_tokens: Optional[bool] = Field(default=True, description="If true, restricts intermediate tokens to more stable tokens to reduce slippage exposure")
    only_direct_routes: Optional[bool] = Field(default=False, description="If true, limits routing to single-hop routes only (may result in worse routes but simpler transactions)")
    as_legacy_transaction: Optional[bool] = Field(default=False, description="If true, uses legacy transaction format instead of versioned transaction")
    platform_fee_bps: Optional[int] = Field(default=None, description="Platform fees in basis points")
    max_accounts: Optional[int] = Field(default=64, description="Rough estimate of maximum number of accounts for the quote")
    dynamic_slippage: Optional[bool] = Field(default=False, description="If true, slippage_bps will be overridden by Dynamic Slippage's estimated value")
    query: Optional[str] = Field(default=None, description="Search query for tokens (symbol, name, or mint address)")
    mint_address: Optional[str] = Field(default=None, description="Specific token mint address for detailed information")
    mint_addresses: Optional[List[str]] = Field(default=None, description="List of mint addresses for multiple token lookup (max 100)")
    reason: str = Field(default=None, description="Purpose of calling the tool")

class JupiterTool(BaseTool):
    """Unified tool for Jupiter AG APIs - token swaps and discovery."""
    name: str = "jupiter_ag_apis"
    description: str = """
    Comprehensive Jupiter AG API access tool for Solana token swaps and discovery.
    
    This tool provides access to:
    - Token swap quotes with optimal routing across multiple DEXes
    - Token discovery and search by symbol, name, or mint address
    - Verified token filtering to avoid scam tokens
    - Multi-token information retrieval
    - Popular token listings
    
    Swap Quote Features:
    - Aggregates liquidity from various DEXes (Raydium, Orca, etc.)
    - Configurable slippage tolerance and routing preferences
    - Support for both exact input and exact output modes
    - DEX inclusion/exclusion filters
    - Dynamic slippage estimation
    - Platform fee integration
    
    Token Discovery Features:
    - Search by symbol (e.g., 'USDC', 'SOL')
    - Search by name (e.g., 'Wrapped Solana', 'USD Coin')
    - Search by mint address
    - Verified token filtering
    - Multi-token batch lookup
    - Popular token listings
    
    Perfect for building DeFi applications, token analysis, 
    swap route optimization, and token discovery on Solana.
    """
    args_schema: type = JupiterToolInput
    
    def __init__(self):
        super().__init__()
        self._jupiter_source = None
    
    def _get_jupiter_source(self):
        """Get or create Jupiter data source."""
        if self._jupiter_source is None:
            self._jupiter_source = create_jupiter_source()
        return self._jupiter_source
    
    def _run(self, action: str, **kwargs) -> str:
        """Run Jupiter API query."""
        try:
            jupiter_source = self._get_jupiter_source()
            
            if action == "get_quote":
                return self._handle_get_quote(jupiter_source, **kwargs)
            elif action == "search_tokens":
                return self._handle_search_tokens(jupiter_source, **kwargs)
            elif action == "get_token_info":
                return self._handle_get_token_info(jupiter_source, **kwargs)
            elif action == "get_verified_tokens":
                return self._handle_get_verified_tokens(jupiter_source, **kwargs)
            elif action == "get_token_by_symbol":
                return self._handle_get_token_by_symbol(jupiter_source, **kwargs)
            elif action == "get_token_by_name":
                return self._handle_get_token_by_name(jupiter_source, **kwargs)
            elif action == "get_multiple_tokens":
                return self._handle_get_multiple_tokens(jupiter_source, **kwargs)
            elif action == "get_popular_tokens":
                return self._handle_get_popular_tokens(jupiter_source, **kwargs)
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Error in Jupiter tool: {str(e)}"
    
    def _handle_get_quote(self, jupiter_source, **kwargs) -> str:
        """Handle get_quote action."""
        required_fields = ["input_mint", "output_mint", "amount"]
        for field in required_fields:
            if not kwargs.get(field):
                return f"Missing required field: {field}"
        
        # Validate DEX parameters - only one of dexes or exclude_dexes should be specified
        dexes = kwargs.get("dexes")
        exclude_dexes = kwargs.get("exclude_dexes")
        if dexes and exclude_dexes:
            return "Error: Cannot specify both 'dexes' and 'exclude_dexes' parameters. Use only one of them."
        
        try:
            input_token_info = jupiter_source.get_token_info(kwargs["input_mint"])
            output_token_info = jupiter_source.get_token_info(kwargs["output_mint"])
            print("input_token_info", input_token_info)
            print("output_token_info", output_token_info)
            input_token= input_token_info[0]
            output_token = output_token_info[0]
            
            result = jupiter_source.get_quote(
                input_mint=kwargs["input_mint"],
                output_mint=kwargs["output_mint"],
                amount=kwargs["amount"],
                slippage_bps=kwargs.get("slippage_bps"),
                swap_mode=kwargs.get("swap_mode", "ExactIn"),
                dexes=dexes,
                exclude_dexes=exclude_dexes,
                restrict_intermediate_tokens=kwargs.get("restrict_intermediate_tokens", True),
                only_direct_routes=kwargs.get("only_direct_routes", False),
                as_legacy_transaction=kwargs.get("as_legacy_transaction", False),
                platform_fee_bps=kwargs.get("platform_fee_bps"),
                max_accounts=kwargs.get("max_accounts", 64),
                dynamic_slippage=kwargs.get("dynamic_slippage", False)
            )
            result["input_token_info"] = input_token
            result["output_token_info"] = output_token
            
            return self._format_response("get_quote", result, **kwargs)
        except Exception as e:
            return f"Error getting quote: {str(e)}"
    
    def _handle_search_tokens(self, jupiter_source, **kwargs) -> str:
        """Handle search_tokens action."""
        if not kwargs.get("query"):
            return "Missing required field: query"
        
        try:
            result = jupiter_source.search_tokens(kwargs["query"])
            return self._format_response("search_tokens", result, **kwargs)
        except Exception as e:
            return f"Error searching tokens: {str(e)}"
    
    def _handle_get_token_info(self, jupiter_source, **kwargs) -> str:
        """Handle get_token_info action."""
        if not kwargs.get("mint_address"):
            return "Missing required field: mint_address"
        
        try:
            result = jupiter_source.get_token_info(kwargs["mint_address"])
            return self._format_response("get_token_info", result, **kwargs)
        except Exception as e:
            return f"Error getting token info: {str(e)}"
    
    def _handle_get_verified_tokens(self, jupiter_source, **kwargs) -> str:
        """Handle get_verified_tokens action."""
        if not kwargs.get("query"):
            return "Missing required field: query"
        
        try:
            result = jupiter_source.get_verified_tokens(kwargs["query"])
            return self._format_response("get_verified_tokens", result, **kwargs)
        except Exception as e:
            return f"Error getting verified tokens: {str(e)}"
    
    def _handle_get_token_by_symbol(self, jupiter_source, **kwargs) -> str:
        """Handle get_token_by_symbol action."""
        if not kwargs.get("query"):
            return "Missing required field: query (should be token symbol)"
        
        try:
            result = jupiter_source.get_token_by_symbol(kwargs["query"])
            return self._format_response("get_token_by_symbol", result, **kwargs)
        except Exception as e:
            return f"Error getting token by symbol: {str(e)}"
    
    def _handle_get_token_by_name(self, jupiter_source, **kwargs) -> str:
        """Handle get_token_by_name action."""
        if not kwargs.get("query"):
            return "Missing required field: query (should be token name)"
        
        try:
            result = jupiter_source.get_token_by_name(kwargs["query"])
            return self._format_response("get_token_by_name", result, **kwargs)
        except Exception as e:
            return f"Error getting token by name: {str(e)}"
    
    def _handle_get_multiple_tokens(self, jupiter_source, **kwargs) -> str:
        """Handle get_multiple_tokens action."""
        if not kwargs.get("mint_addresses"):
            return "Missing required field: mint_addresses"
        
        try:
            result = jupiter_source.get_multiple_tokens(kwargs["mint_addresses"])
            return self._format_response("get_multiple_tokens", result, **kwargs)
        except Exception as e:
            return f"Error getting multiple tokens: {str(e)}"
    
    def _handle_get_popular_tokens(self, jupiter_source, **kwargs) -> str:
        """Handle get_popular_tokens action."""
        try:
            result = jupiter_source.get_popular_tokens()
            return self._format_response("get_popular_tokens", result, **kwargs)
        except Exception as e:
            return f"Error getting popular tokens: {str(e)}"
    
    def _format_response(self, action: str, result: Dict[str, Any], **kwargs) -> str:
        """Format the response with both human-readable text and JSON data."""
        try:
            response_data = {
                "json_data": result,
                "action": action,
               
            }
            if action == "get_quote":
                response_data["user_action"] = True
           
            return response_data
                
        except Exception as e:
            error_response = {
                "human_readable": f"Error formatting response: {str(e)}\nRaw result: {json.dumps(result, indent=2)}",
                "json_data": result,
                "provide_quote_json": False,
                "action": action,
                "error": str(e)
            }
            return error_response
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async run method."""
        return self._run(action, **kwargs) 

jupiter_tools = [
    JupiterTool()
]