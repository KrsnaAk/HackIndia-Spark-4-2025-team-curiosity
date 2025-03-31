#!/usr/bin/env python
"""
Test script for the unified CryptoAPI
"""

import os
import sys
import json
from pprint import pprint
from time import sleep

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CryptoAPI
from app.utils.api.crypto import CryptoAPI

# ANSI color codes for terminal output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(message):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}=== {message} {RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def print_success(message):
    """Print a success message"""
    print(f"{GREEN}{message}{RESET}")

def print_warning(message):
    """Print a warning message"""
    print(f"{YELLOW}{message}{RESET}")

def print_error(message):
    """Print an error message"""
    print(f"{RED}{message}{RESET}")

def test_crypto_price():
    """Test cryptocurrency price retrieval from different providers"""
    print_header("TESTING CRYPTO PRICE RETRIEVAL")
    crypto_api = CryptoAPI()
    
    cryptocurrencies = ["BTC", "ETH", "DOGE", "SOL", "SHIB", "LINK", "$ALCH"]
    
    for symbol in cryptocurrencies:
        try:
            print(f"Testing price for {symbol}...")
            
            # Test with default provider order
            result = crypto_api.get_crypto_price(symbol)
            print(f"Provider: {result.get('provider', 'unknown')}")
            
            if "error" in result:
                print_warning(f"Error: {result.get('message')}")
            else:
                price = result.get("price", 0)
                price_str = f"${price:,.2f}" if price >= 1 else f"${price:.8f}"
                print_success(f"Price: {price_str}")
                print(f"24h Change: {result.get('percent_change_24h', 0):.2f}%")
                print(f"Market Cap: ${result.get('market_cap', 0):,.2f}")
            
            print("")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
    
    # Test specific provider preference
    print("Testing with preferred provider (CoinGecko)...")
    result = crypto_api.get_crypto_price("BTC", preferred_provider="coingecko")
    print(f"Provider used: {result.get('provider', 'unknown')}")
    if "error" not in result:
        print_success(f"Successfully retrieved BTC price from preferred provider")

def test_crypto_details():
    """Test cryptocurrency details retrieval"""
    print_header("TESTING CRYPTO DETAILS RETRIEVAL")
    crypto_api = CryptoAPI()
    
    cryptocurrencies = ["BTC", "ETH", "DOGE"]
    
    for symbol in cryptocurrencies:
        try:
            print(f"Testing details for {symbol}...")
            result = crypto_api.get_crypto_details(symbol)
            
            if "error" in result:
                print_warning(f"Error: {result.get('message')}")
            else:
                print_success(f"Successfully retrieved details for {symbol}")
                print(f"Provider: {result.get('provider', 'unknown')}")
                print(f"Name: {result.get('name', '')}")
                
                # Print description snippet if available
                description = result.get("description", "")
                if description:
                    print(f"Description snippet: {description[:100]}...")
                
                # Print some market data if available
                market_data = result.get("market_data", {})
                if market_data:
                    current_price = market_data.get("current_price", {}).get("usd", 0)
                    price_str = f"${current_price:,.2f}" if current_price >= 1 else f"${current_price:.8f}"
                    print(f"Current price: {price_str}")
            
            print("")
        except Exception as e:
            print_error(f"Exception: {str(e)}")

def test_historical_data():
    """Test historical data retrieval"""
    print_header("TESTING HISTORICAL DATA RETRIEVAL")
    crypto_api = CryptoAPI()
    
    print("Testing historical data for BTC (7 days, daily)...")
    try:
        result = crypto_api.get_historical_data("BTC", days=7, interval="daily")
        
        if not result:
            print_warning("No historical data returned")
        else:
            print_success(f"Retrieved {len(result)} data points")
            if len(result) > 0:
                print(f"First data point: {json.dumps(result[0], indent=2)}")
                print(f"Provider: {result[0].get('provider', 'unknown') if isinstance(result[0], dict) else 'unknown'}")
    except Exception as e:
        print_error(f"Exception: {str(e)}")
    
    print("\nTesting historical data for ETH (24 hours, hourly)...")
    try:
        result = crypto_api.get_historical_data("ETH", days=1, interval="hourly")
        
        if not result:
            print_warning("No historical data returned")
        else:
            print_success(f"Retrieved {len(result)} data points")
    except Exception as e:
        print_error(f"Exception: {str(e)}")

