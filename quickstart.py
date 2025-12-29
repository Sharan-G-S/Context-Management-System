"""
Quick start script for Context Management System.
Demonstrates basic usage with MongoDB, RAG, and Agents.
"""

import os
from dotenv import load_dotenv

from cms.storage.sqlite import SQLiteStorage
from cms.llm.groq_client import GroqClient
from cms.rag.pipeline import RAGPipeline
from cms.agents.research_agent import ResearchAgent

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("Context Management System - Quick Start")
    print("SeptemberAI")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    
    # Storage (SQLite - no external database needed!)
    storage = SQLiteStorage(
        db_path=os.getenv('SQLITE_DB_PATH', 'cms_memory.db')
    )
    print("   - SQLite storage initialized (local file-based)")
    
    # LLM Client
    llm_client = GroqClient(api_key=os.getenv('GROQ_API_KEY'))
    print("   - Groq LLM client initialized")
    
    # RAG Pipeline
    rag_pipeline = RAGPipeline(storage=storage, llm_client=llm_client)
    print("   - RAG pipeline initialized")
    
    # Research Agent
    research_agent = ResearchAgent(
        llm_client=llm_client,
        storage=storage,
        rag_pipeline=rag_pipeline
    )
    print("   - Research agent initialized")
    
    # Ingest sample document
    print("\n2. Ingesting sample document...")
    sample_doc = """
    Context Management Systems are critical for LLM applications.
    They manage three types of memory: core memory for system instructions,
    semantic memory for knowledge facts, and episodic memory for experiences.
    
    RAG (Retrieval-Augmented Generation) enhances LLM responses by retrieving
    relevant context from a knowledge base before generation.
    
    Agents can autonomously execute tasks using tools and reasoning.
    """
    
    doc_id = rag_pipeline.ingest_document(
        content=sample_doc,
        metadata={'source': 'sample_document', 'topic': 'CMS'}
    )
    print(f"   - Document ingested: {doc_id}")
    
    # Query RAG system
    print("\n3. Querying RAG system...")
    question = "What are the three types of memory in CMS?"
    result = rag_pipeline.answer_question(question)
    print(f"   Q: {question}")
    print(f"   A: {result['answer']}")
    print(f"   Sources: {len(result['sources'])}")
    
    # Run research agent
    print("\n4. Running research agent...")
    research_question = "How does RAG enhance LLM responses?"
    research_result = research_agent.research(research_question)
    print(f"   Q: {research_question}")
    print(f"   A: {research_result['answer']}")
    print(f"   Method: {research_result['method']}")
    
    # Get statistics
    print("\n5. System statistics...")
    stats = storage.get_statistics()
    print(f"   - RAG Documents: {stats['rag_documents_count']}")
    print(f"   - Agent Logs: {stats['agent_logs_count']}")
    print(f"   - Database Size: {stats['database_size_mb']:.2f} MB")
    
    print("\n" + "=" * 60)
    print("Quick start complete!")
    print("Open http://localhost:5000 to access the dashboard")
    print("=" * 60)
    
    # Close connection
    storage.close()

if __name__ == "__main__":
    main()
