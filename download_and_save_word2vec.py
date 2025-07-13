#!/usr/bin/env python3
"""Download and save Word2Vec model locally"""
import gensim.downloader as api
from gensim.models import KeyedVectors
import os

model_dir = "models"
model_path = os.path.join(model_dir, "word2vec-google-news-300.bin")

if os.path.exists(model_path):
    print(f"Model already exists at {model_path}")
    print("Loading to verify...")
    model = KeyedVectors.load(model_path)
    print(f"Model loaded successfully! Vocabulary size: {len(model.key_to_index)}")
else:
    print("Downloading Word2Vec Google News model (1.7GB)...")
    print("This will take several minutes but only needs to be done once...")
    
    # Download model
    model = api.load('word2vec-google-news-300')
    
    print("\nSaving model locally for faster loading...")
    model.save(model_path)
    print(f"Model saved to {model_path}")

# Test it
print("\nTesting word similarities:")
test_pairs = [
    ("cat", "dog"),
    ("king", "queen"),
    ("food", "eating"),
    ("umami", "taste"),
    ("umami", "food"),
    ("computer", "laptop")
]

for w1, w2 in test_pairs:
    try:
        sim = model.similarity(w1, w2)
        print(f"{w1:10} ↔ {w2:10} : {round(sim * 100)}/100")
    except KeyError as e:
        print(f"{w1:10} ↔ {w2:10} : Not in vocabulary")