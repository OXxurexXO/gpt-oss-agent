#!/usr/bin/env python3
"""
File Agent - Natural language file system operations using local GPT-OSS models
Enhanced version with comprehensive error handling and safety features
"""

import os
import sys
import json
import shutil
import subprocess
import glob
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager

# Import our enhanced utilities and exceptions
from exceptions import (
    FileOperationError, PermissionError as GPTPermissionError,
    FileNotFoundError as GPTFileNotFoundError, ValidationError
)
from utils import (
    retry_with_backoff, safe_ollama_chat, sanitize_input,
    validate_file_path, ErrorHandler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_COMMAND_OUTPUT = 50000  # 50KB
SAFE_DIRECTORIES = [os.getcwd(), '/tmp', os.path.expanduser('~/Downloads')]
DANGEROUS_COMMANDS = ['rm -rf /', 'format', 'dd if=', 'mkfs', ':(){ :|:& };:']

class SafeFileOperations:
    """Enhanced file operations with safety checks and error handling"""
    
    @staticmethod
    def validate_path(path: str) -> str:
        """Validate and sanitize file path"""
        if not validate_file_path(path):
            raise ValidationError(f"Invalid or unsafe path: {path}")
        return os.path.abspath(path)
    
    @staticmethod
    def check_file_size(path: str) -> bool:
        """Check if file size is within safe limits"""
        try:
            size = os.path.getsize(path)
            if size > MAX_FILE_SIZE:
                raise FileOperationError(f"File too large: {size} bytes (max: {MAX_FILE_SIZE})")
            return True
        except OSError as e:
            raise FileOperationError(f"Cannot check file size: {e}")
    
    @staticmethod
    @retry_with_backoff(max_retries=2, exceptions=(OSError,))
    def list_files(path: str = ".") -> List[str]:
        """List files in directory with error handling"""
        try:
            safe_path = SafeFileOperations.validate_path(path)
            if not os.path.exists(safe_path):
                raise GPTFileNotFoundError(f"Directory not found: {safe_path}")
            if not os.path.isdir(safe_path):
                raise FileOperationError(f"Not a directory: {safe_path}")
            
            files = os.listdir(safe_path)
            return sorted(files)
        except PermissionError:
            raise GPTPermissionError(f"Permission denied: {path}")
        except Exception as e:
            logger.error(f"Failed to list files in {path}: {e}")
            raise FileOperationError(f"Failed to list files: {e}")
    
    @staticmethod
    @retry_with_backoff(max_retries=2, exceptions=(OSError,))
    def read_file(path: str) -> str:
        """Read file content with safety checks"""
        try:
            safe_path = SafeFileOperations.validate_path(path)
            if not os.path.exists(safe_path):
                raise GPTFileNotFoundError(f"File not found: {safe_path}")
            if not os.path.isfile(safe_path):
                raise FileOperationError(f"Not a file: {safe_path}")
            
            SafeFileOperations.check_file_size(safe_path)
            
            with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return content
        except PermissionError:
            raise GPTPermissionError(f"Permission denied: {path}")
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise FileOperationError(f"Failed to read file: {e}")
    
    @staticmethod
    def write_file(path: str, content: str, backup: bool = True) -> str:
        """Write content to file with optional backup"""
        try:
            safe_path = SafeFileOperations.validate_path(path)
            
            # Create backup if file exists
            if backup and os.path.exists(safe_path):
                backup_path = f"{safe_path}.backup"
                shutil.copy2(safe_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Ensure parent directory exists
            parent_dir = os.path.dirname(safe_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File '{safe_path}' written successfully."
        except PermissionError:
            raise GPTPermissionError(f"Permission denied: {path}")
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise FileOperationError(f"Failed to write file: {e}")
    
    @staticmethod
    def create_directory(path: str) -> str:
        """Create directory with safety checks"""
        try:
            safe_path = SafeFileOperations.validate_path(path)
            
            if os.path.exists(safe_path):
                if os.path.isdir(safe_path):
                    return f"Directory already exists: {safe_path}"
                else:
                    raise FileOperationError(f"Path exists but is not a directory: {safe_path}")
            
            os.makedirs(safe_path, exist_ok=True)
            return f"Directory '{safe_path}' created successfully."
        except PermissionError:
            raise GPTPermissionError(f"Permission denied: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise FileOperationError(f"Failed to create directory: {e}")
    
    @staticmethod
    def delete_file(path: str, confirm: bool = True) -> str:
        """Delete file or directory with confirmation"""
        try:
            safe_path = SafeFileOperations.validate_path(path)
            
            if not os.path.exists(safe_path):
                raise GPTFileNotFoundError(f"Path not found: {safe_path}")
            
            # Safety check for important directories
            protected_paths = ['/', '/home', '/etc', '/usr', '/var', '/bin', '/sbin']
            if any(safe_path == p or safe_path.startswith(p + '/') for p in protected_paths):
                raise ValidationError(f"Cannot delete protected path: {safe_path}")
            
            if os.path.isdir(safe_path):
                shutil.rmtree(safe_path)
                return f"Directory '{safe_path}' deleted successfully."
            else:
                os.remove(safe_path)
                return f"File '{safe_path}' deleted successfully."
        except PermissionError:
            raise GPTPermissionError(f"Permission denied: {path}")
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            raise FileOperationError(f"Failed to delete: {e}")
    
    @staticmethod
    def move_file(source: str, destination: str) -> str:
        """Move or rename file/directory with validation"""
        try:
            safe_source = SafeFileOperations.validate_path(source)
            safe_dest = SafeFileOperations.validate_path(destination)
            
            if not os.path.exists(safe_source):
                raise GPTFileNotFoundError(f"Source not found: {safe_source}")
            
            # Ensure destination parent directory exists
            dest_parent = os.path.dirname(safe_dest)
            if dest_parent and not os.path.exists(dest_parent):
                os.makedirs(dest_parent, exist_ok=True)
            
            shutil.move(safe_source, safe_dest)
            return f"Moved '{safe_source}' to '{safe_dest}' successfully."
        except PermissionError:
            raise GPTPermissionError(f"Permission denied")
        except Exception as e:
            logger.error(f"Failed to move {source} to {destination}: {e}")
            raise FileOperationError(f"Failed to move file: {e}")
    
    @staticmethod
    def search_file_content(file_path: str, search_string: str) -> str:
        """Search for text within a file with error handling"""
        try:
            safe_path = SafeFileOperations.validate_path(file_path)
            if not os.path.exists(safe_path):
                raise GPTFileNotFoundError(f"File not found: {safe_path}")
            
            SafeFileOperations.check_file_size(safe_path)
            
            matching_lines = []
            with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    if search_string in line:
                        matching_lines.append(f"{line_num}: {line.strip()}")
                    if len(matching_lines) > 100:  # Limit results
                        matching_lines.append("... (results truncated)")
                        break
            
            if not matching_lines:
                return "No matching lines found."
            return "\n".join(matching_lines)
        except Exception as e:
            logger.error(f"Failed to search in {file_path}: {e}")
            raise FileOperationError(f"Failed to search file: {e}")
    
    @staticmethod
    def run_shell_command(command: str, timeout: int = 30) -> str:
        """Run shell command with safety checks and timeout"""
        try:
            # Sanitize and validate command
            command = sanitize_input(command, max_length=1000)
            
            # Check for dangerous commands
            for dangerous in DANGEROUS_COMMANDS:
                if dangerous in command.lower():
                    raise ValidationError(f"Dangerous command detected: {dangerous}")
            
            # Run with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            
            # Truncate output if too long
            output = result.stdout[:MAX_COMMAND_OUTPUT]
            errors = result.stderr[:MAX_COMMAND_OUTPUT]
            
            if len(result.stdout) > MAX_COMMAND_OUTPUT:
                output += "\n... (output truncated)"
            if len(result.stderr) > MAX_COMMAND_OUTPUT:
                errors += "\n... (errors truncated)"
            
            return f"Output: {output}\nErrors: {errors}\nExit code: {result.returncode}"
        except subprocess.TimeoutExpired:
            raise FileOperationError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            raise FileOperationError(f"Failed to run command: {e}")
    
    @staticmethod
    def glob_files(pattern: str) -> List[str]:
        """Find files by pattern with safety checks"""
        try:
            # Validate pattern doesn't try to access parent directories
            if '..' in pattern:
                raise ValidationError("Pattern cannot contain parent directory references")
            
            matches = glob.glob(pattern, recursive=True)
            # Limit results to prevent memory issues
            if len(matches) > 1000:
                matches = matches[:1000]
                matches.append("... (results truncated)")
            
            return matches if matches else [f"No files found matching: {pattern}"]
        except Exception as e:
            logger.error(f"Failed to glob files with pattern {pattern}: {e}")
            raise FileOperationError(f"Failed to find files: {e}")

class EnhancedFileAgent:
    """AI agent for natural language file system operations with enhanced error handling"""
    
    def __init__(self, model: str = "gpt-oss:20b", fallback_model: str = "gpt-oss:7b"):
        self.model = model
        self.fallback_model = fallback_model
        self.conversation_history = []
        self.safe_ops = SafeFileOperations()
        
        # Test Ollama connection
        try:
            import ollama
            ollama.list()
            logger.info("Connected to Ollama successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            print("❌ Failed to connect to Ollama. Make sure it's running: ollama serve")
            sys.exit(1)
    
    def _create_tool_registry(self) -> Dict[str, callable]:
        """Create registry of safe tools"""
        return {
            'list_files': self.safe_ops.list_files,
            'read_file': self.safe_ops.read_file,
            'write_file': self.safe_ops.write_file,
            'create_directory': self.safe_ops.create_directory,
            'delete_file': self.safe_ops.delete_file,
            'move_file': self.safe_ops.move_file,
            'search_file_content': self.safe_ops.search_file_content,
            'run_shell_command': self.safe_ops.run_shell_command,
            'glob_files': self.safe_ops.glob_files,
        }
    
    def execute_command(self, user_input: str) -> Optional[str]:
        """Execute user command with comprehensive error handling"""
        try:
            # Sanitize input
            user_input = sanitize_input(user_input)
            
            # Get AI suggestion with fallback
            messages = [
                {'role': 'system', 'content': self._get_system_prompt()},
                {'role': 'user', 'content': user_input}
            ]
            
            response = safe_ollama_chat(
                model=self.model,
                messages=messages,
                fallback_model=self.fallback_model,
                timeout=60
            )
            
            response_text = response['message']['content']
            logger.info(f"AI response: {response_text}")
            
            # Parse and execute with error handling
            tools = self._create_tool_registry()
            results = []
            
            for tool_call in self._parse_tool_calls(response_text):
                tool_name = tool_call['name']
                args = tool_call['args']
                
                if tool_name not in tools:
                    logger.warning(f"Unknown tool: {tool_name}")
                    continue
                
                try:
                    with ErrorHandler(f"executing {tool_name}"):
                        result = tools[tool_name](*args)
                        results.append(f"✅ {tool_name}: {result}")
                except Exception as e:
                    error_msg = f"❌ {tool_name} failed: {e}"
                    logger.error(error_msg)
                    results.append(error_msg)
            
            return "\n".join(results) if results else "No operations performed"
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"Error: {e}"
    
    def _get_system_prompt(self) -> str:
        """Get enhanced system prompt with safety instructions"""
        return """You are a safe and helpful file system agent. 

SAFETY RULES:
1. Never delete system files or directories
2. Always validate paths before operations
3. Create backups before modifying files
4. Limit command output to reasonable sizes
5. Refuse dangerous shell commands

Available tools:
- list_files(path) - List files safely
- read_file(path) - Read with size limits
- write_file(path, content) - Write with backup
- create_directory(path) - Create safely
- delete_file(path) - Delete with confirmation
- move_file(source, dest) - Move with validation
- search_file_content(path, text) - Search with limits
- run_shell_command(cmd) - Run with timeout and safety
- glob_files(pattern) - Find files safely

Respond with tool calls in format: tool_name(arg1, arg2)
"""
    
    def _parse_tool_calls(self, response_text: str) -> List[Dict]:
        """Parse tool calls from AI response with error handling"""
        tool_calls = []
        tools = self._create_tool_registry()
        
        for line in response_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            for tool_name in tools:
                if line.startswith(tool_name + '(') and line.endswith(')'):
                    try:
                        args_str = line[len(tool_name)+1:-1]
                        args = self._parse_arguments(args_str)
                        tool_calls.append({
                            'name': tool_name,
                            'args': args
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse {tool_name} call: {e}")
                    break
        
        return tool_calls
    
    def _parse_arguments(self, args_str: str) -> List[str]:
        """Parse function arguments safely"""
        if not args_str.strip():
            return []
        
        # Simple CSV parsing with quote handling
        args = []
        current_arg = ''
        in_quotes = False
        quote_char = None
        
        for char in args_str:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == ',' and not in_quotes:
                args.append(current_arg.strip(' "\''))
                current_arg = ''
            else:
                current_arg += char
        
        if current_arg:
            args.append(current_arg.strip(' "\''))
        
        return args

def main():
    """Main function with error handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced GPT-OSS File Agent")
    parser.add_argument("command", nargs="*", help="Command to execute")
    parser.add_argument("-m", "--model", default="gpt-oss:20b", help="Primary model")
    parser.add_argument("-f", "--fallback", default="gpt-oss:7b", help="Fallback model")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        agent = EnhancedFileAgent(model=args.model, fallback_model=args.fallback)
        
        if args.command:
            command = ' '.join(args.command)
            result = agent.execute_command(command)
            print(result)
        else:
            print("Interactive mode not implemented in this version")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()