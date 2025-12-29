// RAG System JavaScript

const ingestForm = document.getElementById('ingest-form');
const queryForm = document.getElementById('query-form');
const ingestResult = document.getElementById('ingest-result');
const queryResults = document.getElementById('query-results');

// Handle document ingestion
ingestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const content = document.getElementById('doc-content').value;
    const source = document.getElementById('doc-source').value;
    
    ingestResult.textContent = 'Ingesting document...';
    ingestResult.className = 'result-message';
    
    try {
        const response = await fetch('/api/rag/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                metadata: source ? { source: source } : {}
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            ingestResult.textContent = `Document ingested successfully! ID: ${data.document_id}`;
            ingestResult.className = 'result-message success';
            ingestForm.reset();
            loadRAGStats();
        } else {
            ingestResult.textContent = `Error: ${data.error}`;
            ingestResult.className = 'result-message error';
        }
    } catch (error) {
        ingestResult.textContent = `Error: ${error.message}`;
        ingestResult.className = 'result-message error';
    }
});

// Handle query
queryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = document.getElementById('question').value;
    const topK = document.getElementById('top-k').value;
    
    queryResults.style.display = 'block';
    document.getElementById('answer').textContent = 'Searching...';
    document.getElementById('sources').innerHTML = '';
    
    try {
        const response = await fetch('/api/rag/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                top_k: parseInt(topK)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            document.getElementById('answer').textContent = result.answer;
            
            if (result.sources.length > 0) {
                document.getElementById('sources').innerHTML = result.sources.map((source, idx) => {
                    return `
                        <div class="source-item">
                            <strong>Source ${idx + 1}</strong>
                            <p><strong>Similarity:</strong> ${source.similarity.toFixed(3)}</p>
                            <p>${source.content}</p>
                            ${source.metadata.source ? `<p><strong>From:</strong> ${source.metadata.source}</p>` : ''}
                        </div>
                    `;
                }).join('');
            } else {
                document.getElementById('sources').innerHTML = '<p>No sources found</p>';
            }
        } else {
            document.getElementById('answer').textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        document.getElementById('answer').textContent = `Error: ${error.message}`;
    }
});

async function loadRAGStats() {
    try {
        const response = await fetch('/api/rag/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('rag-total-docs').textContent = stats.total_documents;
            document.getElementById('rag-db-size').textContent = stats.database_size_mb.toFixed(2) + ' MB';
        }
    } catch (error) {
        console.error('Error loading RAG stats:', error);
    }
}

// Load stats on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRAGStats();
});
