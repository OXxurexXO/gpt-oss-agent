#!/usr/bin/env python3
"""
Knowledge Agent - Privacy-first RAG system using local GPT-OSS models

A comprehensive knowledge management system that indexes documents, code, and files
locally and provides intelligent search and analysis capabilities using GPT-OSS models.
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# Third-party imports
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import ollama
    import PyPDF2
    from docx import Document
except ImportError as e:
    print(f"Missing dependencies. Install with:")
    print("pip install chromadb sentence-transformers ollama pypdf2 python-docx")
    exit(1)

@dataclass
class DocumentChunk:
    content: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any]

class KnowledgeAgent:
    """Privacy-first knowledge management system using local GPT-OSS models."""
    
    def __init__(self, data_dir: str = "./knowledge_base", model: str = "gpt-oss:20b"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.model = model
        
        # Initialize embedding model (runs locally)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector database
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize document tracking database
        self.db_path = self.data_dir / "documents.db"
        self._init_document_db()
        
        # Supported file extensions
        self.supported_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.json', '.csv',
            '.pdf', '.docx', '.html', '.xml', '.yaml', '.yml',
            '.cpp', '.c', '.h', '.java', '.go', '.rs', '.rb',
            '.php', '.sh', '.sql', '.r', '.scala', '.kt'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _init_document_db(self):
        """Initialize SQLite database for document tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT,
                    last_modified TIMESTAMP,
                    indexed_at TIMESTAMP,
                    chunk_count INTEGER
                )
            """)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _is_file_indexed(self, file_path: Path) -> bool:
        """Check if file is already indexed and up to date"""
        try:
            current_hash = self._get_file_hash(file_path)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT file_hash FROM documents WHERE file_path = ?",
                    (str(file_path),)
                )
                result = cursor.fetchone()
                return result and result[0] == current_hash
        except:
            return False
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        try:
            if file_path.suffix == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_path.suffix == '.docx':
                return self._extract_docx_text(file_path)
            else:
                # Plain text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            self.logger.warning(f"Could not extract text from {file_path}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF files"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX files"""
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
        return [chunk for chunk in chunks if chunk.strip()]
    
    def index_file(self, file_path: Path) -> int:
        """Index a single file"""
        if self._is_file_indexed(file_path):
            self.logger.info(f"File {file_path} already indexed and up to date")
            return 0
        
        # Extract text
        text = self.extract_text_from_file(file_path)
        if not text.strip():
            return 0
        
        # Create chunks
        chunks = self.chunk_text(text)
        if not chunks:
            return 0
        
        # Remove old chunks for this file
        try:
            self.collection.delete(where={"source": str(file_path)})
        except:
            pass
        
        # Create embeddings and store
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_path}_{i}"
            chunk_objects.append(DocumentChunk(
                content=chunk,
                source=str(file_path),
                chunk_id=chunk_id,
                metadata={
                    "source": str(file_path),
                    "chunk_index": i,
                    "file_type": file_path.suffix,
                    "indexed_at": datetime.now().isoformat()
                }
            ))
        
        # Add to vector database
        self.collection.add(
            documents=[chunk.content for chunk in chunk_objects],
            metadatas=[chunk.metadata for chunk in chunk_objects],
            ids=[chunk.chunk_id for chunk in chunk_objects]
        )
        
        # Update document tracking
        file_hash = self._get_file_hash(file_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (file_path, file_hash, last_modified, indexed_at, chunk_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(file_path),
                file_hash,
                datetime.fromtimestamp(file_path.stat().st_mtime),
                datetime.now(),
                len(chunks)
            ))
        
        self.logger.info(f"Indexed {file_path} with {len(chunks)} chunks")
        return len(chunks)
    
    def index_directory(self, directory: Path, recursive: bool = True) -> Dict[str, int]:
        """Index all supported files in a directory"""
        results = {"indexed": 0, "skipped": 0, "errors": 0}
        
        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    # Skip hidden files and common non-content directories
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                    if any(skip in str(file_path) for skip in ['node_modules', '__pycache__', '.git']):
                        continue
                    
                    chunks = self.index_file(file_path)
                    if chunks > 0:
                        results["indexed"] += 1
                    else:
                        results["skipped"] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error indexing {file_path}: {e}")
                    results["errors"] += 1
        
        return results
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'][0]:
            return []
        
        search_results = []
        for i in range(len(results['documents'][0])):
            search_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return search_results
    
    def chat_with_knowledge(self, query: str) -> str:
        """Chat with your knowledge base using GPT-OSS"""
        # Search for relevant context
        search_results = self.search(query, n_results=3)
        
        if not search_results:
            return "I couldn't find any relevant information in your knowledge base for that query."
        
        # Build context
        context_parts = []
        for result in search_results:
            source = Path(result['metadata']['source']).name
            context_parts.append(f"From {source}:\n{result['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following information from the user's knowledge base, please answer their question:

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a helpful answer based on the context above. If the context doesn't contain enough information to fully answer the question, please say so and suggest what additional information might be needed."""
        
        # Query GPT-OSS
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content']
        except Exception as e:
            return f"Error querying GPT-OSS: {e}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(chunk_count) FROM documents")
            files, chunks = cursor.fetchone()
        
        return {
            "total_files": files or 0,
            "total_chunks": chunks or 0,
            "collection_count": self.collection.count()
        }

def main():
    """Interactive CLI for the Knowledge Agent"""
    agent = KnowledgeAgent()
    
    print("🧠 GPT-OSS Knowledge Agent")
    print("Your private AI that knows your files!")
    print()
    
    while True:
        print("\nOptions:")
        print("1. Index a directory")
        print("2. Chat with your knowledge")
        print("3. Search documents")
        print("4. View statistics")
        print("5. Exit")
        
        choice = input("\nChoose an option (1-5): ").strip()
        
        if choice == "1":
            dir_path = input("Enter directory path to index: ").strip()
            if os.path.exists(dir_path):
                print(f"Indexing {dir_path}...")
                results = agent.index_directory(Path(dir_path))
                print(f"✅ Indexed {results['indexed']} files, skipped {results['skipped']}, errors: {results['errors']}")
            else:
                print("❌ Directory not found")
        
        elif choice == "2":
            query = input("Ask a question about your documents: ").strip()
            if query:
                print("\n🤖 Thinking...")
                response = agent.chat_with_knowledge(query)
                print(f"\n💬 {response}")
        
        elif choice == "3":
            query = input("Search for: ").strip()
            if query:
                results = agent.search(query)
                print(f"\n🔍 Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    source = Path(result['metadata']['source']).name
                    preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    print(f"\n{i}. From: {source}")
                    print(f"   {preview}")
        
        elif choice == "4":
            stats = agent.get_stats()
            print(f"\n📊 Knowledge Base Stats:")
            print(f"   Files indexed: {stats['total_files']}")
            print(f"   Text chunks: {stats['total_chunks']}")
            print(f"   Vector database entries: {stats['collection_count']}")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
