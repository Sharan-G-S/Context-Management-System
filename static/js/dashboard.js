// Dashboard JavaScript

async function loadStats() {
    try {
        const response = await fetch('/api/memory/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('core-count').textContent = stats.core_memory_count;
            document.getElementById('semantic-count').textContent = stats.semantic_memory_count;
            document.getElementById('episodic-count').textContent = stats.episodic_memory_count;
            document.getElementById('working-count').textContent = stats.working_memory_count;
            document.getElementById('rag-count').textContent = stats.rag_documents_count;
            document.getElementById('agent-logs-count').textContent = stats.agent_logs_count;
            document.getElementById('db-size').textContent = stats.database_size_mb.toFixed(2) + ' MB';
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
            
            // Update flow diagram
            updateFlowDiagram(stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateFlowDiagram(stats) {
    document.getElementById('flow-working').textContent = `${stats.working_memory_count} items`;
    document.getElementById('flow-semantic').textContent = stats.semantic_memory_count;
    document.getElementById('flow-episodic').textContent = stats.episodic_memory_count;
    document.getElementById('flow-core').textContent = stats.core_memory_count;
}

// Token counting (approximate - 1 token ≈ 4 characters for English)
function estimateTokens(text) {
    return Math.ceil(text.length / 4);
}

// Advanced context optimization for efficient context management
function optimizeContext(text) {
    let optimized = text;
    
    // 1. Remove extra whitespace
    optimized = optimized.replace(/\s+/g, ' ').trim();
    
    // 2. Remove common filler words
    const fillers = ['basically', 'actually', 'literally', 'like', 'you know', 'I mean', 'sort of', 'kind of', 'well', 'um', 'uh', 'really', 'very', 'just', 'quite', 'rather'];
    fillers.forEach(filler => {
        const regex = new RegExp('\\b' + filler + '\\b', 'gi');
        optimized = optimized.replace(regex, '');
    });
    
    // 3. Replace verbose phrases with concise alternatives
    const replacements = [
        // Context Management specific
        { from: /Context Management System \(CMS\)/gi, to: 'CMS' },
        { from: /Retrieval-Augmented Generation \(RAG\)/gi, to: 'RAG' },
        { from: /Artificial Intelligence \(AI\) (is an advanced method|agents?)/gi, to: 'AI $2' },
        { from: /Artificial Intelligence \(AI\)/gi, to: 'AI' },
        
        // Memory and data related
        { from: /memory hierarchies \(short-term\/working, episodic, semantic\)/gi, to: 'memory hierarchies' },
        { from: /short-term\/working, episodic, semantic/gi, to: 'multi-tier' },
        { from: /external vector databases/gi, to: 'vector DBs' },
        { from: /external knowledge bases/gi, to: 'knowledge bases' },
        { from: /for lasting knowledge/gi, to: 'for storage' },
        { from: /for immediate tasks/gi, to: 'for tasks' },
        
        // Process and action related
        { from: /involves using/gi, to: 'uses' },
        { from: /combining fast/gi, to: 'combining' },
        { from: /in-context windows/gi, to: 'context windows' },
        { from: /optimizing via/gi, to: 'optimizing through' },
        { from: /and optimizing via/gi, to: 'optimizing via' },
        { from: /text generation process/gi, to: 'generation' },
        { from: /generation process/gi, to: 'generation' },
        
        // Efficiency related
        { from: /to efficiently blend/gi, to: 'blending' },
        { from: /for coherent, long-term understanding/gi, to: 'for long-term understanding' },
        { from: /coherent, long-term/gi, to: 'long-term' },
        { from: /reducing token use and improving accuracy/gi, to: 'reducing tokens, improving accuracy' },
        
        // General verbose phrases
        { from: /in order to/gi, to: 'to' },
        { from: /due to the fact that/gi, to: 'because' },
        { from: /at this point in time/gi, to: 'now' },
        { from: /for the purpose of/gi, to: 'to' },
        { from: /with regard to/gi, to: 'about' },
        { from: /primarily used in/gi, to: 'used in' },
        { from: /adaptively determines/gi, to: 'determines' },
        { from: /This contrasts with traditional, static/gi, to: 'Unlike static' },
        { from: /before generation begins/gi, to: 'before generation' }
    ];
    
    replacements.forEach(({ from, to }) => {
        optimized = optimized.replace(from, to);
    });
    
    // 4. Simplify parenthetical expressions (keep short ones, remove long explanations)
    optimized = optimized.replace(/\([^)]{30,}\)/g, '');
    
    // 5. Replace compound phrases with simpler versions
    const simplifications = [
        { from: /real-time data, past events, and general facts/gi, to: 'data, events, and facts' },
        { from: /summarization, hybrid retrieval, and memory compression/gi, to: 'summarization and compression' },
        { from: /immediate tasks with/gi, to: 'tasks with' }
    ];
    
    simplifications.forEach(({ from, to }) => {
        optimized = optimized.replace(from, to);
    });
    
    // 6. Remove repeated or redundant words
    optimized = optimized.replace(/\b(\w+)\s+\1\b/gi, '$1');
    
    // 7. Shorten common technical terms
    const technicalShorthand = [
        { from: /database(s?)/gi, to: 'DB$1' },
        { from: /information/gi, to: 'info' },
        { from: /configuration/gi, to: 'config' },
        { from: /implementation/gi, to: 'impl' },
        { from: /Implementing/gi, to: 'Implementing' } // Keep this one
    ];
    
    // Apply only to non-starting words
    const words = optimized.split(' ');
    optimized = words.map((word, index) => {
        if (index > 0) {
            technicalShorthand.forEach(({ from, to }) => {
                if (from.source !== 'Implementing') {
                    word = word.replace(from, to);
                }
            });
        }
        return word;
    }).join(' ');
    
    // 8. Final cleanup
    optimized = optimized.replace(/\s+/g, ' ');
    optimized = optimized.replace(/,\s*,/g, ',');
    optimized = optimized.replace(/\.\s*\./g, '.');
    optimized = optimized.replace(/\s+([.,;:])/g, '$1');
    optimized = optimized.trim();
    
    // 9. If still no significant reduction, apply aggressive optimization
    const currentTokens = estimateTokens(optimized);
    const originalTokens = estimateTokens(text);
    const reduction = ((originalTokens - currentTokens) / originalTokens) * 100;
    
    if (reduction < 10) {
        // Remove adjectives and adverbs
        const wordsToRemove = ['fast', 'efficient', 'efficiently', 'coherent', 'general', 'immediate', 'lasting'];
        wordsToRemove.forEach(word => {
            const regex = new RegExp('\\b' + word + '\\s+', 'gi');
            optimized = optimized.replace(regex, '');
        });
        
        // Simplify connecting phrases
        optimized = optimized.replace(/,\s*and\s*/g, ', ');
        optimized = optimized.replace(/\s+and\s+/g, ', ');
        
        // Final cleanup
        optimized = optimized.replace(/\s+/g, ' ').trim();
    }
    
    return optimized;
}

// Handle context query form
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
    
    const form = document.getElementById('context-query-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const queryText = document.getElementById('query-text').value;
            const originalTokens = estimateTokens(queryText);
            const optimized = optimizeContext(queryText);
            const optimizedTokens = estimateTokens(optimized);
            const savings = ((originalTokens - optimizedTokens) / originalTokens * 100).toFixed(1);
            
            // Show visualization
            const visualization = document.getElementById('token-visualization');
            visualization.style.display = 'block';
            
            // Update token counts
            document.getElementById('original-tokens').textContent = originalTokens;
            document.getElementById('optimized-tokens').textContent = optimizedTokens;
            document.getElementById('token-savings').textContent = savings + '%';
            
            // Update text previews
            document.getElementById('original-text-preview').textContent = queryText;
            document.getElementById('optimized-text-preview').textContent = optimized;
            
            // Update savings details
            const tokensSaved = originalTokens - optimizedTokens;
            document.getElementById('tokens-saved').textContent = `Saved ${tokensSaved} tokens`;
            
            // Update visual comparison bars
            const barOriginal = document.getElementById('bar-original');
            const barOptimized = document.getElementById('bar-optimized');
            const originalWidth = 100;
            const optimizedWidth = (optimizedTokens / originalTokens * 100).toFixed(1);
            
            // Animate bars
            setTimeout(() => {
                barOriginal.style.width = originalWidth + '%';
                barOptimized.style.width = optimizedWidth + '%';
            }, 100);
            
            // Update bar labels
            document.getElementById('bar-original-value').textContent = `${originalTokens} tokens`;
            document.getElementById('bar-optimized-value').textContent = `${optimizedTokens} tokens`;
            
            // Update efficiency summary
            document.getElementById('efficiency-percent').textContent = savings + '%';
            document.getElementById('efficiency-tokens').textContent = tokensSaved;
            
            // Draw token chart
            drawTokenChart(originalTokens, optimizedTokens, tokensSaved);
            
            // Store in memory layers
            await storeInMemory(queryText, optimized, originalTokens, optimizedTokens, tokensSaved);
            
            // Scroll to results
            visualization.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    }
});

// Store optimization in memory layers
async function storeInMemory(originalText, optimizedText, originalTokens, optimizedTokens, tokensSaved) {
    try {
        // Store in Working Memory (recent optimization)
        await fetch('/api/memory/working', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                context: `Token optimization: ${originalTokens} → ${optimizedTokens} tokens`,
                metadata: { 
                    original: originalText.substring(0, 100) + '...',
                    optimized: optimizedText.substring(0, 100) + '...',
                    savings: tokensSaved
                }
            })
        });
        
        // Store in Semantic Memory (knowledge about optimization)
        await fetch('/api/memory/semantic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                entity: 'token_optimization',
                relation: 'achieved_reduction',
                value: `${tokensSaved} tokens (${((tokensSaved / originalTokens) * 100).toFixed(1)}%)`,
                metadata: {
                    original_tokens: originalTokens,
                    optimized_tokens: optimizedTokens,
                    timestamp: new Date().toISOString()
                }
            })
        });
        
        // Store in Episodic Memory (event of optimization)
        await fetch('/api/memory/episodic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event: 'Context optimization performed',
                context: `Original: ${originalTokens} tokens, Optimized: ${optimizedTokens} tokens, Saved: ${tokensSaved} tokens`,
                metadata: {
                    original_preview: originalText.substring(0, 150),
                    optimized_preview: optimizedText.substring(0, 150),
                    reduction_percentage: ((tokensSaved / originalTokens) * 100).toFixed(1)
                }
            })
        });
        
        // Store full content in Core Memory if reduction is significant (>20%)
        if ((tokensSaved / originalTokens) * 100 > 20) {
            await fetch('/api/memory/core', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    key: `optimization_${Date.now()}`,
                    value: optimizedText,
                    importance: Math.min(10, Math.floor((tokensSaved / originalTokens) * 50)),
                    metadata: {
                        original_tokens: originalTokens,
                        optimized_tokens: optimizedTokens,
                        savings: tokensSaved
                    }
                })
            });
        }
        
        // Refresh stats to show new memory counts
        await loadStats();
        
        console.log('✅ Memory stored across all layers');
    } catch (error) {
        console.error('Error storing memory:', error);
    }
}

