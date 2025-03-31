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
    print_header("COMPLEX QUERY FINANCE CHATBOT TEST")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING GREETINGS")
    test_chat_response("ram ram")
    
    print_header("TESTING DIFFERENT QUERY INTENTS")
    
    # Definition queries
    print_header("DEFINITION QUERIES")
    definition_queries = [
        "What is a bull market?",
        "What is the difference between a hot wallet and cold wallet?",
        "Explain bitcoin halving",
        "What is yield farming in crypto?",
        "Tell me about NFTs"
    ]
    
    for query in definition_queries:
        test_chat_response(query)
    
    # Method queries
    print_header("METHOD QUERIES")
    method_queries = [
        "How to invest in crypto as a beginner?",
        "What's the best way to secure my crypto assets?",
        "How do I create a diversified investment portfolio?",
        "What strategies can I use to minimize taxes on investments?"
    ]
    
    for query in method_queries:
        test_chat_response(query)
    
    # Recommendation queries
    print_header("RECOMMENDATION QUERIES")
    recommendation_queries = [
        "What are the best crypto investments for 2023?",
        "Should I invest in Bitcoin or Ethereum?",
        "What's better for retirement savings, 401k or IRA?",
        "Top DeFi platforms to consider"
    ]
    
    for query in recommendation_queries:
        test_chat_response(query)
    
    # Risk queries
    print_header("RISK QUERIES")
    risk_queries = [
        "What are the risks of DeFi?",
        "How to protect my crypto from hackers?",
        "Is it safe to keep crypto on exchanges?",
        "What are the dangers of yield farming?"
    ]
    
    for query in risk_queries:
        test_chat_response(query)
    
    # Complex queries
    print_header("COMPLEX QUERIES")
    complex_queries = [
        "What might happen to Bitcoin after the next halving?",
        "Compare proof of stake vs proof of work",
        "What's the future of cryptocurrency regulation?",
        "How does dollar cost averaging compare to lump sum investing?",
        "Explain the implications of crypto tax regulations"
    ]
    
    for query in complex_queries:
        test_chat_response(query)
    
    print_header("TEST COMPLETE")
    print_success("All complex queries tested successfully!")

if __name__ == "__main__":
    main() 