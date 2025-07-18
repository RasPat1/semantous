#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import gensim.downloader as api
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'semantle-dynamic-graph-' + str(random.randint(1000, 9999)))

# Enable CORS for frontend development
CORS(app, supports_credentials=True, origins='*', allow_headers='*')

# Initialize models
print("Loading Sentence-BERT model...")
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Sentence-BERT loaded!")

word2vec_model = None
glove_model = None

# Cache for embeddings and similarities
embedding_cache = {}
similarity_cache = {}

def load_models():
    """Load Word2Vec and GloVe models on demand"""
    global word2vec_model, glove_model
    
    if word2vec_model is None:
        try:
            print("Loading Word2Vec model...")
            word2vec_model = api.load('word2vec-google-news-300')
            print("Word2Vec loaded!")
        except:
            print("Failed to load Word2Vec model")
    
    if glove_model is None:
        try:
            print("Loading GloVe model...")
            glove_model = api.load('glove-wiki-gigaword-100')
            print("GloVe loaded!")
        except:
            print("Failed to load GloVe model")

def get_conceptnet_similarity(word1, word2):
    """Get similarity from ConceptNet API"""
    try:
        url = f"http://api.conceptnet.io/relatedness?node1=/c/en/{word1}&node2=/c/en/{word2}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Convert from [-1, 1] to [0, 100]
            return (data.get('value', 0) + 1) * 50
    except:
        pass
    return 0

def get_sentence_bert_similarity(word1, word2):
    """Get similarity using Sentence-BERT"""
    # Get embeddings from cache or compute
    if word1 not in embedding_cache:
        embedding_cache[word1] = sentence_model.encode([word1])[0]
    if word2 not in embedding_cache:
        embedding_cache[word2] = sentence_model.encode([word2])[0]
    
    # Calculate cosine similarity
    emb1 = embedding_cache[word1]
    emb2 = embedding_cache[word2]
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return similarity * 100

def get_word2vec_similarity(word1, word2):
    """Get similarity using Word2Vec"""
    if word2vec_model is None:
        load_models()
    
    try:
        if word2vec_model and word1 in word2vec_model and word2 in word2vec_model:
            similarity = word2vec_model.similarity(word1, word2)
            # Convert from [-1, 1] to [0, 100]
            return (similarity + 1) * 50
    except:
        pass
    return 0

def get_glove_similarity(word1, word2):
    """Get similarity using GloVe"""
    if glove_model is None:
        load_models()
    
    try:
        if glove_model and word1 in glove_model and word2 in glove_model:
            similarity = glove_model.similarity(word1, word2)
            # Convert from [-1, 1] to [0, 100]
            return (similarity + 1) * 50
    except:
        pass
    return 0

def calculate_similarity(word1, word2, model='sentence-bert'):
    """Calculate similarity between two words using specified model"""
    # Check cache first
    cache_key = f"{model}:{word1}:{word2}"
    cache_key_reverse = f"{model}:{word2}:{word1}"
    
    if cache_key in similarity_cache:
        return similarity_cache[cache_key]
    if cache_key_reverse in similarity_cache:
        return similarity_cache[cache_key_reverse]
    
    # Calculate based on model
    if model == 'conceptnet':
        similarity = get_conceptnet_similarity(word1, word2)
    elif model == 'sentence-bert':
        similarity = get_sentence_bert_similarity(word1, word2)
    elif model == 'word2vec':
        similarity = get_word2vec_similarity(word1, word2)
    elif model == 'glove':
        similarity = get_glove_similarity(word1, word2)
    else:
        similarity = 0
    
    # Cache the result
    similarity_cache[cache_key] = similarity
    return similarity

def calculate_all_similarities(words, target_word, model='sentence-bert'):
    """Calculate similarities between all words and create graph data"""
    nodes = []
    links = []
    
    # Add target node
    nodes.append({
        'id': target_word,
        'label': '?',
        'score': 100,
        'isTarget': True,
        'group': 'target'
    })
    
    # Add guess nodes and calculate their similarities to target
    for word in words:
        if word != target_word:
            score = calculate_similarity(word, target_word, model)
            nodes.append({
                'id': word,
                'label': word,
                'score': score,
                'isTarget': False,
                'group': 'guess'
            })
    
    # For each non-target node, find its best connection
    for i, node in enumerate(nodes):
        if not node['isTarget']:
            best_target = None
            best_similarity = -1
            
            # Check similarity with all other nodes
            for j, other_node in enumerate(nodes):
                if i != j:  # Don't connect to self
                    similarity = calculate_similarity(node['id'], other_node['id'], model)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_target = other_node['id']
            
            # Create link to best match
            if best_target:
                links.append({
                    'source': node['id'],
                    'target': best_target,
                    'value': best_similarity,
                    'type': 'best-match'
                })
    
    return {'nodes': nodes, 'links': links}

