"""
Finnhub API client for real-time stock data
"""
import os
import logging
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv
from ..base import BaseAPIClient
from ..cache import get_from_cache, save_to_cache

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FinnhubAPI(BaseAPIClient):
    """
    Finnhub API client for real-time stock data
    """
    def __init__(self, api_key: Optional[str] = None):
        # Get base URL from environment or use default
        base_url = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")
        
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")
        
        super().__init__(
            base_url=base_url,
            api_key=self.api_key,
            api_name="finnhub"
        )
        
        if not self.api_key:
            logger.warning("Finnhub API key not found or invalid. Some functionality may be limited.")
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock price data from Finnhub
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict containing stock price data
        """
        try:
            if not self.api_key:
                return {"error": "Finnhub API key not configured"}
                
            # Clean the symbol
            symbol = symbol.upper().strip()
            
            # Check cache first
            cache_key = f"stock_price_{symbol}"
            cached_data = get_from_cache(self.api_name, cache_key, {}, cache_type="memory")
            if cached_data:
                return cached_data
            
            # Make API request
            url = f"{self.base_url}/quote"
            params = {
                "symbol": symbol,
                "token": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
            if not data or "c" not in data:
                return {"error": f"No data available for symbol {symbol}"}
                
            # Format response
            result = {
                "symbol": symbol,
                "price": data["c"],  # Current price
                "change": data["d"],  # Change
                "change_percent": data["dp"],  # Change percent
                "high": data["h"],  # High price of the day
                "low": data["l"],  # Low price of the day
                "open": data["o"],  # Open price of the day
                "previous_close": data["pc"],  # Previous close price
                "timestamp": data["t"],  # Timestamp
                "provider": "finnhub"
            }
            
            # Cache the result for 5 seconds
            save_to_cache(self.api_name, cache_key, {}, result, cache_type="memory")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching stock price from Finnhub: {str(e)}")
            return {"error": f"Failed to fetch stock price: {str(e)}"}
    
    async def search_symbol(self, query: str) -> Optional[str]:
        """
        Search for a stock symbol
        
        Args:
            query: Search query (company name or symbol)
            
        Returns:
            Best matching symbol or None if not found
        """
        try:
            if not self.api_key:
                return None
                
            # Check cache first
            cache_key = f"symbol_search_{query}"
            cached_data = get_from_cache(self.api_name, cache_key, {}, cache_type="memory")
            if cached_data:
                return cached_data
            
            url = f"{self.base_url}/search"
            params = {
                "q": query,
                "token": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
            result = None
            if data and "result" in data and data["result"]:
                # Get the first (best) match
                result = data["result"][0]["symbol"]
                
            # Cache the result
            save_to_cache(self.api_name, cache_key, {}, result, cache_type="memory")
            return result
            
        except Exception as e:
            logger.error(f"Error searching symbol on Finnhub: {str(e)}")
            return None 