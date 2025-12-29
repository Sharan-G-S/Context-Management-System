"""
Working Memory: Recent conversation turns and temporary task state.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque

from .base import BaseMemoryStore, MemoryBlock, MemoryType, MemoryScope


class ConversationTurn(MemoryBlock):
    """Extended memory block for conversation turns."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_type = MemoryType.WORKING
        
        # Turn-specific fields
        self.role: str = kwargs.get('role', 'user')  # user, assistant, system
        self.turn_number: int = kwargs.get('turn_number', 0)
        
        # Context tracking
        self.task: Optional[str] = None
        self.subtasks: List[str] = []
        self.completed: bool = False
        
        # References
        self.references: List[str] = []  # IDs of referenced memory blocks
        self.summary: Optional[str] = None


class WorkingMemory(BaseMemoryStore):
    """
    Working memory stores recent conversation turns and temporary task state.
    
    Characteristics:
    - Short-term (recent turns only)
    - Auto-pruning based on age and size
    - FIFO with importance exceptions
    - Temporary scope (cleared between sessions)
    - Variable importance (0.3-0.7)
    
    Features:
    - Conversation history management
    - Turn summarization
    - Task state tracking
    - Automatic compression when full
    """
    
    def __init__(self, max_tokens: int = 3000, max_turns: int = 10,
                 compression_threshold: float = 0.8):
        super().__init__(max_tokens=max_tokens)
        self.max_turns = max_turns
        self.compression_threshold = compression_threshold
        
        # Ordered queue of turn IDs (FIFO)
        self._turn_queue: deque = deque(maxlen=max_turns)
        
        # Current turn number
        self._turn_counter: int = 0
        
        # Task state
        self._current_task: Optional[str] = None
        self._task_context: Dict[str, Any] = {}
    
    def add(self, item: MemoryBlock) -> bool:
        """Add turn to working memory."""
        if not isinstance(item, ConversationTurn):
            # Convert to ConversationTurn
            turn = ConversationTurn(
                id=item.id,
                content=item.content,
                scope=MemoryScope.TEMPORARY,
                importance=item.importance,
                tags=item.tags,
                metadata=item.metadata,
                token_count=item.token_count,
                turn_number=self._turn_counter,
            )
        else:
            turn = item
            if turn.turn_number == 0:
                turn.turn_number = self._turn_counter
        
        self._turn_counter += 1
        
        # Check if compression needed
        token_usage = self.get_total_tokens() + turn.token_count
        if token_usage > self.max_tokens * self.compression_threshold:
            self._compress_oldest_turns()
        
        # Add turn
        self._items[turn.id] = turn
        self._turn_queue.append(turn.id)
        
        # If queue full, remove oldest (unless important)
        if len(self._turn_queue) > self.max_turns:
            oldest_id = self._turn_queue[0]
            oldest = self._items.get(oldest_id)
            
            if oldest and oldest.importance < 0.7:
                self.delete(oldest_id)
        
        return True
    
    def get(self, item_id: str) -> Optional[ConversationTurn]:
        """Retrieve turn by ID."""
        item = self._items.get(item_id)
        if item:
            item.update_access()
        return item
    
    def update(self, item: MemoryBlock) -> bool:
        """Update existing turn."""
        if item.id not in self._items:
            return False
        
        self._items[item.id] = item
        return True
    
    def delete(self, item_id: str) -> bool:
        """Delete turn by ID."""
        if item_id not in self._items:
            return False
        
        del self._items[item_id]
        
        # Remove from queue
        if item_id in self._turn_queue:
            self._turn_queue.remove(item_id)
        
        return True
    
    def search(self, query: str, top_k: int = 5) -> List[ConversationTurn]:
        """Search for relevant turns."""
        query_lower = query.lower()
        matches = []
        
        for item in self._items.values():
            if query_lower in item.content.lower():
                matches.append(item)
        
        # Sort by recency and relevance
        matches.sort(key=lambda x: x.calculate_composite_score(), reverse=True)
        return matches[:top_k]
    
    def get_all(self) -> List[ConversationTurn]:
        """Get all turns in chronological order."""
        items = [self._items[tid] for tid in self._turn_queue if tid in self._items]
        return items
    
    def get_recent(self, n: int = 5) -> List[ConversationTurn]:
        """Get N most recent turns."""
        recent_ids = list(self._turn_queue)[-n:]
        return [self._items[tid] for tid in recent_ids if tid in self._items]
    
    def get_conversation_history(self, format: str = "list") -> Any:
        """Get conversation history in various formats."""
        turns = self.get_all()
        
        if format == "list":
            return turns
        elif format == "text":
            return self._format_as_text(turns)
        elif format == "messages":
            return self._format_as_messages(turns)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _format_as_text(self, turns: List[ConversationTurn]) -> str:
        """Format turns as plain text."""
        lines = []
        for turn in turns:
            if isinstance(turn, ConversationTurn):
                prefix = f"{turn.role.upper()}: "
            else:
                prefix = "USER: "
            lines.append(f"{prefix}{turn.content}")
        return "\n\n".join(lines)
    
    def _format_as_messages(self, turns: List[ConversationTurn]) -> List[Dict[str, str]]:
        """Format turns as message dictionaries (for LLM APIs)."""
        messages = []
        for turn in turns:
            if isinstance(turn, ConversationTurn):
                messages.append({
                    "role": turn.role,
                    "content": turn.content,
                })
            else:
                messages.append({
                    "role": "user",
                    "content": turn.content,
                })
        return messages
    
    def add_user_turn(self, content: str, importance: float = 0.5,
                      tags: Optional[List[str]] = None, token_count: int = 0) -> str:
        """Convenience method to add user turn."""
        turn = ConversationTurn(
            content=content,
            scope=MemoryScope.TEMPORARY,
            importance=importance,
            tags=tags or [],
            token_count=token_count,
            role="user",
            turn_number=self._turn_counter,
        )
        self.add(turn)
        return turn.id
    
    def add_assistant_turn(self, content: str, importance: float = 0.5,
                          tags: Optional[List[str]] = None, token_count: int = 0) -> str:
        """Convenience method to add assistant turn."""
        turn = ConversationTurn(
            content=content,
            scope=MemoryScope.TEMPORARY,
            importance=importance,
            tags=tags or [],
            token_count=token_count,
            role="assistant",
            turn_number=self._turn_counter,
        )
        self.add(turn)
        return turn.id
    
    def set_current_task(self, task: str, context: Optional[Dict[str, Any]] = None):
        """Set the current task context."""
        self._current_task = task
        self._task_context = context or {}
    
    def get_current_task(self) -> Optional[str]:
        """Get the current task."""
        return self._current_task
    
    def get_task_context(self) -> Dict[str, Any]:
        """Get the current task context."""
        return self._task_context
    
    def clear_task(self):
        """Clear the current task."""
        self._current_task = None
        self._task_context = {}
    
    def _compress_oldest_turns(self):
        """Compress or summarize oldest turns to save space."""
        if len(self._turn_queue) < 3:
            return
        
        # Get oldest 3 turns (if available)
        to_compress_ids = list(self._turn_queue)[:3]
        to_compress = [self._items[tid] for tid in to_compress_ids if tid in self._items]
        
        if not to_compress:
            return
        
        # Create summary
        summary_content = self._create_summary(to_compress)
        summary_tokens = sum(t.token_count for t in to_compress)
        
        # Create compressed turn
        compressed = ConversationTurn(
            content=summary_content,
            scope=MemoryScope.TEMPORARY,
            importance=max(t.importance for t in to_compress),
            tags=["summary"],
            token_count=summary_tokens // 3,  # Assume 3x compression
            role="system",
            turn_number=to_compress[0].turn_number if isinstance(to_compress[0], ConversationTurn) else 0,
        )
        compressed.summary = summary_content
        
        # Replace old turns with compressed version
        for turn_id in to_compress_ids:
            self.delete(turn_id)
        
        self._items[compressed.id] = compressed
        self._turn_queue.appendleft(compressed.id)
    
    def _create_summary(self, turns: List[ConversationTurn]) -> str:
        """Create summary of multiple turns."""
        # Simple extractive summary (in production, use LLM)
        contents = []
        for turn in turns:
            if isinstance(turn, ConversationTurn):
                prefix = f"[{turn.role}]"
            else:
                prefix = "[user]"
            
            # Take first sentence or 100 chars
            content = turn.content.split('.')[0][:100]
            contents.append(f"{prefix} {content}")
        
        return " | ".join(contents)
    
    def summarize_all(self) -> str:
        """Create summary of all turns."""
        turns = self.get_all()
        return self._create_summary(turns)
    
    def get_turn_statistics(self) -> Dict[str, Any]:
        """Get statistics about working memory."""
        turns = list(self._items.values())
        
        user_turns = [t for t in turns if isinstance(t, ConversationTurn) and t.role == "user"]
        assistant_turns = [t for t in turns if isinstance(t, ConversationTurn) and t.role == "assistant"]
        
        return {
            "total_turns": len(turns),
            "user_turns": len(user_turns),
            "assistant_turns": len(assistant_turns),
            "total_tokens": self.get_total_tokens(),
            "avg_tokens_per_turn": self.get_total_tokens() / len(turns) if turns else 0,
            "compression_ratio": len(self._turn_queue) / self._turn_counter if self._turn_counter > 0 else 1.0,
            "current_task": self._current_task,
        }
