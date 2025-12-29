"""
Context Assembly Engine: Selects, orders, and structures context for LLM prompts.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from ..memory.base import MemoryBlock, MemoryType
from ..tokens.counter import TokenAccountant, TokenBudget
from ..summarization.engine import CompressionEngine


@dataclass
class AssemblySection:
    """Represents a section of assembled context."""
    
    name: str
    content: str
    token_count: int
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    items: List[MemoryBlock] = field(default_factory=list)


class ContextSelector:
    """
    Selects relevant memory items for inclusion in context.
    """
    
    def __init__(self, importance_weights: Optional[Dict[str, float]] = None):
        self.importance_weights = importance_weights or {
            "recency": 0.3,
            "relevance": 0.4,
            "importance": 0.3,
        }
    
    def select(self, items: List[MemoryBlock], query: Optional[str] = None,
              max_items: Optional[int] = None, min_importance: float = 0.0) -> List[MemoryBlock]:
        """Select items based on scoring criteria."""
        
        # Filter by minimum importance
        filtered = [item for item in items if item.importance >= min_importance]
        
        # Score items
        scored = []
        for item in filtered:
            score = self._calculate_score(item, query)
            scored.append((item, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Apply limit
        if max_items:
            scored = scored[:max_items]
        
        return [item for item, score in scored]
    
    def _calculate_score(self, item: MemoryBlock, query: Optional[str]) -> float:
        """Calculate composite score for item."""
        
        # Base importance
        importance_score = item.importance
        
        # Recency score
        recency_score = item.calculate_recency_score()
        
        # Relevance score (if query provided)
        relevance_score = 0.0
        if query:
            relevance_score = self._calculate_relevance(item, query)
        
        # Weighted combination
        weights = self.importance_weights
        score = (
            importance_score * weights.get("importance", 0.3) +
            recency_score * weights.get("recency", 0.3) +
            relevance_score * weights.get("relevance", 0.4)
        )
        
        return score
    
    def _calculate_relevance(self, item: MemoryBlock, query: str) -> float:
        """Calculate relevance of item to query."""
        query_lower = query.lower()
        content_lower = item.content.lower()
        
        # Simple keyword matching
        score = 0.0
        
        # Check for query words in content
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if query_words:
            overlap = len(query_words & content_words)
            score = overlap / len(query_words)
        
        # Check tags
        if any(query_lower in tag.lower() for tag in item.tags):
            score += 0.3
        
        return min(score, 1.0)
    
    def select_by_type(self, items: List[MemoryBlock], 
                      memory_type: MemoryType) -> List[MemoryBlock]:
        """Select items by memory type."""
        return [item for item in items if item.memory_type == memory_type]
    
    def deduplicate(self, items: List[MemoryBlock], 
                   similarity_threshold: float = 0.9) -> List[MemoryBlock]:
        """Remove duplicate or very similar items."""
        unique = []
        seen_content = set()
        
        for item in items:
            # Simple content-based deduplication
            content_hash = hash(item.content.lower().strip())
            
            if content_hash not in seen_content:
                unique.append(item)
                seen_content.add(content_hash)
        
        return unique


class ContextOrganizer:
    """
    Organizes selected items into structured sections.
    """
    
    def __init__(self, section_order: Optional[List[str]] = None,
                position_bias_mitigation: bool = True):
        self.section_order = section_order or [
            "system",
            "core_memory",
            "semantic_memory",
            "episodic_memory",
            "working_memory",
            "current_task",
        ]
        self.position_bias_mitigation = position_bias_mitigation
    
    def organize(self, items_by_type: Dict[str, List[MemoryBlock]],
                current_task: Optional[str] = None) -> List[AssemblySection]:
        """Organize items into sections."""
        
        sections = []
        
        for section_name in self.section_order:
            items = items_by_type.get(section_name, [])
            
            if section_name == "current_task" and current_task:
                # Special handling for current task
                section = AssemblySection(
                    name=section_name,
                    content=current_task,
                    token_count=len(current_task.split()),  # Approximate
                    priority=100,  # Highest priority
                )
                sections.append(section)
            elif items:
                # Regular memory section
                content = self._format_section(section_name, items)
                section = AssemblySection(
                    name=section_name,
                    content=content,
                    token_count=sum(item.token_count for item in items),
                    priority=self._get_section_priority(section_name),
                    items=items,
                )
                sections.append(section)
        
        # Apply position bias mitigation if enabled
        if self.position_bias_mitigation:
            sections = self._mitigate_position_bias(sections)
        
        return sections
    
    def _format_section(self, section_name: str, items: List[MemoryBlock]) -> str:
        """Format items as section content."""
        
        # Section header
        header = f"## {section_name.replace('_', ' ').title()}\n\n"
        
        # Format items
        item_texts = []
        for item in items:
            # Add item content
            text = item.content
            
            # Add metadata if important
            if item.tags:
                text += f"\n_Tags: {', '.join(item.tags)}_"
            
            item_texts.append(text)
        
        content = "\n\n".join(item_texts)
        
        return header + content
    
    def _get_section_priority(self, section_name: str) -> int:
        """Get priority for section."""
        priorities = {
            "system": 100,
            "core_memory": 90,
            "current_task": 100,
            "working_memory": 80,
            "semantic_memory": 70,
            "episodic_memory": 60,
        }
        return priorities.get(section_name, 50)
    
    def _mitigate_position_bias(self, sections: List[AssemblySection]) -> List[AssemblySection]:
        """
        Mitigate position bias by strategically ordering sections.
        
        Important information should appear at start and end,
        less important in the middle.
        """
        if len(sections) <= 2:
            return sections
        
        # Sort by priority
        sorted_sections = sorted(sections, key=lambda x: x.priority, reverse=True)
        
        # Interleave high-priority items at start and end
        result = []
        start_idx = 0
        end_idx = len(sorted_sections) - 1
        
        use_start = True
        while start_idx <= end_idx:
            if use_start:
                result.append(sorted_sections[start_idx])
                start_idx += 1
            else:
                result.insert(len(result) // 2, sorted_sections[end_idx])
                end_idx -= 1
            use_start = not use_start
        
        return result


class ContextAssembler:
    """
    Main context assembly engine.
    
    Orchestrates selection, organization, and rendering of context.
    """
    
    def __init__(self, token_accountant: TokenAccountant,
                compression_engine: Optional[CompressionEngine] = None,
                selector: Optional[ContextSelector] = None,
                organizer: Optional[ContextOrganizer] = None):
        
        self.token_accountant = token_accountant
        self.compression_engine = compression_engine or CompressionEngine()
        self.selector = selector or ContextSelector()
        self.organizer = organizer or ContextOrganizer()
        
        # Assembly state
        self.last_assembly: Optional[Dict[str, Any]] = None
    
    def assemble(self, 
                core_items: List[MemoryBlock],
                semantic_items: List[MemoryBlock],
                episodic_items: List[MemoryBlock],
                working_items: List[MemoryBlock],
                current_task: Optional[str] = None,
                query: Optional[str] = None,
                token_budget: Optional[TokenBudget] = None) -> Dict[str, Any]:
        """
        Assemble context from memory items.
        
        Returns:
            Dictionary with assembled context and metadata
        """
        
        if token_budget is None:
            token_budget = self.token_accountant.get_budget()
        
        if token_budget is None:
            raise ValueError("Token budget not set")
        
        # Reset budget
        token_budget.reset()
        
        # Phase 1: Select relevant items
        selected = self._select_items(
            core_items, semantic_items, episodic_items, working_items,
            query, token_budget
        )
        
        # Phase 2: Organize into sections
        sections = self.organizer.organize(selected, current_task)
        
        # Phase 3: Allocate tokens and compress if needed
        final_sections = self._allocate_and_compress(sections, token_budget)
        
        # Phase 4: Render final prompt
        prompt = self._render_prompt(final_sections)
        
        # Track assembly
        self.last_assembly = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "sections": [
                {
                    "name": s.name,
                    "token_count": s.token_count,
                    "item_count": len(s.items),
                }
                for s in final_sections
            ],
            "total_tokens": sum(s.token_count for s in final_sections),
            "budget_report": token_budget.get_usage_report(),
        }
        
        return self.last_assembly
    
    def _select_items(self, core_items, semantic_items, episodic_items, working_items,
                     query, token_budget) -> Dict[str, List[MemoryBlock]]:
        """Select items for each section."""
        
        selected = {}
        
        # Core memory: always include all (high importance)
        selected["core_memory"] = self.selector.deduplicate(core_items)
        
        # Semantic memory: select by relevance
        semantic_budget = token_budget.get_budget("semantic")
        selected["semantic_memory"] = self._select_within_budget(
            semantic_items, query, semantic_budget
        )
        
        # Episodic memory: select recent and relevant
        episodic_budget = token_budget.get_budget("episodic")
        selected["episodic_memory"] = self._select_within_budget(
            episodic_items, query, episodic_budget
        )
        
        # Working memory: include recent turns
        working_budget = token_budget.get_budget("working")
        selected["working_memory"] = self._select_within_budget(
            working_items, query, working_budget
        )
        
        return selected
    
    def _select_within_budget(self, items: List[MemoryBlock], 
                             query: Optional[str], budget: int) -> List[MemoryBlock]:
        """Select items that fit within token budget."""
        
        # Score and sort items
        selected = self.selector.select(items, query)
        
        # Take items until budget exhausted
        result = []
        used_tokens = 0
        
        for item in selected:
            if used_tokens + item.token_count <= budget:
                result.append(item)
                used_tokens += item.token_count
            else:
                break
        
        return result
    
    def _allocate_and_compress(self, sections: List[AssemblySection],
                               token_budget: TokenBudget) -> List[AssemblySection]:
        """Allocate tokens to sections and compress if needed."""
        
        final_sections = []
        
        for section in sections:
            section_budget = token_budget.get_budget(section.name)
            
            if section_budget == 0:
                # No budget allocated, skip or use reserve
                continue
            
            if section.token_count <= section_budget:
                # Fits within budget
                token_budget.allocate(section.name, section.token_count)
                final_sections.append(section)
            else:
                # Needs compression
                compressed = self._compress_section(section, section_budget)
                token_budget.allocate(section.name, compressed.token_count)
                final_sections.append(compressed)
        
        return final_sections
    
    def _compress_section(self, section: AssemblySection, 
                         target_tokens: int) -> AssemblySection:
        """Compress section to fit token budget."""
        
        # Estimate target characters (4 chars per token)
        target_chars = target_tokens * 4
        
        # Compress content
        compressed_content = self.compression_engine.adaptive_compress(
            section.content, target_tokens
        )
        
        # Count actual tokens
        actual_tokens = self.token_accountant.count(compressed_content)
        
        return AssemblySection(
            name=section.name,
            content=compressed_content,
            token_count=actual_tokens,
            priority=section.priority,
            metadata={**section.metadata, "compressed": True},
            items=section.items,  # Keep reference to original items
        )
    
    def _render_prompt(self, sections: List[AssemblySection]) -> str:
        """Render final prompt from sections."""
        
        parts = []
        
        for section in sections:
            parts.append(section.content)
        
        return "\n\n".join(parts)
    
    def get_last_assembly(self) -> Optional[Dict[str, Any]]:
        """Get information about last assembly."""
        return self.last_assembly
    
    def preview_assembly(self, *args, **kwargs) -> Dict[str, Any]:
        """Preview what would be assembled without actually doing it."""
        
        # Save current state
        saved_assembly = self.last_assembly
        
        # Do assembly
        result = self.assemble(*args, **kwargs)
        
        # Restore state
        self.last_assembly = saved_assembly
        
        return result
