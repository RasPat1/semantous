#!/usr/bin/env python3
from gensim.models import KeyedVectors

# Load the Word2Vec model
print("Loading Word2Vec model...")
model = KeyedVectors.load("models/word2vec-google-news-300.bin")

# Find most similar words to umami
print("\nFinding 20 most similar words to 'umami':")
try:
    similar_words = model.most_similar('umami', topn=20)
    
    print("\nTop 20 words most similar to 'umami':")
    for i, (word, similarity) in enumerate(similar_words, 1):
        score = round(similarity * 100)
        print(f"{i:2d}. {word:20} : {score}/100")
        
except KeyError:
    print("'umami' not found in vocabulary")