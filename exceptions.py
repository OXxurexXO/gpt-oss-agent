#!/usr/bin/env python3
"""
Custom exception classes for GPT-OSS Agent
"""

class GPTOSSAgentError(Exception):
    """Base exception for all GPT-OSS Agent errors"""
    pass

class ModelError(GPTOSSAgentError):
    """Errors related to model operations"""
    pass

class ModelNotFoundError(ModelError):
    """Raised when a model is not found or not available"""
    pass

class ModelTimeoutError(ModelError):
    """Raised when a model operation times out"""
    pass

class FileOperationError(GPTOSSAgentError):
    """Errors related to file operations"""
    pass

class PermissionError(FileOperationError):
    """Raised when lacking permissions for file operations"""
    pass

class FileNotFoundError(FileOperationError):
    """Raised when a file is not found"""
    pass

class KnowledgeBaseError(GPTOSSAgentError):
    """Errors related to knowledge base operations"""
    pass

class IndexingError(KnowledgeBaseError):
    """Raised when indexing operations fail"""
    pass

class SearchError(KnowledgeBaseError):
    """Raised when search operations fail"""
    pass

class DatabaseError(KnowledgeBaseError):
    """Raised when database operations fail"""
    pass

class ValidationError(GPTOSSAgentError):
    """Raised when input validation fails"""
    pass

class ConfigurationError(GPTOSSAgentError):
    """Raised when configuration is invalid or missing"""
    pass