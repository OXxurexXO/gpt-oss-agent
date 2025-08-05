#!/usr/bin/env python3
"""
Setup script for GPT-OSS Agent
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gpt-oss-agent",
    version="1.0.0",
    author="GPT-OSS Agent Contributors",
    description="Privacy-first AI agent system using local GPT-OSS models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/gpt-oss-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
        "Topic :: Text Processing :: Indexing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gpt-oss-agent=gpt_oss_agent:main",
            "knowledge-agent=knowledge_agent:main",
            "file-agent=file_agent:main",
        ],
    },
    keywords="ai, gpt, ollama, rag, file-management, knowledge-base, privacy, local-ai",
    project_urls={
        "Bug Reports": "https://github.com/your-username/gpt-oss-agent/issues",
        "Source": "https://github.com/your-username/gpt-oss-agent",
        "Documentation": "https://github.com/your-username/gpt-oss-agent/wiki",
    },
)
