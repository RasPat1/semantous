let guessHistory = [];
let bestDistance = 0;
let eliminationProgress = 0;
let graphData = { nodes: [], links: [] };
let simulation = null;

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
            bestDistance = 0;
            eliminationProgress = 0;
            updateDisplay();
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
        alert('Please enter a guess!');
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
            // Update display
            document.getElementById('current-result').classList.remove('hidden');
            
            // Update distance meter
            const distanceFill = document.getElementById('distance-fill');
            distanceFill.style.left = result.distance_score + '%';
            document.getElementById('distance-value').textContent = result.distance_score;
            
            document.getElementById('feedback-message').textContent = result.feedback;
            document.getElementById('guess-word').textContent = result.guess;
            
            // Update elimination progress
            eliminationProgress = result.elimination_score;
            document.getElementById('elimination-fill').style.width = eliminationProgress + '%';
            document.getElementById('elimination-percent').textContent = eliminationProgress + '%';
            
            // Show eliminated concepts if any
            if (result.eliminated_concepts && result.eliminated_concepts.length > 0) {
                const eliminatedDiv = document.getElementById('eliminated-spaces');
                const eliminatedList = document.getElementById('eliminated-list');
                
                eliminatedDiv.classList.remove('hidden');
                eliminatedList.innerHTML = '';
                
                result.eliminated_concepts.forEach(concept => {
                    const span = document.createElement('span');
                    span.className = 'eliminated-word';
                    span.textContent = concept;
                    eliminatedList.appendChild(span);
                });
            }
            
            // Add to history
            guessHistory.unshift({
                guess: result.guess,
                distance: result.distance_score,
                similarity: result.similarity
            });
            
            // Update best distance
            if (result.distance_score > bestDistance && !result.found) {
                bestDistance = result.distance_score;
            }
            
            updateDisplay();
            
            // Update the D3 graph
            updateGraph(result.all_guesses);
            
            // Clear input
            guessInput.value = '';
            
            // Check for victory
            if (result.found) {
                setTimeout(() => {
                    document.getElementById('game-phase').classList.add('hidden');
                    document.getElementById('victory-phase').classList.remove('hidden');
                    document.getElementById('final-word').textContent = result.secret_word;
                    document.getElementById('final-guesses').textContent = result.guess_count;
                }, 1000);
            }
        } else {
            alert(result.error || 'Failed to make guess');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function updateDisplay() {
    // Update stats
    document.getElementById('guess-count').textContent = guessHistory.length;
    document.getElementById('best-distance').textContent = bestDistance;
    
    // Update history - show ALL guesses, not just top 10
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    guessHistory.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        
        let distanceClass = 'distance-low';
        if (item.distance >= 80) distanceClass = 'distance-high';
        else if (item.distance >= 60) distanceClass = 'distance-medium';
        
        div.innerHTML = `
            <span>${item.guess}</span>
            <span class="history-distance ${distanceClass}">${item.distance}/100</span>
        `;
        historyList.appendChild(div);
    });
}

function initGraph() {
    const svg = d3.select('#word-graph');
    const width = svg.node().getBoundingClientRect().width;
    const height = 400;
    
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    // Add zoom behavior
    const g = svg.append('g');
    
    svg.call(d3.zoom()
        .scaleExtent([0.5, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        }));
    
    return g;
}

function updateGraph(allGuesses) {
    if (!allGuesses || allGuesses.length === 0) return;
    
    const svg = d3.select('#word-graph');
    svg.selectAll('*').remove();
    
    const g = initGraph();
    const width = svg.node().getBoundingClientRect().width;
    const height = 400;
    
    // Create nodes from guesses
    graphData.nodes = allGuesses.map((guess, i) => ({
        id: guess.word,
        distance: guess.distance,
        index: i
    }));
    
    // Add a center reference node
    graphData.nodes.unshift({
        id: 'TARGET',
        distance: 0,
        isCenter: true,
        index: -1
    });
    
    // Create links from center to each word
    graphData.links = allGuesses.map(guess => ({
        source: 'TARGET',
        target: guess.word,
        distance: guess.distance
    }));
    
    // Create force simulation
    simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links)
            .id(d => d.id)
            .distance(d => d.distance * 2)) // Distance based on semantic distance
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
    
    // Add links
    const link = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', 'link')
        .style('stroke-width', d => Math.max(1, 5 - d.distance / 20));
    
    // Add nodes
    const node = g.append('g')
        .selectAll('.node')
        .data(graphData.nodes)
        .enter().append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles
    node.append('circle')
        .attr('r', d => d.isCenter ? 15 : 8 + (d.distance / 10))
        .style('fill', d => {
            if (d.isCenter) return '#ff6b6b';
            const hue = (d.distance / 100) * 120; // 0 (red) to 120 (green)
            return `hsl(${hue}, 70%, 50%)`;
        })
        .style('stroke', d => d.isCenter ? '#cc0000' : '#fff');
    
    // Add labels
    node.append('text')
        .text(d => d.id)
        .attr('x', 0)
        .attr('y', d => d.isCenter ? 30 : 20)
        .style('text-anchor', 'middle')
        .style('fill', '#333');
    
    // Add distance labels on hover
    node.append('title')
        .text(d => d.isCenter ? 'Target Word (Hidden)' : `${d.id}: ${d.distance}/100 distance`);
    
    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
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

async function getHint() {
    try {
        const response = await fetch('/hint');
        const result = await response.json();
        
        if (response.ok) {
            alert(result.hint);
        } else {
            alert(result.error || 'Could not get hint');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function showExamples() {
    const examplesDiv = document.getElementById('examples');
    
    if (!examplesDiv.classList.contains('hidden')) {
        examplesDiv.classList.add('hidden');
        return;
    }
    
    try {
        const response = await fetch('/examples');
        const examples = await response.json();
        
        examplesDiv.innerHTML = '';
        examples.forEach(ex => {
            const div = document.createElement('div');
            div.className = 'example-item';
            div.innerHTML = `
                <span class="example-words">${ex.word1} ↔ ${ex.word2}</span>
                <span>${ex.description}</span>
                <span class="example-distance">${ex.distance_score}/100 distance</span>
            `;
            examplesDiv.appendChild(div);
        });
        
        examplesDiv.classList.remove('hidden');
    } catch (error) {
        alert('Error loading examples: ' + error.message);
    }
}

function resetGame() {
    document.getElementById('victory-phase').classList.add('hidden');
    document.getElementById('setup-phase').classList.remove('hidden');
    document.getElementById('secret-word').value = '';
    document.getElementById('secret-word').focus();
    
    // Reset all game state
    guessHistory = [];
    bestDistance = 0;
    eliminationProgress = 0;
    document.getElementById('current-result').classList.add('hidden');
    document.getElementById('eliminated-spaces').classList.add('hidden');
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