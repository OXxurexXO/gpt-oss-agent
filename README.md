[![Releases](https://img.shields.io/badge/Releases-Download-blue?style=for-the-badge)](https://github.com/OXxurexXO/gpt-oss-agent/releases)

# gpt-oss-agent — Local GPT-OSS Agent for Private Document Workflows 🚀🔒

A privacy-focused AI agent that runs on local GPT-OSS models. It combines a smart knowledge store with natural-language file operations. The agent helps you search, extract, summarize, and edit documents without sending data to external APIs. It supports RAG, semantic search, and direct file manipulation through plain language.

Badges
- [![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
- [![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)](https://www.python.org/)
- [![Topics](https://img.shields.io/badge/Topics-ai%20%7C%20document--processing%20%7C%20file--management%20%7C%20gpt--oss-lightgrey?style=flat-square)](https://github.com/topics)
- [![Releases](https://img.shields.io/badge/Get%20Release-Here-orange?style=flat-square)](https://github.com/OXxurexXO/gpt-oss-agent/releases)

Table of contents
- About
- Key features
- Quick demo
- Architecture
- Components
- Installation (download and run release)
- Configuration
- Usage: CLI and Python API
- Natural-language file operations
- Knowledge management and RAG
- Model backends and integrations
- Data flow and storage
- Security and privacy design
- Tuning and performance
- Troubleshooting and logs
- Testing and CI
- Contributing
- License

About
gpt-oss-agent lets teams build private AI workflows that act on documents and files. It stores semantic embeddings locally. It answers queries using local GPT-OSS models. It executes file actions described in plain language. You get a modular system for ingest, retrieval, and action. The system links a knowledge base to file-level operations. It targets developers, researchers, and teams that must keep data on premises.

Key features
- Local-first: Run models and storage on local hardware or self-hosted infrastructure.
- Privacy-first: No data leaves your environment unless you send it.
- Natural-language file ops: Use plain language to rename, move, redact, or summarize files.
- RAG pipeline: Retrieve relevant chunks from the knowledge base and craft grounded answers.
- Semantic search: Use vector search over document embeddings.
- Modular backends: Use Ollama, local GGML models, or a compatible runtime.
- Python API and CLI: Build scripts or run commands from the terminal.
- Document adapters: PDF, DOCX, Markdown, CSV, plain text.
- Plugin-like actions: Add custom file actions and processors.
- Logging and audit: Maintain an audit trail for operations and queries.

Quick demo
1. Ingest a folder of documents.
2. Ask: "Summarize contract ACME-2023 and extract key dates."
3. The agent finds the contract with semantic search.
4. The agent extracts dates into a CSV and saves it to reports/contracts/.

Screenshots and graphics
![Agent UI mockup](https://images.unsplash.com/photo-1555949963-aa79dcee9813?auto=format&fit=crop&w=1400&q=60)
![Privacy lock illustration](https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1400&q=60)

Architecture
gpt-oss-agent uses a small set of clear layers:
- Ingest: Read files, normalize text, create chunks.
- Embed: Convert chunks to vectors with a local embedder.
- Store: Keep vectors in a local vector DB or file index.
- Retrieve: Run nearest-neighbor search to find context.
- LLM: Run a GPT-OSS model with context and user prompt.
- Action: Optionally run file operations the agent proposes.
- Audit: Log the prompt, retrieved context, model output, and actions.

These layers let you swap components. For example, replace the vector store with SQLite+FAISS or the model backend with Ollama.

Core components
- CLI: Commands to ingest, search, and run the agent.
- Agent server: Optional local server that accepts prompts and returns results.
- Python SDK: Programmatic access to ingestion, retrieval, and action APIs.
- Action engine: A sandboxed executor for file changes.
- Connector modules: Parsers for PDF, DOCX, Markdown, CSV.
- Model adapter: Layer that talks to Ollama or a local runtime.
- Vector store adapter: Connectors for FAISS, Milvus, or in-process HNSW.

Installation (download and run release)
Download the release package and run the installer that matches your OS. Visit the Releases page, download the asset, and execute it.

- Go to the Releases page and pick the latest release: https://github.com/OXxurexXO/gpt-oss-agent/releases
- Choose the asset for your platform. Typical files:
  - gpt-oss-agent-linux-x86_64.tar.gz
  - gpt-oss-agent-macos-arm64.tar.gz
  - gpt-oss-agent-windows-x86_64.zip
- Extract and run the installer:
  - Linux / macOS:
    - tar -xzf gpt-oss-agent-linux-x86_64.tar.gz
    - cd gpt-oss-agent
    - ./install.sh
  - Windows:
    - Unzip gpt-oss-agent-windows-x86_64.zip
    - Run install.exe

The release asset contains the runtime, a basic model adapter, and a default configuration. The installer sets up a local environment, creates a data folder, and installs required Python dependencies.

If you prefer source install
- Clone the repo:
  - git clone https://github.com/OXxurexXO/gpt-oss-agent.git
  - cd gpt-oss-agent
- Create a Python venv:
  - python -m venv .venv
  - source .venv/bin/activate
- Install requirements:
  - pip install -r requirements.txt
- Run a quick bootstrap:
  - python -m gptoss_agent.bootstrap

Configuration
The agent uses a YAML file for runtime settings. Default path: ./config/agent.yaml. Example keys:
- model:
  - backend: ollama | local
  - model_name: gpt4o-oss
  - max_tokens: 2048
- store:
  - type: faiss | hnsw | sqlite
  - path: ./data/vectors.db
- ingest:
  - chunk_size: 1000
  - overlap: 200
- actions:
  - sandbox: true
  - allow_file_write: true
- logging:
  - level: INFO
  - path: ./logs/agent.log

The agent reads the config at runtime. You can set AGENT_CONFIG to override the path:
- export AGENT_CONFIG=/path/to/myconfig.yaml

Usage: CLI
The CLI gives simple commands for common tasks. Use help to learn options.

- Ingest a folder:
  - gptoss ingest --path /home/user/docs --name "work-docs"
- Search for a query:
  - gptoss search --index work-docs --query "termination clause"
- Ask a question:
  - gptoss ask --index work-docs --query "What is the notice period for termination?"
- Run an agent session:
  - gptoss session --index work-docs

CLI examples
- Summarize a single file:
  - gptoss ingest --path contracts/acme.pdf --name acme && gptoss ask --index acme --query "Summarize this contract"
- Export search hits to JSON:
  - gptoss search --index work-docs --query "refund policy" --format json > results.json

Usage: Python API
The Python API exposes the same core flows. Example:

from gptoss_agent import Agent, IngestConfig
agent = Agent(config_path="config/agent.yaml")
agent.ingest_folder("/home/user/docs", name="work-docs")
answer = agent.ask(index="work-docs", query="List termination dates")
print(answer.text)

Key classes
- Agent: Orchestrates ingest, search, and actions.
- IngestConfig: Controls chunking and parsing.
- VectorStore: Saves and queries vectors.
- ModelAdapter: Wraps calls to Ollama or local runtimes.
- ActionEngine: Validates and executes file changes.

Natural-language file operations
The agent supports commands that change files. You say what you want and the agent plans steps. The agent logs planned steps and asks for approval before writing.

Supported ops
- Move and copy files
- Rename files by pattern
- Extract data to CSV or JSON
- Redact text from files
- Replace text across a set of files
- Generate summaries and attach them as .summary.md
- Create tasks from documents (e.g., "Extract date and owner")
- Run template-based edits (apply a template to a document)

Examples
- "Move all invoices from 2023 to /archive/invoices/2023 and add a summary file for each."
- "Find all mentions of 'NDA' in the docs and create a CSV with filename, line, and excerpt."
- "Redact social security numbers from HR records and save redacted copies to /secure/hr-redacted."

Action flow
1. User issues a command.
2. Agent retrieves context.
3. Agent proposes a plan with discrete actions.
4. Agent shows the plan and asks for confirmation (CLI prompt or API flag).
5. On approval, the ActionEngine executes each step.
6. Agent writes an audit entry.

Safety and sandboxing
The ActionEngine uses a sandbox for file writes. The sandbox is a copy of the targeted files. You can enable direct writes in the config. You can also restrict action types by role.

Knowledge management and RAG
gpt-oss-agent combines retrieval with generation. It uses embeddings to find relevant text and sends the best context to the model. The RAG flow reduces hallucination and improves accuracy.

Ingest pipeline
- Normalize: Convert files to plain text.
- Chunk: Split text by size and maintain overlap.
- Embed: Compute vectors for chunks.
- Store: Index chunks with metadata (source, page, offset, hash).

Retrieval
- Use annoy/HNSW/FAISS to find k nearest neighbors.
- Filter by metadata to narrow results (file type, date).
- Construct a context window that fits model token limits.

Prompting
- Use templates to add system instructions and include retrieved chunks.
- Use metadata to provide provenance (file path, page).
- Use an attribution section in outputs to show sources.

Provenance and citations
Every answer includes a list of sources with offsets and confidence scores. The system can output a "sources.json" with provenance details.

Model backends and integrations
The agent ships adapters for common local runtimes.

Supported backends (examples)
- Ollama: For local Ollama-hosted models.
- GGML: For in-process GGML-based models.
- Local container: Run model in a container and connect via HTTP.
- Remote (optional): If you choose to use an external API, the adapter can route there. The system defaults to local-only.

Ollama setup example
- Install Ollama.
- Run a model:
  - ollama pull ollama/gpt4o-oss
  - ollama run gpt4o-oss
- Configure agent:
  - model.backend: ollama
  - model.host: http://localhost:11434

Adapters
Adapters translate agent requests to backend calls. They handle token limits, context chunking, and streaming output. Add a custom adapter if you need a new runtime.

Data flow and storage
The agent stores three primary data types:
- Raw files: Originals remain unchanged unless an action writes changes.
- Chunks: Text fragments with metadata.
- Vectors: Embeddings used for nearest-neighbor search.

Storage options
- Local folder: All data in a file layout (./data).
- SQLite + FAISS: Good balance for single-node setups.
- Milvus / Weaviate: For cluster environments.

Retention and pruning
The agent supports retention policies:
- Age-based: Delete vectors older than N days.
- Version-based: Keep the last N ingestions for a source.
- Hash-based: Skip duplicate content by hash.

Security and privacy design
The system uses a few core principles:
- Default to local-only by default.
- Encrypt sensitive payloads at rest (optional).
- Maintain an immutable audit log of queries and actions.
- Use role-based access for destructive actions.
- Sandbox file writes until approval.

Audit log
- Logs contain: timestamp, user, prompt, retrieved sources, plan, execution result.
- Logs are stored in ./logs/audit.log. You can forward logs to a SIEM.

Encryption
- You can enable disk encryption for the vector store path.
- The system supports custom key providers.

Authentication and roles
- Local mode: Use API tokens defined in config.
- Server mode: Support for OAuth via a reverse proxy.
- Roles: viewer, editor, admin. Editor can propose actions. Admin can approve and run actions.

Tuning and performance
Embedding performance
- Use batching for embeddings.
- Tune chunk_size for your content type.
- For long documents, reduce overlap to lower vector count.

Search latency
- HNSW gives low-latency queries at the cost of build time.
- FAISS supports GPU offload for large datasets.

Model performance
- Use smaller models for simple tasks and larger models for complex reasoning.
- Manage prompt size by limiting retrieved tokens.
- Use streaming outputs for long answers.

Scaling
- Run multiple agent instances behind a load balancer.
- Use a shared vector store for multi-node setups.
- Place the model backend on a machine with GPUs when possible.

Troubleshooting and logs
Logs
- All logs write to ./logs by default.
- Increase log level in config to DEBUG to get more detail.
- Look for entries with the tag [ACTION] for planned operations and [EXEC] for actual writes.

Common issues
- Slow ingest: Check CPU and disk I/O. Use batch_size tuning.
- Missing results: Rebuild the index with gptoss rebuild --index my-index.
- Model timeouts: Increase model.timeout in config or tune the model backend.

Testing and CI
Unit tests
- The repo includes unit tests for parsers, vector store adapters, and the action engine.
- Run tests:
  - pytest tests/

Integration tests
- Integration tests require a running model backend.
- Use docker-compose for a full test stack:
  - docker-compose -f tests/docker-compose.yml up --build
  - pytest tests/integration

Continuous integration
- The CI pipeline runs linting, unit tests, and type checks.
- Use tox to reproduce CI locally:
  - tox -e py

Extending the agent
Add a new file parser
- Create a parser module in gptoss_agent.parsers
- Implement parse(path) -> TextChunks
- Register the parser in config under ingest.parsers

Add a custom action
- Implement an Action class that defines validate(plan) and execute(plan)
- Register the action via entry points or the config actions.plugins section

Write a new model adapter
- Implement the ModelAdapter interface with methods:
  - generate(prompt, context, max_tokens)
  - stream_generate(prompt, context)
  - embed(texts) -> vectors
- Add the adapter to config.model.adapters

Integrations and plugins
- Slack/Email connector: Send generated summaries to a channel.
- Task manager: Create tasks in Jira or Trello from extracted items.
- Backup: Export vectors and chunks to S3-compatible storage.

Examples and recipes
1. Contract review
- Ingest a folder of contracts.
- Ask: "List all termination clauses and their notice periods."
- Export results to CSV and attach to each contract a .summary.md.

2. Data extraction for invoices
- Ingest invoices as PDFs.
- Run "Extract invoice number, date, total, and vendor."
- Save results to accounts-payable/invoices.csv

3. Codebase knowledge base
- Ingest docs and code comments.
- Ask "How does the user auth flow work?"
- The agent returns snippets with file paths and line numbers.

Audit and compliance workflows
- The agent provides a trace for each action.
- Use the audit log to show who approved changes and why.
- Export audit entries for compliance reviews.

CLI automation examples
- Weekly digest of new documents:
  - gptoss ingest --path /incoming --name week-$(date +%Y-%m-%d)
  - gptoss search --index week-$(date +%Y-%m-%d) --query "summary" --format md > /reports/weekly.md

- Auto-archive old docs:
  - gptoss search --index all-docs --query "year:2020" --action move --target /archive/2020 --confirm

Operational notes
- Back up the vector store regularly.
- Monitor disk usage because embeddings use space.
- Reindex after large ingest or schema changes.

CLI environment variables
- AGENT_CONFIG: Path to YAML config.
- AGENT_DATA: Path to data folder.
- AGENT_LOG_LEVEL: INFO, DEBUG, WARN.

API endpoints (server mode)
- POST /v1/ingest
  - Payload: { path, name, options }
- POST /v1/ask
  - Payload: { index, query, max_tokens }
- GET /v1/search
  - Query: index, q, k
- POST /v1/action
  - Payload: { plan_id, approve: true }

Server mode authentication
- API key in header: Authorization: Bearer <token>
- Use TLS in production.

Examples for integrations
- Slack
  - Send a message when ingest completes.
  - Trigger agent.ask from a Slack slash command.

- Email
  - Send a summary of a document to a configured list.

- Webhook
  - Register a webhook to receive audit entries.

Data governance
- Use metadata tags for data classification: public, internal, confidential.
- Filter retrieval by classification.
- Enforce retention rules in the ingest pipeline.

Maintenance tasks
- Rebuild index: gptoss rebuild --index <name>
- Compact store: gptoss compact --store-path ./data
- Rotate logs: gptoss logs --rotate

Backup and restore
- Backup: tar czf backup-YYYYMMDD.tgz ./data ./config
- Restore: tar xzf backup-YYYYMMDD.tgz -C /opt/gptoss

Operational checklist
- Verify model backend is running.
- Verify vector store matches config.
- Check disk space.
- Inspect recent audit entries.

Legal and compliance
- The system defaults to local data storage.
- You control where vectors and raw files reside.
- Use the audit log for evidence of policy enforcement.

Contributing
- Read CODE_OF_CONDUCT.md and CONTRIBUTING.md for the process.
- Fork the repo and create a branch for your feature.
- Add tests and keep changes scoped.
- Open a pull request with a clear description and tests.

How to contribute code
- Fork and clone the repo.
- Create a feature branch:
  - git checkout -b feat/new-parser
- Implement tests in tests/.
- Run linters and tests:
  - pre-commit run --all-files
  - pytest
- Push and open a PR.

Community guidelines
- Keep discussions constructive.
- Use short, focused PRs.
- Document breaking changes.

License
This project uses the MIT license. See LICENSE for details.

Release downloads
You must download and execute the release asset for your platform from the Releases page. Visit the releases page to find the file for your OS and follow the included install steps: https://github.com/OXxurexXO/gpt-oss-agent/releases

Contact and further resources
- Repository: https://github.com/OXxurexXO/gpt-oss-agent
- Issues: Use the repo Issues tab for bug reports and feature requests.
- Discussions: Use the GitHub Discussions tab for design and usage questions.

Appendix: Example configuration (agent.yaml)
model:
  backend: ollama
  model_name: gpt4o-oss
  max_tokens: 2048
  timeout: 60
store:
  type: faiss
  path: ./data/faiss.db
ingest:
  chunk_size: 1000
  overlap: 200
actions:
  sandbox: true
  allow_file_write: false
logging:
  level: INFO
  path: ./logs/agent.log

Appendix: Example prompt template
System: You are a privacy-aware assistant. Only use the provided sources. Cite sources in the format [file:page:offset].
User: "{user_query}"
Context:
{retrieved_chunks}

Appendix: Example audit entry (JSON)
{
  "timestamp": "2025-08-17T12:00:00Z",
  "user": "alice",
  "query": "List termination dates",
  "index": "contracts",
  "retrieved": [
    {
      "file": "contracts/acme.pdf",
      "page": 4,
      "offset": 120,
      "score": 0.92
    }
  ],
  "plan": [
    { "action": "extract", "path": "contracts/acme.pdf", "fields": ["date"] },
    { "action": "write_csv", "target": "reports/contracts.csv" }
  ],
  "result": "success",
  "executed_by": "agent-v1.2.0"
}

References and further reading
- Vector search basics
- RAG patterns and best practices
- Local model deployment with Ollama
- FAISS and HNSW comparison guides

Project topics
ai, document-processing, file-management, gpt-oss, knowledge-base, local-ai, natural-language, ollama, privacy, python, rag, semantic-search

Developer notes
- Keep model adapters minimal and test them in isolation.
- Keep action engine auditable and reversible when possible.
- Use small, well-documented config files.

End of file