"""
Main Context Manager API - Central interface for CMS.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .core.memory import (
    CoreMemory, SemanticMemory, EpisodicMemory, WorkingMemory,
    MemoryBlock, SemanticFact, Episode, ConversationTurn,
    MemoryScope
)
from .core.tokens import TokenAccountant
from .core.summarization import CompressionEngine
from .core.assembly import ContextAssembler, ContextSelector, ContextOrganizer
from .optimization import ContextOptimizer
from .policies.policy import CMSPolicy
from .config import Config, load_config


class ContextManager:
    """
    Main Context Management System API.
    
    Provides a clean interface for managing LLM context across
    multiple memory tiers with automatic optimization and assembly.
    """
    
    def __init__(self, config: Optional[Config] = None, 
                policy: Optional[CMSPolicy] = None):
        """
        Initialize Context Manager.
        
        Args:
            config: Configuration object (loads from file if None)
            policy: Policy object (derived from config if None)
        """
        
        # Load configuration
        self.config = config or load_config()
        
        # Load or create policy
        if policy:
            self.policy = policy
        else:
            config_path = self.config.get("config_path", "config/default_config.yaml")
            self.policy = CMSPolicy.from_yaml(config_path)
        
        # Validate policy
        self.policy.validate()
        
        # Initialize memory stores
        self.core_memory = CoreMemory(
            max_tokens=self.policy.memory.core_max_tokens
        )
        
        self.semantic_memory = SemanticMemory(
            max_tokens=self.policy.memory.semantic_max_tokens,
            max_entries=self.policy.memory.semantic_max_entries,
            similarity_threshold=self.policy.memory.semantic_similarity_threshold,
        )
        
        self.episodic_memory = EpisodicMemory(
            max_tokens=self.policy.memory.episodic_max_tokens,
            max_entries=self.policy.memory.episodic_max_entries,
            retention_days=self.policy.memory.episodic_retention_days,
        )
        
        self.working_memory = WorkingMemory(
            max_tokens=self.policy.memory.working_max_tokens,
            max_turns=self.policy.memory.working_max_turns,
            compression_threshold=self.policy.memory.working_compression_threshold,
        )
        
        # Initialize token accounting
        model_config = self.config.get_section("model")
        self.token_accountant = TokenAccountant(
            model=model_config.get("name", "gpt-4"),
            max_tokens=model_config.get("max_tokens", 8192),
        )
        
        # Set token budget
        self.token_accountant.set_budget(self.policy.token.to_dict())
        
        # Initialize compression engine
        self.compression_engine = CompressionEngine(
            strategy=self.policy.summarization.strategy
        )
        
        # Initialize context assembly
        self.context_selector = ContextSelector(
            importance_weights=self.policy.assembly.get_importance_weights()
        )
        
        self.context_organizer = ContextOrganizer(
            section_order=self.policy.assembly.section_order,
            position_bias_mitigation=self.policy.assembly.position_bias_mitigation,
        )
        
        self.context_assembler = ContextAssembler(
            token_accountant=self.token_accountant,
            compression_engine=self.compression_engine,
            selector=self.context_selector,
            organizer=self.context_organizer,
        )
        
        # Initialize optimization
        self.optimizer = ContextOptimizer(
            strategies=self.policy.optimization.strategies
        )
        
        # State tracking
        self.session_id = datetime.now().isoformat()
        self.interaction_count = 0
    
    # === Core Memory API ===
    
    def set_core_memory(self, key: str, content: str, importance: float = 1.0,
                       tags: Optional[List[str]] = None) -> bool:
        """
        Set a core memory item (system instruction, rule, policy).
        
        Args:
            key: Unique identifier
            content: Memory content
            importance: Importance score (should be >= 0.9)
            tags: Optional tags
        """
        token_count = self.token_accountant.count(content)
        return self.core_memory.set_system_instruction(
            key, content, importance, tags or [], token_count
        )
    
    def get_core_memory(self, key: str) -> Optional[str]:
        """Get core memory by key."""
        return self.core_memory.get_system_instruction(key)
    
    # === Semantic Memory API ===
    
    def add_fact(self, content: str, entity: Optional[str] = None,
                relation: Optional[str] = None, importance: float = 0.7,
                tags: Optional[List[str]] = None) -> str:
        """
        Add a semantic fact to long-term memory.
        
        Args:
            content: Fact content
            entity: Related entity
            relation: Relation type
            importance: Importance score
            tags: Optional tags
        
        Returns:
            Fact ID
        """
        token_count = self.token_accountant.count(content)
        
        fact = SemanticFact(
            content=content,
            scope=MemoryScope.SESSION,
            importance=importance,
            tags=tags or [],
            token_count=token_count,
        )
        fact.entity = entity
        fact.relation = relation
        
        self.semantic_memory.add(fact)
        return fact.id
    
    def search_facts(self, query: str, top_k: int = 5) -> List[SemanticFact]:
        """Search semantic memory for relevant facts."""
        return self.semantic_memory.search(query, top_k)
    
    # === Episodic Memory API ===
    
    def add_episode(self, content: str, event_type: Optional[str] = None,
                   participants: Optional[List[str]] = None,
                   importance: float = 0.6,
                   tags: Optional[List[str]] = None) -> str:
        """
        Add an episodic event to long-term memory.
        
        Args:
            content: Episode description
            event_type: Type of event
            participants: List of participants
            importance: Importance score
            tags: Optional tags
        
        Returns:
            Episode ID
        """
        token_count = self.token_accountant.count(content)
        
        episode = Episode(
            content=content,
            scope=MemoryScope.SESSION,
            importance=importance,
            tags=tags or [],
            token_count=token_count,
        )
        episode.event_type = event_type
        episode.participants = participants or []
        
        self.episodic_memory.add(episode)
        return episode.id
    
    def get_recent_episodes(self, hours: int = 24, limit: int = 10) -> List[Episode]:
        """Get recent episodes."""
        return self.episodic_memory.get_recent(hours, limit)
    
    # === Working Memory API ===
    
    def record_interaction(self, user_input: str, assistant_response: str,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Record a user-assistant interaction.
        
        Args:
            user_input: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata
        
        Returns:
            Dictionary with user and assistant turn IDs
        """
        self.interaction_count += 1
        
        # Count tokens
        user_tokens = self.token_accountant.count(user_input)
        assistant_tokens = self.token_accountant.count(assistant_response)
        
        # Add user turn
        user_id = self.working_memory.add_user_turn(
            content=user_input,
            importance=0.6,
            tags=["interaction", f"turn_{self.interaction_count}"],
            token_count=user_tokens,
        )
        
        # Add assistant turn
        assistant_id = self.working_memory.add_assistant_turn(
            content=assistant_response,
            importance=0.6,
            tags=["interaction", f"turn_{self.interaction_count}"],
            token_count=assistant_tokens,
        )
        
        # Extract facts if enabled
        if metadata and metadata.get("extract_facts", False):
            facts = self.compression_engine.fact_extractor.extract_facts(
                user_input + " " + assistant_response
            )
            for fact in facts:
                if fact["confidence"] > 0.7:
                    self.add_fact(
                        content=fact["content"],
                        importance=0.7,
                        tags=["extracted", f"turn_{self.interaction_count}"]
                    )
        
        return {
            "user_turn_id": user_id,
            "assistant_turn_id": assistant_id,
        }
    
    def get_conversation_history(self, n: int = 10) -> List[ConversationTurn]:
        """Get recent conversation history."""
        return self.working_memory.get_recent(n)
    
    # === Context Assembly API ===
    
    def render_prompt(self, current_task: Optional[str] = None,
                     query: Optional[str] = None,
                     max_tokens: Optional[int] = None) -> str:
        """
        Render optimized prompt for LLM.
        
        Args:
            current_task: Description of current task
            query: Optional query for relevance ranking
            max_tokens: Override max tokens
        
        Returns:
            Assembled prompt string
        """
        
        # Update token budget if max_tokens provided
        if max_tokens:
            self.token_accountant.max_tokens = max_tokens
            self.token_accountant.set_budget(self.policy.token.to_dict())
        
        # Get items from each memory
        core_items = self.core_memory.get_all()
        semantic_items = self.semantic_memory.get_all()
        episodic_items = self.episodic_memory.get_all()
        working_items = self.working_memory.get_all()
        
        # Apply optimization
        if self.policy.optimization.enabled:
            context = {"query": query or current_task or ""}
            
            semantic_items = self.optimizer.optimize(semantic_items, 
                                                    {**context, "memory_type": "semantic"})
            episodic_items = self.optimizer.optimize(episodic_items,
                                                    {**context, "memory_type": "episodic"})
            working_items = self.optimizer.optimize(working_items,
                                                   {**context, "memory_type": "working"})
        
        # Assemble context
        assembly_result = self.context_assembler.assemble(
            core_items=core_items,
            semantic_items=semantic_items,
            episodic_items=episodic_items,
            working_items=working_items,
            current_task=current_task,
            query=query,
        )
        
        return assembly_result["prompt"]
    
    def preview_context(self, current_task: Optional[str] = None,
                       query: Optional[str] = None) -> Dict[str, Any]:
        """Preview what would be included in context without rendering."""
        return self.context_assembler.preview_assembly(
            core_items=self.core_memory.get_all(),
            semantic_items=self.semantic_memory.get_all(),
            episodic_items=self.episodic_memory.get_all(),
            working_items=self.working_memory.get_all(),
            current_task=current_task,
            query=query,
        )
    
    # === Inspection API ===
    
    def inspect_context(self) -> Dict[str, Any]:
        """Get detailed information about last context assembly."""
        return self.context_assembler.get_last_assembly()
    
    def inspect_memory(self) -> Dict[str, Any]:
        """Get statistics about all memory stores."""
        return {
            "core": {
                "count": self.core_memory.get_count(),
                "tokens": self.core_memory.get_total_tokens(),
            },
            "semantic": {
                "count": self.semantic_memory.get_count(),
                "tokens": self.semantic_memory.get_total_tokens(),
            },
            "episodic": {
                "count": self.episodic_memory.get_count(),
                "tokens": self.episodic_memory.get_total_tokens(),
            },
            "working": {
                "count": self.working_memory.get_count(),
                "tokens": self.working_memory.get_total_tokens(),
                **self.working_memory.get_turn_statistics(),
            },
            "total_tokens": (
                self.core_memory.get_total_tokens() +
                self.semantic_memory.get_total_tokens() +
                self.episodic_memory.get_total_tokens() +
                self.working_memory.get_total_tokens()
            ),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return {
            "session_id": self.session_id,
            "interactions": self.interaction_count,
            "memory": self.inspect_memory(),
            "model": self.token_accountant.get_model_info(),
        }
    
    # === Maintenance API ===
    
    def update_memory(self, memory_type: str, content: str, **kwargs) -> str:
        """Generic method to add to any memory type."""
        if memory_type == "semantic":
            return self.add_fact(content, **kwargs)
        elif memory_type == "episodic":
            return self.add_episode(content, **kwargs)
        elif memory_type == "core":
            key = kwargs.get("key", f"core_{datetime.now().timestamp()}")
            self.set_core_memory(key, content, **kwargs)
            return key
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def clear_working_memory(self):
        """Clear working memory (conversation history)."""
        self.working_memory.clear(preserve_permanent=True)
    
    def prune_memory(self, importance_threshold: float = 0.3):
        """Prune low-importance items from all memory stores."""
        self.semantic_memory.prune_by_importance(importance_threshold)
        self.episodic_memory.prune_by_importance(importance_threshold)
        self.working_memory.prune_by_importance(importance_threshold)
    
    # === Customization API ===
    
    def set_importance_scorer(self, scorer: Callable):
        """Set custom importance scoring function."""
        self.policy.importance.custom_scorer = scorer
    
    def add_optimization_strategy(self, name: str, optimizer):
        """Add custom optimization strategy."""
        self.optimizer.add_strategy(name, optimizer)
    
    def set_log_level(self, level: str):
        """Set logging level."""
        # Would integrate with logging system
        pass
