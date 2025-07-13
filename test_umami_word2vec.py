#!/usr/bin/env python3
import gensim.downloader as api

print("Loading Word2Vec model...")
model = api.load('glove-wiki-gigaword-100')

print("\nTesting umami similarities with Word2Vec/GloVe:")
test_words = [
    "food", "taste", "flavor", "savory", "savoury", "delicious", 
    "meat", "mushroom", "cheese", "soy", "sauce", "eating",
    "sweet", "sour", "bitter", "salty", "yummy", "meal",
    "cook", "kitchen", "restaurant", "chef", "dish", "cuisine"
]

results = []
for word in test_words:
    try:
        sim = model.similarity("umami", word.lower())
        score = round(sim * 100)
        results.append((word, score))
    except KeyError:
        results.append((word, "Not in vocab"))

# Sort by score
results.sort(key=lambda x: x[1] if isinstance(x[1], int) else -1, reverse=True)

print("\nUmami similarity scores:")
for word, score in results:
    if isinstance(score, int):
        print(f"{word:15} : {score}/100")
    else:
        print(f"{word:15} : {score}")

# Check if umami is even in the vocabulary
try:
    _ = model["umami"]
    print("\n'umami' IS in the vocabulary")
except KeyError:
    print("\n'umami' is NOT in the vocabulary - this is the problem!")