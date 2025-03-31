"""
Binance API client for cryptocurrency data
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import hmac
import hashlib
import time

from app.utils.api.base import BaseAPIClient
from app.utils.api.config import BINANCE_BASE_URL, BINANCE_API_KEY, BINANCE_API_SECRET

logger = logging.getLogger(__name__)

class BinanceClient(BaseAPIClient):
    """Client for Binance cryptocurrency APIs"""
    
    def __init__(self):
        """Initialize Binance API client"""
        super().__init__(
            base_url=BINANCE_BASE_URL,
            api_key=BINANCE_API_KEY,
            api_name="binance"
        )
        self.api_secret = BINANCE_API_SECRET
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers with Binance API key"""
        headers = super()._prepare_headers(additional_headers)
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC SHA256 signature for authenticated requests
        
        Args:
            params: Request parameters
            
        Returns:
            Signature string
        """
        if not self.api_secret:
            return ""
            
        # Convert params to query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        # Create signature
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current cryptocurrency price
        
        Args:
            symbol: Binance trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
            
        Returns:
            Dictionary with price information
        """
        try:
            # Ensure symbol is in correct format
            symbol = symbol.upper()
            if not symbol.endswith("USDT") and not symbol.endswith("BTC") and not symbol.endswith("ETH"):
                symbol = f"{symbol}USDT"  # Default to USDT pair
            
            response = self.get("ticker/24hr", {"symbol": symbol})
            
            if "symbol" not in response:
                logger.warning(f"Invalid response format from Binance for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find cryptocurrency data for {symbol}"
                }
            
            # Format the data for our needs
            price_data = {
                "symbol": response.get("symbol", symbol),
                "price": float(response.get("lastPrice", 0)),
                "price_change": float(response.get("priceChange", 0)),
                "price_change_percent": float(response.get("priceChangePercent", 0)),
                "high_24h": float(response.get("highPrice", 0)),
                "low_24h": float(response.get("lowPrice", 0)),
                "volume_24h": float(response.get("volume", 0)),
                "quote_volume": float(response.get("quoteVolume", 0)),
                "open_price": float(response.get("openPrice", 0)),
                "close_price": float(response.get("lastPrice", 0)),
                "count": int(response.get("count", 0)),
                "last_updated": datetime.now().isoformat()
            }
            
            return price_data
        
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency price for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch cryptocurrency data: {str(e)}"
            }
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get exchange information including trading rules
        
        Args:
            symbol: Optional symbol to get specific trading info
            
        Returns:
            Dictionary with exchange information
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        
        try:
            response = self.get("exchangeInfo", params)
            
            if "symbols" not in response:
                logger.warning("Invalid response format from Binance exchange info")
                return {"error": "invalid_response"}
            
            return response
        
        except Exception as e:
            logger.error(f"Error fetching exchange info: {str(e)}")
            return {"error": "api_error", "message": str(e)}
    
    def get_historical_klines(self, symbol: str, interval: str = "1d", limit: int = 500) -> Dict[str, Any]:
        """
        Get historical klines (candlestick) data
        
        Args:
            symbol: Trading pair
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: Number of klines to return (max 1000)
            
        Returns:
            Dictionary with historical price data
        """
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000)  # Ensure we don't exceed API limit
        }
        
        try:
            response = self.get("klines", params)
            
            if not isinstance(response, list):
                logger.warning(f"Invalid response format from Binance klines for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find historical data for {symbol}"
                }
            
            # Format the data for our needs
            historical_data = {
                "symbol": symbol.upper(),
                "interval": interval,
                "data": []
            }
            
            # Binance kline format: [time, open, high, low, close, volume, ...]
            for kline in response:
                if len(kline) >= 6:
                    timestamp = kline[0]
                    date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    
                    historical_data["data"].append({
                        "time": timestamp,
                        "date": date,
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5])
                    })
            
            return historical_data
        
        except Exception as e:
            logger.error(f"Error fetching historical klines for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch historical data: {str(e)}"
            }
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        """
        Get latest price for a symbol or all symbols
        
        Args:
            symbol: Optional trading pair
            
        Returns:
            Dictionary with price data or list of price data for all symbols
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        
        try:
            response = self.get("ticker/price", params)
            
            if symbol and isinstance(response, dict) and "symbol" in response:
                return {
                    "symbol": response.get("symbol"),
                    "price": float(response.get("price", 0)),
                    "last_updated": datetime.now().isoformat()
                }
            elif isinstance(response, list):
                # Format all prices
                results = []
                for item in response:
                    results.append({
                        "symbol": item.get("symbol"),
                        "price": float(item.get("price", 0))
                    })
                return results
            else:
                logger.warning(f"Invalid response format from Binance ticker price for {symbol}")
                return {"error": "invalid_response"}
        
        except Exception as e:
            logger.error(f"Error fetching ticker price for {symbol if symbol else 'all symbols'}: {str(e)}")
            return {"error": "api_error", "message": str(e)}
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book for a symbol
        
        Args:
            symbol: Trading pair
            limit: Depth of order book (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Dictionary with order book data
        """
        params = {
            "symbol": symbol.upper(),
            "limit": min(limit, 5000)  # Ensure we don't exceed API limit
        }
        
        try:
            response = self.get("depth", params)
            
            if "bids" not in response or "asks" not in response:
                logger.warning(f"Invalid response format from Binance order book for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find order book data for {symbol}"
                }
            
            # Format the data for our needs
            order_book = {
                "symbol": symbol.upper(),
                "lastUpdateId": response.get("lastUpdateId", 0),
                "bids": [],
                "asks": []
            }
            
            # Process bids and asks (format: [price, quantity])
            for bid in response.get("bids", []):
                if len(bid) >= 2:
                    order_book["bids"].append({
                        "price": float(bid[0]),
                        "quantity": float(bid[1])
                    })
            
            for ask in response.get("asks", []):
                if len(ask) >= 2:
                    order_book["asks"].append({
                        "price": float(ask[0]),
                        "quantity": float(ask[1])
                    })
            
            return order_book
        
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch order book data: {str(e)}"
            } 