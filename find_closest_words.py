#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
import numpy as np
from itertools import combinations

# Common English words to test
common_words = [
    # Animals
    "cat", "dog", "bird", "fish", "horse", "cow", "pig", "sheep", "mouse", "rabbit",
    # Food
    "apple", "banana", "bread", "milk", "cheese", "meat", "vegetable", "fruit", "pizza", "pasta",
    # Colors
    "red", "blue", "green", "yellow", "black", "white", "purple", "orange", "pink", "brown",
    # Emotions
    "happy", "sad", "angry", "excited", "scared", "love", "hate", "joy", "fear", "peace",
    # Actions
    "run", "walk", "jump", "swim", "fly", "eat", "sleep", "work", "play", "think",
    # Objects
    "car", "house", "book", "phone", "computer", "chair", "table", "door", "window", "tree",
    # Weather
    "rain", "sun", "snow", "wind", "cloud", "storm", "hot", "cold", "warm", "cool",
    # Time
    "day", "night", "morning", "evening", "hour", "minute", "second", "week", "month", "year",
    # Family
    "mother", "father", "sister", "brother", "child", "parent", "family", "baby", "wife", "husband",
    # Body
    "hand", "foot", "head", "eye", "ear", "nose", "mouth", "arm", "leg", "heart",
    # Nature
    "ocean", "mountain", "river", "forest", "desert", "beach", "lake", "island", "valley", "hill",
    # Abstract
    "time", "space", "life", "death", "truth", "lie", "good", "bad", "right", "wrong",
    # Professions
    "doctor", "teacher", "student", "lawyer", "engineer", "artist", "writer", "singer", "actor", "chef",
    # Places
    "home", "school", "office", "store", "hospital", "restaurant", "park", "city", "country", "world"
]

print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Computing embeddings for {len(common_words)} words...")
embeddings = model.encode(common_words)

# Calculate all pairwise similarities
print("Calculating pairwise similarities...")
similarities = []

for i, (word1, emb1) in enumerate(zip(common_words, embeddings)):
    for j, (word2, emb2) in enumerate(zip(common_words, embeddings)):
        if i < j:  # Avoid duplicates and self-comparison
            # Cosine similarity
            cosine_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            similarity_score = round(max(0, cosine_sim) * 100)
            similarities.append((word1, word2, similarity_score))

# Sort by similarity (highest first)
similarities.sort(key=lambda x: x[2], reverse=True)

print("\n=== TOP 100 CLOSEST WORD PAIRS ===")
print("(Higher scores = more similar in meaning)\n")

for i, (word1, word2, score) in enumerate(similarities[:100], 1):
    print(f"{i:3d}. {word1:15s} ↔ {word2:15s} : {score}/100")

print("\n=== BOTTOM 20 MOST DISTANT WORD PAIRS ===")
print("(These would score highest in Antisemantle!)\n")

for i, (word1, word2, score) in enumerate(similarities[-20:], 1):
    distance = 100 - score
    print(f"{i:3d}. {word1:15s} ↔ {word2:15s} : {distance}/100 distance ({score}/100 similarity)")