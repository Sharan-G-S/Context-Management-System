#!/usr/bin/env python3
"""Add sample data to the CMS database for demonstration"""

import os
import uuid
import sqlite3
import json
from datetime import datetime

def add_sample_data():
    """Add sample memory data to database"""
    
    # Initialize database connection
    db_path = os.getenv('SQLITE_DB_PATH', 'cms_memory.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Adding sample data to CMS database...")
    
    # Add Core Memory items
    print("\n✓ Adding Core Memory items...")
    core_items = [
        {"content": "User prefers Python for backend development", "importance": 0.9, "tags": ["preference", "development"]},
        {"content": "Project uses SQLite for lightweight data storage", "importance": 0.85, "tags": ["technology", "database"]},
        {"content": "System runs on Flask web framework", "importance": 0.8, "tags": ["framework", "web"]}
    ]
    for item in core_items:
        cursor.execute('''
            INSERT INTO core_memory (id, content, importance, timestamp, tags, metadata, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            item["content"],
            item["importance"],
            datetime.now().isoformat(),
            json.dumps(item["tags"]),
            json.dumps({}),
            len(item["content"].split())
        ))
    
    # Add Semantic Memory facts
    print("✓ Adding Semantic Memory facts...")
    semantic_items = [
        {"content": "Flask is_a Python web framework", "entity": "Flask", "relation": "is_a", "importance": 0.85},
        {"content": "SQLite is_a embedded database engine", "entity": "SQLite", "relation": "is_a", "importance": 0.8},
        {"content": "Context Management optimizes token usage", "entity": "Context Management", "relation": "optimizes", "importance": 0.9},
        {"content": "SeptemberAI develops AI applications", "entity": "SeptemberAI", "relation": "develops", "importance": 0.75}
    ]
    for item in semantic_items:
        cursor.execute('''
            INSERT INTO semantic_memory (id, content, entity, relation, importance, timestamp, metadata, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            item["content"],
            item["entity"],
            item["relation"],
            item["importance"],
            datetime.now().isoformat(),
            json.dumps({}),
            len(item["content"].split())
        ))
    
    # Add Episodic Memory episodes
    print("✓ Adding Episodic Memory episodes...")
    episodic_items = [
        {"content": "User created new context management project", "event_type": "project_creation", "importance": 0.9},
        {"content": "Switched from MongoDB to SQLite", "event_type": "technology_change", "importance": 0.85},
        {"content": "Implemented ultra-shining violet UI", "event_type": "ui_update", "importance": 0.8},
        {"content": "Fixed text contrast and loading issues", "event_type": "bug_fix", "importance": 0.75}
    ]
    for item in episodic_items:
        cursor.execute('''
            INSERT INTO episodic_memory (id, content, event_type, importance, timestamp, metadata, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            item["content"],
            item["event_type"],
            item["importance"],
            datetime.now().isoformat(),
            json.dumps({}),
            len(item["content"].split())
        ))
    
    # Add Working Memory turns
    print("✓ Adding Working Memory turns...")
    working_items = [
        {"role": "user", "content": "How does context management work?", "turn": 1, "importance": 0.7},
        {"role": "assistant", "content": "Context management optimizes token usage by selecting relevant information.", "turn": 2, "importance": 0.7},
        {"role": "user", "content": "Can you show the memory flow?", "turn": 3, "importance": 0.7},
        {"role": "assistant", "content": "Flow: Input → Working → Long-term → Optimizer → Output", "turn": 4, "importance": 0.7}
    ]
    for item in working_items:
        cursor.execute('''
            INSERT INTO working_memory (id, content, role, turn_number, importance, timestamp, metadata, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            item["content"],
            item["role"],
            item["turn"],
            item["importance"],
            datetime.now().isoformat(),
            json.dumps({}),
            len(item["content"].split())
        ))
    
    conn.commit()
    
    print("\nSample data added successfully!")
    print("\nDatabase Statistics:")
    cursor.execute("SELECT COUNT(*) FROM core_memory")
    core_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM semantic_memory")
    semantic_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM episodic_memory")
    episodic_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM working_memory")
    working_count = cursor.fetchone()[0]
    
    print(f"  Core Memory: {core_count} items")
    print(f"  Semantic Memory: {semantic_count} facts")
    print(f"  Episodic Memory: {episodic_count} episodes")
    print(f"  Working Memory: {working_count} turns")
    
    conn.close()

if __name__ == "__main__":
    add_sample_data()
