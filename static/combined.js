let guessHistory = [];
let semantleSimulation = null;
let antisemantleSimulation = null;

async function setWords() {
    const semantleWord = document.getElementById('semantle-word').value.trim();
    const antisemantleWord = document.getElementById('antisemantle-word').value.trim();
    
    if (!semantleWord || !antisemantleWord) {
        alert('Please enter both words!');
        return;
    }
    
    try {
        const response = await fetch('/set_words', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                semantle_word: semantleWord,
                antisemantle_word: antisemantleWord
            })
        });
        
        if (response.ok) {
            document.getElementById('setup-phase').classList.add('hidden');
            document.getElementById('game-phase').classList.remove('hidden');
            document.getElementById('guess-input').focus();
            
            // Initialize graphs
            initGraphs();
            
            // Reset game state
            guessHistory = [];
            updateDisplay();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to set words');
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
            document.getElementById('semantle-score').textContent = result.semantle_score;
            document.getElementById('semantle-feedback').textContent = result.semantle_feedback;
            
            document.getElementById('antisemantle-score').textContent = result.antisemantle_distance;
            document.getElementById('antisemantle-feedback').textContent = result.antisemantle_feedback;
            
            document.getElementById('guess-count').textContent = result.guess_count;
            
            // Add to history
            guessHistory = result.all_guesses;
            updateDisplay();
            
            // Update graphs
            updateSemantleGraph(result.all_guesses);
            updateAntisemantleGraph(result.all_guesses);
            
            // Clear input
            guessInput.value = '';
            
            // Check for victory
            if (result.semantle_won || result.antisemantle_won) {
                let title = '';
                let message = '';
                
                if (result.semantle_won && result.antisemantle_won) {
                    title = '🎉 Double Victory! 🎉';
                    message = `Found both words in ${result.guess_count} guesses!`;
                } else if (result.semantle_won) {
                    title = '🎯 Semantle Victory!';
                    message = `Found "${result.semantle_word}" in ${result.guess_count} guesses!`;
                } else {
                    title = '🔄 Antisemantle Victory!';
                    message = `Found "${result.antisemantle_word}" in ${result.guess_count} guesses!`;
                }
                
                document.getElementById('victory-title').textContent = title;
                document.getElementById('victory-message').textContent = message;
                document.getElementById('victory-modal').classList.remove('hidden');
            }
        } else {
            alert(result.error || 'Failed to make guess');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function updateDisplay() {
    // Update Semantle history
    const semantleHistory = document.getElementById('semantle-history');
    semantleHistory.innerHTML = '';
    
    // Update Antisemantle history
    const antisemantleHistory = document.getElementById('antisemantle-history');
    antisemantleHistory.innerHTML = '';
    
    // Show all guesses
    guessHistory.forEach(item => {
        // Semantle history item
        const semDiv = document.createElement('div');
        semDiv.className = 'history-item';
        semDiv.innerHTML = `
            <span>${item.word}</span>
            <span class="history-score" style="color: hsl(${item.semantle_score * 1.2}, 70%, 50%)">${item.semantle_score}/100</span>
        `;
        semantleHistory.appendChild(semDiv);
        
        // Antisemantle history item
        const antiDiv = document.createElement('div');
        antiDiv.className = 'history-item';
        antiDiv.innerHTML = `
            <span>${item.word}</span>
            <span class="history-score" style="color: hsl(${item.antisemantle_distance * 1.2}, 70%, 50%)">${item.antisemantle_distance}/100</span>
        `;
        antisemantleHistory.appendChild(antiDiv);
    });
}

function initGraphs() {
    // Initialize both graphs
    const semantleSvg = d3.select('#semantle-graph');
    const antisemantleSvg = d3.select('#antisemantle-graph');
    
    // Clear any existing content
    semantleSvg.selectAll('*').remove();
    antisemantleSvg.selectAll('*').remove();
}

function updateSemantleGraph(guesses) {
    const svg = d3.select('#semantle-graph');
    svg.selectAll('*').remove();
    
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    const g = svg.append('g');
    
    // Create nodes
    const nodes = guesses.map((guess, i) => ({
        id: guess.word,
        score: guess.semantle_score,
        index: i
    }));
    
    // Add center target
    nodes.unshift({
        id: 'TARGET',
        score: 100,
        isCenter: true,
        index: -1
    });
    
    // Create links (distance inversely proportional to similarity)
    const links = guesses.map(guess => ({
        source: 'TARGET',
        target: guess.word,
        distance: 100 - guess.semantle_score
    }));
    
    // Force simulation - closer words are pulled closer
    semantleSimulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(d => d.distance * 1.5))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(25));
    
    // Add links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('class', 'link')
        .style('stroke-width', d => Math.max(1, (100 - d.distance) / 20));
    
    // Add nodes
    const node = g.append('g')
        .selectAll('.node')
        .data(nodes)
        .enter().append('g')
        .attr('class', 'node');
    
    // Add circles
    node.append('circle')
        .attr('r', d => d.isCenter ? 12 : 6 + (d.score / 15))
        .style('fill', d => {
            if (d.isCenter) return '#667eea';
            const hue = (d.score / 100) * 120;
            return `hsl(${hue}, 70%, 50%)`;
        })
        .style('stroke', '#fff');
    
    // Add labels
    node.append('text')
        .text(d => d.id)
        .attr('y', d => d.isCenter ? 25 : 18)
        .style('font-size', d => d.isCenter ? '12px' : '10px');
    
    // Add tooltips
    node.append('title')
        .text(d => d.isCenter ? 'Target (Hidden)' : `${d.id}: ${d.score}/100 similarity`);
    
    // Update positions
    semantleSimulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function updateAntisemantleGraph(guesses) {
    const svg = d3.select('#antisemantle-graph');
    svg.selectAll('*').remove();
    
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    const g = svg.append('g');
    
    // Create nodes
    const nodes = guesses.map((guess, i) => ({
        id: guess.word,
        distance: guess.antisemantle_distance,
        index: i
    }));
    
    // Add center target
    nodes.unshift({
        id: 'TARGET',
        distance: 0,
        isCenter: true,
        index: -1
    });
    
    // Create links
    const links = guesses.map(guess => ({
        source: 'TARGET',
        target: guess.word,
        distance: guess.antisemantle_distance
    }));
    
    // Force simulation - distant words are pushed further
    antisemantleSimulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(d => d.distance * 2))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(25));
    
    // Add links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('class', 'link')
        .style('stroke-width', d => Math.max(1, 5 - d.distance / 20));
    
    // Add nodes
    const node = g.append('g')
        .selectAll('.node')
        .data(nodes)
        .enter().append('g')
        .attr('class', 'node');
    
    // Add circles
    node.append('circle')
        .attr('r', d => d.isCenter ? 12 : 6 + (d.distance / 15))
        .style('fill', d => {
            if (d.isCenter) return '#ff6b6b';
            const hue = (d.distance / 100) * 120;
            return `hsl(${hue}, 70%, 50%)`;
        })
        .style('stroke', '#fff');
    
    // Add labels
    node.append('text')
        .text(d => d.id)
        .attr('y', d => d.isCenter ? 25 : 18)
        .style('font-size', d => d.isCenter ? '12px' : '10px');
    
    // Add tooltips
    node.append('title')
        .text(d => d.isCenter ? 'Target (Hidden)' : `${d.id}: ${d.distance}/100 distance`);
    
    // Update positions
    antisemantleSimulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
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
        
        examplesDiv.innerHTML = '<div style="color: #aaa; margin-bottom: 10px;">Example word pairs:</div>';
        examples.forEach(ex => {
            const div = document.createElement('div');
            div.className = 'example-item';
            div.innerHTML = `
                <span>${ex.word1} ↔ ${ex.word2}</span>
                <span>${ex.description}</span>
                <span>Similarity: ${ex.similarity} | Distance: ${ex.distance}</span>
            `;
            examplesDiv.appendChild(div);
        });
        
        examplesDiv.classList.remove('hidden');
    } catch (error) {
        alert('Error loading examples: ' + error.message);
    }
}

function resetGame() {
    document.getElementById('victory-modal').classList.add('hidden');
    document.getElementById('game-phase').classList.add('hidden');
    document.getElementById('setup-phase').classList.remove('hidden');
    
    // Clear inputs
    document.getElementById('semantle-word').value = '';
    document.getElementById('antisemantle-word').value = '';
    document.getElementById('semantle-word').focus();
    
    // Reset displays
    document.getElementById('semantle-score').textContent = '--';
    document.getElementById('antisemantle-score').textContent = '--';
    document.getElementById('semantle-feedback').textContent = '';
    document.getElementById('antisemantle-feedback').textContent = '';
    document.getElementById('guess-count').textContent = '0';
    
    // Clear history
    guessHistory = [];
    updateDisplay();
}

// Allow Enter key for inputs
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('semantle-word').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('antisemantle-word').focus();
        }
    });
    
    document.getElementById('antisemantle-word').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') setWords();
    });
    
    document.getElementById('guess-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') makeGuess();
    });
});