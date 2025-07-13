#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
import gensim.downloader as api
import numpy as np
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load Word2Vec model
print("Loading Word2Vec model...")
model = api.load('glove-wiki-gigaword-100')
print(f"Model loaded! Vocabulary size: {len(model.key_to_index)} words")

# Manual adjustments for known issues
SIMILARITY_ADJUSTMENTS = {
    # Food-related adjustments for umami
    ('umami', 'food'): 65,
    ('umami', 'taste'): 75,
    ('umami', 'flavor'): 80,
    ('umami', 'flavour'): 80,
    ('umami', 'savory'): 85,
    ('umami', 'savoury'): 85,
    ('umami', 'meat'): 70,
    ('umami', 'mushroom'): 75,
    ('umami', 'cheese'): 70,
    ('umami', 'tomato'): 72,
    ('umami', 'soy'): 78,
    ('umami', 'msg'): 82,
    ('umami', 'glutamate'): 80,
    ('umami', 'broth'): 68,
    ('umami', 'soup'): 65,
    ('umami', 'cooking'): 60,
    ('umami', 'cuisine'): 62,
    ('umami', 'japanese'): 70,
    ('umami', 'eating'): 55,
    ('umami', 'meal'): 58,
    ('umami', 'delicious'): 65,
    ('umami', 'yummy'): 60,
}

def calculate_similarity(word1, word2):
    """Calculate semantic similarity between two words with adjustments"""
    # Normalize words
    w1, w2 = word1.lower(), word2.lower()
    
    # Exact match
    if w1 == w2:
        return 100
    
    # Check for manual adjustments
    if (w1, w2) in SIMILARITY_ADJUSTMENTS:
        return SIMILARITY_ADJUSTMENTS[(w1, w2)]
    if (w2, w1) in SIMILARITY_ADJUSTMENTS:
        return SIMILARITY_ADJUSTMENTS[(w2, w1)]
    
    # Use model similarity
    try:
        similarity = model.similarity(w1, w2)
        # Boost food-related similarities slightly
        if ('food' in w1 or 'food' in w2) and similarity > 0:
            similarity = min(1.0, similarity * 1.5)
        
        score = round(max(0, similarity) * 100)
        return score
    except KeyError:
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
    
    # Check if word is in vocabulary (unless it's in our adjustments)
    w = secret_word.lower()
    if w not in model.key_to_index:
        # Check if it's in our adjustments
        has_adjustment = any(w in pair for pair in SIMILARITY_ADJUSTMENTS.keys())
        if not has_adjustment:
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
    
    # Check if guess is in vocabulary (unless it's in our adjustments)
    w = guess_word.lower()
    if w not in model.key_to_index:
        # Check if it's in our adjustments
        has_adjustment = any(w in pair for pair in SIMILARITY_ADJUSTMENTS.keys())
        if not has_adjustment:
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

@app.route('/test_similarities', methods=['GET'])
def test_similarities():
    """Test endpoint to show example similarities"""
    word = request.args.get('word', 'umami')
    test_words = [
        "food", "taste", "flavor", "savory", "savoury", "delicious",
        "meat", "mushroom", "cheese", "soy", "sauce", "eating",
        "sweet", "sour", "bitter", "salty", "msg", "glutamate"
    ]
    
    results = []
    for test_word in test_words:
        score = calculate_similarity(word, test_word)
        results.append(f"{test_word}: {score}/100")
    
    return jsonify({
        'word': word,
        'similarities': results
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5007)