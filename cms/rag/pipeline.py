"""
RAG pipeline for document ingestion and retrieval.
Integrates with MongoDB storage and Groq LLM.
"""

from typing import List, Dict, Any, Optional
import uuid

from cms.storage.sqlite import SQLiteStorage
from cms.llm.groq_client import GroqClient
from cms.rag.chunker import DocumentChunker


class RAGPipeline:
    """RAG system for document ingestion and context retrieval."""
    
    def __init__(
        self,
        storage: SQLiteStorage,
        llm_client: GroqClient,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """Initialize RAG pipeline.
        
        Args:
            storage: MongoDB storage backend
            llm_client: Groq LLM client
            chunk_size: Size of document chunks
            chunk_overlap: Overlap between chunks
        """
        self.storage = storage
        self.llm = llm_client
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def ingest_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """Ingest document into RAG system.
        
        Args:
            content: Document content
            metadata: Optional metadata (source, author, date, etc.)
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        doc_id = doc_id or str(uuid.uuid4())
        
        # Chunk document
        chunks = self.chunker.chunk_text(content, metadata)
        
        # Generate embeddings and store
        for chunk in chunks:
            embedding = self.llm.generate_embedding(chunk['content'])
            
            self.storage.save_rag_document(
                doc_id=doc_id,
                content=chunk['content'],
                embedding=embedding,
                metadata=chunk['metadata'],
                chunk_index=chunk['chunk_index']
            )
        
        return doc_id
    
    def ingest_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Ingest multiple documents.
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata', 'doc_id'
            
        Returns:
            List of document IDs
        """
        doc_ids = []
        
        for doc in documents:
            doc_id = self.ingest_document(
                content=doc['content'],
                metadata=doc.get('metadata'),
                doc_id=doc.get('doc_id')
            )
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filter: Optional metadata filters
            
        Returns:
            List of relevant document chunks with similarity scores
        """
        # Generate query embedding
        query_embedding = self.llm.generate_embedding(query)
        
        # Search storage
        results = self.storage.search_rag_documents(
            query_embedding=query_embedding,
            top_k=top_k,
            metadata_filter=metadata_filter
        )
        
        return results
    
    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Answer question using RAG.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            metadata_filter: Optional metadata filters
            
        Returns:
            Dict with 'answer', 'sources', 'context'
        """
        # Retrieve relevant documents
        results = self.retrieve(
            query=question,
            top_k=top_k,
            metadata_filter=metadata_filter
        )
        
        if not results:
            return {
                'answer': "I don't have enough information to answer this question.",
                'sources': [],
                'context': ""
            }
        
        # Build context from results
        context = "\n\n".join([
            f"[Source {i+1}]: {doc['content']}"
            for i, doc in enumerate(results)
        ])
        
        # Generate answer
        answer = self.llm.answer_question(
            question=question,
            context=context
        )
        
        return {
            'answer': answer,
            'sources': [
                {
                    'document_id': doc['document_id'],
                    'chunk_index': doc['chunk_index'],
                    'content': doc['content'],
                    'similarity': doc.get('similarity', 0.0),
                    'metadata': doc.get('metadata', {})
                }
                for doc in results
            ],
            'context': context
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from RAG system.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        return self.storage.delete_rag_document(doc_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics.
        
        Returns:
            Dict with document counts and storage info
        """
        stats = self.storage.get_statistics()
        return {
            'total_documents': stats['rag_documents_count'],
            'database_size_mb': stats['database_size_mb']
        }
