"""
Document chunking for RAG system.
Splits documents into semantic chunks for embedding.
"""

from typing import List, Dict, Any, Optional
import re


class DocumentChunker:
    """Split documents into semantic chunks for RAG."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separator: str = "\n\n"
    ):
        """Initialize document chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks
            separator: Primary separator for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk text into smaller segments.
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with 'content', 'metadata', 'chunk_index'
        """
        # Split by separator first
        sections = text.split(self.separator)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # If section fits in current chunk
            if len(current_chunk) + len(section) + len(self.separator) <= self.chunk_size:
                if current_chunk:
                    current_chunk += self.separator + section
                else:
                    current_chunk = section
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'metadata': metadata or {},
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1
                
                # Start new chunk with overlap
                if len(current_chunk) > self.chunk_overlap:
                    overlap = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap + self.separator + section
                else:
                    current_chunk = section
                
                # If section itself is too large, split it
                while len(current_chunk) > self.chunk_size:
                    chunks.append({
                        'content': current_chunk[:self.chunk_size],
                        'metadata': metadata or {},
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1
                    current_chunk = current_chunk[self.chunk_size - self.chunk_overlap:]
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'metadata': metadata or {},
                'chunk_index': chunk_index
            })
        
        return chunks
    
    def chunk_by_sentences(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk text by sentences for better semantic boundaries.
        
        Args:
            text: Input text
            metadata: Optional metadata
            
        Returns:
            List of chunk dicts
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk + ".",
                        'metadata': metadata or {},
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1
                current_chunk = sentence
        
        if current_chunk:
            chunks.append({
                'content': current_chunk + ".",
                'metadata': metadata or {},
                'chunk_index': chunk_index
            })
        
        return chunks
