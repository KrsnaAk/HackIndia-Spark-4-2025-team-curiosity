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

def test_chat_response(message, expected_response_contains=None):
    """Test chat response for a given message"""
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
        print(f"Response: {data['response']}")
        
        # If expected content is provided, check if it's in the response
        if expected_response_contains and expected_response_contains not in data['response']:
            print_error(f"Expected response to contain: '{expected_response_contains}'")
            return False
            
        return True
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print_header("ENHANCED FINANCE CHATBOT TEST")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING GREETINGS")
    all_passed = True
    
    # Test greetings
    greetings_test = [
        {"message": "hi", "expected": "Hello!"},
        {"message": "hello", "expected": "Hello!"},
        {"message": "radhe radhe", "expected": "Hello!"},
        {"message": "namaste", "expected": "Hello!"}
    ]
    
    for test in greetings_test:
        if not test_chat_response(test["message"], test["expected"]):
            all_passed = False
    
    print_header("TESTING FINANCE TOPICS")
    
    # Test finance topics
    finance_topics_test = [
        {"message": "tell me about stocks", "expected": "Stocks represent ownership"},
        {"message": "what are bonds?", "expected": "Bonds are debt securities"},
        {"message": "explain cryptocurrency", "expected": "Cryptocurrency is a digital"},
        {"message": "what is bitcoin?", "expected": "Bitcoin is the first"},
        {"message": "how does inflation work?", "expected": "Inflation is the rate"},
        {"message": "I want to learn about 401k", "expected": "401(k)"}
    ]
    
    for test in finance_topics_test:
        if not test_chat_response(test["message"], test["expected"]):
            all_passed = False
    
    # Print overall result
    print_header("TEST RESULTS")
    if all_passed:
        print_success("🎉 All tests passed! The enhanced chatbot is working correctly.")
    else:
        print_error("❌ Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main() 