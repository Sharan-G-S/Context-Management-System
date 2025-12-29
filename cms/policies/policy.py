"""
Policy-driven control layer for context management.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import yaml


@dataclass
class MemoryPolicy:
    """Policy for memory management."""
    
    # Core memory
    core_max_tokens: int = 1000
    core_importance_threshold: float = 0.9
    core_immutable: bool = True
    
    # Semantic memory
    semantic_max_tokens: int = 2000
    semantic_max_entries: int = 1000
    semantic_similarity_threshold: float = 0.7
    
    # Episodic memory
    episodic_max_tokens: int = 1500
    episodic_max_entries: int = 500
    episodic_retention_days: int = 30
    
    # Working memory
    working_max_tokens: int = 3000
    working_max_turns: int = 10
    working_compression_threshold: float = 0.8


@dataclass
class TokenPolicy:
    """Policy for token budget allocation."""
    
    # Token budgets (as percentages)
    system: float = 0.10
    core: float = 0.12
    semantic: float = 0.25
    episodic: float = 0.18
    working: float = 0.30
    reserve: float = 0.05
    
    # Budget enforcement
    strict_budget: bool = True
    allow_overflow: bool = False
    overflow_strategy: str = "compress"  # compress, truncate, summarize
    
    def validate(self):
        """Validate policy configuration."""
        total = self.system + self.core + self.semantic + self.episodic + self.working + self.reserve
        if total > 1.0:
            raise ValueError(f"Total token allocation {total} exceeds 1.0")
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for TokenBudget."""
        return {
            "system": self.system,
            "core": self.core,
            "semantic": self.semantic,
            "episodic": self.episodic,
            "working": self.working,
            "reserve": self.reserve,
        }


@dataclass
class SummarizationPolicy:
    """Policy for summarization and compression."""
    
    enabled: bool = True
    model: str = "gpt-3.5-turbo"
    strategy: str = "extractive"  # extractive, abstractive, hybrid
    compression_ratio: float = 0.3
    min_length: int = 100
    max_length: int = 500
    batch_size: int = 5


@dataclass
class AssemblyPolicy:
    """Policy for context assembly."""
    
    # Section ordering
    section_order: list = field(default_factory=lambda: [
        "system",
        "core_memory",
        "semantic_memory",
        "episodic_memory",
        "working_memory",
        "current_task",
    ])
    
    # Importance weights
    recency_weight: float = 0.3
    relevance_weight: float = 0.4
    importance_weight: float = 0.3
    
    # Features
    position_bias_mitigation: bool = True
    deduplication: bool = True
    
    def get_importance_weights(self) -> Dict[str, float]:
        """Get importance weights as dictionary."""
        return {
            "recency": self.recency_weight,
            "relevance": self.relevance_weight,
            "importance": self.importance_weight,
        }


@dataclass
class ImportancePolicy:
    """Policy for importance scoring."""
    
    # Base scores for different types
    user_explicit: float = 1.0
    system_critical: float = 0.95
    task_relevant: float = 0.8
    recent_interaction: float = 0.7
    background_info: float = 0.5
    
    # Custom scoring function
    custom_scorer: Optional[Callable] = None


@dataclass
class OptimizationPolicy:
    """Policy for context optimization."""
    
    enabled: bool = True
    strategies: list = field(default_factory=lambda: [
        "relevance_ranking",
        "temporal_decay",
        "importance_pruning",
        "semantic_clustering",
    ])
    
    # Auto-pruning
    auto_prune: bool = True
    prune_interval_hours: int = 24
    prune_threshold: float = 0.4
    
    # Adaptive budgets
    adaptive_budgets: bool = True
    predictive_loading: bool = False


@dataclass
class CMSPolicy:
    """Complete CMS policy configuration."""
    
    memory: MemoryPolicy = field(default_factory=MemoryPolicy)
    token: TokenPolicy = field(default_factory=TokenPolicy)
    summarization: SummarizationPolicy = field(default_factory=SummarizationPolicy)
    assembly: AssemblyPolicy = field(default_factory=AssemblyPolicy)
    importance: ImportancePolicy = field(default_factory=ImportancePolicy)
    optimization: OptimizationPolicy = field(default_factory=OptimizationPolicy)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CMSPolicy":
        """Load policy from YAML file."""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return cls(
            memory=MemoryPolicy(**config.get("memory", {})),
            token=TokenPolicy(**config.get("token_budget", {})),
            summarization=SummarizationPolicy(**config.get("summarization", {})),
            assembly=AssemblyPolicy(
                section_order=config.get("assembly", {}).get("section_order", []),
                recency_weight=config.get("assembly", {}).get("importance_weights", {}).get("recency", 0.3),
                relevance_weight=config.get("assembly", {}).get("importance_weights", {}).get("relevance", 0.4),
                importance_weight=config.get("assembly", {}).get("importance_weights", {}).get("importance", 0.3),
                position_bias_mitigation=config.get("assembly", {}).get("position_bias_mitigation", True),
                deduplication=config.get("assembly", {}).get("deduplication", True),
            ),
            importance=ImportancePolicy(**config.get("policies", {}).get("importance_scoring", {})),
            optimization=OptimizationPolicy(
                enabled=config.get("optimization", {}).get("enabled", True),
                strategies=config.get("optimization", {}).get("strategies", []),
                auto_prune=config.get("optimization", {}).get("auto_prune", {}).get("enabled", True),
                prune_interval_hours=config.get("optimization", {}).get("auto_prune", {}).get("interval_hours", 24),
                prune_threshold=config.get("optimization", {}).get("auto_prune", {}).get("threshold", 0.4),
            ),
        )
    
    def validate(self):
        """Validate all policies."""
        self.token.validate()
        
        # Validate weights sum to 1.0
        weights = self.assembly.get_importance_weights()
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Importance weights sum to {total}, expected 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory": self.memory.__dict__,
            "token": self.token.__dict__,
            "summarization": self.summarization.__dict__,
            "assembly": self.assembly.__dict__,
            "importance": self.importance.__dict__,
            "optimization": self.optimization.__dict__,
        }
