#!/usr/bin/env python3
"""
Quick Start Example for GPT-OSS Agent

This example demonstrates the basic usage of the GPT-OSS Agent system.
Run this script to see the agent in action with sample operations.
"""

import os
import tempfile
from pathlib import Path

# Import the agents
from knowledge_agent import KnowledgeAgent
from file_agent import FileAgent
from gpt_oss_agent import GPTOSSAgent

def create_sample_documents():
    """Create sample documents for demonstration"""
    
    # Create a temporary directory for samples
    sample_dir = Path("./sample_documents")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample project documentation
    (sample_dir / "project_overview.md").write_text("""
# My AI Project

This is a sample AI project that demonstrates:

## Features
- Natural language processing
- Document analysis
- File operations
- Knowledge management

## Technologies
- Python
- GPT-OSS models
- Vector databases
- Local AI processing

## Goals
- Build intelligent automation
- Maintain privacy and control
- Create reusable workflows
""")
    
    # Sample code file
    (sample_dir / "main.py").write_text("""
#!/usr/bin/env python3
'''
Sample Python application demonstrating AI integration
'''

import os
from typing import List, Dict

class AIAssistant:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.capabilities = [
            "text_analysis",
            "file_operations", 
            "knowledge_search"
        ]
    
    def process_request(self, request: str) -> str:
        '''Process user request with AI'''
        # Implementation would go here
        return f"Processing: {request}"
    
    def get_capabilities(self) -> List[str]:
        '''Return list of AI capabilities'''
        return self.capabilities

if __name__ == "__main__":
    assistant = AIAssistant("gpt-oss:20b")
    print("AI Assistant initialized")
    print(f"Capabilities: {assistant.get_capabilities()}")
""")
    
    # Sample configuration
    (sample_dir / "config.json").write_text("""{
    "model": "gpt-oss:20b",
    "max_tokens": 2048,
    "temperature": 0.7,
    "knowledge_base": {
        "chunk_size": 1000,
        "overlap": 200,
        "index_types": [".md", ".py", ".txt", ".json"]
    },
    "file_operations": {
        "safe_mode": true,
        "backup_enabled": true,
        "max_file_size": "10MB"
    }
}""")
    
    return sample_dir

def demo_knowledge_agent():
    """Demonstrate the Knowledge Agent capabilities"""
    print("\n🧠 KNOWLEDGE AGENT DEMO")
    print("=" * 50)
    
    # Create sample documents
    sample_dir = create_sample_documents()
    print(f"✅ Created sample documents in {sample_dir}")
    
    # Initialize knowledge agent
    agent = KnowledgeAgent(data_dir="./demo_knowledge_base")
    
    # Index the sample documents
    print("\n📚 Indexing sample documents...")
    results = agent.index_directory(sample_dir)
    print(f"✅ Indexed {results['indexed']} files")
    
    # Demonstrate search
    print("\n🔍 Searching for 'AI capabilities'...")
    search_results = agent.search("AI capabilities", n_results=2)
    
    for i, result in enumerate(search_results, 1):
        source = Path(result['metadata']['source']).name
        preview = result['content'][:100] + "..."
        print(f"   {i}. From {source}: {preview}")
    
    # Demonstrate chat
    print("\n💬 Chatting with knowledge base...")
    response = agent.chat_with_knowledge("What technologies are mentioned in my project?")
    print(f"🤖 Response: {response[:200]}...")
    
    # Show stats
    stats = agent.get_stats()
    print(f"\n📊 Knowledge Base Stats:")
    print(f"   Files: {stats['total_files']}")
    print(f"   Chunks: {stats['total_chunks']}")

def demo_file_agent():
    """Demonstrate the File Agent capabilities"""
    print("\n🤖 FILE AGENT DEMO")
    print("=" * 50)
    
    # Initialize file agent
    agent = FileAgent()
    
    # Create a test directory
    print("📁 Creating test directory...")
    agent.execute_command("create a directory called test_output")
    
    # Create a sample file
    print("📝 Creating sample file...")
    agent.execute_command("create a file called test_output/hello.py with a simple hello world script")
    
    # List files
    print("📋 Listing files...")
    agent.execute_command("list files in test_output directory")
    
    # Read file content
    print("👀 Reading file content...")
    agent.execute_command("show me the content of test_output/hello.py")

def demo_unified_agent():
    """Demonstrate the Unified Agent capabilities"""
    print("\n🚀 UNIFIED AGENT DEMO")
    print("=" * 50)
    
    # Initialize unified agent (uses existing knowledge base)
    agent = GPTOSSAgent()
    
    # Demonstrate hybrid operation
    print("🔄 Hybrid operation: knowledge + file action...")
    agent.process_request("find information about AI technologies and create a summary file")

def main():
    """Run the complete demonstration"""
    print("🎉 GPT-OSS AGENT QUICK START DEMO")
    print("=" * 50)
    print("This demo shows the capabilities of the GPT-OSS Agent system")
    print("Make sure you have:")
    print("  • Ollama running (ollama serve)")
    print("  • GPT-OSS model available (ollama pull gpt-oss:20b)")
    print()
    
    try:
        # Demo each component
        demo_knowledge_agent()
        demo_file_agent()
        demo_unified_agent()
        
        print("\n🎉 DEMO COMPLETE!")
        print("=" * 50)
        print("Next steps:")
        print("  • Index your own documents with knowledge_agent.py")
        print("  • Try file operations with file_agent.py")  
        print("  • Use the unified agent with gpt_oss_agent.py")
        print("  • Explore the interactive modes for each agent")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure Ollama is running and GPT-OSS models are available")

if __name__ == "__main__":
    main()
