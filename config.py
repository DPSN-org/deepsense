"""
Configuration class for DeepSense Framework.
Documents all environment variables used throughout the framework and examples.

Note: The framework automatically loads .env files on import (via deepsense/__init__.py).
This config.py serves as documentation and optional validation.
"""

import os
from typing import Optional

# Note: .env file is automatically loaded by deepsense/__init__.py
# This class provides a centralized reference for all environment variables

class Config:
    """Configuration class documenting all environment variables used in DeepSense."""
    
    # ========== LLM Configuration ==========
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai", "anthropic", "google"
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    # ========== Database Configuration ==========
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    
    # ========== Sandbox Configuration ==========
    SANDBOX_URL: str = os.getenv("SANDBOX_URL", "http://localhost:8000/run")
    
    # ========== AWS S3 Configuration (Optional) ==========
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_BUCKET: str = os.getenv("AWS_BUCKET", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # ========== Datasource API Keys ==========
    # Helius (Solana blockchain data)
    HELIUS_API_KEY: str = os.getenv("HELIUS_API_KEY", "")
    
    # News API
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # GitHub API
    GITHUB_API_KEY: str = os.getenv("GITHUB_API_KEY", "")
    
    # OpenWeatherMap API
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    
    # Amadeus Flight API
    AMADEUS_CLIENT_ID: str = os.getenv("AMADEUS_CLIENT_ID", "")
    AMADEUS_CLIENT_SECRET: str = os.getenv("AMADEUS_CLIENT_SECRET", "")
    
    # DPSN Intelligence API
    DPSN_API_TOKEN: str = os.getenv("DPSN_API_TOKEN", "")
    
    # ========== Application Configuration ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ========== LangSmith Configuration (Optional) ==========
    LANGSMITH_TRACING: str = os.getenv("LANGSMITH_TRACING", "")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            bool: True if required configuration is present, False otherwise
        """
        required_keys = [
            "OPENAI_API_KEY",  # Required for default LLM provider
        ]
        
        missing_keys = []
        for key in required_keys:
            value = getattr(cls, key)
            if not value:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"⚠️  Missing required environment variables: {', '.join(missing_keys)}")
            print("Please check your .env file or environment variables.")
            return False
        
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """
        Get LLM configuration based on provider.
        
        Returns:
            dict: Configuration dictionary with provider, model, and API key
        """
        provider = cls.LLM_PROVIDER.lower()
        
        if provider == "openai":
            return {
                "provider": "openai",
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "model": cls.OPENAI_MODEL,  # Can be overridden
                "api_key": cls.ANTHROPIC_API_KEY
            }
        elif provider == "google":
            return {
                "provider": "google",
                "model": cls.GEMINI_MODEL,
                "api_key": cls.GEMINI_API_KEY
            }
        else:
            return {
                "provider": "openai",
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY
            }
    
    @classmethod
    def get_datasource_keys(cls) -> dict:
        """
        Get all datasource API keys.
        
        Returns:
            dict: Dictionary of datasource names and their API keys
        """
        return {
            "helius": cls.HELIUS_API_KEY,
            "news": cls.NEWS_API_KEY,
            "github": cls.GITHUB_API_KEY,
            "openweather": cls.OPENWEATHER_API_KEY,
            "amadeus_client_id": cls.AMADEUS_CLIENT_ID,
            "amadeus_client_secret": cls.AMADEUS_CLIENT_SECRET,
            "dpsn": cls.DPSN_API_TOKEN,
        }
    
    @classmethod
    def print_config(cls, show_secrets: bool = False) -> None:
        """
        Print current configuration (optionally hiding secrets).
        
        Args:
            show_secrets: If True, show API keys. If False, mask them.
        """
        print("=" * 60)
        print("DeepSense Configuration")
        print("=" * 60)
        
        print("\n📡 LLM Configuration:")
        print(f"  Provider: {cls.LLM_PROVIDER}")
        print(f"  Model: {cls.OPENAI_MODEL}")
        if show_secrets:
            print(f"  OpenAI API Key: {cls.OPENAI_API_KEY[:10]}..." if cls.OPENAI_API_KEY else "  OpenAI API Key: (not set)")
            print(f"  Anthropic API Key: {cls.ANTHROPIC_API_KEY[:10]}..." if cls.ANTHROPIC_API_KEY else "  Anthropic API Key: (not set)")
            print(f"  Gemini API Key: {cls.GEMINI_API_KEY[:10]}..." if cls.GEMINI_API_KEY else "  Gemini API Key: (not set)")
        else:
            print(f"  OpenAI API Key: {'✅ Set' if cls.OPENAI_API_KEY else '❌ Not set'}")
            print(f"  Anthropic API Key: {'✅ Set' if cls.ANTHROPIC_API_KEY else '❌ Not set'}")
            print(f"  Gemini API Key: {'✅ Set' if cls.GEMINI_API_KEY else '❌ Not set'}")
        
        print("\n💾 Database Configuration:")
        print(f"  MongoDB URI: {cls.MONGODB_URI}")
        
        print("\n🔧 Sandbox Configuration:")
        print(f"  Sandbox URL: {cls.SANDBOX_URL}")
        
        print("\n☁️  AWS S3 Configuration:")
        print(f"  Region: {cls.AWS_REGION}")
        print(f"  Bucket: {cls.AWS_BUCKET if cls.AWS_BUCKET else '(not set)'}")
        print(f"  Access Key: {'✅ Set' if cls.AWS_ACCESS_KEY_ID else '❌ Not set'}")
        
        print("\n🔑 Datasource API Keys:")
        datasource_keys = cls.get_datasource_keys()
        for name, key in datasource_keys.items():
            if name in ["amadeus_client_id", "amadeus_client_secret"]:
                status = "✅ Set" if key else "❌ Not set"
                print(f"  {name}: {status}")
            else:
                status = "✅ Set" if key else "❌ Not set"
                print(f"  {name}: {status}")
        
        print("\n⚙️  Application Configuration:")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        
        print("=" * 60)

# Global config instance
config = Config()

