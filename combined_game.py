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
    return render_template('combined.html')

@app.route('/set_words', methods=['POST'])
def set_words():
    data = request.json
    semantle_word = data.get('semantle_word', '').strip()
    antisemantle_word = data.get('antisemantle_word', '').strip()
    
    if not semantle_word or not antisemantle_word:
        return jsonify({'error': 'Please provide both words'}), 400
    
    session['semantle_word'] = semantle_word
    session['antisemantle_word'] = antisemantle_word
    session['guesses'] = []
    session['guess_count'] = 0
    
    return jsonify({'success': True})

@app.route('/guess', methods=['POST'])
def guess():
    if 'semantle_word' not in session or 'antisemantle_word' not in session:
        return jsonify({'error': 'No words set yet'}), 400
    
    data = request.json
    guess_word = data.get('guess', '').strip()
    
    if not guess_word:
        return jsonify({'error': 'Please provide a guess'}), 400
    
    semantle_word = session['semantle_word']
    antisemantle_word = session['antisemantle_word']
    
    # Calculate similarities
    semantle_score = calculate_similarity(semantle_word, guess_word)
    antisemantle_score = calculate_similarity(antisemantle_word, guess_word)
    antisemantle_distance = 100 - antisemantle_score
    
    session['guess_count'] = session.get('guess_count', 0) + 1
    session['guesses'] = session.get('guesses', []) + [{
        'word': guess_word,
        'semantle_score': semantle_score,
        'antisemantle_score': antisemantle_score,
        'antisemantle_distance': antisemantle_distance
    }]
    
    # Check wins
    semantle_won = guess_word.lower() == semantle_word.lower()
    antisemantle_won = guess_word.lower() == antisemantle_word.lower()
    
    # Get all guesses data for graphs
    all_guesses = session['guesses']
    
    # Feedback for Semantle
    if semantle_score == 100:
        semantle_feedback = "🎉 Found the Semantle word!"
    elif semantle_score >= 80:
        semantle_feedback = "🔥 Very hot!"
    elif semantle_score >= 60:
        semantle_feedback = "♨️ Hot!"
    elif semantle_score >= 40:
        semantle_feedback = "🌡️ Warm"
    elif semantle_score >= 20:
        semantle_feedback = "❄️ Cold"
    else:
        semantle_feedback = "🧊 Freezing"
    
    # Feedback for Antisemantle
    if antisemantle_won:
        antisemantle_feedback = "🎯 Found the Antisemantle word!"
    elif antisemantle_distance >= 80:
        antisemantle_feedback = "🌟 Excellent distance!"
    elif antisemantle_distance >= 60:
        antisemantle_feedback = "✨ Good distance"
    elif antisemantle_distance >= 40:
        antisemantle_feedback = "🔸 OK distance"
    elif antisemantle_distance >= 20:
        antisemantle_feedback = "⚠️ Too close!"
    else:
        antisemantle_feedback = "💥 Way too similar!"
    
    result = {
        'guess': guess_word,
        'semantle_score': semantle_score,
        'semantle_feedback': semantle_feedback,
        'antisemantle_distance': antisemantle_distance,
        'antisemantle_feedback': antisemantle_feedback,
        'guess_count': session['guess_count'],
        'semantle_won': semantle_won,
        'antisemantle_won': antisemantle_won,
        'all_guesses': all_guesses
    }
    
    if semantle_won:
        result['semantle_word'] = semantle_word
    if antisemantle_won:
        result['antisemantle_word'] = antisemantle_word
    
    return jsonify(result)

@app.route('/examples', methods=['GET'])
def examples():
    examples = [
        ("cat", "dog", "both are pets"),
        ("happy", "joyful", "synonyms"),
        ("hot", "cold", "opposites"),
        ("computer", "banana", "unrelated")
    ]
    
    results = []
    for word1, word2, desc in examples:
        similarity = calculate_similarity(word1, word2)
        distance = 100 - similarity
        results.append({
            'word1': word1,
            'word2': word2,
            'description': desc,
            'similarity': similarity,
            'distance': distance
        })
    
    return jsonify(results)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5002)