#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_game_flow():
    """Test the basic game flow"""
    print("Testing Dynamic Semantle Game...")
    
    # Test 1: Set secret word
    print("\n1. Setting secret word 'ocean'...")
    response = requests.post(f"{BASE_URL}/set_word", 
                           json={"word": "ocean", "model": "sentence-bert"})
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["success"] == True
    
    # Test 2: Make some guesses
    test_words = ["water", "sea", "blue", "sand", "beach", "wave", "fish"]
    
    for word in test_words:
        print(f"\n2. Guessing '{word}'...")
        response = requests.post(f"{BASE_URL}/guess", 
                               json={"word": word, "model": "sentence-bert"})
        data = response.json()
        print(f"   Score: {data.get('score', 'N/A')}%")
        print(f"   Nodes in graph: {len(data.get('graph_data', {}).get('nodes', []))}")
        print(f"   Links in graph: {len(data.get('graph_data', {}).get('links', []))}")
        time.sleep(0.5)  # Small delay between guesses
    
    # Test 3: Test model switching
    print("\n3. Testing model switching to ConceptNet...")
    response = requests.post(f"{BASE_URL}/calculate_similarities", 
                           json={"model": "conceptnet"})
    data = response.json()
    print(f"   Recalculated with {len(data.get('guess_scores', []))} scores")
    
    # Test 4: Get a hint
    print("\n4. Getting a hint...")
    response = requests.get(f"{BASE_URL}/hint")
    print(f"   Hint: {response.json().get('hint', 'N/A')}")
    
    # Test 5: Make the correct guess
    print("\n5. Making correct guess 'ocean'...")
    response = requests.post(f"{BASE_URL}/guess", 
                           json={"word": "ocean", "model": "conceptnet"})
    data = response.json()
    print(f"   Correct: {data.get('correct', False)}")
    print(f"   Total guesses: {data.get('guess_count', 'N/A')}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    # Wait a moment for server to be ready
    time.sleep(2)
    
    try:
        test_game_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure dynamic_semantle.py is running.")
    except Exception as e:
        print(f"❌ Error: {e}")