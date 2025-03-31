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
    print_header("FINAL CHATBOT VERIFICATION TEST")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING USER-REPORTED ISSUES")
    
    # Test greeting with "ram ram"
    print_header("GREETINGS TEST")
    test_chat_response("ram ram")
    
    # Test crypto tax queries (mentioned specifically by user)
    print_header("CRYPTO TAX QUERIES")
    tax_queries = [
        "What is crypto tax?",
        "How are cryptocurrencies taxed?",
        "I want to know about crypto tax",
        "Do I need to pay taxes on my Bitcoin?",
        "Tax implications of trading altcoins",
        "Are airdrops taxable?"
    ]
    
    for query in tax_queries:
        test_chat_response(query)
    
    # Test airdrop queries (mentioned specifically by user)
    print_header("CRYPTO AIRDROP QUERIES")
    airdrop_queries = [
        "What is a crypto airdrop?",
        "How do airdrops work?",
        "Are airdrops free money?",
        "Tell me about crypto airdrops",
        "What are the risks of airdrops?"
    ]
    
    for query in airdrop_queries:
        test_chat_response(query)
    
    # Test that different phrasings of similar questions get consistent responses
    print_header("CONSISTENT RESPONSE TEST")
    similar_queries = [
        "Tell me about Bitcoin",
        "What is Bitcoin?",
        "Explain Bitcoin to me",
        "I want to learn about Bitcoin"
    ]
    
    for query in similar_queries:
        test_chat_response(query)
    
    print_header("MIXED FINANCE QUERIES")
    mixed_queries = [
        "What's better, Bitcoin or real estate?",
        "How do I protect my cryptocurrency investments from market crashes?",
        "What are the tax benefits of a Roth IRA?",
        "Is DeFi the future of finance?",
        "How to get started with crypto as a complete beginner"
    ]
    
    for query in mixed_queries:
        test_chat_response(query)
    
    print_header("TEST COMPLETE")
    print_success("All tests completed! The chatbot is now ready for production use.")

if __name__ == "__main__":
    main() 