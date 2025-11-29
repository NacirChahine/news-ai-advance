import os
import json
import math
import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings using Ollama."""
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.ollama_endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/embeddings")

    def generate(self, text: str) -> List[float]:
        """Generate embeddings for a single text string."""
        if not text:
            return []
            
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = requests.post(self.ollama_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []

class VectorStore:
    """A simple in-memory vector store."""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        
    def add_document(self, text: str, metadata: Dict[str, Any] = None, embedding: List[float] = None):
        """Add a document to the store."""
        if embedding is None:
            # In a real app, we'd generate it here, but we'll assume it's passed or handled by RAGPipeline
            return
            
        self.documents.append({
            "text": text,
            "metadata": metadata or {},
            "embedding": embedding
        })
        
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents using cosine similarity."""
        if not self.documents or not query_embedding:
            return []
            
        results = []
        for doc in self.documents:
            doc_embedding = doc["embedding"]
            if not doc_embedding:
                continue
                
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            results.append({
                "document": doc,
                "score": similarity
            })
            
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return dot_product / (norm_v1 * norm_v2)

class WebSearcher:
    """Handles web search operations."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'WEB_SEARCH_API_KEY', '')
        self.cx = getattr(settings, 'WEB_SEARCH_CX', '')
        self.provider = getattr(settings, 'WEB_SEARCH_PROVIDER', 'google')
        self._validate_config()
        
    def _validate_config(self):
        """Validate the configuration for web search."""
        if not self.api_key:
            logger.warning("WEB_SEARCH_API_KEY is not configured. Web search will be disabled.")
            return
            
        if self.provider == 'google':
            if not self.cx:
                logger.error("WEB_SEARCH_CX (Google Custom Search Engine ID) is not configured. "
                           "Please set this in your environment or settings.py. "
                           "Web search will be disabled.")
            elif self.cx == self.api_key:
                logger.error("WEB_SEARCH_CX appears to be the same as WEB_SEARCH_API_KEY. "
                           "The CX parameter should be your Custom Search Engine ID, not your API key. "
                           "Please check your configuration at https://programmablesearchengine.google.com/")
        
    def _sanitize_query(self, query: str) -> Optional[str]:
        """Sanitize and validate search query."""
        if not query or not query.strip():
            logger.warning("Empty search query provided.")
            return None
            
        # Trim whitespace
        sanitized = query.strip()
        
        # Limit query length (Google has a 2048 character limit for the entire URL)
        max_query_length = 1500  # Conservative limit
        if len(sanitized) > max_query_length:
            logger.warning(f"Query too long ({len(sanitized)} chars), truncating to {max_query_length} chars.")
            sanitized = sanitized[:max_query_length]
            
        return sanitized
        
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Perform a web search."""
        if not self.api_key:
            logger.debug("Web search skipped: API key not configured.")
            return []
            
        # Sanitize query
        sanitized_query = self._sanitize_query(query)
        if not sanitized_query:
            return []
            
        if self.provider == 'google':
            return self._search_google(sanitized_query, num_results)
        # Add other providers here
        return []
        
    def _search_google(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using Google Custom Search JSON API."""
        # Validate configuration before making request
        if not self.cx:
            logger.error("Cannot perform Google search: WEB_SEARCH_CX is not configured.")
            return []
            
        if self.cx == self.api_key:
            logger.error("Cannot perform Google search: WEB_SEARCH_CX appears to be incorrectly set to the API key value.")
            return []
            
        # Validate num_results (Google allows 1-10)
        num_results = max(1, min(num_results, 10))
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': num_results
        }
        
        try:
            logger.debug(f"Performing Google search for query: {query[:100]}...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    })
                logger.info(f"Google search returned {len(results)} results.")
            else:
                logger.warning(f"Google search returned no items for query: {query[:100]}")
            return results
        except requests.exceptions.HTTPError as e:
            # Log detailed error information
            error_msg = f"Google search HTTP error: {e}"
            if hasattr(e.response, 'text'):
                try:
                    error_data = e.response.json()
                    error_msg += f"\n{json.dumps(error_data, indent=2)}"
                except:
                    error_msg += f"\nResponse: {e.response.text[:500]}"
            logger.error(error_msg)
            return []
        except requests.exceptions.Timeout:
            logger.error(f"Google search timeout for query: {query[:100]}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Google search request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Google search: {e}")
            return []

class RAGPipeline:
    """Main RAG pipeline."""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.web_searcher = WebSearcher()
        
    def add_document(self, text: str, metadata: Dict[str, Any] = None):
        """Add a document to the RAG system."""
        embedding = self.embedding_generator.generate(text)
        if embedding:
            self.vector_store.add_document(text, metadata, embedding)
            
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        embedding = self.embedding_generator.generate(query)
        if not embedding:
            return []
        return self.vector_store.search(embedding, top_k)
        
    def web_search_and_add(self, query: str, num_results: int = 3):
        """Perform web search and add results to the vector store."""
        results = self.web_searcher.search(query, num_results)
        for result in results:
            text = f"{result['title']}\n{result['snippet']}"
            self.add_document(text, metadata={"source": result['link'], "title": result['title']})
            
    def get_augmented_context(self, query: str) -> str:
        """Get context from the vector store for a query."""
        results = self.retrieve(query)
        context = ""
        for res in results:
            doc = res['document']
            context += f"Source: {doc['metadata'].get('source', 'Unknown')}\n"
            context += f"Content: {doc['text']}\n\n"
        return context

class FactChecker:
    """Professional fact-checking workflow."""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag = rag_pipeline
        
    def check(self, claim: str) -> Dict[str, Any]:
        """Perform a fact check on a claim."""
        # 1. Search web for information
        self.rag.web_search_and_add(claim)
        
        # 2. Retrieve relevant context
        context = self.rag.get_augmented_context(claim)
        
        # 3. Use LLM to verify (this logic is in utils.py, but we prepare the context here)
        return {
            "claim": claim,
            "context": context
        }