// Draw token optimization chart
function drawTokenChart(original, optimized, saved) {
    const canvas = document.getElementById('tokenChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.parentElement.clientWidth;
    const height = 300;
    canvas.width = width;
    canvas.height = height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Chart settings
    const padding = 60;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const barWidth = chartWidth / 4;
    const maxValue = Math.max(original, optimized) * 1.2;
    
    // Draw background grid
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Draw y-axis labels
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.textAlign = 'right';
        const value = Math.round(maxValue * (1 - i / 5));
        ctx.fillText(value.toString(), padding - 10, y + 4);
    }
    
    // Draw bars with animation (simplified for immediate display)
    const bars = [
        { x: padding + barWidth * 0.5, value: original, color: 'rgba(249, 115, 22, 0.8)', label: 'Original' },
        { x: padding + barWidth * 1.5, value: optimized, color: 'rgba(34, 197, 94, 0.8)', label: 'Optimized' },
        { x: padding + barWidth * 2.5, value: saved, color: 'rgba(59, 130, 246, 0.8)', label: 'Saved' }
    ];
    
    bars.forEach(bar => {
        const barHeight = (bar.value / maxValue) * chartHeight;
        const x = bar.x - barWidth / 4;
        const y = padding + chartHeight - barHeight;
        
        // Draw bar
        ctx.fillStyle = bar.color;
        ctx.fillRect(x, y, barWidth / 2, barHeight);
        
        // Draw border
        ctx.strokeStyle = bar.color.replace('0.8', '1');
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, barWidth / 2, barHeight);
        
        // Draw value on top
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(bar.value.toString(), bar.x, y - 10);
        
        // Draw label
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.font = '14px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillText(bar.label, bar.x, height - padding + 25);
    });
    
    // Draw x-axis
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding + chartHeight);
    ctx.lineTo(width - padding, padding + chartHeight);
    ctx.stroke();
    
    // Draw y-axis
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, padding + chartHeight);
    ctx.stroke();
}
