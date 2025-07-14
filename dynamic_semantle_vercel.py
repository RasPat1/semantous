from flask import Flask, render_template, request, jsonify, session
import requests
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'semantle-dynamic-graph-' + str(random.randint(1000, 9999)))

# Cache for similarities
similarity_cache = {}

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
    return random.randint(10, 30)  # Fallback random similarity

def calculate_similarity(word1, word2):
    """Calculate similarity between two words"""
    # Check cache first
    cache_key = f"{word1}:{word2}"
    cache_key_reverse = f"{word2}:{word1}"
    
    if cache_key in similarity_cache:
        return similarity_cache[cache_key]
    if cache_key_reverse in similarity_cache:
        return similarity_cache[cache_key_reverse]
    
    # Calculate similarity
    similarity = get_conceptnet_similarity(word1, word2)
    
    # Cache the result
    similarity_cache[cache_key] = similarity
    return similarity

def calculate_all_similarities(words, target_word):
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
            score = calculate_similarity(word, target_word)
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
                    similarity = calculate_similarity(node['id'], other_node['id'])
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
        
        # Clear cache for new game
        global similarity_cache
        similarity_cache = {}
        
        return jsonify({'success': True, 'message': f'Secret word set to "{word}"'})
    
    return jsonify({'success': False, 'error': 'Invalid word'}), 400

@app.route('/guess', methods=['POST'])
def guess():
    if not session.get('target_word'):
        return jsonify({'error': 'No target word set'}), 400
    
    data = request.json
    guess_word = data.get('word', '').lower().strip()
    
    if not guess_word:
        return jsonify({'error': 'Invalid guess'}), 400
    
    # Check if already guessed
    if guess_word in session['guesses']:
        return jsonify({'error': 'Already guessed'}), 400
    
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
            'graph_data': calculate_all_similarities(session['guesses'], session['target_word'])
        })
    
    # Calculate similarity
    score = calculate_similarity(guess_word, session['target_word'])
    
    # Get updated graph data
    graph_data = calculate_all_similarities(session['guesses'], session['target_word'])
    
    return jsonify({
        'correct': False,
        'word': guess_word,
        'score': score,
        'guess_count': session['guess_count'],
        'graph_data': graph_data
    })

@app.route('/calculate_similarities', methods=['POST'])
def calculate_similarities():
    """Recalculate all similarities (for ConceptNet only version, this is the same)"""
    if not session.get('target_word'):
        return jsonify({'error': 'No game in progress'}), 400
    
    # Recalculate all similarities
    graph_data = calculate_all_similarities(session['guesses'], session['target_word'])
    
    # Also return updated scores for guess history
    guess_scores = []
    for guess in session['guesses']:
        score = calculate_similarity(guess, session['target_word'])
        guess_scores.append({
            'word': guess,
            'score': score,
            'correct': guess == session['target_word']
        })
    
    return jsonify({
        'graph_data': graph_data,
        'guess_scores': guess_scores,
        'model': 'conceptnet'
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
    app.run(debug=True)