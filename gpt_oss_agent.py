#!/usr/bin/env python3
"""
GPT-OSS Agent - Unified intelligent agent system

Combines knowledge management with file operations for the ultimate AI assistant.
Uses local GPT-OSS models via Ollama for complete privacy and control.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict

# Import both agents
from knowledge_agent import KnowledgeAgent
from file_agent import FileAgent, TOOLS

class GPTOSSAgent:
    """Unified AI agent combining knowledge management and file operations."""
    
    def __init__(self, model: str = "gpt-oss:20b"):
        print("🚀 Initializing GPT-OSS Agent...")
        
        # Initialize knowledge agent
        print("🧠 Loading Knowledge Agent...")
        self.knowledge_agent = KnowledgeAgent(model=model)
        
        # Initialize file agent
        print("🤖 Loading File Agent...")
        self.file_agent = FileAgent(model=model)
        
        # Get knowledge base stats
        kb_stats = self.knowledge_agent.get_stats()
        print(f"✅ Knowledge Base: {kb_stats['total_files']} files, {kb_stats['total_chunks']} chunks")
        print(f"✅ File Agent: {len(TOOLS)} tools available")
        
    def process_request(self, user_input: str):
        """Process user request intelligently"""
        
        # Determine request type based on keywords
        file_keywords = ['create', 'delete', 'move', 'list', 'show', 'run', 'execute', 'git', 'find files', 'ls']
        knowledge_keywords = ['find', 'search', 'analyze', 'explain', 'what', 'how', 'why', 'compare', 'tell me']
        
        user_lower = user_input.lower()
        
        # Check for explicit file operations
        is_file_operation = any(keyword in user_lower for keyword in file_keywords)
        is_knowledge_query = any(keyword in user_lower for keyword in knowledge_keywords)
        
        if is_file_operation and not is_knowledge_query:
            print("🤖 Using File Agent for file operations...")
            self.file_agent.execute_command(user_input)
            
        elif is_knowledge_query and not is_file_operation:
            print("🧠 Using Knowledge Agent for analysis...")
            self.query_knowledge(user_input)
            
        else:
            # Hybrid approach - use both!
            print("🚀 Using Hybrid Approach - Knowledge + File Operations...")
            self.hybrid_approach(user_input)
    
    def query_knowledge(self, query: str):
        """Query the knowledge base"""
        try:
            response = self.knowledge_agent.chat_with_knowledge(query)
            print(f"\n🧠 Knowledge Agent Response:")
            print(response)
        except Exception as e:
            print(f"❌ Knowledge query error: {e}")
    
    def hybrid_approach(self, request: str):
        """Use both systems intelligently"""
        print("\n🔍 Step 1: Searching knowledge base...")
        
        # First, search knowledge base
        search_results = self.knowledge_agent.search(request, n_results=3)
        
        if search_results:
            print(f"📚 Found {len(search_results)} relevant items in knowledge base")
            
            # Get knowledge-based insights
            knowledge_response = self.knowledge_agent.chat_with_knowledge(request)
            print(f"\n🧠 Knowledge Analysis:")
            print(knowledge_response)
            
            print(f"\n🤖 Step 2: File operations based on analysis...")
            
            # Try to extract actionable items from the knowledge
            if any(word in request.lower() for word in ['create', 'generate', 'make', 'build']):
                print("💡 Detected creation request - using file agent...")
                self.file_agent.execute_command(request)
            elif any(word in request.lower() for word in ['find', 'search', 'locate']):
                print("💡 Detected search request - using file agent...")
                self.file_agent.execute_command(request)
            else:
                print("💡 Analysis complete - no file operations needed")
        else:
            print("📂 No relevant knowledge found - using file agent...")
            self.file_agent.execute_command(request)
    
    def run_interactive(self):
        """Interactive mode"""
        print("\n" + "="*60)
        print("🎉 GPT-OSS AGENT - READY!")
        print("="*60)
        print("Intelligent agent with knowledge + file operations")
        print("Powered by local GPT-OSS models - completely private!")
        print("\nType 'exit' to quit, 'help' for examples")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n💫 What would you like to do? > ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n💡 Example commands:")
                    print("\n🧠 Knowledge Queries:")
                    print("  • 'What are my main development projects?'")
                    print("  • 'Analyze my authentication patterns'")
                    print("  • 'Find notes about Docker configuration'")
                    
                    print("\n🤖 File Operations:")
                    print("  • 'List all Python files'")
                    print("  • 'Create a new script with hello world'")
                    print("  • 'Show me the git status'")
                    
                    print("\n🚀 Hybrid Operations:")
                    print("  • 'Find my API code and create a new endpoint'")
                    print("  • 'Analyze my testing patterns and create test files'")
                    print("  • 'Search my configs and create a project template'")
                    
                    print("\n📚 Setup Commands:")
                    print("  • Use knowledge_agent.py to index your documents first")
                    print("  • Then use this unified agent for combined operations")
                    continue
                
                if user_input.lower() == 'index':
                    print("📁 Quick indexing mode...")
                    dir_path = input("Enter directory to index (or press Enter for current): ").strip()
                    if not dir_path:
                        dir_path = "."
                    
                    if os.path.exists(dir_path):
                        print(f"Indexing {dir_path}...")
                        results = self.knowledge_agent.index_directory(Path(dir_path))
                        print(f"✅ Indexed {results['indexed']} files, skipped {results['skipped']}")
                    else:
                        print("❌ Directory not found")
                    continue
                
                if user_input.lower() == 'stats':
                    stats = self.knowledge_agent.get_stats()
                    print(f"\n📊 Knowledge Base Stats:")
                    print(f"   Files indexed: {stats['total_files']}")
                    print(f"   Text chunks: {stats['total_chunks']}")
                    print(f"   Vector database entries: {stats['collection_count']}")
                    continue
                
                if not user_input:
                    continue
                
                self.process_request(user_input)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT-OSS Agent - Unified AI Assistant")
    parser.add_argument("command", nargs="*", help="Command to execute")
    parser.add_argument("-m", "--model", default="gpt-oss:20b", help="GPT-OSS model to use")
    
    args = parser.parse_args()
    
    # Initialize unified agent
    agent = GPTOSSAgent(model=args.model)
    
    if args.command:
        # Single command mode
        command = ' '.join(args.command)
        agent.process_request(command)
    else:
        # Interactive mode
        agent.run_interactive()

if __name__ == "__main__":
    main()
