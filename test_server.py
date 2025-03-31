#!/usr/bin/env python
import requests
import json
import time
import sys

def test_query(message):
    print(f"Testing query: {message}")
    try:
        response = requests.post(
            'http://localhost:8000/api/chat/',
            json={'message': message},
            timeout=10
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 50)

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)
    
    # Test basic greeting
    test_query("Hello")
    
    # Test Bitcoin price query
    test_query("What is the current price of Bitcoin?")
    
    # Test price prediction with $ALCH
    test_query("Predict the price of $ALCH")
    
    # Test price prediction with different wording
    test_query("What's your prediction for the price of Alchemy Pay?") 