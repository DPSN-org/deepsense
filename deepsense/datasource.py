"""
Core Datasource Module for DeepSense Framework
Handles API client management and data retrieval for various data sources.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging
import inspect
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tool metadata storage - maps (class_name, method_name) to tool metadata
_tool_registry: Dict[str, Dict[str, Any]] = {}

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

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    user_action: bool = False
):
    """
    Decorator to mark datasource methods as tools.
    
    Args:
        name: Tool name (defaults to method name). 
              If multiple methods share the same name, they become a unified tool.
        description: Tool description (defaults to method docstring)
        user_action: If True, marks this tool as returning user actions
    
    Example:
        @tool(name="jupiter_ag_apis", user_action=True)
        def get_quote(self, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Call {func.__name__} on datasource"
        
        # Get class name from function's qualname
        qualname_parts = func.__qualname__.split('.')
        if len(qualname_parts) > 1:
            class_name = qualname_parts[-2]
            method_name = qualname_parts[-1]
            registry_key = f"{class_name}.{method_name}"
        else:
            # If no class in qualname, try to get from function's __self__ or annotations
            registry_key = func.__name__
        
        # Store metadata
        _tool_registry[registry_key] = {
            "name": tool_name,
            "description": tool_desc,
            "user_action": user_action,
            "func": func,
            "method_name": func.__name__
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

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
    
    def get_tools(self) -> List['Tool']:
        """
        Automatically create LangChain tools from methods decorated with @tool.
        Methods sharing the same tool name become a unified tool with action parameter.
        
        Returns:
            List of LangChain Tool instances
        """
        try:
            from langchain_core.tools import Tool
            from pydantic import BaseModel, Field, create_model
        except ImportError:
            raise ImportError("langchain_core.tools and pydantic are required to create tools from datasources")
        
        # Collect decorated methods
        decorated_methods: List[Dict[str, Any]] = []
        class_name = self.__class__.__name__
        
        # Check all classes in MRO (Method Resolution Order) to find decorated methods
        for cls in self.__class__.__mro__:
            if cls == object or cls == ABC:
                continue
            
            for method_name in dir(cls):
                if method_name.startswith('_'):
                    continue
                
                # Get the method from the class
                method = getattr(cls, method_name, None)
                if not method or not callable(method):
                    continue
                
                # Check if method has tool metadata
                registry_key = f"{cls.__name__}.{method_name}"
                if registry_key not in _tool_registry:
                    continue
                
                # Get the bound method from instance
                bound_method = getattr(self, method_name)
                
                metadata = _tool_registry[registry_key].copy()
                metadata["method"] = bound_method
                decorated_methods.append(metadata)
        
        if not decorated_methods:
            return []
        
        # Group methods by tool name
        tools_by_name: Dict[str, List[Dict[str, Any]]] = {}
        for method_data in decorated_methods:
            tool_name = method_data["name"]
            if tool_name not in tools_by_name:
                tools_by_name[tool_name] = []
            tools_by_name[tool_name].append(method_data)
        
        tools = []
        
        for tool_name, methods in tools_by_name.items():
            if len(methods) > 1:
                # Multiple methods → create unified tool with action parameter
                action_descriptions = []
                all_params: Dict[str, Dict[str, Any]] = {}
                
                for method_data in methods:
                    method_name = method_data["method_name"]
                    method = method_data["method"]
                    docstring = inspect.getdoc(method) or f"Call {method_name}"
                    
                    # Extract first sentence from docstring for action description
                    first_sentence = docstring.split('.')[0].strip()
                    action_descriptions.append(f"- '{method_name}': {first_sentence}")
                    
                    # Collect parameters from method signature
                    sig = inspect.signature(method)
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        
                        # Get parameter type
                        param_type = param.annotation
                        if param_type == inspect.Parameter.empty:
                            param_type = str
                        
                        # Get default value
                        if param.default == inspect.Parameter.empty:
                            param_default = ...
                        else:
                            param_default = param.default
                        
                        # Get description from docstring or param name
                        param_desc = f"Parameter {param_name}"
                        
                        # Store parameter info (handle conflicts by keeping first occurrence)
                        if param_name not in all_params:
                            all_params[param_name] = {
                                "type": param_type,
                                "default": param_default,
                                "description": param_desc
                            }
                
                # Generate action field description
                action_description = f"Action to perform:\n\n{chr(10).join(action_descriptions)}"
                
                # Create input schema with action parameter and all collected parameters
                fields = {
                    "action": (str, Field(description=action_description))
                }
                
                # Add all parameters as optional (since they're used by different actions)
                for param_name, param_info in all_params.items():
                    # Make all params optional for unified tools
                    if param_info["default"] == ...:
                        fields[param_name] = (Optional[param_info["type"]], Field(default=None, description=param_info["description"]))
                    else:
                        fields[param_name] = (param_info["type"], Field(default=param_info["default"], description=param_info["description"]))
                
                # Create dynamic input schema
                InputSchema = create_model(f"{tool_name.replace(' ', '_')}Input", **fields)
                
                # Generate tool description from first method or combine descriptions
                tool_description = methods[0].get("description", "")
                if not tool_description or len(methods) > 1:
                    # Combine descriptions
                    desc_parts = [f"Unified tool for {tool_name} with the following actions:"]
                    for method_data in methods:
                        method_name = method_data["method_name"]
                        docstring = inspect.getdoc(method_data["method"]) or f"Call {method_name}"
                        desc_parts.append(f"- {method_name}: {docstring.split('.')[0]}")
                    tool_description = "\n".join(desc_parts)
                
                # Create unified tool function
                def create_unified_func(methods_list):
                    def unified_func(action: str, **kwargs) -> str:
                        # Find method by action name
                        for method_data in methods_list:
                            if method_data["method_name"] == action:
                                method = method_data["method"]
                                try:
                                    # Filter kwargs to only include method's actual parameters
                                    sig = inspect.signature(method)
                                    method_params = {k: v for k, v in kwargs.items() 
                                                   if k in sig.parameters and k != 'self'}
                                    
                                    result = method(**method_params)
                                    
                                    # Handle user_action flag
                                    if method_data.get("user_action"):
                                        if isinstance(result, dict):
                                            if "user_action" not in result:
                                                result["user_action"] = True
                                        else:
                                            result = {
                                                "user_action": True,
                                                "data": result,
                                                "timestamp": datetime.now().isoformat(),
                                                "source": self.config.name
                                            }
                                    
                                    return json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                                except Exception as e:
                                    logger.error(f"Error in unified tool {tool_name} action {action}: {e}")
                                    return json.dumps({"error": str(e), "action": action}, indent=2)
                        return json.dumps({"error": f"Unknown action: {action}", "available_actions": [m["method_name"] for m in methods_list]}, indent=2)
                    return unified_func
                
                tools.append(Tool(
                    name=tool_name,
                    description=tool_description,
                    func=create_unified_func(methods),
                    args_schema=InputSchema
                ))
            else:
                # Single method → create simple tool
                method_data = methods[0]
                method = method_data["method"]
                method_name = method_data["method_name"]
                
                # Get method signature
                sig = inspect.signature(method)
                params = {name: param for name, param in sig.parameters.items() if name != 'self'}
                
                def create_simple_func(method_func, user_action_flag):
                    def simple_func(*args, **kwargs) -> str:
                        try:
                            result = method_func(*args, **kwargs)
                            
                            # Handle user_action flag
                            if user_action_flag:
                                if isinstance(result, dict):
                                    if "user_action" not in result:
                                        result["user_action"] = True
                                else:
                                    result = {
                                        "user_action": True,
                                        "data": result,
                                        "timestamp": datetime.now().isoformat(),
                                        "source": self.config.name
                                    }
                            
                            return json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                        except Exception as e:
                            logger.error(f"Error in tool {tool_name}: {e}")
                            return json.dumps({"error": str(e)}, indent=2)
                    return simple_func
                
                tools.append(Tool(
                    name=tool_name,
                    description=method_data["description"],
                    func=create_simple_func(method, method_data.get("user_action", False))
                ))
        
        return tools

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
    
    def create_tool_from_method(
        self,
        source_name: str,
        method_name: str,
        tool_name: Optional[str] = None,
        tool_description: Optional[str] = None,
        use_user_action: bool = False
    ) -> 'Tool':
        """
        Create a LangChain Tool from a datasource method.
        
        Args:
            source_name: Name of the registered datasource
            method_name: Name of the method to call on the datasource
            tool_name: Optional custom tool name (defaults to method_name)
            tool_description: Optional tool description
            use_user_action: If True, wraps result with user_action flag
            
        Returns:
            LangChain Tool instance
        """
        try:
            from langchain_core.tools import Tool
        except ImportError:
            raise ImportError("langchain_core.tools is required to create tools from datasources")
        
        source = self.get_source(source_name)
        if not source:
            raise ValueError(f"Data source '{source_name}' not found")
        
        if not hasattr(source, method_name):
            raise ValueError(f"Method '{method_name}' not found on datasource '{source_name}'")
        
        method = getattr(source, method_name)
        if not callable(method):
            raise ValueError(f"'{method_name}' is not a callable method")
        
        # Get method signature for documentation
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Remove 'self' if present
        if params and params[0] == 'self':
            params = params[1:]
        
        def tool_func(*args, **kwargs) -> str:
            """Tool function that calls the datasource method."""
            try:
                # Call the datasource method
                result = method(*args, **kwargs)
                
                # If use_user_action is True and result doesn't already have user_action, wrap it
                if use_user_action and isinstance(result, dict) and result.get("user_action") != True:
                    result = {
                        "user_action": True,
                        "data": result,
                        "timestamp": datetime.now().isoformat(),
                        "source": source_name
                    }
                elif use_user_action and not isinstance(result, dict):
                    result = {
                        "user_action": True,
                        "data": {"result": result},
                        "timestamp": datetime.now().isoformat(),
                        "source": source_name
                    }
                
                # Always return as JSON string for tool compatibility
                if isinstance(result, str):
                    return result
                return json.dumps(result, indent=2)
            except Exception as e:
                error_result = {"error": str(e), "source": source_name, "method": method_name}
                return json.dumps(error_result, indent=2)
        
        # Generate tool name and description
        final_tool_name = tool_name or f"{source_name}_{method_name}"
        final_description = tool_description or f"Call {method_name} on {source_name} datasource"
        
        return Tool(
            name=final_tool_name,
            description=final_description,
            func=tool_func
        )
    
    def create_tools_from_source(
        self,
        source_name: str,
        method_filter: Optional[Callable[[str], bool]] = None,
        use_user_action: bool = False
    ) -> List['Tool']:
        """
        Automatically create tools from all public methods of a datasource.
        
        Args:
            source_name: Name of the registered datasource
            method_filter: Optional function to filter which methods to include
                          (takes method name, returns True to include)
            use_user_action: If True, all methods will wrap results with user_action flag
            
        Returns:
            List of LangChain Tool instances
        """
        try:
            from langchain_core.tools import Tool
        except ImportError:
            raise ImportError("langchain_core.tools is required to create tools from datasources")
        
        source = self.get_source(source_name)
        if not source:
            raise ValueError(f"Data source '{source_name}' not found")
        
        tools = []
        
        # Get all public methods (not starting with _)
        for method_name in dir(source):
            if method_name.startswith('_'):
                continue
            
            method = getattr(source, method_name)
            if not callable(method):
                continue
            
            # Skip special methods and base class methods
            if method_name in ['get', 'post', 'rpc_post', 'get_data', 'format_with_user_action', 'health_check']:
                continue
            
            # Apply filter if provided
            if method_filter and not method_filter(method_name):
                continue
            
            # Create tool from this method
            try:
                tool = self.create_tool_from_method(
                    source_name=source_name,
                    method_name=method_name,
                    use_user_action=use_user_action
                )
                tools.append(tool)
            except Exception as e:
                logger.warning(f"Failed to create tool from {source_name}.{method_name}: {e}")
                continue
        
        return tools

