"""
Alpha Vantage API client for stock market data
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from app.utils.api.base import BaseAPIClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AlphaVantageClient(BaseAPIClient):
    """Client for Alpha Vantage stock market APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage API client"""
        # Get base URL from environment or use default
        base_url = os.getenv("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")
        
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
        
        if not self.api_key:
            logger.warning("No Alpha Vantage API key provided. API calls will likely fail.")
        
        super().__init__(
            base_url=base_url,
            api_key=self.api_key,
            api_name="alpha_vantage"
        )
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price information
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock price information
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            response = self.get("", params=params)
            
            if "Global Quote" not in response:
                logger.warning(f"Invalid response format from Alpha Vantage for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find stock data for {symbol}"
                }
            
            quote = response["Global Quote"]
            
            # Format the data for our needs
            price_data = {
                "symbol": symbol.upper(),
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": float(quote.get("10. change percent", "0%").replace("%", "")),
                "volume": int(float(quote.get("06. volume", 0))),
                "previous_close": float(quote.get("08. previous close", 0)),
                "last_updated": datetime.now().isoformat()
            }
            
            return price_data
        
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch stock data: {str(e)}"
            }
            
    async def get_stock_price_async(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price information (async version)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock price information
        """
        # Use the synchronous method since Alpha Vantage doesn't need async calls
        # This maintains compatibility with the StockAPI interface
        try:
            return self.get_stock_price(symbol)
        except Exception as e:
            logger.error(f"Async error fetching stock price for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch stock data: {str(e)}"
            }
    
    def get_historical_data(self, symbol: str, interval: str = "daily", output_size: str = "compact") -> Dict[str, Any]:
        """
        Get historical stock data
        
        Args:
            symbol: Stock symbol
            interval: Time interval - 'daily', 'weekly', or 'monthly'
            output_size: 'compact' for latest 100 points, 'full' for 20+ years
            
        Returns:
            Dictionary with historical price data
        """
        function_map = {
            "daily": "TIME_SERIES_DAILY",
            "weekly": "TIME_SERIES_WEEKLY",
            "monthly": "TIME_SERIES_MONTHLY"
        }
        
        params = {
            "function": function_map.get(interval, "TIME_SERIES_DAILY"),
            "symbol": symbol,
            "outputsize": output_size,
            "apikey": self.api_key
        }
        
        try:
            response = self.get("", params=params)
            
            # Determine which key contains the time series data
            time_series_key = None
            for key in response.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                logger.warning(f"Invalid response format from Alpha Vantage historical data for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find historical data for {symbol}"
                }
            
            time_series = response[time_series_key]
            
            # Format the data for our needs
            historical_data = {
                "symbol": symbol.upper(),
                "interval": interval,
                "data": []
            }
            
            for date, values in time_series.items():
                historical_data["data"].append({
                    "date": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(float(values.get("5. volume", 0)))
                })
            
            # Sort by date (newest first)
            historical_data["data"].sort(key=lambda x: x["date"], reverse=True)
            
            return historical_data
        
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch historical data: {str(e)}"
            }
    
    def search_stocks(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Search for stocks by keywords
        
        Args:
            keywords: Search keywords
            
        Returns:
            List of matching stocks
        """
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": self.api_key
        }
        
        try:
            response = self.get("", params=params)
            
            if "bestMatches" not in response:
                logger.warning(f"Invalid response format from Alpha Vantage search for {keywords}")
                return []
            
            matches = response["bestMatches"]
            results = []
            
            for match in matches:
                results.append({
                    "symbol": match.get("1. symbol", ""),
                    "name": match.get("2. name", ""),
                    "type": match.get("3. type", ""),
                    "region": match.get("4. region", ""),
                    "currency": match.get("8. currency", "")
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching stocks with keywords '{keywords}': {str(e)}")
            return []
    
    def get_market_indices(self) -> List[Dict[str, Any]]:
        """
        Get data for major market indices
        
        Returns:
            List of market indices with latest values
        """
        # List of major indices to fetch
        indices = [
            "^GSPC",  # S&P 500
            "^DJI",   # Dow Jones
            "^IXIC",  # NASDAQ
            "^FTSE",  # FTSE 100
            "^NSEI",  # NIFTY 50
            "^BSESN"  # SENSEX
        ]
        
        results = []
        
        for idx in indices:
            try:
                price_data = self.get_stock_price(idx)
                if "error" not in price_data:
                    results.append(price_data)
            except Exception as e:
                logger.error(f"Error fetching data for index {idx}: {str(e)}")
        
        return results 