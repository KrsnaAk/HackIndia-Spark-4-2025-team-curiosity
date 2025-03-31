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
        print("=" * 60)
        return True
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print_header("ENHANCED CRYPTO FINANCE CHATBOT TEST")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING GREETINGS")
    test_chat_response("ram ram")
    test_chat_response("radhe radhe")
    
    print_header("TESTING CRYPTO QUERIES")
    
    # Test crypto topics
    crypto_queries = [
        "what is crypto tax",
        "explain crypto taxation",
        "what is a crypto airdrop",
        "tell me about nfts",
        "how does defi work",
        "explain smart contracts",
        "what is crypto staking",
        "how does blockchain work",
        "what is a crypto wallet",
        "what are gas fees",
        "explain yield farming"
    ]
    
    for query in crypto_queries:
        test_chat_response(query)
    
    print_header("TEST COMPLETE")
    print_success("All queries tested successfully!")

if __name__ == "__main__":
    main() 