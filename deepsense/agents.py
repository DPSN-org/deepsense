"""
Agent definitions for DeepSense Framework
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

class Agent:
    """Base agent class."""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0,
        api_key: Optional[str] = None
    ):
        """
        Initialize an agent.
        
        Args:
            name: Agent name
            system_prompt: System prompt for the agent
            model: LLM model name
            temperature: Temperature for LLM
            api_key: OpenAI API key
        """
        self.name = name
        self.system_prompt = system_prompt
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key
        )
    
    def get_system_message(self) -> SystemMessage:
        """Get the system message for this agent."""
        return SystemMessage(content=self.system_prompt)

