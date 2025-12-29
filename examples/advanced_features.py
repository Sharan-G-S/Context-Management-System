"""
Advanced features demonstration: Semantic + Episodic memory with optimization.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cms import ContextManager, Config
from datetime import datetime, timedelta


def main():
    print("=== Advanced Context Management Features ===\n")
    
    # Initialize with custom configuration
    config = Config.from_dict({
        "model": {
            "name": "gpt-4",
            "max_tokens": 8192,
        },
        "memory": {
            "semantic": {
                "max_entries": 500,
                "similarity_threshold": 0.75,
            },
            "episodic": {
                "max_entries": 300,
                "retention_days": 14,
            },
        },
        "optimization": {
            "enabled": True,
            "strategies": [
                "relevance_ranking",
                "temporal_decay",
                "importance_pruning",
                "semantic_clustering",
            ],
        },
    })
    
    cm = ContextManager(config=config)
    
    # === Feature 1: Semantic Memory with Knowledge Graph ===
    print("Feature 1: Semantic Memory System")
    print("-" * 50)
    
    # Build a knowledge base about machine learning
    print("\nBuilding ML knowledge base...")
    
    facts = [
        ("Machine learning is a subset of artificial intelligence", "ML", "definition", 0.9),
        ("Supervised learning uses labeled data for training", "supervised_learning", "technique", 0.85),
        ("Neural networks are inspired by biological neurons", "neural_networks", "architecture", 0.8),
        ("Overfitting occurs when model memorizes training data", "overfitting", "problem", 0.8),
        ("Cross-validation helps prevent overfitting", "cross_validation", "technique", 0.75),
        ("Gradient descent is an optimization algorithm", "gradient_descent", "algorithm", 0.85),
        ("Deep learning uses multiple layers of neural networks", "deep_learning", "architecture", 0.9),
        ("Backpropagation is used to train neural networks", "backpropagation", "algorithm", 0.85),
    ]
    
    fact_ids = []
    for content, entity, relation, importance in facts:
        fact_id = cm.add_fact(
            content=content,
            entity=entity,
            relation=relation,
            importance=importance,
            tags=["ml", "knowledge"]
        )
        fact_ids.append(fact_id)
    
    print(f"Added {len(fact_ids)} facts to semantic memory")
    
    # Search for relevant facts
    print("\nSearching for 'neural network training'...")
    results = cm.search_facts("neural network training", top_k=3)
    for fact in results:
        print(f"  ✓ {fact.content}")
        print(f"    Entity: {fact.entity}, Importance: {fact.importance:.2f}")
    
    # === Feature 2: Episodic Memory with Temporal Patterns ===
    print("\n\nFeature 2: Episodic Memory System")
    print("-" * 50)
    
    # Simulate a series of interactions over time
    print("\nRecording user interaction episodes...")
    
    episodes = [
        ("User asked about supervised learning basics", "question", ["user", "assistant"], 0.7),
        ("Explained supervised learning with examples", "teaching", ["assistant"], 0.8),
        ("User requested code example for linear regression", "request", ["user"], 0.75),
        ("Provided scikit-learn code example", "code_help", ["assistant"], 0.8),
        ("User reported error in the code", "bug_report", ["user"], 0.9),
        ("Debugged and fixed the import statement", "debugging", ["assistant"], 0.85),
        ("User successfully ran the code", "success", ["user"], 0.7),
        ("User asked about model evaluation metrics", "question", ["user"], 0.75),
    ]
    
    episode_ids = []
    for content, event_type, participants, importance in episodes:
        ep_id = cm.add_episode(
            content=content,
            event_type=event_type,
            participants=participants,
            importance=importance,
            tags=["ml", "session"]
        )
        episode_ids.append(ep_id)
    
    print(f"Added {len(episode_ids)} episodes to episodic memory")
    
    # Get recent episodes
    print("\nRecent episodes:")
    recent = cm.get_recent_episodes(hours=24, limit=5)
    for ep in recent:
        print(f"  ✓ [{ep.event_type}] {ep.content}")
        print(f"    Participants: {', '.join(ep.participants)}, Importance: {ep.importance:.2f}")
    
    # Detect patterns
    print("\nDetecting interaction patterns...")
    patterns = cm.episodic_memory.detect_patterns(min_frequency=2)
    for pattern in patterns:
        print(f"  Pattern: {pattern['pattern']}")
        print(f"    Frequency: {pattern['frequency']}, Avg Importance: {pattern['avg_importance']:.2f}")
    
    # === Feature 3: Advanced Context Optimization ===
    print("\n\nFeature 3: Context Optimization Strategies")
    print("-" * 50)
    
    # Add more diverse content
    print("\nAdding diverse content for optimization demo...")
    
    # Some old, less relevant facts
    cm.add_fact(
        "Python was created by Guido van Rossum",
        entity="Python",
        importance=0.4,
        tags=["history", "python"]
    )
    
    # Recent, highly relevant fact
    cm.add_fact(
        "Use train_test_split from sklearn to split datasets",
        entity="sklearn",
        importance=0.9,
        tags=["ml", "sklearn", "current"]
    )
    
    # Test optimization with different queries
    queries = [
        "neural network training",
        "model evaluation",
        "debugging code errors",
    ]
    
    print("\nTesting context optimization with different queries:")
    for query in queries:
        print(f"\n  Query: '{query}'")
        
        # Preview what would be included
        preview = cm.preview_context(
            current_task=f"Help user with: {query}",
            query=query
        )
        
        print(f"    Total tokens: {preview['total_tokens']}")
        print(f"    Sections included: {len(preview['sections'])}")
        
        for section in preview['sections']:
            print(f"      - {section['name']}: {section['token_count']} tokens")
    
    # === Demonstrate Budget Management ===
    print("\n\nBudget Management")
    print("-" * 50)
    
    # Render with token budget
    print("\nRendering optimized prompt with 4000 token budget...")
    prompt = cm.render_prompt(
        current_task="Help user understand neural network training",
        query="neural networks backpropagation",
        max_tokens=4000
    )
    
    # Get budget report
    context_info = cm.inspect_context()
    budget_report = context_info['budget_report']
    
    print(f"\nBudget Utilization:")
    print(f"  Total Budget: {budget_report['total_budget']} tokens")
    print(f"  Total Used: {budget_report['total_used']} tokens")
    print(f"  Utilization: {budget_report['utilization']:.1%}")
    print(f"\nSection Breakdown:")
    
    for section, stats in budget_report['sections'].items():
        if stats['used'] > 0:
            print(f"  {section}:")
            print(f"    Budget: {stats['budget']} ({stats['percentage']:.0%})")
            print(f"    Used: {stats['used']} ({stats['utilization']:.1%})")
            print(f"    Remaining: {stats['remaining']}")
    
    # === Memory Maintenance ===
    print("\n\nMemory Maintenance")
    print("-" * 50)
    
    print("\nBefore pruning:")
    stats_before = cm.inspect_memory()
    print(f"  Semantic: {stats_before['semantic']['count']} items")
    print(f"  Episodic: {stats_before['episodic']['count']} items")
    
    # Prune low-importance items
    print("\nPruning items with importance < 0.5...")
    cm.prune_memory(importance_threshold=0.5)
    
    print("\nAfter pruning:")
    stats_after = cm.inspect_memory()
    print(f"  Semantic: {stats_after['semantic']['count']} items")
    print(f"  Episodic: {stats_after['episodic']['count']} items")
    
    # === Final Summary ===
    print("\n\nFinal System Summary")
    print("=" * 50)
    
    metrics = cm.get_metrics()
    print(f"Session ID: {metrics['session_id']}")
    print(f"Total Interactions: {metrics['interactions']}")
    print(f"\nMemory Distribution:")
    print(f"  Core: {metrics['memory']['core']['count']} items, {metrics['memory']['core']['tokens']} tokens")
    print(f"  Semantic: {metrics['memory']['semantic']['count']} items, {metrics['memory']['semantic']['tokens']} tokens")
    print(f"  Episodic: {metrics['memory']['episodic']['count']} items, {metrics['memory']['episodic']['tokens']} tokens")
    print(f"  Working: {metrics['memory']['working']['count']} items, {metrics['memory']['working']['tokens']} tokens")
    print(f"  Total: {metrics['memory']['total_tokens']} tokens")
    
    print("\nAdvanced features demonstration completed!")


if __name__ == "__main__":
    main()
