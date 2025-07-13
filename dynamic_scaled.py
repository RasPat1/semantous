#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
from gensim.models import KeyedVectors
import numpy as np
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load Word2Vec model from local file
print("Loading Word2Vec model from local file...")
model_path = "models/word2vec-google-news-300.bin"
model = KeyedVectors.load(model_path)
print(f"Model loaded! Vocabulary size: {len(model.key_to_index)} words")

# Cache for closest word scores
closest_word_cache = {}

def get_closest_word_score(word):
    """Get the similarity score of the closest word to the given word"""
    if word in closest_word_cache:
        return closest_word_cache[word]
    
    try:
        # Get the most similar word (excluding itself)
        similar = model.most_similar(word, topn=1)
        if similar:
            closest_score = similar[0][1]  # Raw similarity score (0-1)
        else:
            closest_score = 0.5
    except:
        closest_score = 0.5
    
    closest_word_cache[word] = closest_score
    return closest_score

def calculate_similarity(word1, word2):
    """Calculate scaled semantic similarity between two words"""
    # Exact match gets 100
    if word1.lower() == word2.lower():
        return 100
    
    try:
        # Get raw similarity (-1 to 1, but usually 0 to 1 for words)
        raw_similarity = model.similarity(word1, word2)
        
        # Get the highest possible similarity for word1 (its closest neighbor)
        max_similarity = get_closest_word_score(word1)
        
        # Scale the similarity relative to the maximum
        # If raw_similarity = max_similarity, score = 99
        # If raw_similarity = 0, score = 0
        # We use 99 as max (not 100) to reserve 100 for exact matches
        
        if max_similarity > 0:
            # Scale from 0 to 99 based on ratio to maximum
            scaled_score = (raw_similarity / max_similarity) * 99
            # Ensure minimum score for any match is at least 1
            scaled_score = max(1, scaled_score)
        else:
            # Fallback to direct scaling
            scaled_score = max(0, raw_similarity) * 99
        
        return round(scaled_score)
        
    except KeyError:
        # If word not in vocabulary, return low similarity
        return 5

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
    
    # Check if word is in vocabulary
    if secret_word not in model.key_to_index:
        # Try lowercase
        if secret_word.lower() not in model.key_to_index:
            # Try title case
            if secret_word.title() not in model.key_to_index:
                return jsonify({'error': f'"{secret_word}" not in vocabulary. Try a different word.'}), 400
            else:
                secret_word = secret_word.title()
        else:
            secret_word = secret_word.lower()
    
    # Clear cache for new game
    closest_word_cache.clear()
    
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
    
    # Check if guess is in vocabulary
    original_guess = guess_word
    if guess_word not in model.key_to_index:
        # Try lowercase
        if guess_word.lower() in model.key_to_index:
            guess_word = guess_word.lower()
        # Try title case
        elif guess_word.title() in model.key_to_index:
            guess_word = guess_word.title()
        else:
            return jsonify({'error': f'"{original_guess}" not in vocabulary. Try a different word.'}), 400
    
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
    
    # Get feedback (adjusted for new scale)
    if score == 100:
        feedback = "🎉 Congratulations! You found the word!"
    elif score >= 90:
        feedback = "🔥 Extremely hot! Almost there!"
    elif score >= 80:
        feedback = "♨️  Very hot! Very close!"
    elif score >= 70:
        feedback = "🌡️  Hot! Getting warmer."
    elif score >= 60:
        feedback = "☀️  Warm. Good direction."
    elif score >= 50:
        feedback = "🌤️  Lukewarm. Somewhat related."
    elif score >= 40:
        feedback = "⛅ Cool. Keep exploring."
    elif score >= 30:
        feedback = "❄️  Cold. Try another angle."
    elif score >= 20:
        feedback = "🧊 Very cold. Different direction."
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

@app.route('/test_scaling', methods=['GET'])
def test_scaling():
    """Test the scaling system with a word"""
    word = request.args.get('word', 'umami')
    
    if word not in model.key_to_index:
        return jsonify({'error': 'Word not found'}), 404
    
    # Get top 10 similar words
    similar = model.most_similar(word, topn=10)
    
    # Calculate both raw and scaled scores
    results = []
    for similar_word, raw_score in similar:
        scaled_score = calculate_similarity(word, similar_word)
        results.append({
            'word': similar_word,
            'raw_score': round(raw_score * 100),
            'scaled_score': scaled_score
        })
    
    # Also test some random words
    test_words = ['food', 'computer', 'happy', 'taste', 'flavor']
    for test_word in test_words:
        if test_word in model.key_to_index:
            try:
                raw = model.similarity(word, test_word)
                scaled = calculate_similarity(word, test_word)
                results.append({
                    'word': test_word,
                    'raw_score': round(raw * 100),
                    'scaled_score': scaled
                })
            except:
                pass
    
    return jsonify({
        'target_word': word,
        'max_raw_score': round(similar[0][1] * 100) if similar else 0,
        'similarities': results
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5009)