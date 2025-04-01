"""
Yahoo Finance API client for stock market data
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

from app.utils.api.base import BaseAPIClient
from app.utils.api.config import YAHOO_FINANCE_BASE_URL

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class YahooFinanceClient(BaseAPIClient):
    """Client for Yahoo Finance stock market APIs"""
    
    def __init__(self):
        """Initialize Yahoo Finance API client"""
        # Get base URL from environment or use default
        base_url = os.getenv("YAHOO_FINANCE_BASE_URL", "https://query1.finance.yahoo.com/v8/finance")
        
        super().__init__(
            base_url=base_url,
            api_key=None,  # Yahoo Finance doesn't require an API key
            api_name="yahoo_finance"
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
            "symbols": symbol,
            "fields": "regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketVolume,regularMarketPreviousClose,shortName,longName,marketCap,currency"
        }
        
        try:
            response = self.get("quote", params=params)
            
            if "quoteResponse" not in response or "result" not in response["quoteResponse"] or not response["quoteResponse"]["result"]:
                logger.warning(f"Invalid response format from Yahoo Finance for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find stock data for {symbol}"
                }
            
            quote = response["quoteResponse"]["result"][0]
            
            # Format the data for our needs
            price_data = {
                "symbol": symbol.upper(),
                "name": quote.get("longName", quote.get("shortName", symbol.upper())),
                "price": quote.get("regularMarketPrice", 0),
                "change": quote.get("regularMarketChange", 0),
                "change_percent": quote.get("regularMarketChangePercent", 0),
                "volume": quote.get("regularMarketVolume", 0),
                "previous_close": quote.get("regularMarketPreviousClose", 0),
                "market_cap": quote.get("marketCap", 0),
                "currency": quote.get("currency", "USD"),
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
        # Yahoo Finance doesn't need async calls, use the synchronous method
        try:
            return self.get_stock_price(symbol)
        except Exception as e:
            logger.error(f"Async error fetching stock price for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch stock data: {str(e)}"
            }
    
    def get_historical_data(self, symbol: str, interval: str = "1d", range_period: str = "1mo") -> Dict[str, Any]:
        """
        Get historical stock data
        
        Args:
            symbol: Stock symbol
            interval: Time interval - '1d', '1wk', '1mo'
            range_period: Time range - '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'
            
        Returns:
            Dictionary with historical price data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "range": range_period,
            "includePrePost": "false",
            "events": "div,split"
        }
        
        try:
            response = self.get("chart", params=params)
            
            if "chart" not in response or "result" not in response["chart"] or not response["chart"]["result"]:
                logger.warning(f"Invalid response format from Yahoo Finance historical data for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find historical data for {symbol}"
                }
            
            chart_data = response["chart"]["result"][0]
            
            timestamps = chart_data.get("timestamp", [])
            quotes = chart_data.get("indicators", {}).get("quote", [{}])[0]
            
            # Format the data for our needs
            historical_data = {
                "symbol": symbol.upper(),
                "interval": interval,
                "range": range_period,
                "data": []
            }
            
            for i in range(len(timestamps)):
                if i < len(timestamps):
                    timestamp = timestamps[i]
                    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    
                    historical_data["data"].append({
                        "date": date,
                        "open": quotes.get("open", [])[i] if i < len(quotes.get("open", [])) else None,
                        "high": quotes.get("high", [])[i] if i < len(quotes.get("high", [])) else None,
                        "low": quotes.get("low", [])[i] if i < len(quotes.get("low", [])) else None,
                        "close": quotes.get("close", [])[i] if i < len(quotes.get("close", [])) else None,
                        "volume": quotes.get("volume", [])[i] if i < len(quotes.get("volume", [])) else None
                    })
            
            return historical_data
        
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch historical data: {str(e)}"
            }
    
    def get_market_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of major market indices
        
        Returns:
            List of market indices with latest values
        """
        try:
            response = self.get("market/v2/get-summary", {})
            
            if "marketSummaryResponse" not in response or "result" not in response["marketSummaryResponse"]:
                logger.warning("Invalid response format from Yahoo Finance market summary")
                return []
            
            results = []
            for item in response["marketSummaryResponse"]["result"]:
                results.append({
                    "symbol": item.get("symbol", ""),
                    "name": item.get("shortName", ""),
                    "price": item.get("regularMarketPrice", {}).get("raw", 0),
                    "change": item.get("regularMarketChange", {}).get("raw", 0),
                    "change_percent": item.get("regularMarketChangePercent", {}).get("raw", 0),
                    "last_updated": datetime.now().isoformat()
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching market summary: {str(e)}")
            return []
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for stocks, ETFs, indices, etc.
        
        Args:
            query: Search query
            
        Returns:
            List of matching securities
        """
        try:
            params = {
                "q": query,
                "quotesCount": 10,
                "newsCount": 0,
                "listsCount": 0
            }
            
            response = self.get("search", params=params)
            
            if "quotes" not in response:
                return []
            
            results = []
            for quote in response["quotes"]:
                results.append({
                    "symbol": quote.get("symbol", ""),
                    "name": quote.get("longname", quote.get("shortname", "")),
                    "exchange": quote.get("exchange", ""),
                    "type": quote.get("quoteType", ""),
                    "score": quote.get("score", 0)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching stocks with query '{query}': {str(e)}")
            return [] 