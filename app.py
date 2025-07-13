#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
from sentence_transformers import SentenceTransformer
import numpy as np
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load model once at startup
print("Loading language model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!")

def calculate_similarity(word1, word2):
    """Calculate semantic similarity between two words"""
    embedding1 = model.encode([word1])[0]
    embedding2 = model.encode([word2])[0]
    
    cosine_sim = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    score = round(max(0, cosine_sim) * 100)
    
    # Exact match gets 100
    if word1.lower() == word2.lower():
        score = 100
    
    return score

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_word', methods=['POST'])
def set_word():
    data = request.json
    secret_word = data.get('word', '').strip()
    
    if not secret_word:
        return jsonify({'error': 'Please provide a word'}), 400
    
    session['secret_word'] = secret_word
    session['guesses'] = []
    session['guess_count'] = 0
    
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
    score = calculate_similarity(secret_word, guess_word)
    
    session['guess_count'] = session.get('guess_count', 0) + 1
    
    # Get feedback
    if score == 100:
        feedback = "🎉 Congratulations! You found the word!"
    elif score >= 80:
        feedback = "🔥 Very hot! Extremely similar meaning!"
    elif score >= 70:
        feedback = "♨️  Hot! Very close semantically!"
    elif score >= 60:
        feedback = "🌡️  Warm. Related concept."
    elif score >= 50:
        feedback = "🌤️  Lukewarm. Somewhat related."
    elif score >= 40:
        feedback = "❄️  Cool. Distant connection."
    elif score >= 30:
        feedback = "🧊 Cold. Very different meaning."
    else:
        feedback = "⛄ Freezing! Completely unrelated."
    
    result = {
        'guess': guess_word,
        'score': score,
        'feedback': feedback,
        'guess_count': session['guess_count'],
        'found': score == 100
    }
    
    if score == 100:
        result['secret_word'] = secret_word
    
    return jsonify(result)

@app.route('/examples', methods=['GET'])
def examples():
    examples = [
        ("cat", "dog", "both are pets"),
        ("happy", "joyful", "synonyms"),
        ("car", "automobile", "same thing"),
        ("hot", "cold", "opposites"),
        ("king", "queen", "related concepts"),
        ("computer", "banana", "unrelated")
    ]
    
    results = []
    for word1, word2, desc in examples:
        score = calculate_similarity(word1, word2)
        results.append({
            'word1': word1,
            'word2': word2,
            'description': desc,
            'score': score
        })
    
    return jsonify(results)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5000)