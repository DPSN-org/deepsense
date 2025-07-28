"""
Token estimation utilities for LangGraph applications.
"""

import json
import tiktoken
from typing import Union, Dict, List, Any


def estimate_token_count(data: Union[Dict, List, str], model: str = "claude-3-opus") -> int:
    """
    Estimate the number of tokens a given object will consume for a specified model.
    
    Args:
        data: dict, list, str, or any JSON-serializable object
        model: str — "gpt-4", "gpt-4o", "gpt-3.5-turbo" for OpenAI, or "claude" for Anthropic

    Returns:
        Estimated token count (int)
    """
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, separators=(',', ':'))  # compact representation
    elif isinstance(data, str):
        data_str = data
    else:
        raise ValueError("Data must be a JSON-serializable dict, list, or string")

    # Estimate for Claude
    if "claude" in model.lower():
        # Claude roughly uses 1 token per 3.5 characters
        return int(len(data_str) / 3.5)

    # Estimate for OpenAI models using tiktoken
    if not tiktoken:
        raise ImportError("Please install tiktoken: pip install tiktoken")

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")  # fallback

    tokens = encoding.encode(data_str)
    return len(tokens)


def estimate_tokens_for_messages(messages: List[Dict[str, Any]], model: str = "gpt-4o") -> int:
    """
    Estimate token count for a list of messages (like in a conversation).
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model name for token estimation
        
    Returns:
        Estimated total token count
    """
    total_tokens = 0
    
    for message in messages:
        # Add tokens for role
        total_tokens += estimate_token_count(message.get('role', ''), model)
        
        # Add tokens for content
        content = message.get('content', '')
        if isinstance(content, str):
            total_tokens += estimate_token_count(content, model)
        elif isinstance(content, list):
            # Handle multimodal content (text + images, etc.)
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    total_tokens += estimate_token_count(item.get('text', ''), model)
    
    return total_tokens


def chunk_data_by_tokens(data: str, max_tokens: int = 30000, model: str = "gpt-4o") -> List[str]:
    """
    Split data into chunks based on token count.
    
    Args:
        data: String data to chunk
        max_tokens: Maximum tokens per chunk
        model: Model name for token estimation
        
    Returns:
        List of data chunks
    """
    
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    print("splitting data by tokens")
    # Split by lines to avoid breaking in the middle of content
    lines = data.split('\n')
    # print(lines)
    # print("lines", len(lines))
    for line in lines:
        line_tokens = estimate_token_count(line, model)
        
        if  line_tokens < max_tokens:
            chunks.append(line)
        else:
            # Single line is too long, split it by characters and estimate tokens
            # Split into smaller pieces that fit within max_tokens
            remaining_line = line
            while len(remaining_line) > 0:
                print("length of remaining line", len(remaining_line))
                # Estimate how many characters we can fit
                char_limit = max_tokens * 4  # Rough estimate: 1 token ≈ 4 characters
                if len(remaining_line) <= char_limit:
                    chunks.append(remaining_line)
                    break
                else:
                    # Split at a reasonable boundary (space, comma, etc.)
                    split_point = char_limit
                    for i in range(char_limit, max(0, char_limit - 100), -1):
                        if remaining_line[i] in ',.;!?':
                            split_point = i + 1
                            break
                    
                    chunks.append(remaining_line[:split_point])
                    remaining_line = remaining_line[split_point:]
        
    
    # Add the last chunk if not empty
   
    
    return chunks 