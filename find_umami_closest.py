#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
import numpy as np

# Target word
target_word = "umami"

# Large vocabulary of words to compare against
vocabulary = [
    # Tastes and flavors
    "sweet", "sour", "bitter", "salty", "savory", "taste", "flavor", "delicious", "tasty",
    "spicy", "tangy", "pungent", "mild", "rich", "robust", "zesty", "bland", "astringent",
    
    # Food items that might have umami
    "mushroom", "tomato", "cheese", "meat", "soy", "sauce", "broth", "stock", "soup",
    "seaweed", "kelp", "fish", "seafood", "beef", "pork", "chicken", "bacon", "parmesan",
    "miso", "tofu", "tempeh", "nori", "kombu", "dashi", "oyster", "anchovy", "sardine",
    
    # Cooking and culinary terms
    "cooking", "cuisine", "recipe", "ingredient", "seasoning", "spice", "herb", "marinade",
    "fermented", "aged", "cured", "smoked", "grilled", "roasted", "braised", "simmered",
    
    # Asian cuisine terms
    "Japanese", "Asian", "Chinese", "Korean", "Thai", "Vietnamese", "ramen", "sushi",
    "teriyaki", "wasabi", "ginger", "garlic", "sesame", "rice", "noodle", "wok", "stir-fry",
    
    # Scientific/chemical terms
    "glutamate", "MSG", "monosodium", "amino", "acid", "protein", "enzyme", "fermentation",
    "chemical", "compound", "molecule", "receptor", "tongue", "palate", "gustatory",
    
    # Sensory and descriptive words
    "sensation", "perception", "aroma", "smell", "texture", "mouthfeel", "aftertaste",
    "complex", "deep", "intense", "subtle", "balanced", "harmonious", "layered", "nuanced",
    
    # Other basic tastes comparison
    "sweetness", "sourness", "bitterness", "saltiness", "savoury", "yummy", "appetizing",
    "delectable", "scrumptious", "palatable", "flavorful", "aromatic", "fragrant",
    
    # General food words
    "food", "meal", "dish", "cuisine", "eating", "dining", "gourmet", "culinary",
    "gastronomy", "epicurean", "foodie", "chef", "kitchen", "restaurant", "menu",
    
    # More specific umami-rich foods
    "truffle", "shiitake", "porcini", "portobello", "romano", "gruyere", "roquefort",
    "prosciutto", "salami", "kimchi", "sauerkraut", "pickled", "vinegar", "balsamic",
    
    # Unrelated words for contrast
    "car", "house", "computer", "mountain", "happiness", "democracy", "mathematics",
    "purple", "running", "book", "window", "telephone", "guitar", "painting", "cloud"
]

print(f"Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Computing embedding for '{target_word}'...")
target_embedding = model.encode([target_word])[0]

print(f"Computing embeddings for {len(vocabulary)} comparison words...")
vocab_embeddings = model.encode(vocabulary)

# Calculate similarities
print("Calculating similarities...")
similarities = []

for word, embedding in zip(vocabulary, vocab_embeddings):
    # Cosine similarity
    cosine_sim = np.dot(target_embedding, embedding) / (np.linalg.norm(target_embedding) * np.linalg.norm(embedding))
    similarity_score = round(max(0, cosine_sim) * 100)
    similarities.append((word, similarity_score))

# Sort by similarity (highest first)
similarities.sort(key=lambda x: x[1], reverse=True)

print(f"\n=== TOP 100 WORDS CLOSEST TO '{target_word.upper()}' ===")
print("(Higher scores = more similar in meaning)\n")

for i, (word, score) in enumerate(similarities[:100], 1):
    print(f"{i:3d}. {word:20s} : {score}/100")

print(f"\n=== BOTTOM 20 WORDS MOST DISTANT FROM '{target_word.upper()}' ===")
print("(These would score highest against 'umami' in Antisemantle!)\n")

for i, (word, score) in enumerate(similarities[-20:], 1):
    distance = 100 - score
    print(f"{i:3d}. {word:20s} : {distance}/100 distance ({score}/100 similarity)")