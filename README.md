# GPT-OSS Agent

A powerful, privacy-first AI agent system that combines intelligent knowledge management with natural language file operations. Uses local GPT-OSS models via Ollama for complete privacy and control.

## 🌟 Features

### 🧠 **Knowledge Agent**
- **Private RAG System**: Index documents, code, PDFs locally
- **Semantic Search**: Find content by meaning, not just keywords
- **Intelligent Analysis**: Chat with your documents using GPT-OSS
- **Vector Database**: Fast similarity search with ChromaDB
- **Complete Privacy**: All data stays on your machine

### 🤖 **File Agent**
- **Natural Language Operations**: Control files with plain English
- **Smart File Management**: Create, read, modify, organize files
- **Code Operations**: Format, lint, run code with AI assistance
- **Git Integration**: Natural language git operations
- **Shell Commands**: Execute system commands intelligently

### ⚡ **Unified Agent**
- **Hybrid Intelligence**: Combines knowledge analysis + file operations
- **Smart Routing**: Automatically chooses the right approach
- **Workflow Automation**: Chain knowledge discovery with file actions
- **Extensible**: Easy to add new capabilities

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- GPT-OSS models (20B or 120B)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/gpt-oss-agent.git
cd gpt-oss-agent

# Create virtual environment
python -m venv agent_env
source agent_env/bin/activate  # On Windows: agent_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull GPT-OSS models
ollama pull gpt-oss:20b    # Smaller, faster model
ollama pull gpt-oss:120b   # Larger, more capable model
```

### Quick Test

```bash
# Test the file agent
python file_agent.py "list all files in current directory"

# Test the knowledge agent (after indexing some documents)
python knowledge_agent.py

# Test the unified agent
python gpt_oss_agent.py "analyze my development projects"
```

## 📚 Usage Examples

### Knowledge Agent

```bash
# Interactive mode
python knowledge_agent.py

# Example queries
"Find all my authentication code patterns"
"What APIs have I worked with?"
"Analyze my Docker configurations"
"Search for notes about machine learning"
```

### File Agent

```bash
# Single commands
python file_agent.py "create a Python script that prints hello world"
python file_agent.py "find all Python files in this directory"
python file_agent.py "show me the git status"

# Interactive mode
python file_agent.py
```

### Unified Agent

```bash
# Hybrid operations that combine knowledge + file operations
python gpt_oss_agent.py "find my API patterns and create a new endpoint"
python gpt_oss_agent.py "analyze my test files and create a new test"
python gpt_oss_agent.py "search my configs and create a project template"
```

## 📖 Documentation

### Indexing Your Documents

```python
from knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent()

# Index a directory
agent.index_directory("./my_documents")

# Index specific files
agent.index_file("./important_doc.pdf")

# Get statistics
stats = agent.get_stats()
print(f"Indexed {stats['total_files']} files")
```

### Available File Operations

- `list_files(path)` - List files in directory
- `read_file(path)` - Read file content
- `write_file(path, content)` - Write content to file
- `create_directory(path)` - Create directory
- `move_file(source, dest)` - Move/rename file
- `run_shell_command(cmd)` - Execute shell command
- `git_status()` - Git repository status
- `git_add(path)` - Stage files for commit
- `git_commit(message)` - Commit changes
- `glob_files(pattern)` - Find files by pattern

### Supported File Types

**Documents**: `.txt`, `.md`, `.pdf`, `.docx`, `.rtf`  
**Code**: `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.cpp`, `.swift`  
**Data**: `.json`, `.yaml`, `.csv`, `.sql`, `.xml`  
**Config**: `.env`, `.gitignore`, `.dockerfile`, `.conf`

## ⚙️ Configuration

### Model Selection

```python
# Use different GPT-OSS models
agent = KnowledgeAgent(model="gpt-oss:120b")  # More capable
agent = FileAgent(model="gpt-oss:20b")        # Faster
```

### Performance Tuning

```python
# Adjust indexing parameters
agent.index_directory(
    "./documents",
    chunk_size=1000,        # Text chunk size
    overlap=200,            # Chunk overlap
    max_workers=8           # Parallel processing
)
```

## 🛠️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   GPT-OSS       │    │   Local Data    │
│                 │    │   (via Ollama)  │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          v                      v                      v
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Agent                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │ Knowledge Agent │              │   File Agent    │           │
│  │                 │              │                 │           │
│  │ • Semantic      │              │ • File Ops      │           │
│  │   Search        │              │ • Shell Cmds    │           │
│  │ • RAG           │              │ • Git Ops       │           │
│  │ • Analysis      │              │ • Code Ops      │           │
│  └─────────────────┘              └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
          │                      │                      │
          v                      v                      v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ChromaDB      │    │   File System   │    │   Git Repos     │
│   (Vectors)     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Development

### Running Tests

```bash
# Test knowledge agent
python -m pytest tests/test_knowledge_agent.py

# Test file agent  
python -m pytest tests/test_file_agent.py

# Test unified agent
python -m pytest tests/test_unified_agent.py
```

### Adding New Tools

```python
def my_custom_tool(arg1, arg2):
    """Custom tool description"""
    # Implementation
    return result

# Register the tool
TOOLS['my_custom_tool'] = my_custom_tool
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for releasing GPT-OSS models
- [Ollama](https://ollama.ai) for local model serving
- [ChromaDB](https://www.trychroma.com/) for vector database
- [SentenceTransformers](https://www.sbert.net/) for embeddings

## 🆘 Support

- 📖 [Documentation](https://github.com/your-username/gpt-oss-agent/wiki)
- 🐛 [Issue Tracker](https://github.com/your-username/gpt-oss-agent/issues)
- 💬 [Discussions](https://github.com/your-username/gpt-oss-agent/discussions)

## 🎯 Roadmap

- [ ] Web UI for easier interaction
- [ ] Plugin system for extensibility
- [ ] Multi-language support
- [ ] Advanced workflow automation
- [ ] Integration with popular dev tools
- [ ] Mobile companion app

---

**Built with ❤️ for the open source community**
