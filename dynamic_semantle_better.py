#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
import gensim.downloader as api
import numpy as np
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load better Word2Vec model
print("Loading Word2Vec Google News model (this is 1.7GB, may take a few minutes on first run)...")
print("This model has much better word relationships than GloVe-100...")
model = api.load('word2vec-google-news-300')
print(f"Model loaded! Vocabulary size: {len(model.key_to_index)} words")

def calculate_similarity(word1, word2):
    """Calculate semantic similarity between two words"""
    try:
        # Word2Vec similarity (0 to 1)
        similarity = model.similarity(word1.lower(), word2.lower())
        # Convert to 0-100 scale
        score = round(max(0, similarity) * 100)
        
        # Exact match gets 100
        if word1.lower() == word2.lower():
            score = 100
            
        return score
    except KeyError:
        # Try with original case if lowercase fails
        try:
            similarity = model.similarity(word1, word2)
            score = round(max(0, similarity) * 100)
            if word1.lower() == word2.lower():
                score = 100
            return score
        except KeyError:
            # If word not in vocabulary, return low similarity
            return 10

def find_most_similar_node(new_word, existing_nodes):
    """Find which existing node is most similar to the new word"""
    max_similarity = -1
    most_similar = None
    
    for node in existing_nodes:
        sim = calculate_similarity(new_word, node['word'])
        if sim > max_similarity:
            max_similarity = sim
            most_similar = node['word']
    
    return most_similar, max_similarity

def rebuild_connections(nodes):
    """Rebuild all connections so each node connects to its most similar neighbor"""
    connections = []
    
    for node in nodes:
        if node['isSecret']:
            continue  # Secret word doesn't connect to others
        
        # Find most similar node
        max_sim = -1
        best_target = None
        
        for other in nodes:
            if other['word'] == node['word']:
                continue
            
            sim = calculate_similarity(node['word'], other['word'])
            if sim > max_sim:
                max_sim = sim
                best_target = other['word']
        
        if best_target:
            connections.append({
                'source': node['word'],
                'target': best_target,
                'similarity': max_sim
            })
    
    return connections

@app.route('/')
def index():
    return render_template('dynamic_semantle.html')

@app.route('/set_word', methods=['POST'])
def set_word():
    data = request.json
    secret_word = data.get('word', '').strip()
    
    if not secret_word:
        return jsonify({'error': 'Please provide a word'}), 400
    
    # Check if word is in vocabulary (try both cases)
    if secret_word.lower() not in model.key_to_index and secret_word not in model.key_to_index:
        return jsonify({'error': f'"{secret_word}" not in vocabulary. Try a more common word.'}), 400
    
    session['secret_word'] = secret_word
    session['nodes'] = [{'word': secret_word, 'isSecret': True, 'score': 100}]
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
    
    # Check if guess is in vocabulary (try both cases)
    if guess_word.lower() not in model.key_to_index and guess_word not in model.key_to_index:
        return jsonify({'error': f'"{guess_word}" not in vocabulary. Try a more common word.'}), 400
    
    secret_word = session['secret_word']
    score = calculate_similarity(secret_word, guess_word)
    
    session['guess_count'] = session.get('guess_count', 0) + 1
    
    # Add new node
    new_node = {
        'word': guess_word,
        'isSecret': False,
        'score': score  # Similarity to secret word
    }
    
    nodes = session.get('nodes', [])
    nodes.append(new_node)
    session['nodes'] = nodes
    
    # Rebuild all connections
    connections = rebuild_connections(nodes)
    
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
        'found': found,
        'nodes': nodes,
        'connections': connections
    }
    
    if found:
        result['secret_word'] = secret_word
    
    return jsonify(result)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5006)