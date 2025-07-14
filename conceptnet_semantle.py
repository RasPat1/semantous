#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
import requests
import secrets
import os
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ConceptNet API endpoint
CONCEPTNET_API = "http://api.conceptnet.io"

def calculate_similarity(word1, word2):
    """Calculate semantic similarity between two words using ConceptNet API"""
    
    # Exact match gets 100
    if word1.lower() == word2.lower():
        return 100
    
    try:
        # Make API request to ConceptNet
        response = requests.get(
            f"{CONCEPTNET_API}/relatedness",
            params={
                "node1": f"/c/en/{word1.lower().replace(' ', '_')}",
                "node2": f"/c/en/{word2.lower().replace(' ', '_')}"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # ConceptNet returns a value between -1 and 1
            # Convert to 0-100 scale
            relatedness = data.get('value', 0)
            score = round(max(0, (relatedness + 1) * 50))  # Convert -1,1 to 0,100
            return score
        else:
            # Fallback to a simple comparison if API fails
            return 0
            
    except Exception as e:
        print(f"Error calling ConceptNet API: {e}")
        return 0

@app.route('/')
def index():
    return render_template('conceptnet.html')

@app.route('/set_word', methods=['POST'])
def set_word():
    data = request.json
    secret_word = data.get('word', '').strip()
    
    if not secret_word:
        return jsonify({'error': 'Please provide a word'}), 400
    
    session['secret_word'] = secret_word
    session['guesses'] = []
    session['guess_count'] = 0
    session['start_time'] = time.time()
    
    return jsonify({'success': True})

@app.route('/guess', methods=['POST'])
def guess():
    if 'secret_word' not in session:
        return jsonify({'error': 'No word set yet'}), 400
    
    data = request.json
    guess_word = data.get('guess', '').strip()
    
    if not guess_word:
        return jsonify({'error': 'Please provide a guess'}), 400
    
    secret_word = session['secret_word']
    
    # Check if already guessed
    if guess_word.lower() in [g.lower() for g in session.get('guesses', [])]:
        return jsonify({'error': 'You already guessed that word'}), 400
    
    score = calculate_similarity(secret_word, guess_word)
    
    session['guess_count'] = session.get('guess_count', 0) + 1
    session['guesses'] = session.get('guesses', []) + [guess_word]
    
    # Check if found
    found = guess_word.lower() == secret_word.lower()
    
    # Get feedback
    if score == 100:
        feedback = "🎉 Congratulations! You found the word!"
    elif score >= 80:
        feedback = "🔥 Very hot! Extremely similar!"
    elif score >= 70:
        feedback = "♨️  Hot! Very close!"
    elif score >= 60:
        feedback = "🌡️  Warm. Getting closer."
    elif score >= 50:
        feedback = "🌤️  Lukewarm. Somewhat related."
    elif score >= 40:
        feedback = "❄️  Cool. Keep trying."
    elif score >= 30:
        feedback = "🧊 Cold. Different direction."
    else:
        feedback = "⛄ Freezing! Very unrelated."
    
    result = {
        'guess': guess_word,
        'score': score,
        'feedback': feedback,
        'guess_count': session['guess_count'],
        'found': found
    }
    
    if found:
        result['secret_word'] = secret_word
        result['time_taken'] = round(time.time() - session.get('start_time', time.time()))
    
    return jsonify(result)

@app.route('/hint', methods=['GET'])
def hint():
    if 'secret_word' not in session:
        return jsonify({'error': 'No word set yet'}), 400
    
    secret_word = session['secret_word']
    guess_count = session.get('guess_count', 0)
    
    # Provide hints based on number of guesses
    if guess_count < 10:
        hint = f"The word has {len(secret_word)} letters"
    elif guess_count < 20:
        hint = f"The word starts with '{secret_word[0]}'"
    elif guess_count < 30:
        hint = f"The word starts with '{secret_word[:2]}'"
    else:
        hint = f"The word is '{secret_word[:3]}...'"
    
    return jsonify({'hint': hint})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5004)

# For Vercel
app = app