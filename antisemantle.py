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

def get_elimination_score(secret_word, guesses):
    """Calculate how well the guesses eliminate the secret word"""
    if not guesses:
        return 0
    
    # Get average similarity of secret word to all guesses
    similarities = []
    for guess in guesses:
        sim = calculate_similarity(secret_word, guess)
        similarities.append(sim)
    
    # The lower the average similarity, the better the elimination
    avg_similarity = np.mean(similarities)
    elimination_score = 100 - avg_similarity
    
    return round(elimination_score)

@app.route('/')
def antisemantle():
    return render_template('antisemantle.html')

@app.route('/set_word', methods=['POST'])
def set_word():
    data = request.json
    secret_word = data.get('word', '').strip()
    
    if not secret_word:
        return jsonify({'error': 'Please provide a word'}), 400
    
    session['secret_word'] = secret_word
    session['guesses'] = []
    session['guess_count'] = 0
    session['eliminated_spaces'] = []
    
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
    
    # Calculate similarity to secret word
    similarity = calculate_similarity(secret_word, guess_word)
    
    # In Antisemantle, lower similarity is better!
    distance_score = 100 - similarity
    
    session['guess_count'] = session.get('guess_count', 0) + 1
    session['guesses'] = session.get('guesses', []) + [guess_word]
    
    # Check if found (exact match)
    found = guess_word.lower() == secret_word.lower()
    
    # Calculate elimination progress
    elimination_score = get_elimination_score(secret_word, session['guesses'])
    
    # Get feedback based on distance
    if found:
        feedback = "🎯 Found it! The most distant word!"
    elif distance_score >= 90:
        feedback = "🌟 Excellent! Nearly orthogonal semantic space!"
    elif distance_score >= 80:
        feedback = "💫 Great! Very distant meaning!"
    elif distance_score >= 70:
        feedback = "✨ Good! Quite unrelated!"
    elif distance_score >= 60:
        feedback = "🔸 Decent. Somewhat distant."
    elif distance_score >= 50:
        feedback = "🔶 OK. Could be more distant."
    elif distance_score >= 40:
        feedback = "⚠️  Careful! Getting too related."
    elif distance_score >= 30:
        feedback = "🔥 Too close! Very related meaning!"
    else:
        feedback = "💥 Way too similar! Try opposite concepts!"
    
    # Generate hint about eliminated spaces
    eliminated_concepts = []
    for g in session['guesses']:
        if calculate_similarity(secret_word, g) < 30:  # Very unrelated
            eliminated_concepts.append(g)
    
    # Get all guesses with their distances for the graph
    all_guesses_data = []
    for g in session['guesses']:
        dist = 100 - calculate_similarity(secret_word, g)
        all_guesses_data.append({
            'word': g,
            'distance': dist
        })
    
    result = {
        'guess': guess_word,
        'distance_score': distance_score,
        'similarity': similarity,
        'feedback': feedback,
        'guess_count': session['guess_count'],
        'elimination_score': elimination_score,
        'found': found,
        'eliminated_concepts': eliminated_concepts[-5:],  # Last 5 good eliminations
        'total_guesses': len(session['guesses']),
        'all_guesses': all_guesses_data
    }
    
    if found:
        result['secret_word'] = secret_word
    
    return jsonify(result)

@app.route('/hint', methods=['GET'])
def hint():
    if 'secret_word' not in session or 'guesses' not in session:
        return jsonify({'error': 'No game in progress'}), 400
    
    guesses = session.get('guesses', [])
    if len(guesses) < 5:
        return jsonify({'hint': 'Make at least 5 guesses first!'})
    
    secret_word = session['secret_word']
    
    # Find semantic categories to avoid
    categories_to_avoid = []
    for guess in guesses:
        sim = calculate_similarity(secret_word, guess)
        if sim < 30:
            categories_to_avoid.append(guess)
    
    hint_text = f"The word is semantically distant from: {', '.join(categories_to_avoid[-3:])}"
    
    return jsonify({'hint': hint_text})

@app.route('/examples', methods=['GET'])
def examples():
    # Example showing distance scores
    examples = [
        ("computer", "banana", "unrelated concepts"),
        ("hot", "cold", "opposites"),
        ("king", "democracy", "contrasting ideas"),
        ("ocean", "desert", "opposite environments"),
        ("love", "algorithm", "emotion vs logic"),
        ("cat", "dog", "too similar!")
    ]
    
    results = []
    for word1, word2, desc in examples:
        similarity = calculate_similarity(word1, word2)
        distance = 100 - similarity
        results.append({
            'word1': word1,
            'word2': word2,
            'description': desc,
            'distance_score': distance,
            'similarity': similarity
        })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)