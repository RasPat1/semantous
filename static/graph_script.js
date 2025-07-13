let guessHistory = [];
let simulation = null;
let allNodes = [];
let allLinks = [];
let pairwiseSims = {};

async function setWord() {
    const wordInput = document.getElementById('secret-word');
    const word = wordInput.value.trim();
    
    if (!word) {
        alert('Please enter a word!');
        return;
    }
    
    try {
        const response = await fetch('/set_word', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ word: word })
        });
        
        if (response.ok) {
            document.getElementById('setup-phase').classList.add('hidden');
            document.getElementById('game-phase').classList.remove('hidden');
            document.getElementById('guess-input').focus();
            
            // Reset game state
            guessHistory = [];
            allNodes = [];
            allLinks = [];
            pairwiseSims = {};
            updateDisplay();
            initGraph();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to set word');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function makeGuess() {
    const guessInput = document.getElementById('guess-input');
    const guess = guessInput.value.trim();
    
    if (!guess) {
        return;
    }
    
    try {
        const response = await fetch('/guess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ guess: guess })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Update displays
            document.getElementById('current-score').textContent = result.score;
            document.getElementById('feedback').textContent = result.feedback;
            document.getElementById('guess-count').textContent = result.guess_count;
            
            // Update history
            guessHistory = result.all_scores;
            pairwiseSims = result.pairwise_similarities;
            updateDisplay();
            
            // Update graph
            updateGraph(result.all_scores, result.pairwise_similarities);
            
            // Clear input
            guessInput.value = '';
            
            // Check for victory
            if (result.found) {
                setTimeout(() => {
                    document.getElementById('final-word').textContent = result.secret_word;
                    document.getElementById('final-guesses').textContent = result.guess_count;
                    document.getElementById('victory-modal').classList.remove('hidden');
                }, 500);
            }
        } else {
            alert(result.error || 'Failed to make guess');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function updateDisplay() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    guessHistory.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        const color = getScoreColor(item.score);
        div.innerHTML = `
            <span>${item.word}</span>
            <span class="history-score" style="color: ${color}">${item.score}/100</span>
        `;
        historyList.appendChild(div);
    });
}

function getScoreColor(score) {
    // Returns color based on score (0-100)
    if (score >= 80) return '#00ff00';
    if (score >= 60) return '#88ff00';
    if (score >= 40) return '#ffff00';
    if (score >= 20) return '#ff8800';
    return '#ff0000';
}

function initGraph() {
    const svg = d3.select('#word-graph');
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    // Add zoom
    const g = svg.append('g');
    svg.call(d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        }));
    
    // Add container groups
    g.append('g').attr('class', 'links');
    g.append('g').attr('class', 'link-labels');
    g.append('g').attr('class', 'nodes');
}

function updateGraph(scores, pairwiseSimilarities) {
    const svg = d3.select('#word-graph');
    const g = svg.select('g');
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    // Create nodes
    allNodes = scores.map((item, i) => ({
        id: item.word,
        score: item.score,
        index: i
    }));
    
    // Add target node
    allNodes.unshift({
        id: 'TARGET',
        score: 100,
        isTarget: true,
        index: -1
    });
    
    // Create links between all pairs of guessed words
    allLinks = [];
    
    // Links from target to each guess
    scores.forEach(item => {
        allLinks.push({
            source: 'TARGET',
            target: item.word,
            similarity: item.score,
            isToTarget: true
        });
    });
    
    // Links between all pairs of guesses
    Object.entries(pairwiseSimilarities).forEach(([pair, similarity]) => {
        const [word1, word2] = pair.split('-');
        allLinks.push({
            source: word1,
            target: word2,
            similarity: similarity,
            isToTarget: false
        });
    });
    
    // Update force simulation
    if (simulation) {
        simulation.stop();
    }
    
    simulation = d3.forceSimulation(allNodes)
        .force('link', d3.forceLink(allLinks)
            .id(d => d.id)
            .distance(d => {
                // Distance inversely proportional to similarity
                return (100 - d.similarity) * 2;
            }))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));
    
    // Update links
    const link = g.select('.links')
        .selectAll('line')
        .data(allLinks);
    
    link.exit().remove();
    
    const linkEnter = link.enter()
        .append('line')
        .attr('class', 'link');
    
    const linkUpdate = linkEnter.merge(link);
    
    linkUpdate
        .style('stroke', d => getScoreColor(d.similarity))
        .style('stroke-width', d => {
            // Thicker lines for higher similarity
            const thickness = Math.pow(d.similarity / 100, 2) * 15; // Exponential scaling for more dramatic effect
            if (d.isToTarget) return Math.max(1, thickness);
            return Math.max(0.5, thickness * 0.7); // Slightly thinner for inter-word connections
        })
        .style('stroke-opacity', d => d.isToTarget ? 0.8 : 0.6);
    
    // Remove link labels - no numbers on graph
    
    // Update nodes
    const node = g.select('.nodes')
        .selectAll('.node')
        .data(allNodes);
    
    node.exit().remove();
    
    const nodeEnter = node.enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    nodeEnter.append('circle');
    nodeEnter.append('text');
    
    const nodeUpdate = nodeEnter.merge(node);
    
    nodeUpdate.select('circle')
        .attr('r', d => d.isTarget ? 20 : 10 + (d.score / 10))
        .style('fill', d => {
            if (d.isTarget) return '#667eea';
            return getScoreColor(d.score);
        });
    
    nodeUpdate.select('text')
        .text(d => d.id)
        .attr('y', d => d.isTarget ? 35 : 25);
    
    // Add tooltips
    nodeUpdate.select('title').remove();
    nodeUpdate.append('title')
        .text(d => d.isTarget ? 'Target (Hidden)' : `${d.id}: ${d.score}/100`);
    
    // Update positions on tick
    simulation.on('tick', () => {
        linkUpdate
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        
        nodeUpdate.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    simulation.alpha(1).restart();
}

function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function resetGame() {
    document.getElementById('victory-modal').classList.add('hidden');
    document.getElementById('game-phase').classList.add('hidden');
    document.getElementById('setup-phase').classList.remove('hidden');
    
    // Clear inputs
    document.getElementById('secret-word').value = '';
    document.getElementById('secret-word').focus();
    
    // Reset displays
    document.getElementById('current-score').textContent = '--';
    document.getElementById('feedback').textContent = '';
    document.getElementById('guess-count').textContent = '0';
    
    // Clear history
    guessHistory = [];
    updateDisplay();
}

// Allow Enter key for inputs
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('secret-word').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') setWord();
    });
    
    document.getElementById('guess-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') makeGuess();
    });
});