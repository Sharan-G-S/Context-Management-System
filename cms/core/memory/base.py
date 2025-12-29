"""
Base memory module defining common interfaces and data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class MemoryType(Enum):
    """Types of memory in the system."""
    CORE = "core"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    WORKING = "working"


class MemoryScope(Enum):
    """Scope of memory persistence."""
    PERMANENT = "permanent"  # Never deleted
    SESSION = "session"      # Deleted when session ends
    TEMPORARY = "temporary"  # Deleted after use or timeout


@dataclass
class MemoryBlock:
    """Base class for all memory blocks."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.WORKING
    scope: MemoryScope = MemoryScope.TEMPORARY
    
    # Metadata
    importance: float = 0.5  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    # Tagging and organization
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Versioning
    version: int = 1
    parent_id: Optional[str] = None
    
    # Token tracking
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory block to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "scope": self.scope.value,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": self.tags,
            "metadata": self.metadata,
            "version": self.version,
            "parent_id": self.parent_id,
            "token_count": self.token_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryBlock":
        """Create memory block from dictionary."""
        data["memory_type"] = MemoryType(data["memory_type"])
        data["scope"] = MemoryScope(data["scope"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        return cls(**data)
    
    def update_access(self):
        """Update access timestamp and count."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def calculate_recency_score(self) -> float:
        """Calculate recency score based on last access time."""
        age_hours = (datetime.now() - self.last_accessed).total_seconds() / 3600
        # Exponential decay: score decreases by half every 24 hours
        return 2 ** (-age_hours / 24)
    
    def calculate_composite_score(self, recency_weight: float = 0.3) -> float:
        """Calculate composite score combining importance and recency."""
        recency_score = self.calculate_recency_score()
        return (self.importance * (1 - recency_weight)) + (recency_score * recency_weight)


class BaseMemoryStore(ABC):
    """Abstract base class for memory stores."""
    
    def __init__(self, max_tokens: int = 1000, max_entries: Optional[int] = None):
        self.max_tokens = max_tokens
        self.max_entries = max_entries
        self._items: Dict[str, MemoryBlock] = {}
    
    @abstractmethod
    def add(self, item: MemoryBlock) -> bool:
        """Add item to memory store."""
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[MemoryBlock]:
        """Retrieve item by ID."""
        pass
    
    @abstractmethod
    def update(self, item: MemoryBlock) -> bool:
        """Update existing item."""
        pass
    
    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete item by ID."""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[MemoryBlock]:
        """Search for relevant items."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[MemoryBlock]:
        """Get all items in store."""
        pass
    
    def get_total_tokens(self) -> int:
        """Get total token count across all items."""
        return sum(item.token_count for item in self._items.values())
    
    def get_count(self) -> int:
        """Get number of items in store."""
        return len(self._items)
    
    def prune_by_importance(self, threshold: float) -> int:
        """Remove items below importance threshold."""
        to_delete = [
            item_id for item_id, item in self._items.items()
            if item.importance < threshold and item.scope != MemoryScope.PERMANENT
        ]
        for item_id in to_delete:
            self.delete(item_id)
        return len(to_delete)
    
    def prune_by_age(self, max_age_hours: int) -> int:
        """Remove items older than specified hours."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        to_delete = [
            item_id for item_id, item in self._items.items()
            if item.last_accessed.timestamp() < cutoff 
            and item.scope != MemoryScope.PERMANENT
        ]
        for item_id in to_delete:
            self.delete(item_id)
        return len(to_delete)
    
    def clear(self, preserve_permanent: bool = True):
        """Clear all items from store."""
        if preserve_permanent:
            to_delete = [
                item_id for item_id, item in self._items.items()
                if item.scope != MemoryScope.PERMANENT
            ]
            for item_id in to_delete:
                del self._items[item_id]
        else:
            self._items.clear()
