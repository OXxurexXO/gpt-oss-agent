# Changelog

All notable changes to GPT-OSS Agent will be documented in this file.

## [1.0.0] - 2024-01-XX

### Added
- **Knowledge Agent**: Privacy-first RAG system using local GPT-OSS models
  - Document indexing with support for PDFs, DOCX, text files, and code
  - Semantic search using ChromaDB vector database
  - Intelligent chat interface with your documents
  - Automatic text chunking and embedding generation

- **File Agent**: Natural language file system operations
  - File operations (create, read, write, delete, move)
  - Directory management
  - Shell command execution
  - Git operations integration
  - Pattern-based file searching

- **Unified Agent**: Combined knowledge management and file operations
  - Smart routing between knowledge queries and file operations
  - Hybrid workflows that combine analysis with action
  - Interactive and programmatic interfaces

- **Privacy-First Design**
  - All processing happens locally using Ollama
  - No data sent to external APIs
  - Complete control over your information
  - Works offline

- **Developer Tools**
  - Comprehensive examples and documentation
  - Easy setup and installation
  - Extensible architecture for custom tools
  - Full test coverage

### Technical Features
- Support for GPT-OSS 20B and 120B models
- Vector similarity search with configurable parameters
- Parallel document processing for performance
- Intelligent file type detection and processing
- Robust error handling and logging
- Cross-platform compatibility (macOS, Linux, Windows)

### Dependencies
- Python 3.8+
- Ollama for local model serving
- ChromaDB for vector storage
- SentenceTransformers for embeddings
- PyPDF2 and python-docx for document processing

---

## Future Releases

### Planned for 1.1.0
- [ ] Web UI for easier interaction
- [ ] Plugin system for extensibility
- [ ] Advanced workflow automation
- [ ] Multi-language document support

### Planned for 1.2.0
- [ ] Real-time document watching and indexing
- [ ] Integration with popular development tools
- [ ] Advanced analytics and insights
- [ ] Mobile companion app

---

*This project follows [Semantic Versioning](https://semver.org/).*
