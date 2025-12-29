"""
Basic tests for Context Management System.
"""

import pytest
from cms import ContextManager, Config
from cms.core.memory import MemoryBlock, MemoryType, MemoryScope


class TestCoreMemory:
    """Test core memory functionality."""
    
    def test_set_and_get_core_memory(self):
        cm = ContextManager()
        
        # Set core memory
        success = cm.set_core_memory(
            "test_key",
            "Test system instruction",
            importance=0.95
        )
        assert success is True
        
        # Get core memory
        content = cm.get_core_memory("test_key")
        assert content == "Test system instruction"
    
    def test_core_memory_importance_validation(self):
        cm = ContextManager()
        
        # Should fail with low importance
        with pytest.raises(ValueError):
            cm.set_core_memory(
                "low_importance",
                "This should fail",
                importance=0.5  # Too low for core memory
            )


class TestSemanticMemory:
    """Test semantic memory functionality."""
    
    def test_add_fact(self):
        cm = ContextManager()
        
        # Add a fact
        fact_id = cm.add_fact(
            "Python is a programming language",
            entity="Python",
            relation="definition",
            importance=0.8,
            tags=["python", "language"]
        )
        
        assert fact_id is not None
        assert len(fact_id) > 0
    
    def test_search_facts(self):
        cm = ContextManager()
        
        # Add multiple facts
        cm.add_fact("Python supports multiple programming paradigms", entity="Python")
        cm.add_fact("Python has dynamic typing", entity="Python")
        cm.add_fact("JavaScript is used for web development", entity="JavaScript")
        
        # Search for Python-related facts
        results = cm.search_facts("Python programming", top_k=5)
        
        assert len(results) >= 2
        # Should find Python facts first
        assert "Python" in results[0].content


class TestEpisodicMemory:
    """Test episodic memory functionality."""
    
    def test_add_episode(self):
        cm = ContextManager()
        
        # Add an episode
        episode_id = cm.add_episode(
            "User asked about Python basics",
            event_type="question",
            participants=["user", "assistant"],
            importance=0.7
        )
        
        assert episode_id is not None
        assert len(episode_id) > 0
    
    def test_get_recent_episodes(self):
        cm = ContextManager()
        
        # Add multiple episodes
        for i in range(5):
            cm.add_episode(
                f"Episode {i}",
                event_type="interaction",
                importance=0.6
            )
        
        # Get recent episodes
        recent = cm.get_recent_episodes(hours=24, limit=10)
        
        assert len(recent) == 5


class TestWorkingMemory:
    """Test working memory functionality."""
    
    def test_record_interaction(self):
        cm = ContextManager()
        
        # Record an interaction
        turn_ids = cm.record_interaction(
            user_input="How do I use Python?",
            assistant_response="Python is easy to learn. Start with the basics."
        )
        
        assert "user_turn_id" in turn_ids
        assert "assistant_turn_id" in turn_ids
    
    def test_get_conversation_history(self):
        cm = ContextManager()
        
        # Record multiple interactions
        for i in range(3):
            cm.record_interaction(
                user_input=f"Question {i}",
                assistant_response=f"Answer {i}"
            )
        
        # Get history
        history = cm.get_conversation_history(n=10)
        
        # Should have 6 turns (3 user + 3 assistant)
        assert len(history) == 6


class TestContextAssembly:
    """Test context assembly functionality."""
    
    def test_render_prompt(self):
        cm = ContextManager()
        
        # Set up some memory
        cm.set_core_memory("role", "You are a helpful assistant", importance=1.0)
        cm.add_fact("Python is easy to learn", importance=0.7)
        cm.record_interaction("Hello", "Hi there!")
        
        # Render prompt
        prompt = cm.render_prompt(current_task="Help the user")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include core memory
        assert "helpful assistant" in prompt.lower()
    
    def test_preview_context(self):
        cm = ContextManager()
        
        # Set up memory
        cm.set_core_memory("test", "Test content", importance=1.0)
        
        # Preview context
        preview = cm.preview_context(current_task="Test task")
        
        assert "sections" in preview
        assert "total_tokens" in preview
        assert preview["total_tokens"] > 0


class TestMemoryInspection:
    """Test memory inspection functionality."""
    
    def test_inspect_memory(self):
        cm = ContextManager()
        
        # Add some content
        cm.set_core_memory("test", "Test", importance=1.0)
        cm.add_fact("Fact 1")
        cm.add_episode("Episode 1")
        
        # Inspect memory
        stats = cm.inspect_memory()
        
        assert "core" in stats
        assert "semantic" in stats
        assert "episodic" in stats
        assert "working" in stats
        assert stats["core"]["count"] >= 1
        assert stats["semantic"]["count"] >= 1
        assert stats["episodic"]["count"] >= 1
    
    def test_get_metrics(self):
        cm = ContextManager()
        
        # Record some interactions
        cm.record_interaction("Test", "Response")
        
        # Get metrics
        metrics = cm.get_metrics()
        
        assert "session_id" in metrics
        assert "interactions" in metrics
        assert "memory" in metrics
        assert "model" in metrics
        assert metrics["interactions"] >= 1


class TestMemoryMaintenance:
    """Test memory maintenance functionality."""
    
    def test_clear_working_memory(self):
        cm = ContextManager()
        
        # Add working memory
        cm.record_interaction("Test", "Response")
        
        # Should have items
        stats_before = cm.inspect_memory()
        assert stats_before["working"]["count"] > 0
        
        # Clear
        cm.clear_working_memory()
        
        # Should be empty
        stats_after = cm.inspect_memory()
        assert stats_after["working"]["count"] == 0
    
    def test_prune_memory(self):
        cm = ContextManager()
        
        # Add items with varying importance
        cm.add_fact("Important fact", importance=0.9)
        cm.add_fact("Less important", importance=0.3)
        cm.add_episode("Important episode", importance=0.8)
        cm.add_episode("Less important", importance=0.2)
        
        # Count before pruning
        stats_before = cm.inspect_memory()
        total_before = stats_before["semantic"]["count"] + stats_before["episodic"]["count"]
        
        # Prune items below 0.5
        cm.prune_memory(importance_threshold=0.5)
        
        # Count after pruning
        stats_after = cm.inspect_memory()
        total_after = stats_after["semantic"]["count"] + stats_after["episodic"]["count"]
        
        # Should have fewer items
        assert total_after < total_before


class TestTokenAccounting:
    """Test token accounting functionality."""
    
    def test_token_counting(self):
        cm = ContextManager()
        
        # Count tokens in text
        text = "This is a test sentence with several words."
        count = cm.token_accountant.count(text)
        
        assert count > 0
        assert isinstance(count, int)
    
    def test_budget_enforcement(self):
        cm = ContextManager()
        
        # Add a lot of content
        for i in range(20):
            cm.add_fact(f"Fact number {i} with some content to fill tokens", importance=0.7)
        
        # Render with small budget
        prompt = cm.render_prompt(
            current_task="Test",
            max_tokens=500
        )
        
        # Count tokens in result
        token_count = cm.token_accountant.count(prompt)
        
        # Should respect budget (with some tolerance)
        assert token_count <= 600  # Allow 20% overflow


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
