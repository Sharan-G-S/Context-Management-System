"""
Context Optimization Strategies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

from ..core.memory.base import MemoryBlock


class BaseOptimizer:
    """Base class for optimization strategies."""
    
    def optimize(self, items: List[MemoryBlock], 
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Optimize memory items."""
        raise NotImplementedError


class RelevanceRankingOptimizer(BaseOptimizer):
    """Rank items by relevance to current query/task."""
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Rank by relevance score."""
        
        query = context.get("query", "") if context else ""
        if not query:
            return items
        
        # Score items by relevance
        scored = []
        for item in items:
            score = self._calculate_relevance(item, query)
            scored.append((item, score))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, score in scored]
    
    def _calculate_relevance(self, item: MemoryBlock, query: str) -> float:
        """Calculate relevance score."""
        query_lower = query.lower()
        content_lower = item.content.lower()
        
        # Keyword overlap
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & content_words)
        keyword_score = overlap / len(query_words)
        
        # Tag matching
        tag_score = 1.0 if any(query_lower in tag.lower() for tag in item.tags) else 0.0
        
        # Combine scores
        return (keyword_score * 0.7) + (tag_score * 0.3)


class TemporalDecayOptimizer(BaseOptimizer):
    """Apply temporal decay to older items."""
    
    def __init__(self, decay_rate: float = 0.5, decay_days: int = 7):
        self.decay_rate = decay_rate
        self.decay_days = decay_days
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Apply temporal decay and reorder."""
        
        now = datetime.now()
        
        # Apply decay to importance
        for item in items:
            age_days = (now - item.timestamp).days
            if age_days > self.decay_days:
                # Apply exponential decay
                decay_factor = self.decay_rate ** (age_days / self.decay_days)
                item.metadata["original_importance"] = item.importance
                item.importance *= decay_factor
        
        # Sort by decayed importance
        items.sort(key=lambda x: x.importance, reverse=True)
        
        return items


class ImportancePruningOptimizer(BaseOptimizer):
    """Remove low-importance items."""
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Prune low-importance items."""
        
        return [item for item in items if item.importance >= self.threshold]


class SemanticClusteringOptimizer(BaseOptimizer):
    """Group and deduplicate semantically similar items."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Cluster and deduplicate similar items."""
        
        if not items:
            return items
        
        # Simple content-based clustering
        clusters = []
        clustered_ids = set()
        
        for item in items:
            if item.id in clustered_ids:
                continue
            
            # Start new cluster
            cluster = [item]
            clustered_ids.add(item.id)
            
            # Find similar items
            for other in items:
                if other.id in clustered_ids:
                    continue
                
                similarity = self._calculate_similarity(item, other)
                if similarity >= self.similarity_threshold:
                    cluster.append(other)
                    clustered_ids.add(other.id)
            
            clusters.append(cluster)
        
        # Take representative from each cluster (highest importance)
        result = []
        for cluster in clusters:
            representative = max(cluster, key=lambda x: x.importance)
            result.append(representative)
        
        return result
    
    def _calculate_similarity(self, item1: MemoryBlock, item2: MemoryBlock) -> float:
        """Calculate content similarity."""
        # Simple Jaccard similarity
        words1 = set(item1.content.lower().split())
        words2 = set(item2.content.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


class AdaptiveBudgetOptimizer(BaseOptimizer):
    """Dynamically adjust token budgets based on usage patterns."""
    
    def __init__(self):
        self.usage_history = defaultdict(list)
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """This optimizer adjusts budgets rather than items."""
        
        # Track usage by memory type
        if context and "memory_type" in context:
            memory_type = context["memory_type"]
            total_tokens = sum(item.token_count for item in items)
            self.usage_history[memory_type].append({
                "timestamp": datetime.now(),
                "tokens": total_tokens,
                "items": len(items),
            })
        
        return items
    
    def get_recommended_budgets(self) -> Dict[str, float]:
        """Get recommended budget allocations based on usage."""
        
        if not self.usage_history:
            return {}
        
        # Calculate average usage per type
        avg_usage = {}
        for memory_type, history in self.usage_history.items():
            recent = history[-10:]  # Last 10 entries
            avg_tokens = sum(h["tokens"] for h in recent) / len(recent)
            avg_usage[memory_type] = avg_tokens
        
        # Normalize to percentages
        total = sum(avg_usage.values())
        if total == 0:
            return {}
        
        recommended = {
            memory_type: usage / total
            for memory_type, usage in avg_usage.items()
        }
        
        return recommended


class ContextOptimizer:
    """
    Main optimization orchestrator.
    
    Applies multiple optimization strategies in sequence.
    """
    
    def __init__(self, strategies: Optional[List[str]] = None):
        self.strategies = strategies or [
            "relevance_ranking",
            "temporal_decay",
            "importance_pruning",
            "semantic_clustering",
        ]
        
        # Initialize optimizers
        self.optimizers = {
            "relevance_ranking": RelevanceRankingOptimizer(),
            "temporal_decay": TemporalDecayOptimizer(),
            "importance_pruning": ImportancePruningOptimizer(),
            "semantic_clustering": SemanticClusteringOptimizer(),
            "adaptive_budgets": AdaptiveBudgetOptimizer(),
        }
    
    def optimize(self, items: List[MemoryBlock],
                context: Optional[Dict[str, Any]] = None) -> List[MemoryBlock]:
        """Apply all optimization strategies."""
        
        optimized = items
        
        for strategy_name in self.strategies:
            optimizer = self.optimizers.get(strategy_name)
            if optimizer:
                optimized = optimizer.optimize(optimized, context)
        
        return optimized
    
    def add_strategy(self, name: str, optimizer: BaseOptimizer):
        """Add custom optimization strategy."""
        self.optimizers[name] = optimizer
        if name not in self.strategies:
            self.strategies.append(name)
    
    def remove_strategy(self, name: str):
        """Remove optimization strategy."""
        if name in self.strategies:
            self.strategies.remove(name)
    
    def get_adaptive_budgets(self) -> Dict[str, float]:
        """Get adaptive budget recommendations."""
        adaptive = self.optimizers.get("adaptive_budgets")
        if isinstance(adaptive, AdaptiveBudgetOptimizer):
            return adaptive.get_recommended_budgets()
        return {}
