"""
Flask web application for CMS dashboard.
Provides UI for memory management, RAG, and agent monitoring.
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

from cms.manager import ContextManager
from cms.storage.sqlite import SQLiteStorage
from cms.llm.groq_client import GroqClient
from cms.rag.pipeline import RAGPipeline
from cms.agents.research_agent import ResearchAgent


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize components
storage = None
cms_manager = None
rag_pipeline = None
research_agent = None

def init_components():
    """Initialize CMS components."""
    global storage, cms_manager, rag_pipeline, research_agent
    
    # Initialize storage (SQLite - no external database needed)
    db_path = os.getenv('SQLITE_DB_PATH', 'cms_memory.db')
    storage = SQLiteStorage(db_path=db_path)
    
    # Initialize LLM client
    groq_api_key = os.getenv('GROQ_API_KEY')
    llm_client = GroqClient(api_key=groq_api_key)
    
    # Initialize CMS manager
    cms_manager = ContextManager()
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(
        storage=storage,
        llm_client=llm_client
    )
    
    # Initialize research agent
    research_agent = ResearchAgent(
        llm_client=llm_client,
        storage=storage,
        rag_pipeline=rag_pipeline
    )


@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('index.html')


@app.route('/memory')
def memory_page():
    """Memory management page."""
    return render_template('memory.html')


@app.route('/rag')
def rag_page():
    """RAG interface page."""
    return render_template('rag.html')


@app.route('/agents')
def agents_page():
    """Agent monitoring page."""
    return render_template('agents.html')


# API Endpoints

@app.route('/api/memory/stats', methods=['GET'])
def get_memory_stats():
    """Get memory statistics."""
    try:
        stats = storage.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/memory/core', methods=['GET'])
def get_core_memory():
    """Get core memory items."""
    try:
        items = storage.load_core_memory()
        return jsonify({
            'success': True,
            'items': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/memory/semantic', methods=['GET'])
def get_semantic_memory():
    """Get semantic memory items."""
    try:
        items = storage.load_semantic_memory(limit=50)
        return jsonify({
            'success': True,
            'items': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/memory/episodic', methods=['GET'])
def get_episodic_memory():
    """Get episodic memory items."""
    try:
        items = storage.load_episodic_memory(limit=50)
        return jsonify({
            'success': True,
            'items': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/memory/working', methods=['GET'])
def get_working_memory():
    """Get working memory items."""
    try:
        items = storage.load_working_memory(limit=50)
        return jsonify({
            'success': True,
            'items': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rag/ingest', methods=['POST'])
def ingest_document():
    """Ingest document into RAG system."""
    try:
        data = request.json
        content = data.get('content')
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400
        
        doc_id = rag_pipeline.ingest_document(content, metadata)
        
        return jsonify({
            'success': True,
            'document_id': doc_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rag/query', methods=['POST'])
def query_rag():
    """Query RAG system."""
    try:
        data = request.json
        question = data.get('question')
        top_k = data.get('top_k', 5)
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        result = rag_pipeline.answer_question(question, top_k=top_k)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rag/stats', methods=['GET'])
def get_rag_stats():
    """Get RAG statistics."""
    try:
        stats = rag_pipeline.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/agent/research', methods=['POST'])
def agent_research():
    """Run research agent."""
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        result = research_agent.research(question)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/agent/logs', methods=['GET'])
def get_agent_logs():
    """Get agent execution logs."""
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 50))
        
        logs = storage.get_agent_logs(agent_id=agent_id, limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    import sys
    port = 5001 if len(sys.argv) > 1 and sys.argv[1] == '--port' else 5000
    if len(sys.argv) > 2 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    
    init_components()
    print(f"\n{'='*50}")
    print(f"Context Management System - SeptemberAI")
    print(f"{'='*50}")
    print(f"Server starting on http://localhost:{port}")
    print(f"Database: {os.getenv('SQLITE_DB_PATH', 'cms_memory.db')}")
    print(f"{'='*50}\n")
    app.run(debug=True, host='0.0.0.0', port=port)

