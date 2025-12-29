"""
Basic usage example of the Context Management System.
"""

from cms import ContextManager, load_config

def main():
    # Initialize the Context Manager
    print("Initializing Context Management System...")
    cm = ContextManager()
    
    # Set core memory (system instructions)
    print("\n1. Setting Core Memory (System Instructions)...")
    cm.set_core_memory(
        "system_role",
        "You are a helpful AI assistant specialized in Python programming and software development.",
        importance=1.0,
        tags=["system", "role"]
    )
    
    cm.set_core_memory(
        "coding_guidelines",
        "Always write clean, well-documented code following PEP 8 standards. Include error handling and type hints.",
        importance=0.95,
        tags=["system", "guidelines", "coding"]
    )
    
    # Add some semantic facts (knowledge)
    print("\n2. Adding Semantic Facts (Knowledge Base)...")
    cm.add_fact(
        "Python uses duck typing - if it walks like a duck and quacks like a duck, it's a duck.",
        entity="Python",
        relation="typing_system",
        importance=0.8,
        tags=["python", "typing", "concept"]
    )
    
    cm.add_fact(
        "List comprehensions are faster than equivalent for loops for creating lists.",
        entity="Python",
        relation="performance",
        importance=0.7,
        tags=["python", "performance", "optimization"]
    )
    
    # Add episodic memories (past experiences)
    print("\n3. Adding Episodic Memories (Past Interactions)...")
    cm.add_episode(
        "User asked about implementing binary search. Provided example with time complexity analysis.",
        event_type="coding_help",
        participants=["user", "assistant"],
        importance=0.6,
        tags=["algorithms", "search", "teaching"]
    )
    
    # Simulate a conversation
    print("\n4. Recording Conversation...")
    
    # Turn 1
    cm.record_interaction(
        user_input="How do I read a CSV file in Python?",
        assistant_response="You can use the csv module or pandas. Here's a simple example using csv:\n\nimport csv\nwith open('file.csv', 'r') as f:\n    reader = csv.DictReader(f)\n    for row in reader:\n        print(row)",
        metadata={"extract_facts": True}
    )
    
    # Turn 2
    cm.record_interaction(
        user_input="What about handling large CSV files?",
        assistant_response="For large files, use pandas with chunking:\n\nimport pandas as pd\nfor chunk in pd.read_csv('large_file.csv', chunksize=1000):\n    process(chunk)",
        metadata={"extract_facts": True}
    )
    
    # Turn 3
    cm.record_interaction(
        user_input="Can you show me error handling for file operations?",
        assistant_response="Sure! Always use try-except blocks:\n\ntry:\n    with open('file.csv', 'r') as f:\n        # process file\n        pass\nexcept FileNotFoundError:\n    print('File not found')\nexcept PermissionError:\n    print('Permission denied')",
    )
    
    # Render optimized prompt for next interaction
    print("\n5. Rendering Optimized Prompt...")
    current_task = "User is asking about Python file operations and error handling."
    prompt = cm.render_prompt(
        current_task=current_task,
        query="file operations error handling"
    )
    
    print("\n=== RENDERED PROMPT ===")
    print(prompt)
    print("\n=== END PROMPT ===")
    
    # Inspect context
    print("\n6. Context Inspection...")
    context_info = cm.inspect_context()
    
    print(f"\nTotal tokens used: {context_info['total_tokens']}")
    print("\nSections included:")
    for section in context_info['sections']:
        print(f"  - {section['name']}: {section['token_count']} tokens, {section['item_count']} items")
    
    # Get memory statistics
    print("\n7. Memory Statistics...")
    memory_stats = cm.inspect_memory()
    
    print(f"\nCore Memory: {memory_stats['core']['count']} items, {memory_stats['core']['tokens']} tokens")
    print(f"Semantic Memory: {memory_stats['semantic']['count']} items, {memory_stats['semantic']['tokens']} tokens")
    print(f"Episodic Memory: {memory_stats['episodic']['count']} items, {memory_stats['episodic']['tokens']} tokens")
    print(f"Working Memory: {memory_stats['working']['count']} items, {memory_stats['working']['tokens']} tokens")
    print(f"\nTotal Memory Usage: {memory_stats['total_tokens']} tokens")
    
    # Search for relevant facts
    print("\n8. Searching Semantic Memory...")
    facts = cm.search_facts("Python performance", top_k=3)
    print(f"\nFound {len(facts)} relevant facts:")
    for fact in facts:
        print(f"  - {fact.content[:100]}...")
    
    # Get recent episodes
    print("\n9. Getting Recent Episodes...")
    episodes = cm.get_recent_episodes(hours=24, limit=5)
    print(f"\nFound {len(episodes)} recent episodes:")
    for ep in episodes:
        print(f"  - {ep.event_type}: {ep.content[:100]}...")
    
    # Get conversation history
    print("\n10. Getting Conversation History...")
    history = cm.get_conversation_history(n=5)
    print(f"\nRecent conversation ({len(history)} turns):")
    for turn in history:
        if hasattr(turn, 'role'):
            print(f"  [{turn.role.upper()}]: {turn.content[:80]}...")
    
    # System metrics
    print("\n11. System Metrics...")
    metrics = cm.get_metrics()
    print(f"\nSession ID: {metrics['session_id']}")
    print(f"Total Interactions: {metrics['interactions']}")
    print(f"Model: {metrics['model']['model']}")
    print(f"Max Context: {metrics['model']['max_tokens']} tokens")
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
