"""
Semantic Memory: Knowledge-based fact storage with vector embeddings.
"""

from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime

from .base import BaseMemoryStore, MemoryBlock, MemoryType, MemoryScope


class SemanticFact(MemoryBlock):
    """Extended memory block for semantic facts."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_type = MemoryType.SEMANTIC
        self.embedding: Optional[np.ndarray] = None
        self.entity: Optional[str] = None
        self.relation: Optional[str] = None
        self.linked_facts: List[str] = []  # IDs of related facts


class SemanticMemory(BaseMemoryStore):
    """
    Semantic memory stores knowledge facts with vector embeddings for similarity search.
    
    Characteristics:
    - Knowledge-based (facts, entities, relationships)
    - Vector embeddings for semantic search
    - Deduplication and merging
    - Persistent across sessions
    - Medium-to-high importance (0.5-0.9)
    
    Features:
    - Automatic fact extraction
    - Similarity-based retrieval
    - Fact linking and relationships
    - Knowledge graph structure
    """
    
    def __init__(self, max_tokens: int = 2000, max_entries: int = 1000,
                 embedding_dim: int = 384, similarity_threshold: float = 0.7):
        super().__init__(max_tokens=max_tokens, max_entries=max_entries)
        self.embedding_dim = embedding_dim
        self.similarity_threshold = similarity_threshold
        
        # Vector storage (in production, use FAISS or similar)
        self._embeddings: Dict[str, np.ndarray] = {}
        
        # Entity and relation indices
        self._entity_index: Dict[str, List[str]] = {}  # entity -> fact IDs
        self._relation_index: Dict[str, List[str]] = {}  # relation -> fact IDs
    
    def add(self, item: MemoryBlock) -> bool:
        """Add fact to semantic memory."""
        if not isinstance(item, SemanticFact):
            # Convert to SemanticFact
            fact = SemanticFact(
                id=item.id,
                content=item.content,
                scope=item.scope,
                importance=item.importance,
                tags=item.tags,
                metadata=item.metadata,
                token_count=item.token_count,
            )
        else:
            fact = item
        
        # Check for duplicates or similar facts
        if fact.embedding is not None:
            similar = self._find_similar_facts(fact.embedding)
            if similar:
                # Merge with most similar fact
                self._merge_facts(similar[0], fact)
                return True
        
        # Check token budget
        if self.get_total_tokens() + fact.token_count > self.max_tokens:
            # Prune least important facts
            self._prune_by_importance()
        
        # Check entry limit
        if self.max_entries and len(self._items) >= self.max_entries:
            self._prune_by_importance()
        
        # Add to store
        self._items[fact.id] = fact
        
        # Update indices
        if fact.embedding is not None:
            self._embeddings[fact.id] = fact.embedding
        
        if fact.entity:
            self._entity_index.setdefault(fact.entity, []).append(fact.id)
        
        if fact.relation:
            self._relation_index.setdefault(fact.relation, []).append(fact.id)
        
        return True
    
    def get(self, item_id: str) -> Optional[SemanticFact]:
        """Retrieve fact by ID."""
        item = self._items.get(item_id)
        if item:
            item.update_access()
        return item
    
    def update(self, item: MemoryBlock) -> bool:
        """Update existing fact."""
        if item.id not in self._items:
            return False
        
        old_item = self._items[item.id]
        
        # Remove old indices
        if isinstance(old_item, SemanticFact):
            if old_item.entity and old_item.entity in self._entity_index:
                self._entity_index[old_item.entity].remove(item.id)
            if old_item.relation and old_item.relation in self._relation_index:
                self._relation_index[old_item.relation].remove(item.id)
        
        # Update item
        self._items[item.id] = item
        
        # Update indices
        if isinstance(item, SemanticFact):
            if item.embedding is not None:
                self._embeddings[item.id] = item.embedding
            if item.entity:
                self._entity_index.setdefault(item.entity, []).append(item.id)
            if item.relation:
                self._relation_index.setdefault(item.relation, []).append(item.id)
        
        return True
    
    def delete(self, item_id: str) -> bool:
        """Delete fact by ID."""
        if item_id not in self._items:
            return False
        
        item = self._items[item_id]
        
        # Remove from indices
        if isinstance(item, SemanticFact):
            if item.entity and item.entity in self._entity_index:
                self._entity_index[item.entity].remove(item_id)
            if item.relation and item.relation in self._relation_index:
                self._relation_index[item.relation].remove(item_id)
        
        if item_id in self._embeddings:
            del self._embeddings[item_id]
        
        del self._items[item_id]
        return True
    
    def search(self, query: str, top_k: int = 5, 
               query_embedding: Optional[np.ndarray] = None) -> List[SemanticFact]:
        """Search for relevant facts using semantic similarity."""
        if query_embedding is None:
            # Fallback to tag/content search
            return self._keyword_search(query, top_k)
        
        # Vector similarity search
        similarities = []
        for fact_id, embedding in self._embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= self.similarity_threshold:
                similarities.append((fact_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k facts
        results = []
        for fact_id, sim in similarities[:top_k]:
            fact = self._items[fact_id]
            fact.metadata['similarity'] = sim
            fact.update_access()
            results.append(fact)
        
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[SemanticFact]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        matches = []
        
        for item in self._items.values():
            score = 0.0
            
            # Check tags
            if any(query_lower in tag.lower() for tag in item.tags):
                score += 0.3
            
            # Check content
            if query_lower in item.content.lower():
                score += 0.4
            
            # Check entity
            if isinstance(item, SemanticFact) and item.entity:
                if query_lower in item.entity.lower():
                    score += 0.3
            
            if score > 0:
                matches.append((item, score))
        
        # Sort by score and importance
        matches.sort(key=lambda x: x[1] * x[0].importance, reverse=True)
        return [item for item, _ in matches[:top_k]]
    
    def get_all(self) -> List[SemanticFact]:
        """Get all facts sorted by importance."""
        items = list(self._items.values())
        items.sort(key=lambda x: x.calculate_composite_score(), reverse=True)
        return items
    
    def get_by_entity(self, entity: str) -> List[SemanticFact]:
        """Get all facts related to an entity."""
        fact_ids = self._entity_index.get(entity, [])
        return [self._items[fid] for fid in fact_ids if fid in self._items]
    
    def get_by_relation(self, relation: str) -> List[SemanticFact]:
        """Get all facts with a specific relation."""
        fact_ids = self._relation_index.get(relation, [])
        return [self._items[fid] for fid in fact_ids if fid in self._items]
    
    def link_facts(self, fact_id1: str, fact_id2: str):
        """Create a link between two facts."""
        if fact_id1 in self._items and fact_id2 in self._items:
            fact1 = self._items[fact_id1]
            fact2 = self._items[fact_id2]
            
            if isinstance(fact1, SemanticFact) and isinstance(fact2, SemanticFact):
                if fact_id2 not in fact1.linked_facts:
                    fact1.linked_facts.append(fact_id2)
                if fact_id1 not in fact2.linked_facts:
                    fact2.linked_facts.append(fact_id1)
    
    def _find_similar_facts(self, embedding: np.ndarray, threshold: float = 0.85) -> List[str]:
        """Find facts with similar embeddings."""
        similar = []
        for fact_id, emb in self._embeddings.items():
            similarity = self._cosine_similarity(embedding, emb)
            if similarity >= threshold:
                similar.append((fact_id, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [fid for fid, _ in similar]
    
    def _merge_facts(self, target_id: str, new_fact: SemanticFact):
        """Merge new fact into existing fact."""
        target = self._items[target_id]
        
        # Merge content (simple concatenation, could be smarter)
        if new_fact.content not in target.content:
            target.content += f" {new_fact.content}"
        
        # Merge tags
        target.tags = list(set(target.tags + new_fact.tags))
        
        # Merge metadata
        target.metadata.update(new_fact.metadata)
        
        # Update importance (take max)
        target.importance = max(target.importance, new_fact.importance)
        
        # Update timestamp
        target.last_accessed = datetime.now()
        target.access_count += 1
    
    def _prune_by_importance(self):
        """Remove least important facts to free up space."""
        items = sorted(self._items.values(), key=lambda x: x.calculate_composite_score())
        
        # Remove bottom 10%
        to_remove = max(1, len(items) // 10)
        for item in items[:to_remove]:
            if item.scope != MemoryScope.PERMANENT:
                self.delete(item.id)
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """Export knowledge as a graph structure."""
        nodes = []
        edges = []
        
        for fact in self._items.values():
            if isinstance(fact, SemanticFact):
                nodes.append({
                    "id": fact.id,
                    "label": fact.entity or fact.content[:50],
                    "type": "fact",
                    "importance": fact.importance,
                })
                
                for linked_id in fact.linked_facts:
                    edges.append({
                        "source": fact.id,
                        "target": linked_id,
                        "relation": fact.relation or "related_to",
                    })
        
        return {"nodes": nodes, "edges": edges}
