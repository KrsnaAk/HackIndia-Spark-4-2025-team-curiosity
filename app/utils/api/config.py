"""
Configuration module for API keys and settings
These will be loaded from environment variables or .env file
"""

import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Failed to load .env file: {str(e)}")

def get_env_var(key: str, default: str = "") -> str:
    """
    Get environment variable with error handling
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    try:
        value = os.getenv(key, default)
        if not value and key.endswith("_API_KEY"):
            logger.warning(f"Missing API key for {key}")
        return value
    except Exception as e:
        logger.error(f"Error getting environment variable {key}: {str(e)}")
        return default

def get_int_env_var(key: str, default: int, min_value: int = 1) -> int:
    """
    Get integer environment variable with validation
    
    Args:
        key: Environment variable name
        default: Default value if not found
        min_value: Minimum allowed value
        
    Returns:
        Validated integer value
    """
    try:
        value = int(get_env_var(key, str(default)))
        if value < min_value:
            logger.warning(f"Invalid {key} value {value}, using default of {default}")
            return default
        return value
    except ValueError:
        logger.warning(f"Invalid {key} format, using default of {default}")
        return default

# API KEYS
ALPHA_VANTAGE_API_KEY = get_env_var("ALPHA_VANTAGE_API_KEY", "demo")
COINMARKETCAP_API_KEY = get_env_var("COINMARKETCAP_API_KEY", "")
BINANCE_API_KEY = get_env_var("BINANCE_API_KEY", "")
BINANCE_API_SECRET = get_env_var("BINANCE_API_SECRET", "")
RBI_API_KEY = get_env_var("RBI_API_KEY", "")
GEMINI_API_KEY = get_env_var("GEMINI_API_KEY", "")

# API URLs with fallbacks
ALPHA_VANTAGE_BASE_URL = get_env_var("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")
YAHOO_FINANCE_BASE_URL = get_env_var("YAHOO_FINANCE_BASE_URL", "https://query1.finance.yahoo.com/v8/finance")
NSE_INDIA_BASE_URL = get_env_var("NSE_INDIA_BASE_URL", "https://www.nseindia.com/api")
COINGECKO_BASE_URL = get_env_var("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
COINMARKETCAP_BASE_URL = get_env_var("COINMARKETCAP_BASE_URL", "https://pro-api.coinmarketcap.com/v1")
BINANCE_BASE_URL = get_env_var("BINANCE_BASE_URL", "https://api.binance.com/api/v3")
RBI_BASE_URL = get_env_var("RBI_BASE_URL", "https://api.rbi.org.in/api/v1")

# Cache settings with validation
CACHE_ENABLED = get_env_var("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = get_int_env_var("CACHE_TTL", 300, min_value=1)  # Default 5 minutes
MAX_MEMORY_CACHE_SIZE = get_int_env_var("MAX_MEMORY_CACHE_SIZE", 1000, min_value=100)  # Default 1000 items

# Cache expiry times with validation
CACHE_EXPIRY: Dict[str, int] = {
    "stock_price": get_int_env_var("CACHE_STOCK_PRICE_EXPIRY", 300, min_value=1),  # 5 minutes
    "crypto_price": get_int_env_var("CACHE_CRYPTO_PRICE_EXPIRY", 120, min_value=1),  # 2 minutes
    "forex_rate": get_int_env_var("CACHE_FOREX_RATE_EXPIRY", 3600, min_value=1),  # 1 hour
    "market_index": get_int_env_var("CACHE_MARKET_INDEX_EXPIRY", 600, min_value=1),  # 10 minutes
    "historical_data": get_int_env_var("CACHE_HISTORICAL_DATA_EXPIRY", 86400, min_value=1)  # 24 hours
}

# Request settings with validation
DEFAULT_TIMEOUT = get_int_env_var("API_DEFAULT_TIMEOUT", 10, min_value=1)
MAX_RETRIES = get_int_env_var("API_DEFAULT_RETRIES", 3, min_value=1)

# Default parameters
DEFAULT_STOCK_MARKET = get_env_var("DEFAULT_STOCK_MARKET", "NSE")
DEFAULT_CURRENCY = get_env_var("DEFAULT_CURRENCY", "INR")
DEFAULT_CRYPTO_CURRENCY = get_env_var("DEFAULT_CRYPTO_CURRENCY", "BTC")

# API rate limits (requests per minute)
RATE_LIMITS: Dict[str, int] = {
    "coingecko": get_int_env_var("COINGECKO_RATE_LIMIT", 50, min_value=1),
    "alphavantage": get_int_env_var("ALPHA_VANTAGE_RATE_LIMIT", 5, min_value=1),
    "binance": get_int_env_var("BINANCE_RATE_LIMIT", 1200, min_value=1),
    "coinmarketcap": get_int_env_var("COINMARKETCAP_RATE_LIMIT", 30, min_value=1)
}

# Cache directory settings
CACHE_DIR = get_env_var("CACHE_DIR", "data/cache")
CACHE_FILE_PREFIX = get_env_var("CACHE_FILE_PREFIX", "cache_")
CACHE_FILE_SUFFIX = get_env_var("CACHE_FILE_SUFFIX", ".json")

# Log cache settings
if CACHE_ENABLED:
    logger.info("Cache settings:")
    logger.info(f"  Enabled: {CACHE_ENABLED}")
    logger.info(f"  Default TTL: {CACHE_TTL} seconds")
    logger.info(f"  Max memory cache size: {MAX_MEMORY_CACHE_SIZE} items")
    logger.info(f"  Cache directory: {CACHE_DIR}")
    logger.info("  Cache expiry times:")
    for key, value in CACHE_EXPIRY.items():
        logger.info(f"    {key}: {value} seconds")
else:
    logger.warning("Caching is disabled") 