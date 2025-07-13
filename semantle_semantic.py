#!/usr/bin/env python3
import sys
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers"])
    from sentence_transformers import SentenceTransformer
    import numpy as np

class SemanticSemantleGame:
    def __init__(self):
        print("Loading language model (this may take a moment on first run)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.secret_word = None
        self.secret_embedding = None
        self.guesses = []
        print("Model loaded!\n")
        
    def calculate_similarity(self, word1, word2):
        """Calculate semantic similarity between two words (0-100)"""
        # Get embeddings
        embedding1 = self.model.encode([word1])[0]
        embedding2 = self.model.encode([word2])[0]
        
        # Calculate cosine similarity
        cosine_sim = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        # Convert to 0-100 scale
        # Cosine similarity ranges from -1 to 1, but for words it's usually 0 to 1
        score = max(0, cosine_sim) * 100
        
        return round(score)
    
    def get_feedback(self, score):
        """Provide feedback based on score"""
        if score == 100:
            return "🎉 Congratulations! You found the word!"
        elif score >= 80:
            return "🔥 Very hot! Extremely similar meaning!"
        elif score >= 70:
            return "♨️  Hot! Very close semantically!"
        elif score >= 60:
            return "🌡️  Warm. Related concept."
        elif score >= 50:
            return "🌤️  Lukewarm. Somewhat related."
        elif score >= 40:
            return "❄️  Cool. Distant connection."
        elif score >= 30:
            return "🧊 Cold. Very different meaning."
        else:
            return "⛄ Freezing! Completely unrelated."
    
    def show_examples(self):
        """Show example similarity scores"""
        print("\n=== Example Similarity Scores ===")
        examples = [
            ("cat", "dog", "both are pets"),
            ("happy", "joyful", "synonyms"),
            ("car", "automobile", "same thing"),
            ("hot", "cold", "opposites"),
            ("king", "queen", "related concepts"),
            ("computer", "banana", "unrelated")
        ]
        
        for word1, word2, desc in examples:
            score = self.calculate_similarity(word1, word2)
            print(f"{word1} ↔ {word2}: {score}/100 ({desc})")
        print()
    
    def play(self):
        print("\n=== Welcome to Semantic Semantle! ===")
        print("This version uses AI to measure meaning similarity between words.")
        print("I'll give you a score from 0-100 based on how similar the meanings are.\n")
        
        # Show examples
        show_ex = input("Would you like to see example scores? (y/n): ").lower()
        if show_ex == 'y':
            self.show_examples()
        
        # Get secret word from player 1
        print("Player 1: Please enter the secret word (it will be hidden):")
        self.secret_word = input().strip()
        self.secret_embedding = self.model.encode([self.secret_word])[0]
        
        # Clear screen
        print("\033[2J\033[H")
        
        print("=== The word has been set! ===")
        print("Player 2: Start guessing! Type 'quit' to exit.")
        print("Tip: Think about meaning, not spelling!\n")
        
        guess_count = 0
        best_score = 0
        best_guess = ""
        
        while True:
            guess = input(f"Guess #{guess_count + 1}: ").strip()
            
            if guess.lower() == 'quit':
                print(f"\nThe word was: {self.secret_word}")
                break
            
            if not guess:
                print("Please enter a word.")
                continue
            
            # Calculate semantic similarity
            guess_embedding = self.model.encode([guess])[0]
            cosine_sim = np.dot(self.secret_embedding, guess_embedding) / (
                np.linalg.norm(self.secret_embedding) * np.linalg.norm(guess_embedding)
            )
            score = round(max(0, cosine_sim) * 100)
            
            # Check for exact match
            if guess.lower() == self.secret_word.lower():
                score = 100
            
            feedback = self.get_feedback(score)
            
            guess_count += 1
            self.guesses.append((guess, score))
            
            # Track best guess
            if score > best_score and score < 100:
                best_score = score
                best_guess = guess
            
            print(f"Similarity: {score}/100 - {feedback}")
            
            if score == 100:
                print(f"\nYou got it in {guess_count} guesses!")
                break
            
            # Show progress every 5 guesses
            if guess_count % 5 == 0 and best_score > 0:
                print(f"\nYour best guess so far: '{best_guess}' with {best_score}/100")
                print(f"Keep thinking about words related to '{best_guess}'!\n")

if __name__ == "__main__":
    game = SemanticSemantleGame()
    game.play()