import requests
import json
import time
import sys

# Base URL for the API
BASE_URL = "http://localhost:8000"

def print_colored(text, color_code):
    """Print text with color"""
    print(f"\033[{color_code}m{text}\033[0m")

def print_success(text):
    """Print success message in green"""
    print_colored(text, 92)

def print_error(text):
    """Print error message in red"""
    print_colored(text, 91)

def print_info(text):
    """Print info message in blue"""
    print_colored(text, 94)

def print_header(text):
    """Print header in cyan"""
    print("\n" + "=" * 80)
    print_colored(text, 96)
    print("=" * 80)

def test_server_running():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("Server is running!")
            return True
        else:
            print_error(f"Server is running but returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Server is not running! Please start the server with 'python -m app.main'")
        return False

def test_chat_response(message):
    """Test chat response for a given message and display full response"""
    print_info(f"Testing message: '{message}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/",
            json={"message": message}
        )
        
        if response.status_code != 200:
            print_error(f"Request failed with status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
        data = response.json()
        print_success(f"Response: {data['response']}")
        print("=" * 80)
        return True
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print_header("PRICE PREDICTION CAPABILITY TESTS")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING CRYPTO PRICE PREDICTIONS")
    crypto_prediction_queries = [
        "How much will ETH price increase by 2027?",
        "What will Bitcoin be worth in 5 years?",
        "Can you predict SOL price in the next 10 years?",
        "Will DOGE reach $1 by 2030?",
        "How high can crypto prices go in the future?",
        "What is your forecast for ETH price in 5 years?",
        "Predict Bitcoin value for 2025"
    ]
    
    for query in crypto_prediction_queries:
        test_chat_response(query)
    
    print_header("TESTING STOCK PRICE PREDICTIONS")
    stock_prediction_queries = [
        "How much will AAPL be worth in 5 years?",
        "Can you predict TSLA stock price in 2027?",
        "What will be the value of MSFT by 2030?",
        "Will AMZN reach $200 per share in the next 5 years?",
        "Predict NVDA stock growth for the next decade",
        "How much can tech stocks increase in value in 5 years?",
        "What's your prediction for Apple stock in 2026?"
    ]
    
    for query in stock_prediction_queries:
        test_chat_response(query)
    
    print_header("TESTING GENERAL PREDICTION QUERIES")
    general_prediction_queries = [
        "Can you predict future asset prices?",
        "How do you generate price predictions?",
        "What will the stock market look like in 5 years?",
        "Which cryptocurrency will grow the most in the next 5 years?",
        "Is it possible to predict crypto prices accurately?",
        "What factors affect long-term price predictions?"
    ]
    
    for query in general_prediction_queries:
        test_chat_response(query)
    
    print_header("TEST COMPLETE")
    print_success("All price prediction capabilities tested!")

if __name__ == "__main__":
    main() 