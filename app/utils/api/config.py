"""
Configuration module for API keys and settings
These will be loaded from environment variables or .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API KEYS
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
RBI_API_KEY = os.getenv("RBI_API_KEY", "")

# API URLs
ALPHA_VANTAGE_BASE_URL = os.getenv("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")
YAHOO_FINANCE_BASE_URL = os.getenv("YAHOO_FINANCE_BASE_URL", "https://query1.finance.yahoo.com/v8/finance")
NSE_INDIA_BASE_URL = os.getenv("NSE_INDIA_BASE_URL", "https://www.nseindia.com/api")
COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
COINMARKETCAP_BASE_URL = os.getenv("COINMARKETCAP_BASE_URL", "https://pro-api.coinmarketcap.com/v1")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com/api/v3")
RBI_BASE_URL = "https://api.rbi.org.in/api/v1"

# Caching settings
CACHE_EXPIRY = {
    "stock_price": 300,  # 5 minutes for stock prices
    "crypto_price": 120,  # 2 minutes for crypto prices
    "forex_rate": 3600,  # 1 hour for forex rates
    "market_index": 600,  # 10 minutes for market indices
    "historical_data": 86400  # 24 hours for historical data
}

# Request settings
DEFAULT_TIMEOUT = int(os.getenv("API_DEFAULT_TIMEOUT", "10"))  # seconds
MAX_RETRIES = int(os.getenv("API_DEFAULT_RETRIES", "3"))

# Default parameters
DEFAULT_STOCK_MARKET = "NSE"  # NSE for Indian stocks, can be NYSE, NASDAQ, etc.
DEFAULT_CURRENCY = "INR"  # Indian Rupee
DEFAULT_CRYPTO_CURRENCY = "BTC"  # Bitcoin as default cryptocurrency

# Additional settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # Default 5 minutes

# CoinGecko API
COINGECKO_API_KEY = ""  # Free tier doesn't require an API key

# Google Gemini API
GEMINI_API_KEY = "AIzaSyCJfz7W_MByGacERDDszhcH_23TIJ7j-ho" 