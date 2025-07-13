#!/usr/bin/env python3
"""Download and test Word2Vec model"""
import gensim.downloader as api

print("Available Word2Vec models:")
print("1. word2vec-google-news-300 (1.7GB) - Best quality, 3 million words")
print("2. glove-wiki-gigaword-100 (128MB) - Good quality, smaller")
print("3. glove-wiki-gigaword-50 (65MB) - Decent quality, very small")
print("4. glove-twitter-25 (104MB) - Twitter-trained, casual language")

print("\nDownloading glove-wiki-gigaword-100 (recommended balance of quality/size)...")
print("This will take a few minutes on first download...")

# Download the model
model = api.load('glove-wiki-gigaword-100')

print("\nModel loaded successfully!")
print(f"Vocabulary size: {len(model.key_to_index)} words")

# Test some word similarities
print("\nTesting word similarities:")
test_pairs = [
    ("cat", "dog"),
    ("cat", "kitten"),
    ("king", "queen"),
    ("happy", "joyful"),
    ("computer", "laptop"),
    ("hot", "cold")
]

for word1, word2 in test_pairs:
    try:
        similarity = model.similarity(word1, word2)
        print(f"{word1:10} ↔ {word2:10} : {round(similarity * 100)}/100")
    except KeyError as e:
        print(f"{word1:10} ↔ {word2:10} : Word not in vocabulary")

print("\nTesting word analogies:")
print("king - man + woman = ?")
try:
    result = model.most_similar(positive=['king', 'woman'], negative=['man'], topn=1)
    print(f"Result: {result[0][0]} (similarity: {round(result[0][1] * 100)}/100)")
except KeyError:
    print("Some words not in vocabulary")

print("\nModel ready to use!")