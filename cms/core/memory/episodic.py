"""
Episodic Memory: Experience-based event storage with temporal indexing.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .base import BaseMemoryStore, MemoryBlock, MemoryType, MemoryScope


class Episode(MemoryBlock):
    """Extended memory block for episodic events."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_type = MemoryType.EPISODIC
        
        # Episode-specific fields
        self.event_type: Optional[str] = None
        self.participants: List[str] = []
        self.location: Optional[str] = None
        self.outcome: Optional[str] = None
        
        # Temporal context
        self.start_time: datetime = kwargs.get('start_time', datetime.now())
        self.end_time: Optional[datetime] = kwargs.get('end_time')
        self.duration: Optional[int] = None  # seconds
        
        # Causal relationships
        self.caused_by: List[str] = []  # IDs of preceding episodes
        self.led_to: List[str] = []     # IDs of subsequent episodes
        
        # Emotional/contextual metadata
        self.sentiment: Optional[float] = None  # -1.0 to 1.0
        self.success: Optional[bool] = None


class EpisodicMemory(BaseMemoryStore):
    """
    Episodic memory stores specific events and experiences with temporal context.
    
    Characteristics:
    - Event-based (specific interactions, experiences)
    - Temporal indexing and ordering
    - Causal relationships between events
    - Context of when/why things happened
    - Medium importance (0.4-0.8)
    
    Features:
    - Temporal search and retrieval
    - Event chains and sequences
    - Context reconstruction
    - Pattern detection across episodes
    """
    
    def __init__(self, max_tokens: int = 1500, max_entries: int = 500,
                 retention_days: int = 30):
        super().__init__(max_tokens=max_tokens, max_entries=max_entries)
        self.retention_days = retention_days
        
        # Temporal indices
        self._time_index: Dict[str, List[str]] = defaultdict(list)  # date -> episode IDs
        self._event_type_index: Dict[str, List[str]] = defaultdict(list)  # type -> episode IDs
        self._participant_index: Dict[str, List[str]] = defaultdict(list)  # participant -> episode IDs
    
    def add(self, item: MemoryBlock) -> bool:
        """Add episode to episodic memory."""
        if not isinstance(item, Episode):
            # Convert to Episode
            episode = Episode(
                id=item.id,
                content=item.content,
                scope=item.scope,
                importance=item.importance,
                tags=item.tags,
                metadata=item.metadata,
                token_count=item.token_count,
            )
        else:
            episode = item
        
        # Check token budget
        if self.get_total_tokens() + episode.token_count > self.max_tokens:
            self._prune_old_episodes()
        
        # Check entry limit
        if self.max_entries and len(self._items) >= self.max_entries:
            self._prune_old_episodes()
        
        # Add to store
        self._items[episode.id] = episode
        
        # Update temporal index
        date_key = episode.timestamp.strftime("%Y-%m-%d")
        self._time_index[date_key].append(episode.id)
        
        # Update event type index
        if episode.event_type:
            self._event_type_index[episode.event_type].append(episode.id)
        
        # Update participant index
        for participant in episode.participants:
            self._participant_index[participant].append(episode.id)
        
        return True
    
    def get(self, item_id: str) -> Optional[Episode]:
        """Retrieve episode by ID."""
        item = self._items.get(item_id)
        if item:
            item.update_access()
        return item
    
    def update(self, item: MemoryBlock) -> bool:
        """Update existing episode."""
        if item.id not in self._items:
            return False
        
        self._items[item.id] = item
        
        # Re-index if needed
        if isinstance(item, Episode):
            date_key = item.timestamp.strftime("%Y-%m-%d")
            if item.id not in self._time_index[date_key]:
                self._time_index[date_key].append(item.id)
        
        return True
    
    def delete(self, item_id: str) -> bool:
        """Delete episode by ID."""
        if item_id not in self._items:
            return False
        
        item = self._items[item_id]
        
        # Remove from indices
        if isinstance(item, Episode):
            date_key = item.timestamp.strftime("%Y-%m-%d")
            if item.id in self._time_index[date_key]:
                self._time_index[date_key].remove(item.id)
            
            if item.event_type and item.id in self._event_type_index[item.event_type]:
                self._event_type_index[item.event_type].remove(item.id)
            
            for participant in item.participants:
                if item.id in self._participant_index[participant]:
                    self._participant_index[participant].remove(item.id)
        
        del self._items[item_id]
        return True
    
    def search(self, query: str, top_k: int = 5) -> List[Episode]:
        """Search for relevant episodes."""
        query_lower = query.lower()
        matches = []
        
        for item in self._items.values():
            score = 0.0
            
            # Check event type
            if isinstance(item, Episode) and item.event_type:
                if query_lower in item.event_type.lower():
                    score += 0.3
            
            # Check participants
            if isinstance(item, Episode):
                if any(query_lower in p.lower() for p in item.participants):
                    score += 0.2
            
            # Check tags
            if any(query_lower in tag.lower() for tag in item.tags):
                score += 0.2
            
            # Check content
            if query_lower in item.content.lower():
                score += 0.3
            
            if score > 0:
                matches.append((item, score))
        
        # Sort by score and recency
        matches.sort(key=lambda x: x[1] * x[0].calculate_composite_score(), reverse=True)
        return [item for item, _ in matches[:top_k]]
    
    def get_all(self) -> List[Episode]:
        """Get all episodes sorted by timestamp (most recent first)."""
        items = list(self._items.values())
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items
    
    def get_by_time_range(self, start: datetime, end: datetime) -> List[Episode]:
        """Get episodes within a time range."""
        episodes = []
        current = start
        
        while current <= end:
            date_key = current.strftime("%Y-%m-%d")
            episode_ids = self._time_index.get(date_key, [])
            
            for ep_id in episode_ids:
                if ep_id in self._items:
                    episode = self._items[ep_id]
                    if start <= episode.timestamp <= end:
                        episodes.append(episode)
            
            current += timedelta(days=1)
        
        episodes.sort(key=lambda x: x.timestamp)
        return episodes
    
    def get_recent(self, hours: int = 24, limit: int = 10) -> List[Episode]:
        """Get recent episodes within the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            ep for ep in self._items.values()
            if ep.timestamp >= cutoff
        ]
        recent.sort(key=lambda x: x.timestamp, reverse=True)
        return recent[:limit]
    
    def get_by_event_type(self, event_type: str) -> List[Episode]:
        """Get all episodes of a specific event type."""
        episode_ids = self._event_type_index.get(event_type, [])
        episodes = [self._items[ep_id] for ep_id in episode_ids if ep_id in self._items]
        episodes.sort(key=lambda x: x.timestamp, reverse=True)
        return episodes
    
    def get_by_participant(self, participant: str) -> List[Episode]:
        """Get all episodes involving a participant."""
        episode_ids = self._participant_index.get(participant, [])
        episodes = [self._items[ep_id] for ep_id in episode_ids if ep_id in self._items]
        episodes.sort(key=lambda x: x.timestamp, reverse=True)
        return episodes
    
    def link_episodes(self, cause_id: str, effect_id: str):
        """Create a causal link between two episodes."""
        if cause_id in self._items and effect_id in self._items:
            cause = self._items[cause_id]
            effect = self._items[effect_id]
            
            if isinstance(cause, Episode) and isinstance(effect, Episode):
                if effect_id not in cause.led_to:
                    cause.led_to.append(effect_id)
                if cause_id not in effect.caused_by:
                    effect.caused_by.append(cause_id)
    
    def get_episode_chain(self, episode_id: str, direction: str = "forward") -> List[Episode]:
        """Get chain of causally related episodes."""
        if episode_id not in self._items:
            return []
        
        episode = self._items[episode_id]
        if not isinstance(episode, Episode):
            return [episode]
        
        chain = [episode]
        
        if direction == "forward":
            # Follow led_to links
            for next_id in episode.led_to:
                if next_id in self._items:
                    chain.extend(self.get_episode_chain(next_id, "forward"))
        elif direction == "backward":
            # Follow caused_by links
            for prev_id in episode.caused_by:
                if prev_id in self._items:
                    chain.extend(self.get_episode_chain(prev_id, "backward"))
        else:
            # Get both directions
            chain.extend(self.get_episode_chain(episode_id, "forward")[1:])
            chain.extend(self.get_episode_chain(episode_id, "backward")[1:])
        
        return chain
    
    def _prune_old_episodes(self):
        """Remove episodes older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        to_remove = []
        for ep_id, episode in self._items.items():
            if episode.timestamp < cutoff and episode.scope != MemoryScope.PERMANENT:
                to_remove.append(ep_id)
        
        for ep_id in to_remove:
            self.delete(ep_id)
        
        # If still over budget, remove least important
        if len(to_remove) == 0 and len(self._items) > 0:
            items = sorted(self._items.values(), key=lambda x: x.calculate_composite_score())
            to_remove_count = max(1, len(items) // 10)
            for item in items[:to_remove_count]:
                if item.scope != MemoryScope.PERMANENT:
                    self.delete(item.id)
    
    def get_timeline(self, start: Optional[datetime] = None,
                     end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get timeline view of episodes."""
        if start is None:
            start = datetime.now() - timedelta(days=self.retention_days)
        if end is None:
            end = datetime.now()
        
        episodes = self.get_by_time_range(start, end)
        
        timeline = []
        for ep in episodes:
            if isinstance(ep, Episode):
                timeline.append({
                    "id": ep.id,
                    "timestamp": ep.timestamp.isoformat(),
                    "event_type": ep.event_type,
                    "content": ep.content[:100] + "..." if len(ep.content) > 100 else ep.content,
                    "participants": ep.participants,
                    "importance": ep.importance,
                    "sentiment": ep.sentiment,
                })
        
        return timeline
    
    def detect_patterns(self, min_frequency: int = 3) -> List[Dict[str, Any]]:
        """Detect recurring patterns in episodes."""
        patterns = defaultdict(list)
        
        # Group by event type
        for event_type, episode_ids in self._event_type_index.items():
            if len(episode_ids) >= min_frequency:
                episodes = [self._items[ep_id] for ep_id in episode_ids if ep_id in self._items]
                patterns[event_type] = {
                    "frequency": len(episodes),
                    "avg_importance": sum(ep.importance for ep in episodes) / len(episodes),
                    "recent_count": len([ep for ep in episodes if ep.timestamp > datetime.now() - timedelta(days=7)]),
                }
        
        return [{"pattern": k, **v} for k, v in patterns.items()]
