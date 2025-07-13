let simulation = null;
let svg = null;
let g = null;
const MIN_NODE_SIZE = 8;
const MAX_NODE_SIZE = 30;

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
            
            initGraph();
            updateGraph([{word: 'SECRET', isSecret: true, score: 100}], []);
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
            updateHistory(result.nodes.filter(n => !n.isSecret));
            
            // Update graph with animation
            updateGraph(result.nodes, result.connections);
            
            // Clear input
            guessInput.value = '';
            
            // Check for victory
            if (result.found) {
                setTimeout(() => {
                    document.getElementById('final-word').textContent = result.secret_word;
                    document.getElementById('final-guesses').textContent = result.guess_count;
                    document.getElementById('victory-modal').classList.remove('hidden');
                }, 1000);
            }
        } else {
            alert(result.error || 'Failed to make guess');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function updateHistory(guesses) {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    guesses.forEach(node => {
        const div = document.createElement('div');
        div.className = 'history-item';
        const color = getScoreColor(node.score);
        div.innerHTML = `
            <span>${node.word}</span>
            <span class="history-score" style="color: ${color}">${node.score}/100</span>
        `;
        historyList.appendChild(div);
    });
}

function getScoreColor(score) {
    // Gradient from red to green
    const hue = (score / 100) * 120; // 0 = red, 120 = green
    return `hsl(${hue}, 70%, 50%)`;
}

function getNodeSize(score) {
    // Scale node size based on similarity to secret word
    return MIN_NODE_SIZE + (score / 100) * (MAX_NODE_SIZE - MIN_NODE_SIZE);
}

function initGraph() {
    svg = d3.select('#word-graph');
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    // Add zoom
    g = svg.append('g');
    svg.call(d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        }));
    
    // Add groups for links and nodes
    g.append('g').attr('class', 'links');
    g.append('g').attr('class', 'nodes');
}

function updateGraph(nodes, connections) {
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    // Update nodes data - ensure SECRET word displays properly
    const nodeData = nodes.map(n => ({
        ...n,
        id: n.word,
        displayWord: n.isSecret ? 'SECRET' : n.word
    }));
    
    // Update force simulation
    if (simulation) {
        simulation.stop();
    }
    
    simulation = d3.forceSimulation(nodeData)
        .force('link', d3.forceLink(connections)
            .id(d => d.word)
            .distance(60)  // Reduced from 100 - keeps nodes closer
            .strength(1))
        .force('charge', d3.forceManyBody().strength(-200))  // Reduced from -400 - less repulsion
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeSize(d.score) + 5))  // Tighter collision
        .force('x', d3.forceX(width / 2).strength(0.1))  // Pull nodes toward center
        .force('y', d3.forceY(height / 2).strength(0.1));
    
    // Update links
    const link = g.select('.links')
        .selectAll('line')
        .data(connections, d => `${d.source}-${d.target}`);
    
    // Remove old links
    link.exit()
        .transition()
        .duration(500)
        .style('stroke-opacity', 0)
        .remove();
    
    // Add new links
    const linkEnter = link.enter()
        .append('line')
        .attr('class', 'link')
        .style('stroke-opacity', 0);
    
    // Update all links
    const linkUpdate = linkEnter.merge(link);
    
    linkUpdate
        .classed('new', d => d.target === nodeData[nodeData.length - 1].word)
        .transition()
        .duration(500)
        .style('stroke-opacity', 0.6)
        .style('stroke-width', d => Math.max(1, d.similarity / 25));
    
    // Update nodes
    const node = g.select('.nodes')
        .selectAll('.node')
        .data(nodeData, d => d.word);
    
    // Remove old nodes
    node.exit()
        .transition()
        .duration(500)
        .attr('transform', 'scale(0)')
        .remove();
    
    // Add new nodes
    const nodeEnter = node.enter()
        .append('g')
        .attr('class', d => d.isSecret ? 'node secret' : 'node')
        .attr('transform', `translate(${width/2},${height/2}) scale(0)`)
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    nodeEnter.append('circle');
    nodeEnter.append('text');
    
    // Update all nodes
    const nodeUpdate = nodeEnter.merge(node);
    
    nodeUpdate.select('circle')
        .transition()
        .duration(500)
        .attr('r', d => getNodeSize(d.score))
        .style('fill', d => d.isSecret ? '#667eea' : getScoreColor(d.score));
    
    nodeUpdate.select('text')
        .text(d => d.displayWord)
        .attr('y', d => getNodeSize(d.score) + 15)
        .style('font-size', d => d.isSecret ? '14px' : '12px');
    
    // Animate new nodes appearing
    nodeEnter
        .transition()
        .duration(500)
        .attr('transform', d => `translate(${width/2},${height/2})`);
    
    // Add tooltips
    nodeUpdate.select('title').remove();
    nodeUpdate.append('title')
        .text(d => d.isSecret ? 'Secret Word' : `${d.word}: ${d.score}/100 similarity`);
    
    // Update positions on tick
    simulation.on('tick', () => {
        linkUpdate
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        nodeUpdate
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Restart simulation with some energy
    simulation.alpha(1).restart();
    
    // Highlight new connections briefly
    setTimeout(() => {
        linkUpdate.classed('new', false);
    }, 2000);
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
    document.getElementById('history-list').innerHTML = '';
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