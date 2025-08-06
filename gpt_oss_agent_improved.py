#!/usr/bin/env python3
"""
GPT-OSS Agent - Unified intelligent agent system with comprehensive error handling
Combines knowledge management with file operations for the ultimate AI assistant.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

# Import enhanced agents
from knowledge_agent_improved import EnhancedKnowledgeAgent
from file_agent_improved import EnhancedFileAgent

# Import utilities and exceptions
from exceptions import (
    GPTOSSAgentError, ModelError, FileOperationError,
    KnowledgeBaseError, ValidationError
)
from utils import sanitize_input, ErrorHandler

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging with file and console handlers"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

class UnifiedGPTOSSAgent:
    """Enhanced unified AI agent with comprehensive error handling and recovery"""
    
    def __init__(self, 
                 model: str = "gpt-oss:20b",
                 fallback_model: str = "gpt-oss:7b",
                 data_dir: str = "./knowledge_base",
                 log_level: str = "INFO",
                 log_file: Optional[str] = None):
        """
        Initialize the unified agent with error recovery
        
        Args:
            model: Primary model to use
            fallback_model: Fallback model for error recovery
            data_dir: Directory for knowledge base
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional log file path
        """
        # Setup logging
        self.logger = setup_logging(log_level, log_file or f"logs/gpt_oss_agent_{datetime.now():%Y%m%d}.log")
        self.logger.info("Initializing Unified GPT-OSS Agent...")
        
        self.model = model
        self.fallback_model = fallback_model
        self.initialization_errors = []
        
        # Initialize knowledge agent with error handling
        try:
            self.logger.info("Loading Knowledge Agent...")
            self.knowledge_agent = EnhancedKnowledgeAgent(
                data_dir=data_dir,
                model=model,
                fallback_model=fallback_model
            )
            kb_stats = self.knowledge_agent.get_stats()
            self.logger.info(f"Knowledge Base: {kb_stats}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Knowledge Agent: {e}")
            self.knowledge_agent = None
            self.initialization_errors.append(f"Knowledge Agent: {e}")
        
        # Initialize file agent with error handling
        try:
            self.logger.info("Loading File Agent...")
            self.file_agent = EnhancedFileAgent(
                model=model,
                fallback_model=fallback_model
            )
            self.logger.info("File Agent loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize File Agent: {e}")
            self.file_agent = None
            self.initialization_errors.append(f"File Agent: {e}")
        
        # Check initialization status
        if not self.knowledge_agent and not self.file_agent:
            error_msg = "Failed to initialize any agents:\n" + "\n".join(self.initialization_errors)
            self.logger.critical(error_msg)
            raise GPTOSSAgentError(error_msg)
        
        if self.initialization_errors:
            self.logger.warning(f"Partial initialization: {self.initialization_errors}")
        else:
            self.logger.info("All agents initialized successfully")
    
    def process_request(self, user_input: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user request with intelligent routing and error recovery
        
        Args:
            user_input: User's request
            mode: Optional mode override ('file', 'knowledge', 'hybrid')
        
        Returns:
            Dictionary with results and metadata
        """
        result = {
            'status': 'pending',
            'mode': None,
            'response': None,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Sanitize input
            user_input = sanitize_input(user_input)
            if not user_input:
                raise ValidationError("Empty input provided")
            
            # Determine processing mode
            if mode:
                processing_mode = mode
            else:
                processing_mode = self._determine_mode(user_input)
            
            result['mode'] = processing_mode
            self.logger.info(f"Processing request in {processing_mode} mode: {user_input[:100]}...")
            
            # Route to appropriate handler
            if processing_mode == 'file':
                result['response'] = self._handle_file_operation(user_input)
            elif processing_mode == 'knowledge':
                result['response'] = self._handle_knowledge_query(user_input)
            else:  # hybrid
                result['response'] = self._handle_hybrid_request(user_input)
            
            result['status'] = 'completed'
            
        except ValidationError as e:
            self.logger.warning(f"Validation error: {e}")
            result['status'] = 'failed'
            result['errors'].append(f"Validation: {e}")
            result['response'] = f"Invalid input: {e}"
        
        except (FileOperationError, KnowledgeBaseError) as e:
            self.logger.error(f"Operation error: {e}")
            result['status'] = 'failed'
            result['errors'].append(str(e))
            result['response'] = f"Operation failed: {e}"
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            result['status'] = 'failed'
            result['errors'].append(f"Unexpected: {e}")
            result['response'] = "An unexpected error occurred. Please check the logs."
        
        return result
    
    def _determine_mode(self, user_input: str) -> str:
        """Intelligently determine processing mode based on input"""
        user_lower = user_input.lower()
        
        # Keywords for different modes
        file_keywords = [
            'create', 'delete', 'move', 'rename', 'copy', 'list files',
            'ls', 'mkdir', 'rm', 'mv', 'cp', 'run', 'execute', 'git',
            'shell', 'command', 'terminal', 'write file', 'read file'
        ]
        
        knowledge_keywords = [
            'find', 'search', 'analyze', 'explain', 'what is', 'how does',
            'why', 'when', 'compare', 'tell me about', 'summarize',
            'understand', 'learn', 'knowledge', 'information about'
        ]
        
        # Count keyword matches
        file_score = sum(1 for kw in file_keywords if kw in user_lower)
        knowledge_score = sum(1 for kw in knowledge_keywords if kw in user_lower)
        
        # Determine mode based on scores
        if file_score > knowledge_score * 1.5:
            return 'file'
        elif knowledge_score > file_score * 1.5:
            return 'knowledge'
        else:
            return 'hybrid'
    
    def _handle_file_operation(self, user_input: str) -> str:
        """Handle file operations with error recovery"""
        if not self.file_agent:
            raise FileOperationError("File Agent not available")
        
        try:
            self.logger.debug(f"Executing file operation: {user_input}")
            result = self.file_agent.execute_command(user_input)
            return result or "File operation completed"
        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            raise FileOperationError(f"File operation failed: {e}")
    
    def _handle_knowledge_query(self, user_input: str) -> str:
        """Handle knowledge base queries with error recovery"""
        if not self.knowledge_agent:
            raise KnowledgeBaseError("Knowledge Agent not available")
        
        try:
            self.logger.debug(f"Processing knowledge query: {user_input}")
            
            # Try chat first for natural queries
            response = self.knowledge_agent.chat_with_knowledge(user_input)
            
            if response and response != "No relevant information found in the knowledge base.":
                return response
            
            # Fallback to direct search
            search_results = self.knowledge_agent.search(user_input, n_results=5)
            if search_results:
                formatted = self._format_search_results(search_results)
                return f"Found {len(search_results)} relevant items:\n\n{formatted}"
            else:
                return "No relevant information found in the knowledge base."
                
        except Exception as e:
            self.logger.error(f"Knowledge query failed: {e}")
            raise KnowledgeBaseError(f"Knowledge query failed: {e}")
    
    def _handle_hybrid_request(self, user_input: str) -> str:
        """Handle hybrid requests using both agents"""
        responses = []
        
        # Step 1: Search knowledge base if available
        if self.knowledge_agent:
            try:
                self.logger.debug("Step 1: Searching knowledge base...")
                search_results = self.knowledge_agent.search(user_input, n_results=3)
                
                if search_results:
                    responses.append(f"📚 Found {len(search_results)} relevant items in knowledge base")
                    
                    # Get insights from knowledge
                    knowledge_response = self.knowledge_agent.chat_with_knowledge(user_input)
                    if knowledge_response:
                        responses.append(f"🧠 Knowledge Analysis:\n{knowledge_response}")
            except Exception as e:
                self.logger.warning(f"Knowledge search failed: {e}")
                responses.append(f"⚠️ Knowledge search unavailable: {e}")
        
        # Step 2: Check for actionable file operations
        if self.file_agent:
            try:
                # Detect if user wants to create/modify based on knowledge
                action_keywords = ['create', 'generate', 'make', 'build', 'write', 'save']
                if any(keyword in user_input.lower() for keyword in action_keywords):
                    self.logger.debug("Step 2: Executing file operations...")
                    file_result = self.file_agent.execute_command(user_input)
                    if file_result:
                        responses.append(f"🤖 File Operations:\n{file_result}")
            except Exception as e:
                self.logger.warning(f"File operation failed: {e}")
                responses.append(f"⚠️ File operation unavailable: {e}")
        
        if responses:
            return "\n\n".join(responses)
        else:
            return "Unable to process request with available agents"
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for display"""
        formatted = []
        for i, result in enumerate(results, 1):
            source = result.get('metadata', {}).get('source', 'Unknown')
            content = result.get('content', '')[:200]
            formatted.append(f"{i}. [{source}]\n   {content}...")
        return "\n\n".join(formatted)
    
    def index_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """Index a directory into the knowledge base"""
        if not self.knowledge_agent:
            raise KnowledgeBaseError("Knowledge Agent not available for indexing")
        
        try:
            self.logger.info(f"Indexing directory: {directory}")
            stats = self.knowledge_agent.index_directory(directory, recursive=recursive)
            self.logger.info(f"Indexing complete: {stats}")
            return stats
        except Exception as e:
            self.logger.error(f"Indexing failed: {e}")
            raise KnowledgeBaseError(f"Failed to index directory: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all agents"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'agents': {},
            'initialization_errors': self.initialization_errors
        }
        
        # Knowledge Agent status
        if self.knowledge_agent:
            try:
                kb_stats = self.knowledge_agent.get_stats()
                status['agents']['knowledge'] = {
                    'status': 'operational',
                    'stats': kb_stats
                }
            except Exception as e:
                status['agents']['knowledge'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            status['agents']['knowledge'] = {'status': 'not_initialized'}
        
        # File Agent status
        if self.file_agent:
            status['agents']['file'] = {'status': 'operational'}
        else:
            status['agents']['file'] = {'status': 'not_initialized'}
        
        # Overall status
        operational_count = sum(
            1 for agent in status['agents'].values()
            if agent.get('status') == 'operational'
        )
        
        if operational_count == 2:
            status['overall'] = 'fully_operational'
        elif operational_count == 1:
            status['overall'] = 'partially_operational'
        else:
            status['overall'] = 'not_operational'
        
        return status
    
    def run_interactive(self):
        """Run in interactive mode with enhanced error handling"""
        print("🚀 GPT-OSS Unified Agent (Enhanced)")
        print("=" * 50)
        
        # Show status
        status = self.get_status()
        print(f"Status: {status['overall']}")
        if status['initialization_errors']:
            print(f"⚠️ Initialization warnings:")
            for error in status['initialization_errors']:
                print(f"  - {error}")
        print("=" * 50)
        print("Commands: 'help', 'status', 'index <path>', 'mode <file|knowledge|hybrid>', 'exit'")
        print("=" * 50)
        
        current_mode = None
        
        while True:
            try:
                user_input = input("\n💻 > ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                elif user_input.lower() == 'status':
                    status = self.get_status()
                    print(json.dumps(status, indent=2))
                    continue
                
                elif user_input.lower().startswith('index '):
                    path = user_input[6:].strip()
                    try:
                        stats = self.index_directory(path)
                        print(f"✅ Indexed: {stats}")
                    except Exception as e:
                        print(f"❌ Indexing failed: {e}")
                    continue
                
                elif user_input.lower().startswith('mode '):
                    mode = user_input[5:].strip()
                    if mode in ['file', 'knowledge', 'hybrid']:
                        current_mode = mode
                        print(f"✅ Mode set to: {mode}")
                    else:
                        print("❌ Invalid mode. Use: file, knowledge, or hybrid")
                    continue
                
                # Process regular request
                result = self.process_request(user_input, mode=current_mode)
                
                if result['status'] == 'completed':
                    print(f"\n{result['response']}")
                else:
                    print(f"\n❌ Request failed: {result['response']}")
                    if result['errors']:
                        print(f"Errors: {', '.join(result['errors'])}")
                
            except KeyboardInterrupt:
                print("\n(Use 'exit' to quit)")
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}", exc_info=True)
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
💡 GPT-OSS Agent Help

MODES:
  • file      - File system operations only
  • knowledge - Knowledge base queries only
  • hybrid    - Combined operations (default)

COMMANDS:
  • help              - Show this help
  • status            - Show agent status
  • index <path>      - Index files into knowledge base
  • mode <mode>       - Set processing mode
  • exit              - Exit the program

FILE OPERATIONS:
  • "list files"                    - List current directory
  • "create file test.txt"          - Create a file
  • "read file config.json"         - Read file contents
  • "find all python files"         - Search for files
  • "run git status"                - Execute commands

KNOWLEDGE QUERIES:
  • "search for authentication"     - Search knowledge base
  • "explain how X works"           - Get explanations
  • "find examples of Y"            - Find code examples
  • "what is Z?"                    - Get information

HYBRID OPERATIONS:
  • "find API docs and create a client"
  • "analyze configs and update settings"
  • "search patterns and generate examples"
"""
        print(help_text)

def main():
    """Main entry point with comprehensive error handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced GPT-OSS Unified Agent")
    parser.add_argument("request", nargs="*", help="Request to process")
    parser.add_argument("-m", "--model", default="gpt-oss:20b", help="Primary model")
    parser.add_argument("-f", "--fallback", default="gpt-oss:7b", help="Fallback model")
    parser.add_argument("--mode", choices=['file', 'knowledge', 'hybrid'], help="Processing mode")
    parser.add_argument("--index", help="Index a directory")
    parser.add_argument("--data-dir", default="./knowledge_base", help="Knowledge base directory")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        args.log_level = "DEBUG"
    
    try:
        # Initialize agent
        agent = UnifiedGPTOSSAgent(
            model=args.model,
            fallback_model=args.fallback,
            data_dir=args.data_dir,
            log_level=args.log_level,
            log_file=args.log_file
        )
        
        # Handle different operations
        if args.index:
            stats = agent.index_directory(args.index)
            print(json.dumps(stats, indent=2))
        
        elif args.request:
            request = ' '.join(args.request)
            result = agent.process_request(request, mode=args.mode)
            print(result['response'])
            if result['status'] != 'completed':
                sys.exit(1)
        
        else:
            # Interactive mode
            agent.run_interactive()
    
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()