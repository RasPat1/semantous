#!/usr/bin/env python3
import gensim.downloader as api

print("Downloading Word2Vec Google News model...")
print("This is 1.7GB and will give the best word similarities")
print("It may take 5-10 minutes depending on your connection...")
print("")

# Download the best model
model = api.load('word2vec-google-news-300')

print("\nModel downloaded successfully!")
print(f"Vocabulary size: {len(model.key_to_index)} words")

# Test umami similarities
print("\nTesting 'umami' similarities with the better model:")
test_words = ["food", "taste", "flavor", "savory", "delicious", "meat", "mushroom", "cheese"]

for word in test_words:
    try:
        sim = model.similarity("umami", word)
        print(f"{word:12} : {round(sim * 100)}/100")
    except KeyError:
        print(f"{word:12} : Not in vocabulary")