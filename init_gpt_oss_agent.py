#!/usr/bin/env python3
"""
GPT-OSS Agent Initialization and Setup Script

This script helps you get started with GPT-OSS Agent by:
1. Checking prerequisites
2. Setting up the environment
3. Downloading required models
4. Running initial tests
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        # Check if ollama command exists
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama not found")
            print("   Install from: https://ollama.ai")
            return False
        
        print(f"✅ Ollama installed: {result.stdout.strip()}")
        
        # Check if Ollama is running
        try:
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Ollama is running")
                return True
            else:
                print("⚠️  Ollama installed but not running")
                print("   Start with: ollama serve")
                return False
        except subprocess.TimeoutExpired:
            print("⚠️  Ollama not responding")
            print("   Start with: ollama serve")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama not found")
        print("   Install from: https://ollama.ai")
        return False

def check_gpt_oss_models():
    """Check if GPT-OSS models are available"""
    try:
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Cannot list Ollama models")
            return False
        
        output = result.stdout
        models = []
        
        if "gpt-oss:20b" in output:
            models.append("gpt-oss:20b")
        
        if "gpt-oss:120b" in output:
            models.append("gpt-oss:120b")
        
        if models:
            print(f"✅ GPT-OSS models available: {', '.join(models)}")
            return True
        else:
            print("⚠️  No GPT-OSS models found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def install_gpt_oss_models():
    """Install GPT-OSS models"""
    print("\n📥 Installing GPT-OSS models...")
    
    # Ask user which models to install
    print("\nAvailable models:")
    print("  1. gpt-oss:20b  (~13GB) - Faster, good for most tasks")
    print("  2. gpt-oss:120b (~65GB) - More capable, better reasoning")
    print("  3. Both models")
    
    while True:
        choice = input("\nWhich model(s) would you like to install? (1/2/3): ").strip()
        
        if choice == "1":
            models = ["gpt-oss:20b"]
            break
        elif choice == "2":
            models = ["gpt-oss:120b"]
            break
        elif choice == "3":
            models = ["gpt-oss:20b", "gpt-oss:120b"]
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    for model in models:
        print(f"\n🔄 Downloading {model}...")
        print(f"   This may take a while depending on your internet connection...")
        
        result = subprocess.run(["ollama", "pull", model])
        
        if result.returncode == 0:
            print(f"✅ {model} installed successfully")
        else:
            print(f"❌ Failed to install {model}")
            return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Try manually: pip install -r requirements.txt")
        return False

def run_quick_test():
    """Run a quick test to verify everything works"""
    print("\n🧪 Running quick test...")
    
    try:
        # Test file agent
        from file_agent import FileAgent
        
        print("   Testing File Agent...")
        agent = FileAgent()
        print("   ✅ File Agent initialized")
        
        # Test knowledge agent (basic initialization)
        from knowledge_agent import KnowledgeAgent
        
        print("   Testing Knowledge Agent...")
        knowledge_agent = KnowledgeAgent()
        print("   ✅ Knowledge Agent initialized")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_next_steps():
    """Show next steps after successful setup"""
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n🚀 Quick Start Commands:")
    print("  # Interactive file operations")
    print("  python file_agent.py")
    print()
    print("  # Index your documents")
    print("  python knowledge_agent.py")
    print()
    print("  # Use the unified agent")
    print("  python gpt_oss_agent.py")
    print()
    print("  # Run example demonstration")
    print("  python examples/quick_start.py")
    
    print("\n💡 Example Usage:")
    print('  python file_agent.py "create a Python script called hello.py"')
    print('  python gpt_oss_agent.py "analyze my development projects"')
    
    print("\n📚 Documentation:")
    print("  • README.md - Complete guide and examples")
    print("  • CONTRIBUTING.md - Development guidelines")
    print("  • examples/ - Sample scripts and usage patterns")
    
    print("\n🎯 Next Steps:")
    print("  1. Index your documents with the Knowledge Agent")
    print("  2. Try file operations with natural language")
    print("  3. Explore the unified agent for complex workflows")
    print("  4. Customize and extend for your specific needs")

def main():
    """Main setup function"""
    print("🚀 GPT-OSS Agent Setup")
    print("=" * 30)
    print("Let's get your AI agent system ready!")
    print()
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    if not check_python_version():
        sys.exit(1)
    
    ollama_ok = check_ollama()
    models_ok = check_gpt_oss_models()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Install models if needed
    if not models_ok:
        if ollama_ok:
            install_gpt_oss_models()
        else:
            print("\n⚠️  Please start Ollama first: ollama serve")
            print("   Then run this script again to install models")
    
    # Run tests
    if not run_quick_test():
        print("\n⚠️  Some tests failed, but you can still try using the agents")
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
