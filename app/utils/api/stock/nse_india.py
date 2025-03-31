"""
NSE India API client for Indian stock market data
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.utils.api.base import BaseAPIClient
from app.utils.api.config import NSE_INDIA_BASE_URL

logger = logging.getLogger(__name__)

class NSEIndiaClient(BaseAPIClient):
    """Client for NSE India stock market APIs"""
    
    def __init__(self):
        """Initialize NSE India API client"""
        super().__init__(
            base_url=NSE_INDIA_BASE_URL,
            api_key=None,  # NSE India doesn't require an API key
            api_name="nse_india"
        )
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        NSE requires specific headers to prevent scraping blocking
        """
        headers = super()._prepare_headers(additional_headers)
        headers.update({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.nseindia.com/"
        })
        return headers
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price information for NSE-listed stocks
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock price information
        """
        try:
            # NSE API requires a specific format
            endpoint = f"quote-equity?symbol={symbol.upper()}"
            response = self.get(endpoint, {})
            
            if "priceInfo" not in response:
                logger.warning(f"Invalid response format from NSE India for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find stock data for {symbol}"
                }
            
            price_info = response["priceInfo"]
            meta_info = response.get("metadata", {})
            security_info = response.get("securityInfo", {})
            
            # Format the data for our needs
            price_data = {
                "symbol": symbol.upper(),
                "name": security_info.get("companyName", symbol.upper()),
                "price": price_info.get("lastPrice", 0),
                "change": price_info.get("change", 0),
                "change_percent": price_info.get("pChange", 0),
                "volume": price_info.get("tradedVolume", 0),
                "open": price_info.get("open", 0),
                "high": price_info.get("intraDayHighLow", {}).get("max", 0),
                "low": price_info.get("intraDayHighLow", {}).get("min", 0),
                "previous_close": price_info.get("previousClose", 0),
                "market_cap": meta_info.get("marketCapitalisation", 0),
                "currency": "INR",
                "industry": security_info.get("industry", ""),
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
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status (open/closed)
        
        Returns:
            Dictionary with market status information
        """
        try:
            response = self.get("market-status", {})
            
            if "marketState" not in response:
                logger.warning("Invalid response format from NSE India market status")
                return {"error": "invalid_response"}
            
            market_state = response["marketState"]
            
            status_data = {
                "status": "closed" if market_state[0].get("marketStatus") == "Closed" else "open",
                "market_types": []
            }
            
            for market in market_state:
                status_data["market_types"].append({
                    "name": market.get("market", ""),
                    "status": market.get("marketStatus", ""),
                    "trade_date": market.get("tradeDate", "")
                })
            
            return status_data
        
        except Exception as e:
            logger.error(f"Error fetching market status: {str(e)}")
            return {"error": "api_error", "message": str(e)}
    
    def get_indices(self) -> List[Dict[str, Any]]:
        """
        Get major NSE indices data
        
        Returns:
            List of indices with latest values
        """
        try:
            response = self.get("equity-stockIndices?index=NIFTY%2050", {})
            
            if "data" not in response:
                logger.warning("Invalid response format from NSE India indices")
                return []
            
            results = []
            for item in response["data"]:
                results.append({
                    "symbol": item.get("indexSymbol", ""),
                    "name": item.get("indexName", ""),
                    "price": item.get("last", 0),
                    "change": item.get("change", 0),
                    "change_percent": item.get("perChange", 0),
                    "open": item.get("open", 0),
                    "high": item.get("high", 0),
                    "low": item.get("low", 0),
                    "previous_close": item.get("previousClose", 0),
                    "yearHigh": item.get("yearHigh", 0),
                    "yearLow": item.get("yearLow", 0),
                    "last_updated": datetime.now().isoformat()
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching indices: {str(e)}")
            return []
    
    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for NSE-listed stocks
        
        Args:
            query: Search query
            
        Returns:
            List of matching stocks
        """
        try:
            response = self.get(f"search/autocomplete?q={query}", {})
            
            if "symbols" not in response:
                return []
            
            results = []
            for item in response["symbols"]:
                results.append({
                    "symbol": item.get("symbol", ""),
                    "name": item.get("name", ""),
                    "status": item.get("status", ""),
                    "type": "Equity" if item.get("symbol", "").find(":") == -1 else "Derivative"
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching stocks with query '{query}': {str(e)}")
            return []
    
    def get_top_gainers_losers(self) -> Dict[str, List]:
        """
        Get top gainers and losers in the market
        
        Returns:
            Dictionary with lists of top gainers and losers
        """
        try:
            response = self.get("market-data/top-gainers-losers", {})
            
            if "marketData" not in response:
                logger.warning("Invalid response format from NSE India top gainers/losers")
                return {"gainers": [], "losers": []}
            
            result = {
                "gainers": [],
                "losers": []
            }
            
            # Process gainers
            for item in response.get("marketData", {}).get("NIFTY", {}).get("gainers", []):
                result["gainers"].append({
                    "symbol": item.get("symbol", ""),
                    "series": item.get("series", ""),
                    "price": item.get("lastPrice", 0),
                    "change": item.get("change", 0),
                    "change_percent": item.get("pChange", 0),
                    "volume": item.get("tradedQuantity", 0)
                })
                
            # Process losers
            for item in response.get("marketData", {}).get("NIFTY", {}).get("losers", []):
                result["losers"].append({
                    "symbol": item.get("symbol", ""),
                    "series": item.get("series", ""),
                    "price": item.get("lastPrice", 0),
                    "change": item.get("change", 0),
                    "change_percent": item.get("pChange", 0),
                    "volume": item.get("tradedQuantity", 0)
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching top gainers/losers: {str(e)}")
            return {"gainers": [], "losers": []} 