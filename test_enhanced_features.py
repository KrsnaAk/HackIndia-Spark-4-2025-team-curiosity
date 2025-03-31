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
    print_header("ENHANCED FINANCE CHATBOT TEST")
    
    # Check if server is running
    if not test_server_running():
        sys.exit(1)
    
    print_header("TESTING WEB3 VS CRYPTO")
    web3_queries = [
        "What is the difference between crypto and web3?",
        "Are crypto and web3 the same thing?",
        "Web3 vs cryptocurrency",
        "How does web3 relate to crypto?",
        "Is web3 better than crypto?"
    ]
    
    for query in web3_queries:
        test_chat_response(query)
    
    print_header("TESTING CRYPTO INVESTMENT RECOMMENDATIONS")
    investment_queries = [
        "What are the best crypto coins to invest in?",
        "Suggest me some good cryptocurrencies",
        "Which crypto should I buy?",
        "Top crypto investments",
        "Recommend crypto coins"
    ]
    
    for query in investment_queries:
        test_chat_response(query)
        
    print_header("TESTING CRYPTO PRICING")
    price_queries = [
        "What's the price of BTC?",
        "How much is ETH?",
        "Show me the price of SOL",
        "BTC price",
        "Check DOGE price"
    ]
    
    for query in price_queries:
        test_chat_response(query)
    
    print_header("TESTING CRYPTO TAX BY COUNTRY")
    tax_queries = [
        "How is crypto taxed in India?",
        "Crypto tax rules in UK",
        "What are the tax implications for crypto in Australia?",
        "German crypto taxes",
        "How much tax on cryptocurrency in India?"
    ]
    
    for query in tax_queries:
        test_chat_response(query)
    
    print_header("TESTING NEGATIVE FEEDBACK HANDLING")
    negative_queries = [
        "You're a noob",
        "This bot is useless",
        "You don't understand what I'm asking",
        "You're giving me incorrect information",
        "Your responses are terrible"
    ]
    
    for query in negative_queries:
        test_chat_response(query)
    
    print_header("TEST COMPLETE")
    print_success("All enhanced features tested!")

if __name__ == "__main__":
    main() 