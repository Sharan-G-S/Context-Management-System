"""
Core Memory: Immutable system instructions and critical rules.
"""

from typing import List, Optional
from .base import BaseMemoryStore, MemoryBlock, MemoryType, MemoryScope


class CoreMemory(BaseMemoryStore):
    """
    Core memory stores immutable system instructions, critical rules, and policies.
    
    Characteristics:
    - High importance (>= 0.9)
    - Permanent scope
    - Immutable once set (can version instead of modify)
    - Always included in context
    - Small token footprint
    """
    
    def __init__(self, max_tokens: int = 1000):
        super().__init__(max_tokens=max_tokens)
        self.immutable = True
    
    def add(self, item: MemoryBlock) -> bool:
        """Add item to core memory."""
        # Validate core memory constraints
        if item.importance < 0.9:
            raise ValueError("Core memory items must have importance >= 0.9")
        
        # Set to permanent scope
        item.memory_type = MemoryType.CORE
        item.scope = MemoryScope.PERMANENT
        
        # Check token budget
        if self.get_total_tokens() + item.token_count > self.max_tokens:
            raise ValueError(f"Adding item would exceed core memory token budget ({self.max_tokens})")
        
        # Check for duplicate keys
        if item.id in self._items:
            if self.immutable:
                raise ValueError(f"Core memory is immutable. Use version() to create new version.")
            return False
        
        self._items[item.id] = item
        return True
    
    def get(self, item_id: str) -> Optional[MemoryBlock]:
        """Retrieve item by ID."""
        item = self._items.get(item_id)
        if item:
            item.update_access()
        return item
    
    def update(self, item: MemoryBlock) -> bool:
        """Update existing item (creates new version if immutable)."""
        if item.id not in self._items:
            return False
        
        if self.immutable:
            # Create new version instead of modifying
            new_item = MemoryBlock(
                content=item.content,
                memory_type=MemoryType.CORE,
                scope=MemoryScope.PERMANENT,
                importance=item.importance,
                tags=item.tags.copy(),
                metadata=item.metadata.copy(),
                version=self._items[item.id].version + 1,
                parent_id=item.id,
                token_count=item.token_count,
            )
            self._items[new_item.id] = new_item
            return True
        else:
            self._items[item.id] = item
            return True
    
    def delete(self, item_id: str) -> bool:
        """Delete item by ID (not allowed for immutable core memory)."""
        if self.immutable:
            raise ValueError("Cannot delete from immutable core memory")
        
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
    
    def search(self, query: str, top_k: int = 5) -> List[MemoryBlock]:
        """Search for relevant items (simple tag-based search for core memory)."""
        query_lower = query.lower()
        matches = []
        
        for item in self._items.values():
            # Check tags
            if any(query_lower in tag.lower() for tag in item.tags):
                matches.append(item)
                continue
            
            # Check content
            if query_lower in item.content.lower():
                matches.append(item)
        
        # Sort by importance
        matches.sort(key=lambda x: x.importance, reverse=True)
        return matches[:top_k]
    
    def get_all(self) -> List[MemoryBlock]:
        """Get all items sorted by importance."""
        items = list(self._items.values())
        items.sort(key=lambda x: x.importance, reverse=True)
        return items
    
    def set_system_instruction(self, key: str, instruction: str, importance: float = 1.0,
                               tags: Optional[List[str]] = None, token_count: int = 0):
        """Convenience method to set a system instruction."""
        item = MemoryBlock(
            id=key,
            content=instruction,
            memory_type=MemoryType.CORE,
            scope=MemoryScope.PERMANENT,
            importance=importance,
            tags=tags or [],
            token_count=token_count,
        )
        return self.add(item)
    
    def get_system_instruction(self, key: str) -> Optional[str]:
        """Get system instruction by key."""
        item = self.get(key)
        return item.content if item else None
    
    def export_instructions(self) -> str:
        """Export all instructions as formatted text."""
        items = self.get_all()
        sections = []
        
        for item in items:
            section = f"## {item.id}\n{item.content}"
            if item.tags:
                section += f"\n_Tags: {', '.join(item.tags)}_"
            sections.append(section)
        
        return "\n\n".join(sections)
