#!/usr/bin/env python3
import random
from difflib import SequenceMatcher
import sys

class SemantleGame:
    def __init__(self):
        self.secret_word = None
        self.guesses = []
        
    def calculate_similarity(self, word1, word2):
        """Calculate similarity between two words (0-100)"""
        # Normalize words
        w1 = word1.lower().strip()
        w2 = word2.lower().strip()
        
        # Exact match
        if w1 == w2:
            return 100
        
        # Calculate similarity based on:
        # 1. Character similarity
        char_similarity = SequenceMatcher(None, w1, w2).ratio()
        
        # 2. Length similarity
        len_similarity = 1 - abs(len(w1) - len(w2)) / max(len(w1), len(w2))
        
        # 3. Common prefix/suffix bonus
        prefix_bonus = 0
        for i in range(min(len(w1), len(w2))):
            if w1[i] == w2[i]:
                prefix_bonus += 0.05
            else:
                break
                
        suffix_bonus = 0
        for i in range(1, min(len(w1), len(w2)) + 1):
            if w1[-i] == w2[-i]:
                suffix_bonus += 0.03
            else:
                break
        
        # Weighted combination
        base_score = (char_similarity * 0.6 + len_similarity * 0.2) * 100
        bonus = min((prefix_bonus + suffix_bonus) * 100, 20)
        
        final_score = min(base_score + bonus, 99)  # Max 99 unless exact match
        
        return round(final_score)
    
    def get_feedback(self, score):
        """Provide feedback based on score"""
        if score == 100:
            return "🎉 Congratulations! You found the word!"
        elif score >= 80:
            return "🔥 Very hot! You're extremely close!"
        elif score >= 60:
            return "♨️  Hot! Getting warmer!"
        elif score >= 40:
            return "🌡️  Warm. On the right track."
        elif score >= 20:
            return "❄️  Cold. Try a different approach."
        else:
            return "🧊 Freezing! Very far away."
    
    def play(self):
        print("\n=== Welcome to Semantle! ===")
        print("I'll think of a word, and you try to guess it.")
        print("I'll give you a similarity score from 1-100 for each guess.\n")
        
        # Get secret word from player 1
        print("Player 1: Please enter the secret word (it will be hidden):")
        self.secret_word = input().strip()
        
        # Clear screen (works on most terminals)
        print("\033[2J\033[H")
        
        print("=== The word has been set! ===")
        print("Player 2: Start guessing! Type 'quit' to exit.\n")
        
        guess_count = 0
        
        while True:
            guess = input(f"Guess #{guess_count + 1}: ").strip()
            
            if guess.lower() == 'quit':
                print(f"\nThe word was: {self.secret_word}")
                break
            
            if not guess:
                print("Please enter a word.")
                continue
            
            score = self.calculate_similarity(self.secret_word, guess)
            feedback = self.get_feedback(score)
            
            guess_count += 1
            self.guesses.append((guess, score))
            
            print(f"Similarity: {score}/100 - {feedback}")
            
            if score == 100:
                print(f"\nYou got it in {guess_count} guesses!")
                break
            
            # Show hint every 10 guesses
            if guess_count % 10 == 0:
                print(f"\nHint: The word has {len(self.secret_word)} letters.")

if __name__ == "__main__":
    game = SemantleGame()
    game.play()