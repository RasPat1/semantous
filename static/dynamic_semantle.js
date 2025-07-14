// Game state
let graphData = { nodes: [], links: [] };
let simulation = null;
let svg = null;
let g = null;
let currentModel = 'sentence-bert';
let guessHistory = []; // Store all guesses for sorting

// Color scale for similarity scores
function getColor(score) {
    // Smooth HSL gradient from red (0) to green (120)
    const hue = (score / 100) * 120;
    const saturation = 70;
    const lightness = 50;
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Get node radius based on score
function getNodeRadius(score, isTarget = false) {
    if (isTarget) return 25;
    return 8 + (score / 100) * 12;
}

// Initialize the graph
function initializeGraph() {
    const container = document.querySelector('.graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg = d3.select('#graph')
        .attr('width', width)
        .attr('height', height);

    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Create main group
    g = svg.append('g');

    // Create arrow markers for directed edges
    svg.append('defs').selectAll('marker')
        .data(['arrow'])
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#666');

    // Initialize force simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(d => (100 - d.value) * 2))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeRadius(d.score) + 10));
}

// Update the graph with new data
function updateGraph(data) {
    if (!data || !data.nodes) return;
    
    graphData = data;

    // Clear existing elements
    g.selectAll('.link').remove();
    g.selectAll('.node-group').remove();

    // Create links
    const link = g.selectAll('.link')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', 'link')
        .attr('stroke', d => getColor(d.value))
        .attr('stroke-width', d => 1 + (d.value / 100) * 9)
        .attr('stroke-opacity', d => 0.7 + (d.value / 100) * 0.3)
        .attr('marker-end', 'url(#arrow)');

    // Create node groups
    const nodeGroup = g.selectAll('.node-group')
        .data(graphData.nodes)
        .enter().append('g')
        .attr('class', 'node-group');

    // Add circles
    const node = nodeGroup.append('circle')
        .attr('class', 'node')
        .attr('r', d => getNodeRadius(d.score, d.isTarget))
        .attr('fill', d => d.isTarget ? '#a855f7' : getColor(d.score))
        .attr('stroke', d => d.isTarget ? '#a855f7' : getColor(d.score))
        .attr('stroke-width', d => d.isNew ? 3 : 1.5)
        .attr('stroke-opacity', d => d.isNew ? 1 : 0.8);

    // Add labels
    const label = nodeGroup.append('text')
        .attr('class', 'node-label')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('fill', 'white')
        .text(d => d.label);

    // Add drag behavior
    nodeGroup.call(d3.drag()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // Add hover effects
    nodeGroup
        .on('mouseenter', function(event, d) {
            // Highlight node
            d3.select(this).select('circle')
                .attr('stroke-width', 3);

            // Show tooltip
            const tooltip = document.getElementById('tooltip');
            tooltip.style.opacity = 1;
            tooltip.style.left = `${event.pageX + 10}px`;
            tooltip.style.top = `${event.pageY - 10}px`;
            tooltip.innerHTML = `
                <strong>${d.label}</strong><br>
                Similarity: ${d.score.toFixed(1)}%
            `;
        })
        .on('mouseleave', function(event, d) {
            // Reset highlight
            d3.select(this).select('circle')
                .attr('stroke-width', d.isNew ? 3 : 1.5);

            // Hide tooltip
            document.getElementById('tooltip').style.opacity = 0;
        });

    // Update simulation
    simulation.nodes(graphData.nodes);
    simulation.force('link').links(graphData.links);
    simulation.alpha(0.6).restart();

    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        nodeGroup
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Remove new node highlight after animation
    setTimeout(() => {
        node.attr('stroke-width', 1.5);
        graphData.nodes.forEach(n => n.isNew = false);
    }, 3000);
}

// Drag functions
function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Set secret word
async function setWord() {
    const input = document.getElementById('secret-word');
    const word = input.value.trim().toLowerCase();
    
    if (!word) {
        alert('Please enter a word');
        return;
    }

    try {
        const response = await fetch('/set_word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, model: currentModel })
        });

        const data = await response.json();
        
        if (data.success) {
            // Switch to game phase
            document.getElementById('setup-phase').style.display = 'none';
            document.getElementById('game-phase').style.display = 'block';
            document.getElementById('guess-input').focus();
            
            // Reset guess history
            guessHistory = [];
            document.getElementById('guess-history').innerHTML = '';
            
            // Initialize graph with just the secret node
            updateGraph({
                nodes: [{
                    id: word,
                    label: '?',
                    score: 100,
                    isTarget: true
                }],
                links: []
            });
        } else {
            alert(data.error || 'Failed to set word');
        }
    } catch (error) {
        alert('Error setting word: ' + error.message);
    }
}

// Make a guess
async function makeGuess() {
    const input = document.getElementById('guess-input');
    const guess = input.value.trim().toLowerCase();
    
    if (!guess) return;

    try {
        const response = await fetch('/guess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: guess, model: currentModel })
        });

        const data = await response.json();
        
        if (response.ok) {
            // Clear input
            input.value = '';
            
            // Update guess count
            document.getElementById('guess-count').textContent = data.guess_count;
            
            // Add to history
            addToHistory(data.word, data.score, data.correct);
            
            // Mark new node
            if (data.graph_data && data.graph_data.nodes) {
                data.graph_data.nodes.forEach(node => {
                    if (node.id === guess) {
                        node.isNew = true;
                    }
                });
            }
            
            // Update graph
            updateGraph(data.graph_data);
            
            // Show success message if correct
            if (data.correct) {
                showSuccess(data.word, data.guess_count);
            }
        } else {
            alert(data.error || 'Invalid guess');
        }
    } catch (error) {
        alert('Error making guess: ' + error.message);
    }
}

// Add guess to history and maintain sorted order
function addToHistory(word, score, correct) {
    // Add to our history array
    guessHistory.push({ word, score, correct });
    
    // Sort by score (highest first)
    guessHistory.sort((a, b) => b.score - a.score);
    
    // Rebuild the history display
    rebuildHistoryDisplay();
}

// Rebuild the entire history display in sorted order
function rebuildHistoryDisplay() {
    const history = document.getElementById('guess-history');
    history.innerHTML = ''; // Clear existing
    
    // Add all items in sorted order
    guessHistory.forEach((guess, index) => {
        const item = document.createElement('div');
        item.className = 'guess-item';
        // Add 'new' class only to the most recent guess
        if (guess.word === guessHistory[guessHistory.length - 1].word && index === guessHistory.findIndex(g => g.word === guess.word)) {
            item.className += ' new';
            setTimeout(() => item.classList.remove('new'), 500);
        }
        
        item.innerHTML = `
            <span class="guess-word">${guess.word}</span>
            <span class="guess-score" style="color: ${getColor(guess.score)}">${guess.score.toFixed(1)}%</span>
        `;
        
        history.appendChild(item);
    });
}

// Show success message
function showSuccess(word, guessCount) {
    const successHtml = `
        <div class="success-message">
            <h2>🎉 Congratulations!</h2>
            <div class="word">${word}</div>
            <div class="stats">Found in ${guessCount} ${guessCount === 1 ? 'guess' : 'guesses'}</div>
            <button onclick="location.reload()">Play Again</button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', successHtml);
}

// Get hint
async function getHint() {
    try {
        const response = await fetch('/hint');
        const data = await response.json();
        
        if (response.ok) {
            const container = document.getElementById('hint-container');
            container.innerHTML = `<div class="hint-text">${data.hint}</div>`;
        }
    } catch (error) {
        console.error('Error getting hint:', error);
    }
}

// Switch models
async function switchModel() {
    const newModel = document.getElementById('model-select').value;
    if (newModel === currentModel) return;
    
    currentModel = newModel;
    
    // Show loading indicator
    const graphContainer = document.querySelector('.graph-container');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.textContent = 'Recalculating similarities';
    graphContainer.appendChild(loadingDiv);
    
    try {
        const response = await fetch('/calculate_similarities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: currentModel })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update graph
            updateGraph(data.graph_data);
            
            // Update history scores
            if (data.guess_scores) {
                // Update our history array with new scores
                data.guess_scores.forEach(scoreData => {
                    const historyItem = guessHistory.find(g => g.word === scoreData.word);
                    if (historyItem) {
                        historyItem.score = scoreData.score;
                    }
                });
                
                // Re-sort by new scores
                guessHistory.sort((a, b) => b.score - a.score);
                
                // Rebuild display
                rebuildHistoryDisplay();
            }
        }
    } catch (error) {
        alert('Error switching models: ' + error.message);
    } finally {
        // Remove loading indicator
        loadingDiv.remove();
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeGraph();
    
    // Set up event listeners
    document.getElementById('set-word-btn').addEventListener('click', setWord);
    document.getElementById('secret-word').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') setWord();
    });
    
    document.getElementById('guess-btn').addEventListener('click', makeGuess);
    document.getElementById('guess-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') makeGuess();
    });
    
    document.getElementById('hint-btn').addEventListener('click', getHint);
    
    // Hide model selector if only ConceptNet is available
    if (window.location.hostname.includes('vercel.app')) {
        document.querySelector('.model-selector').style.display = 'none';
    } else {
        document.getElementById('model-select').addEventListener('change', switchModel);
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        const container = document.querySelector('.graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        svg.attr('width', width).attr('height', height);
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
    });
});