# Contributing to GPT-OSS Agent

Thank you for your interest in contributing to GPT-OSS Agent! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed
- GPT-OSS models available (`ollama pull gpt-oss:20b`)

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/haasonsaas/gpt-oss-agent.git
cd gpt-oss-agent

# Create virtual environment
python -m venv dev_env
source dev_env/bin/activate  # On Windows: dev_env\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 pytest
```

## 🛠️ Development Guidelines

### Code Style

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format code
black .

# Check formatting
black --check .
```

We use [Flake8](https://flake8.pycqa.org/) for linting:

```bash
# Lint code
flake8 .
```

### Testing

We use [pytest](https://pytest.org/) for testing:

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

### File Structure

```
gpt-oss-agent/
├── knowledge_agent.py      # Knowledge management system
├── file_agent.py          # File operations agent
├── gpt_oss_agent.py       # Unified agent system
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Example scripts
└── tools/                 # Development tools
```

## 📝 Contribution Types

### 🐛 Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, model used)
- **Error messages** and logs

### ✨ Feature Requests

For new features, please provide:

- **Clear description** of the feature
- **Use case** and motivation
- **Proposed implementation** (if you have ideas)
- **Potential impact** on existing functionality

### 🔧 Code Contributions

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Add tests** for new functionality
5. **Ensure** all tests pass
6. **Run** code formatting and linting
7. **Commit** with clear messages
8. **Push** to your fork
9. **Submit** a Pull Request

### 📚 Documentation

Documentation improvements are always welcome:

- Fix typos and improve clarity
- Add examples and tutorials
- Improve API documentation
- Translate documentation

## 🎯 Areas for Contribution

### High Priority

- [ ] **Web UI** for easier interaction
- [ ] **Plugin system** for extensibility
- [ ] **Multi-language support** for documents
- [ ] **Advanced workflow automation**
- [ ] **Performance optimizations**

### Medium Priority

- [ ] **Integration tests** for complex workflows
- [ ] **Docker containerization**
- [ ] **Configuration management**
- [ ] **Monitoring and logging**
- [ ] **Backup and restore functionality**

### Good First Issues

- [ ] **Add new file operation tools**
- [ ] **Improve error messages**
- [ ] **Add more document format support**
- [ ] **Create example scripts**
- [ ] **Improve documentation**

## 🏗️ Adding New Tools

To add a new file operation tool:

```python
def my_new_tool(arg1, arg2):
    """
    Description of what the tool does.
    
    Args:
        arg1: Description of first argument
        arg2: Description of second argument
    
    Returns:
        Result of the operation
    """
    try:
        # Implementation here
        result = do_something(arg1, arg2)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {e}"

# Register the tool
TOOLS['my_new_tool'] = my_new_tool
```

## 🧪 Testing Guidelines

### Unit Tests

Write unit tests for individual functions:

```python
import pytest
from file_agent import list_files

def test_list_files():
    result = list_files(".")
    assert isinstance(result, list)
    assert len(result) > 0
```

### Integration Tests

Test complete workflows:

```python
def test_knowledge_search_workflow():
    agent = KnowledgeAgent()
    agent.index_file("test_document.txt")
    results = agent.search("test query")
    assert len(results) > 0
```

## 📊 Performance Considerations

- **Optimize** for large document collections
- **Use caching** where appropriate
- **Monitor memory usage** with large models
- **Profile** performance-critical code
- **Consider async operations** for I/O

## 🔒 Security Guidelines

- **Never commit** API keys or secrets
- **Validate** all user inputs
- **Sanitize** file paths and commands
- **Use secure** temporary files
- **Audit** shell command execution

## 🌟 Code Review Process

1. **Automated checks** must pass (tests, linting)
2. **Manual review** by maintainers
3. **Discussion** and feedback
4. **Approval** and merge

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Security considerations addressed

## 🎉 Recognition

Contributors will be:

- **Listed** in the project README
- **Credited** in release notes
- **Invited** to join the maintainer team (for significant contributions)

## ❓ Questions?

- 💬 [GitHub Discussions](https://github.com/haasonsaas/gpt-oss-agent/discussions)
- 🐛 [Issue Tracker](https://github.com/haasonsaas/gpt-oss-agent/issues)
- 📧 Email the maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make GPT-OSS Agent better for everyone!** 🙏
