let guessHistory = [];
let bestScore = 0;
let startTime = null;
let timerInterval = null;

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
            startTime = Date.now();
            updateDisplay();
            startTimer();
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
    
    // Show loading state
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Checking...';
    
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
            // Show result
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
            if (result.score > bestScore) {
                bestScore = result.score;
            }
            
            updateDisplay();
            
            // Clear input
            guessInput.value = '';
            
            // Check for victory
            if (result.found) {
                stopTimer();
                setTimeout(() => {
                    document.getElementById('game-phase').classList.add('hidden');
                    document.getElementById('victory-phase').classList.remove('hidden');
                    document.getElementById('final-word').textContent = result.secret_word;
                    document.getElementById('final-guesses').textContent = result.guess_count;
                    document.getElementById('final-time').textContent = formatTime(result.time_taken);
                }, 1000);
            }
        } else {
            alert(result.error || 'Failed to make guess');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        // Reset button state
        button.disabled = false;
        button.textContent = 'Guess';
    }
}

async function getHint() {
    try {
        const response = await fetch('/hint');
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('hint-text').textContent = result.hint;
            document.getElementById('hint-text').classList.remove('hidden');
        } else {
            alert(result.error || 'Failed to get hint');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function updateDisplay() {
    // Update stats
    document.getElementById('guess-count').textContent = guessHistory.length;
    document.getElementById('best-score').textContent = bestScore || '--';
    
    // Update history list
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    // Sort by score (highest first)
    const sortedHistory = [...guessHistory].sort((a, b) => b.score - a.score);
    
    sortedHistory.slice(0, 10).forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerHTML = `
            <span>${item.guess}</span>
            <span class="history-score">${item.score}/100</span>
        `;
        historyList.appendChild(div);
    });
}

function startTimer() {
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('timer').textContent = formatTime(elapsed);
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function resetGame() {
    stopTimer();
    document.getElementById('victory-phase').classList.add('hidden');
    document.getElementById('setup-phase').classList.remove('hidden');
    document.getElementById('secret-word').value = '';
    document.getElementById('secret-word').focus();
    
    // Reset all game state
    guessHistory = [];
    bestScore = 0;
    document.getElementById('current-result').classList.add('hidden');
    document.getElementById('hint-text').classList.add('hidden');
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