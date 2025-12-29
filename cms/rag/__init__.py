"""
RAG (Retrieval-Augmented Generation) module.
Provides document ingestion, chunking, embedding, and retrieval.
"""

from cms.rag.pipeline import RAGPipeline
from cms.rag.chunker import DocumentChunker

__all__ = ['RAGPipeline', 'DocumentChunker']
