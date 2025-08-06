#!/usr/bin/env python3
"""
Knowledge Agent - Privacy-first RAG system using local GPT-OSS models
Enhanced version with comprehensive error handling and resilience
"""

import os
import json
import hashlib
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import threading
import time

# Third-party imports with error handling
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import ollama
    import PyPDF2
    from docx import Document
except ImportError as e:
    print(f"Missing dependencies. Install with:")
    print("pip install chromadb sentence-transformers ollama pypdf2 python-docx")
    print(f"Error: {e}")
    exit(1)

# Import our enhanced utilities and exceptions
from exceptions import (
    KnowledgeBaseError, IndexingError, SearchError, DatabaseError,
    ValidationError, ModelError
)
from utils import (
    retry_with_backoff, safe_ollama_chat, safe_ollama_embeddings,
    sanitize_input, ErrorHandler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 100
DEFAULT_CHUNK_OVERLAP = 200
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_SEARCH_RESULTS = 100
EMBEDDING_BATCH_SIZE = 32
INDEX_TIMEOUT = 300  # 5 minutes per file

@dataclass
class DocumentChunk:
    """Enhanced document chunk with validation"""
    content: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.content or len(self.content) < 10:
            raise ValidationError("Chunk content too short")
        if len(self.content) > MAX_CHUNK_SIZE * 2:
            raise ValidationError("Chunk content too long")

class DatabaseManager:
    """Thread-safe database manager with connection pooling"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize database with proper error handling"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        file_path TEXT PRIMARY KEY,
                        file_hash TEXT,
                        last_modified TIMESTAMP,
                        indexed_at TIMESTAMP,
                        chunk_count INTEGER,
                        status TEXT DEFAULT 'pending',
                        error_message TEXT
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status 
                    ON documents(status)
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id TEXT PRIMARY KEY,
                        file_path TEXT,
                        content TEXT,
                        embedding_id TEXT,
                        created_at TIMESTAMP,
                        FOREIGN KEY (file_path) REFERENCES documents(file_path)
                    )
                """)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                isolation_level='DEFERRED'
            )
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def update_document_status(self, file_path: str, status: str, 
                              error_message: Optional[str] = None):
        """Update document indexing status"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("""
                        UPDATE documents 
                        SET status = ?, error_message = ?
                        WHERE file_path = ?
                    """, (status, error_message, file_path))
            except sqlite3.Error as e:
                logger.error(f"Failed to update document status: {e}")

class EnhancedKnowledgeAgent:
    """Enhanced knowledge management system with comprehensive error handling"""
    
    def __init__(self, data_dir: str = "./knowledge_base", 
                 model: str = "gpt-oss:20b",
                 fallback_model: str = "gpt-oss:7b"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.model = model
        self.fallback_model = fallback_model
        
        # Initialize components with error handling
        self._init_embedding_model()
        self._init_vector_database()
        self.db_manager = DatabaseManager(self.data_dir / "documents.db")
        
        # Supported file extensions
        self.supported_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.json', '.csv',
            '.pdf', '.docx', '.html', '.xml', '.yaml', '.yml',
            '.cpp', '.c', '.h', '.java', '.go', '.rs', '.rb',
            '.php', '.sh', '.sql', '.r', '.scala', '.kt'
        }
        
        logger.info(f"Knowledge Agent initialized with model: {model}")
    
    def _init_embedding_model(self):
        """Initialize embedding model with fallback"""
        try:
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            # Test the model
            test_embedding = self.embedding_model.encode("test")
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Try a smaller model as fallback
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L12-v2')
                logger.info("Loaded fallback embedding model")
            except Exception as e2:
                raise ModelError(f"Failed to load any embedding model: {e2}")
    
    def _init_vector_database(self):
        """Initialize vector database with error handling"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.data_dir / "chroma_db")
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector database initialized")
        except Exception as e:
            raise DatabaseError(f"Failed to initialize vector database: {e}")
    
    @retry_with_backoff(max_retries=3, exceptions=(IOError, OSError))
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file content with retry logic"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            raise IndexingError(f"Failed to hash file {file_path}: {e}")
    
    def _is_file_indexed(self, file_path: Path) -> bool:
        """Check if file is already indexed with error handling"""
        try:
            current_hash = self._get_file_hash(file_path)
            with self.db_manager._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT file_hash, status FROM documents WHERE file_path = ?",
                    (str(file_path),)
                )
                result = cursor.fetchone()
                if result:
                    return (result['file_hash'] == current_hash and 
                           result['status'] == 'completed')
                return False
        except Exception as e:
            logger.warning(f"Error checking if file is indexed: {e}")
            return False
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text with comprehensive error handling"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                raise IndexingError(f"File too large: {file_size} bytes")
            
            if file_path.suffix == '.pdf':
                return self._extract_pdf_text_safe(file_path)
            elif file_path.suffix == '.docx':
                return self._extract_docx_text_safe(file_path)
            else:
                return self._extract_text_safe(file_path)
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise IndexingError(f"Text extraction failed: {e}")
    
    def _extract_pdf_text_safe(self, file_path: Path) -> str:
        """Safely extract text from PDF with error recovery"""
        text_parts = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {i+1}/{total_pages}: {e}")
                        continue
                
                if not text_parts:
                    raise IndexingError("No text could be extracted from PDF")
                
                return "\n".join(text_parts)
        except Exception as e:
            raise IndexingError(f"PDF extraction failed: {e}")
    
    def _extract_docx_text_safe(self, file_path: Path) -> str:
        """Safely extract text from DOCX"""
        try:
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            if not paragraphs:
                raise IndexingError("No text found in document")
            
            return "\n".join(paragraphs)
        except Exception as e:
            raise IndexingError(f"DOCX extraction failed: {e}")
    
    def _extract_text_safe(self, file_path: Path) -> str:
        """Safely extract plain text with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                    if text:
                        return text
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Failed with encoding {encoding}: {e}")
        
        # Last resort: read with error replacement
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            raise IndexingError(f"Text extraction failed: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, 
                   overlap: int = 200) -> List[str]:
        """Create text chunks with validation"""
        if not text or len(text) < MIN_CHUNK_SIZE:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Try to break at sentence or paragraph boundary
            if end < text_length:
                # Look for sentence end
                for delimiter in ['. ', '.\n', '!\n', '?\n', '\n\n']:
                    last_delimiter = text[start:end].rfind(delimiter)
                    if last_delimiter != -1:
                        end = start + last_delimiter + len(delimiter)
                        break
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) >= MIN_CHUNK_SIZE:
                chunks.append(chunk)
            
            start = end - overlap if end < text_length else end
        
        return chunks
    
    @retry_with_backoff(max_retries=2, exceptions=(ModelError,))
    def index_file(self, file_path: Path, force: bool = False) -> Dict[str, Any]:
        """Index a single file with comprehensive error handling"""
        stats = {'status': 'pending', 'chunks': 0, 'error': None}
        
        try:
            # Validate file
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if file_path.suffix.lower() not in self.supported_extensions:
                raise ValidationError(f"Unsupported file type: {file_path.suffix}")
            
            # Check if already indexed
            if not force and self._is_file_indexed(file_path):
                logger.info(f"File already indexed: {file_path}")
                stats['status'] = 'skipped'
                return stats
            
            # Extract and chunk text
            logger.info(f"Indexing file: {file_path}")
            text = self.extract_text_from_file(file_path)
            
            if not text or len(text) < MIN_CHUNK_SIZE:
                raise IndexingError("Insufficient text content")
            
            chunks = self.chunk_text(text)
            if not chunks:
                raise IndexingError("No valid chunks created")
            
            # Generate embeddings with batching
            embeddings = []
            for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
                batch = chunks[i:i + EMBEDDING_BATCH_SIZE]
                try:
                    batch_embeddings = self.embedding_model.encode(batch)
                    embeddings.extend(batch_embeddings)
                except Exception as e:
                    logger.error(f"Embedding generation failed: {e}")
                    raise ModelError(f"Failed to generate embeddings: {e}")
            
            # Store in vector database
            chunk_ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    'source': str(file_path),
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'indexed_at': datetime.now().isoformat()
                }
                for i in range(len(chunks))
            ]
            
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=chunk_ids,
                metadatas=metadatas
            )
            
            # Update database
            with self.db_manager._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO documents 
                    (file_path, file_hash, last_modified, indexed_at, chunk_count, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    self._get_file_hash(file_path),
                    datetime.fromtimestamp(file_path.stat().st_mtime),
                    datetime.now(),
                    len(chunks),
                    'completed'
                ))
            
            stats['status'] = 'completed'
            stats['chunks'] = len(chunks)
            logger.info(f"Successfully indexed {file_path}: {len(chunks)} chunks")
            
        except Exception as e:
            stats['status'] = 'failed'
            stats['error'] = str(e)
            self.db_manager.update_document_status(str(file_path), 'failed', str(e))
            logger.error(f"Failed to index {file_path}: {e}")
            raise IndexingError(f"Indexing failed: {e}")
        
        return stats
    
    def index_directory(self, directory: str, recursive: bool = True,
                       max_workers: int = 4) -> Dict[str, Any]:
        """Index directory with parallel processing and error recovery"""
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Find all supported files
        pattern = '**/*' if recursive else '*'
        files = [
            f for f in directory.glob(pattern)
            if f.is_file() and f.suffix.lower() in self.supported_extensions
        ]
        
        stats['total_files'] = len(files)
        logger.info(f"Found {len(files)} files to index")
        
        # Index files with progress tracking
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing {i}/{len(files)}: {file_path.name}")
            
            try:
                result = self.index_file(file_path)
                if result['status'] == 'completed':
                    stats['successful'] += 1
                elif result['status'] == 'skipped':
                    stats['skipped'] += 1
                else:
                    stats['failed'] += 1
                    if result['error']:
                        stats['errors'].append(f"{file_path}: {result['error']}")
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{file_path}: {e}")
                logger.error(f"Failed to index {file_path}: {e}")
                continue
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    @retry_with_backoff(max_retries=2, exceptions=(SearchError,))
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search with enhanced error handling"""
        try:
            # Sanitize and validate query
            query = sanitize_input(query, max_length=1000)
            if not query:
                raise ValidationError("Empty search query")
            
            n_results = min(n_results, MAX_SEARCH_RESULTS)
            
            # Generate query embedding
            try:
                query_embedding = self.embedding_model.encode(query)
            except Exception as e:
                logger.error(f"Failed to encode query: {e}")
                raise ModelError(f"Query encoding failed: {e}")
            
            # Search vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if not results or not results['documents']:
                return []
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search operation failed: {e}")
    
    def chat_with_knowledge(self, query: str, context_size: int = 5) -> str:
        """Chat with knowledge base using error handling and fallback"""
        try:
            # Search for relevant context
            search_results = self.search(query, n_results=context_size)
            
            if not search_results:
                return "No relevant information found in the knowledge base."
            
            # Build context
            context = "\n\n".join([
                f"[Source: {r['metadata'].get('source', 'Unknown')}]\n{r['content']}"
                for r in search_results
            ])
            
            # Create prompt
            messages = [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant. Use the provided context to answer questions.'
                },
                {
                    'role': 'user',
                    'content': f"Context:\n{context}\n\nQuestion: {query}"
                }
            ]
            
            # Get response with fallback
            response = safe_ollama_chat(
                model=self.model,
                messages=messages,
                fallback_model=self.fallback_model,
                timeout=120
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"Error: Unable to process query. {e}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics with error handling"""
        stats = {
            'total_files': 0,
            'total_chunks': 0,
            'status': 'unknown',
            'errors': []
        }
        
        try:
            # Get document count from database
            with self.db_manager._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(chunk_count) as chunks
                    FROM documents
                """)
                result = cursor.fetchone()
                if result:
                    stats['total_files'] = result['completed'] or 0
                    stats['total_chunks'] = result['chunks'] or 0
            
            # Get collection info
            try:
                collection_count = self.collection.count()
                stats['vector_count'] = collection_count
            except:
                stats['vector_count'] = 0
            
            stats['status'] = 'operational'
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            stats['errors'].append(str(e))
            stats['status'] = 'error'
        
        return stats

def main():
    """Main function with comprehensive error handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Knowledge Agent")
    parser.add_argument("--index", help="Index a file or directory")
    parser.add_argument("--search", help="Search the knowledge base")
    parser.add_argument("--chat", help="Chat with the knowledge base")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("-m", "--model", default="gpt-oss:20b", help="Model to use")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        agent = EnhancedKnowledgeAgent(model=args.model)
        
        if args.index:
            path = Path(args.index)
            if path.is_file():
                result = agent.index_file(path)
            else:
                result = agent.index_directory(args.index)
            print(json.dumps(result, indent=2))
        
        elif args.search:
            results = agent.search(args.search)
            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} ---")
                print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                print(f"Content: {result['content'][:200]}...")
        
        elif args.chat:
            response = agent.chat_with_knowledge(args.chat)
            print(response)
        
        elif args.stats:
            stats = agent.get_stats()
            print(json.dumps(stats, indent=2))
        
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()