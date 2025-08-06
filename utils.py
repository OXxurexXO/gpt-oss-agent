#!/usr/bin/env python3
"""
Utility functions for GPT-OSS Agent with error handling and retry logic
"""

import time
import logging
import functools
from typing import Any, Callable, Optional, Dict, List
import ollama
from exceptions import ModelError, ModelTimeoutError, ModelNotFoundError

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f} seconds..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator

def validate_model_availability(model_name: str) -> bool:
    """
    Check if a model is available in Ollama
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if model is available, False otherwise
    """
    try:
        models = ollama.list()
        available_models = [m['name'] for m in models.get('models', [])]
        return any(model_name in m for m in available_models)
    except Exception as e:
        logger.error(f"Failed to check model availability: {e}")
        return False

@retry_with_backoff(max_retries=3, exceptions=(ModelError, ConnectionError))
def safe_ollama_chat(
    model: str,
    messages: List[Dict[str, str]],
    timeout: Optional[float] = 300.0,
    fallback_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Safely call Ollama chat API with error handling and retry logic
    
    Args:
        model: Model name to use
        messages: Chat messages
        timeout: Timeout in seconds
        fallback_model: Fallback model to use if primary fails
        
    Returns:
        Ollama response dictionary
        
    Raises:
        ModelNotFoundError: If model is not found
        ModelTimeoutError: If operation times out
        ModelError: For other model-related errors
    """
    try:
        # Check if model is available
        if not validate_model_availability(model):
            if fallback_model and validate_model_availability(fallback_model):
                logger.warning(f"Model {model} not found, using fallback: {fallback_model}")
                model = fallback_model
            else:
                raise ModelNotFoundError(f"Model {model} not found and no valid fallback available")
        
        # Make the API call with timeout
        response = ollama.chat(
            model=model,
            messages=messages,
            options={
                'timeout': timeout
            }
        )
        
        if not response or 'message' not in response:
            raise ModelError(f"Invalid response from model {model}")
        
        return response
        
    except ollama.ResponseError as e:
        if 'timeout' in str(e).lower():
            raise ModelTimeoutError(f"Model {model} timed out after {timeout} seconds")
        elif 'not found' in str(e).lower():
            raise ModelNotFoundError(f"Model {model} not found")
        else:
            raise ModelError(f"Ollama error: {e}")
    except ConnectionError as e:
        logger.error(f"Connection error to Ollama: {e}")
        raise ModelError(f"Failed to connect to Ollama service. Is it running?")
    except Exception as e:
        logger.error(f"Unexpected error in Ollama chat: {e}")
        raise ModelError(f"Unexpected error: {e}")

@retry_with_backoff(max_retries=2, exceptions=(ModelError,))
def safe_ollama_embeddings(
    model: str,
    prompt: str,
    timeout: Optional[float] = 60.0
) -> List[float]:
    """
    Safely generate embeddings with error handling
    
    Args:
        model: Model name to use
        prompt: Text to embed
        timeout: Timeout in seconds
        
    Returns:
        Embedding vector
        
    Raises:
        ModelError: If embedding generation fails
    """
    try:
        response = ollama.embeddings(
            model=model,
            prompt=prompt,
            options={'timeout': timeout}
        )
        
        if not response or 'embedding' not in response:
            raise ModelError(f"Invalid embedding response from model {model}")
        
        return response['embedding']
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise ModelError(f"Embedding generation failed: {e}")

def sanitize_input(user_input: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        user_input: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input string
    """
    if not user_input:
        return ""
    
    # Truncate if too long
    if len(user_input) > max_length:
        logger.warning(f"Input truncated from {len(user_input)} to {max_length} characters")
        user_input = user_input[:max_length]
    
    # Remove potentially dangerous characters for shell commands
    dangerous_chars = ['`', '$', '\\', '\x00', '\n\r']
    for char in dangerous_chars:
        if char in user_input:
            logger.warning(f"Removed dangerous character '{char}' from input")
            user_input = user_input.replace(char, '')
    
    return user_input.strip()

def validate_file_path(path: str, base_dir: Optional[str] = None) -> bool:
    """
    Validate file path to prevent directory traversal attacks
    
    Args:
        path: Path to validate
        base_dir: Base directory to restrict access to
        
    Returns:
        True if path is safe, False otherwise
    """
    import os
    from pathlib import Path
    
    try:
        # Resolve to absolute path
        abs_path = Path(path).resolve()
        
        # Check if trying to access parent directories
        if '..' in str(path):
            logger.warning(f"Path contains parent directory reference: {path}")
            return False
        
        # If base_dir is provided, ensure path is within it
        if base_dir:
            base_abs = Path(base_dir).resolve()
            if not str(abs_path).startswith(str(base_abs)):
                logger.warning(f"Path {path} is outside base directory {base_dir}")
                return False
        
        # Check for suspicious patterns
        suspicious_patterns = ['/etc/', '/sys/', '/proc/', '~/', '/root/']
        for pattern in suspicious_patterns:
            if pattern in str(abs_path):
                logger.warning(f"Suspicious path pattern detected: {pattern} in {path}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False

class ErrorHandler:
    """Context manager for handling errors gracefully"""
    
    def __init__(self, operation_name: str, default_return: Any = None, reraise: bool = False):
        self.operation_name = operation_name
        self.default_return = default_return
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error in {self.operation_name}: {exc_val}")
            if self.reraise:
                return False
            return True
        return False