// Memory Management JavaScript

const tabs = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.getAttribute('data-tab');
        
        // Remove active class from all tabs and contents
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Load data for the selected tab
        loadMemoryData(tabName);
    });
});

async function loadMemoryData(type) {
    const listElement = document.getElementById(`${type}-list`);
    listElement.innerHTML = '<p class="loading">Loading...</p>';
    
    try {
        const response = await fetch(`/api/memory/${type}`);
        const data = await response.json();
        
        if (data.success && data.items.length > 0) {
            listElement.innerHTML = data.items.map(item => {
                return `
                    <div class="memory-item">
                        <strong>${item.content.substring(0, 100)}${item.content.length > 100 ? '...' : ''}</strong>
                        <p><strong>Importance:</strong> ${item.importance.toFixed(2)}</p>
                        <p><strong>Timestamp:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                        ${item.tags && item.tags.length > 0 ? `<p><strong>Tags:</strong> ${item.tags.join(', ')}</p>` : ''}
                        ${item.entity ? `<p><strong>Entity:</strong> ${item.entity}</p>` : ''}
                        ${item.relation ? `<p><strong>Relation:</strong> ${item.relation}</p>` : ''}
                        ${item.event_type ? `<p><strong>Event Type:</strong> ${item.event_type}</p>` : ''}
                        ${item.role ? `<p><strong>Role:</strong> ${item.role}</p>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            listElement.innerHTML = '<p class="loading">No items found</p>';
        }
    } catch (error) {
        console.error(`Error loading ${type} memory:`, error);
        listElement.innerHTML = '<p class="loading">Error loading data</p>';
    }
}

async function loadMemoryCounts() {
    try {
        const response = await fetch('/api/memory/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('overview-core').textContent = stats.core_memory_count;
            document.getElementById('overview-semantic').textContent = stats.semantic_memory_count;
            document.getElementById('overview-episodic').textContent = stats.episodic_memory_count;
            document.getElementById('overview-working').textContent = stats.working_memory_count;
        }
    } catch (error) {
        console.error('Error loading memory counts:', error);
    }
}

// Load core memory by default on page load
document.addEventListener('DOMContentLoaded', () => {
    loadMemoryCounts();
    loadMemoryData('core');
});
