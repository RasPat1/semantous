let guessHistory = [];
let bestScore = 0;

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
            bestScore = 0;
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
            document.getElementById('score-value').textContent = result.score;
            document.getElementById('feedback-message').textContent = result.feedback;
            document.getElementById('guess-word').textContent = result.guess;
            
            // Add to history
            guessHistory.unshift({
                guess: result.guess,
                score: result.score
            });
            
            // Update best score
            if (result.score > bestScore && result.score < 100) {
                bestScore = result.score;
            }
            
            updateDisplay();
            
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
    document.getElementById('best-score').textContent = bestScore;
    
    // Update history
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    guessHistory.slice(0, 10).forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerHTML = `
            <span>${item.guess}</span>
            <span class="history-score">${item.score}/100</span>
        `;
        historyList.appendChild(div);
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
        
        examplesDiv.innerHTML = '';
        examples.forEach(ex => {
            const div = document.createElement('div');
            div.className = 'example-item';
            div.innerHTML = `
                <span class="example-words">${ex.word1} ↔ ${ex.word2}</span>
                <span>${ex.description}</span>
                <span class="example-score">${ex.score}/100</span>
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
    bestScore = 0;
    document.getElementById('current-result').classList.add('hidden');
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