def test_search():
    """Test cryptocurrency search functionality"""
    print_header("TESTING CRYPTO SEARCH")
    crypto_api = CryptoAPI()
    
    search_terms = ["bitcoin", "ethereum", "doge"]
    
    for term in search_terms:
        try:
            print(f"Searching for '{term}'...")
            results = crypto_api.search_crypto(term)
            
            if not results:
                print_warning(f"No results found for '{term}'")
            else:
                print_success(f"Found {len(results)} results")
                # Print first 3 results
                for i, result in enumerate(results[:3]):
                    print(f"{i+1}. {result.get('name', 'Unknown')} ({result.get('symbol', 'Unknown')})")
                    print(f"   Provider: {result.get('provider', 'unknown')}")
            
            print("")
        except Exception as e:
            print_error(f"Exception: {str(e)}")

def test_market_summary():
    """Test market summary functionality"""
    print_header("TESTING MARKET SUMMARY")
    crypto_api = CryptoAPI()
    
    try:
        print("Getting market summary...")
        result = crypto_api.get_market_summary()
        
        if "error" in result:
            print_warning(f"Error: {result.get('message')}")
        else:
            print_success("Successfully retrieved market summary")
            print(f"Provider: {result.get('provider', 'unknown')}")
            print(f"Active cryptocurrencies: {result.get('active_cryptocurrencies', 0):,}")
            print(f"BTC dominance: {result.get('btc_dominance', 0):.2f}%")
            print(f"ETH dominance: {result.get('eth_dominance', 0):.2f}%")
            print(f"Total market cap: ${result.get('total_market_cap', 0):,.2f}")
    except Exception as e:
        print_error(f"Exception: {str(e)}")

def test_trading_pairs():
    """Test trading pairs functionality"""
    print_header("TESTING TRADING PAIRS")
    crypto_api = CryptoAPI()
    
    try:
        print("Getting BTC trading pairs...")
        results = crypto_api.get_trading_pairs(base_symbol="BTC")
        
        if not results:
            print_warning("No trading pairs found")
        else:
            print_success(f"Found {len(results)} trading pairs")
            # Print first 5 trading pairs
            for i, pair in enumerate(results[:5]):
                print(f"{i+1}. {pair.get('symbol', 'Unknown')} ({pair.get('base_symbol', '')} / {pair.get('quote_symbol', '')})")
    except Exception as e:
        print_error(f"Exception: {str(e)}")
    
    try:
        print("\nGetting trading pairs with USDT quote...")
        results = crypto_api.get_trading_pairs(quote_symbol="USDT")
        
        if not results:
            print_warning("No trading pairs found")
        else:
            print_success(f"Found {len(results)} trading pairs")
            # Print first 5 trading pairs
            for i, pair in enumerate(results[:5]):
                print(f"{i+1}. {pair.get('symbol', 'Unknown')} ({pair.get('base_symbol', '')} / {pair.get('quote_symbol', '')})")
    except Exception as e:
        print_error(f"Exception: {str(e)}")

def main():
    """Main test function"""
    print_header("CRYPTO API TEST SUITE")
    
    # Test all functionality
    test_crypto_price()
    sleep(1)  # Avoid rate limiting
    
    test_crypto_details()
    sleep(1)  # Avoid rate limiting
    
    test_historical_data()
    sleep(1)  # Avoid rate limiting
    
    test_search()
    sleep(1)  # Avoid rate limiting
    
    test_market_summary()
    sleep(1)  # Avoid rate limiting
    
    test_trading_pairs()
    
    print_header("TEST COMPLETE")
    print_success("Crypto API test suite completed!")

if __name__ == "__main__":
    main() 