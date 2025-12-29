"""
SQLite storage backend for persistent memory management.
Provides tables for Core, Semantic, Episodic, and Working memory.
No external database required - uses local file storage.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import json
import numpy as np
import os

from cms.core.memory.base import MemoryBlock


class SQLiteStorage:
    """SQLite storage backend for CMS memory persistence."""
    
    def __init__(self, db_path: str = "cms_memory.db"):
        """Initialize SQLite connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create tables for each memory type."""
        cursor = self.conn.cursor()
        
        # Core memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS core_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                importance REAL NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                token_count INTEGER
            )
        ''')
        
        # Semantic memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                importance REAL NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                token_count INTEGER,
                entity TEXT,
                relation TEXT,
                embedding TEXT
            )
        ''')
        
        # Episodic memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                importance REAL NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                token_count INTEGER,
                event_type TEXT,
                participants TEXT
            )
        ''')
        
        # Working memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS working_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                importance REAL NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                token_count INTEGER,
                turn_number INTEGER,
                role TEXT
            )
        ''')
        
        # RAG documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rag_documents (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT,
                metadata TEXT,
                chunk_index INTEGER,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Agent logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT,
                metadata TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_entity ON semantic_memory(entity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_relation ON semantic_memory(relation)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodic_type ON episodic_memory(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memory(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_working_turn ON working_memory(turn_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rag_document ON rag_documents(document_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_id ON agent_logs(agent_id)')
        
        self.conn.commit()
    
    def _serialize_list(self, data: List) -> str:
        """Serialize list to JSON string."""
        return json.dumps(data) if data else '[]'
    
    def _deserialize_list(self, data: str) -> List:
        """Deserialize JSON string to list."""
        return json.loads(data) if data else []
    
    def _serialize_dict(self, data: Dict) -> str:
        """Serialize dict to JSON string."""
        return json.dumps(data) if data else '{}'
    
    def _deserialize_dict(self, data: str) -> Dict:
        """Deserialize JSON string to dict."""
        return json.loads(data) if data else {}
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        data = dict(row)
        if 'tags' in data:
            data['tags'] = self._deserialize_list(data['tags'])
        if 'metadata' in data:
            data['metadata'] = self._deserialize_dict(data['metadata'])
        if 'embedding' in data:
            data['embedding'] = self._deserialize_list(data['embedding'])
        if 'participants' in data:
            data['participants'] = self._deserialize_list(data['participants'])
        return data
    
    # Core Memory Operations
    def save_core_memory(self, memory_block: MemoryBlock) -> bool:
        """Save core memory block to SQLite."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO core_memory 
            (id, content, importance, timestamp, tags, metadata, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_block.id,
            memory_block.content,
            memory_block.importance,
            memory_block.timestamp.isoformat(),
            self._serialize_list(memory_block.tags),
            self._serialize_dict(memory_block.metadata),
            memory_block.token_count
        ))
        self.conn.commit()
        return True
    
    def load_core_memory(self) -> List[Dict[str, Any]]:
        """Load all core memory blocks."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM core_memory ORDER BY importance DESC')
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def delete_core_memory(self, memory_id: str) -> bool:
        """Delete core memory block."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM core_memory WHERE id = ?', (memory_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Semantic Memory Operations
    def save_semantic_fact(
        self,
        memory_block: MemoryBlock,
        entity: Optional[str] = None,
        relation: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Save semantic memory fact with embedding."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO semantic_memory 
            (id, content, importance, timestamp, tags, metadata, token_count, entity, relation, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_block.id,
            memory_block.content,
            memory_block.importance,
            memory_block.timestamp.isoformat(),
            self._serialize_list(memory_block.tags),
            self._serialize_dict(memory_block.metadata),
            memory_block.token_count,
            entity,
            relation,
            self._serialize_list(embedding) if embedding else None
        ))
        self.conn.commit()
        return True
    
    def search_semantic_memory(
        self,
        query_embedding: Optional[List[float]] = None,
        entity: Optional[str] = None,
        relation: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search semantic memory by embedding similarity or metadata."""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM semantic_memory WHERE 1=1'
        params = []
        
        if entity:
            query += ' AND entity = ?'
            params.append(entity)
        if relation:
            query += ' AND relation = ?'
            params.append(relation)
        
        query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        results = [self._row_to_dict(row) for row in cursor.fetchall()]
        
        # Calculate similarity if embedding provided
        if query_embedding and results:
            query_vec = np.array(query_embedding)
            for doc in results:
                if doc.get('embedding'):
                    doc_vec = np.array(doc['embedding'])
                    similarity = np.dot(query_vec, doc_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                    )
                    doc['similarity'] = float(similarity)
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return results
    
    def load_semantic_memory(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load semantic memory facts."""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM semantic_memory LIMIT {limit}')
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # Episodic Memory Operations
    def save_episode(
        self,
        memory_block: MemoryBlock,
        event_type: Optional[str] = None,
        participants: Optional[List[str]] = None
    ) -> bool:
        """Save episodic memory episode."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO episodic_memory 
            (id, content, importance, timestamp, tags, metadata, token_count, event_type, participants)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_block.id,
            memory_block.content,
            memory_block.importance,
            memory_block.timestamp.isoformat(),
            self._serialize_list(memory_block.tags),
            self._serialize_dict(memory_block.metadata),
            memory_block.token_count,
            event_type,
            self._serialize_list(participants) if participants else None
        ))
        self.conn.commit()
        return True
    
    def search_episodes(
        self,
        event_type: Optional[str] = None,
        participant: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search episodes by time range and metadata."""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM episodic_memory WHERE 1=1'
        params = []
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time.isoformat())
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time.isoformat())
        
        query += f' ORDER BY timestamp DESC LIMIT {limit}'
        
        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def load_episodic_memory(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load episodic memory episodes."""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM episodic_memory ORDER BY timestamp DESC LIMIT {limit}')
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # Working Memory Operations
    def save_conversation_turn(
        self,
        memory_block: MemoryBlock,
        turn_number: int,
        role: str
    ) -> bool:
        """Save conversation turn to working memory."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO working_memory 
            (id, content, importance, timestamp, tags, metadata, token_count, turn_number, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_block.id,
            memory_block.content,
            memory_block.importance,
            memory_block.timestamp.isoformat(),
            self._serialize_list(memory_block.tags),
            self._serialize_dict(memory_block.metadata),
            memory_block.token_count,
            turn_number,
            role
        ))
        self.conn.commit()
        return True
    
    def load_working_memory(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load recent conversation turns."""
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM working_memory ORDER BY turn_number DESC LIMIT {limit}')
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def clear_working_memory(self) -> bool:
        """Clear all working memory."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM working_memory')
        self.conn.commit()
        return True
    
    # RAG Document Operations
    def save_rag_document(
        self,
        doc_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: int = 0
    ) -> bool:
        """Save RAG document chunk with embedding."""
        cursor = self.conn.cursor()
        chunk_id = f"{doc_id}_chunk_{chunk_index}"
        cursor.execute('''
            INSERT OR REPLACE INTO rag_documents 
            (id, document_id, content, embedding, metadata, chunk_index, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            chunk_id,
            doc_id,
            content,
            self._serialize_list(embedding),
            self._serialize_dict(metadata or {}),
            chunk_index,
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
        return True
    
    def search_rag_documents(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search RAG documents by embedding similarity."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rag_documents')
        documents = [self._row_to_dict(row) for row in cursor.fetchall()]
        
        if not documents:
            return []
        
        # Calculate cosine similarity
        query_vec = np.array(query_embedding)
        for doc in documents:
            if doc.get('embedding'):
                doc_vec = np.array(doc['embedding'])
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )
                doc['similarity'] = float(similarity)
        
        # Sort by similarity and return top_k
        documents.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return documents[:top_k]
    
    def delete_rag_document(self, doc_id: str) -> bool:
        """Delete all chunks of a RAG document."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM rag_documents WHERE document_id = ?', (doc_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Agent Operations
    def log_agent_action(
        self,
        agent_id: str,
        action: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log agent action for monitoring."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO agent_logs (agent_id, action, result, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            agent_id,
            action,
            str(result),
            self._serialize_dict(metadata or {}),
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
        return True
    
    def get_agent_logs(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve agent logs."""
        cursor = self.conn.cursor()
        if agent_id:
            cursor.execute(
                'SELECT * FROM agent_logs WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?',
                (agent_id, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) as count FROM core_memory')
        stats['core_memory_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM semantic_memory')
        stats['semantic_memory_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM episodic_memory')
        stats['episodic_memory_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM working_memory')
        stats['working_memory_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM rag_documents')
        stats['rag_documents_count'] = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM agent_logs')
        stats['agent_logs_count'] = cursor.fetchone()['count']
        
        # Get database file size in MB
        if os.path.exists(self.db_path):
            stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
        else:
            stats['database_size_mb'] = 0
        
        return stats
    
    def clear_all_memory(self):
        """Clear all memory tables. Use with caution."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM core_memory')
        cursor.execute('DELETE FROM semantic_memory')
        cursor.execute('DELETE FROM episodic_memory')
        cursor.execute('DELETE FROM working_memory')
        self.conn.commit()
    
    def close(self):
        """Close SQLite connection."""
        self.conn.close()