@app.route('/')
def index():
    # Initialize session
    if 'target_word' not in session:
        session['target_word'] = None
        session['guesses'] = []
        session['guess_count'] = 0
        session['current_model'] = 'sentence-bert'
    
    return render_template('dynamic_semantle.html')

@app.route('/set_word', methods=['POST'])
def set_word():
    data = request.json
    word = data.get('word', '').lower().strip()
    
    if word:
        # Reset game state
        session['target_word'] = word
        session['guesses'] = []
        session['guess_count'] = 0
        session['current_model'] = data.get('model', 'sentence-bert')
        
        # Clear caches for new game
        global similarity_cache, embedding_cache
        similarity_cache = {}
        embedding_cache = {}
        
        return jsonify({'success': True, 'message': f'Secret word set to "{word}"'})
    
    return jsonify({'success': False, 'error': 'Invalid word'}), 400

@app.route('/guess', methods=['POST'])
def guess():
    if not session.get('target_word'):
        return jsonify({'error': 'No target word set'}), 400
    
    data = request.json
    guess_word = data.get('word', '').lower().strip()
    model = data.get('model', session.get('current_model', 'sentence-bert'))
    
    if not guess_word:
        return jsonify({'error': 'Invalid guess'}), 400
    
    # Check if already guessed
    if guess_word in session['guesses']:
        return jsonify({'error': 'Already guessed'}), 400
    
    # Update model if changed
    session['current_model'] = model
    
    # Add to guesses
    session['guesses'].append(guess_word)
    session['guess_count'] += 1
    
    # Check if correct
    if guess_word == session['target_word']:
        return jsonify({
            'correct': True,
            'word': guess_word,
            'score': 100,
            'guess_count': session['guess_count'],
            'graph_data': calculate_all_similarities(session['guesses'], session['target_word'], model)
        })
    
    # Calculate similarity
    score = calculate_similarity(guess_word, session['target_word'], model)
    
    # Get updated graph data
    graph_data = calculate_all_similarities(session['guesses'], session['target_word'], model)
    
    return jsonify({
        'correct': False,
        'word': guess_word,
        'score': score,
        'guess_count': session['guess_count'],
        'graph_data': graph_data
    })

@app.route('/calculate_similarities', methods=['POST'])
def calculate_similarities():
    """Recalculate all similarities with a new model"""
    if not session.get('target_word'):
        return jsonify({'error': 'No game in progress'}), 400
    
    data = request.json
    model = data.get('model', 'sentence-bert')
    
    # Update current model
    session['current_model'] = model
    
    # Recalculate all similarities
    graph_data = calculate_all_similarities(session['guesses'], session['target_word'], model)
    
    # Also return updated scores for guess history
    guess_scores = []
    for guess in session['guesses']:
        score = calculate_similarity(guess, session['target_word'], model)
        guess_scores.append({
            'word': guess,
            'score': score,
            'correct': guess == session['target_word']
        })
    
    return jsonify({
        'graph_data': graph_data,
        'guess_scores': guess_scores,
        'model': model
    })

@app.route('/hint', methods=['GET'])
def hint():
    if not session.get('target_word'):
        return jsonify({'error': 'No target word set'}), 400
    
    guess_count = session.get('guess_count', 0)
    target = session['target_word']
    
    # Progressive hints based on guess count
    if guess_count < 10:
        hint = f"The word has {len(target)} letters"
    elif guess_count < 20:
        hint = f"The word starts with '{target[0]}'"
    elif guess_count < 30:
        hint = f"The word starts with '{target[:2]}'"
    else:
        hint = f"The word is '{target[:3]}...'"
    
    return jsonify({'hint': hint, 'guess_count': guess_count})

if __name__ == '__main__':
    app.run(debug=True, port=5001)