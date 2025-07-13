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

def calculate_all_similarities(words):
    """Calculate similarity matrix for all word pairs"""
    similarities = {}
    for i, word1 in enumerate(words):
        for j, word2 in enumerate(words):
            if i < j:  # Only calculate once for each pair
                sim = calculate_similarity(word1, word2)
                similarities[f"{word1}-{word2}"] = sim
    return similarities

@app.route('/')
def index():
    return render_template('graph_semantle.html')

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
    
    # Calculate similarities between all guessed words
    all_words = session['guesses']
    pairwise_similarities = calculate_all_similarities(all_words)
    
    # Get scores for all guesses to the target
    all_scores = []
    for word in all_words:
        word_score = calculate_similarity(secret_word, word)
        all_scores.append({
            'word': word,
            'score': word_score
        })
    
    result = {
        'guess': guess_word,
        'score': score,
        'feedback': feedback,
        'guess_count': session['guess_count'],
        'found': found,
        'all_scores': all_scores,
        'pairwise_similarities': pairwise_similarities
    }
    
    if found:
        result['secret_word'] = secret_word
    
    return jsonify(result)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5003)