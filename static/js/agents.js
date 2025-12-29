// Agents JavaScript

const researchForm = document.getElementById('research-form');
const researchResults = document.getElementById('research-results');
const refreshLogsBtn = document.getElementById('refresh-logs');

// Handle research agent
researchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = document.getElementById('research-question').value;
    
    researchResults.style.display = 'block';
    document.getElementById('result-question').textContent = question;
    document.getElementById('result-answer').textContent = 'Research in progress...';
    document.getElementById('result-analysis').textContent = '';
    document.getElementById('result-sources-count').textContent = '';
    
    try {
        const response = await fetch('/api/agent/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            document.getElementById('result-question').textContent = result.question;
            document.getElementById('result-answer').textContent = result.answer;
            document.getElementById('result-analysis').textContent = result.analysis;
            document.getElementById('result-sources-count').textContent = 
                `${result.sources.length} sources used | Method: ${result.method}`;
            
            // Refresh logs
            loadAgentLogs();
        } else {
            document.getElementById('result-answer').textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        document.getElementById('result-answer').textContent = `Error: ${error.message}`;
    }
});

// Load agent logs
async function loadAgentLogs() {
    const logsContainer = document.getElementById('agent-logs');
    logsContainer.innerHTML = '<p class="loading">Loading logs...</p>';
    
    try {
        const response = await fetch('/api/agent/logs?limit=20');
        const data = await response.json();
        
        if (data.success && data.logs.length > 0) {
            logsContainer.innerHTML = data.logs.map(log => {
                return `
                    <div class="log-item">
                        <div class="log-header">
                            <span>${log.action}</span>
                            <span>${new Date(log.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="log-content">
                            ${log.result.substring(0, 200)}${log.result.length > 200 ? '...' : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            logsContainer.innerHTML = '<p class="loading">No logs found</p>';
        }
    } catch (error) {
        console.error('Error loading agent logs:', error);
        logsContainer.innerHTML = '<p class="loading">Error loading logs</p>';
    }
}

// Refresh logs button
refreshLogsBtn.addEventListener('click', loadAgentLogs);

// Load logs on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAgentLogs();
});
