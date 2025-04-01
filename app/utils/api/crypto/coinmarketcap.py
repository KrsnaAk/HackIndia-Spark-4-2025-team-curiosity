"""
CoinMarketCap API client for cryptocurrency data
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

class CoinMarketCapClient(BaseAPIClient):
    """Client for CoinMarketCap cryptocurrency APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize CoinMarketCap API client"""
        # Get base URL from environment or use default
        base_url = os.getenv("COINMARKETCAP_BASE_URL", "https://pro-api.coinmarketcap.com/v1")
        
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("COINMARKETCAP_API_KEY", "")
        
        if not self.api_key:
            logger.warning("No CoinMarketCap API key provided. API calls will likely fail.")
        
        super().__init__(
            base_url=base_url,
            api_key=self.api_key,
            api_name="coinmarketcap"
        )
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers with CoinMarketCap API key"""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Finance-Chatbot/1.0"
        }
        
        # CoinMarketCap uses X-CMC_PRO_API_KEY header
        if self.api_key:
            headers["X-CMC_PRO_API_KEY"] = self.api_key
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def get_crypto_price(self, symbol: str, convert: str = "USD") -> Dict[str, Any]:
        """
        Get current cryptocurrency price
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            convert: Currency to convert price to
            
        Returns:
            Dictionary with price information
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()
            
            params = {
                "symbol": symbol,
                "convert": convert
            }
            
            response = self.get("cryptocurrency/quotes/latest", params=params)
            
            if "data" not in response or symbol not in response["data"]:
                logger.warning(f"Invalid response format from CoinMarketCap for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find cryptocurrency data for {symbol}"
                }
            
            crypto_data = response["data"][symbol]
            quote_data = crypto_data.get("quote", {}).get(convert, {})
            
            # Format the data for our needs
            price_data = {
                "id": crypto_data.get("id", 0),
                "name": crypto_data.get("name", ""),
                "symbol": symbol,
                "slug": crypto_data.get("slug", ""),
                "price": quote_data.get("price", 0),
                "volume_24h": quote_data.get("volume_24h", 0),
                "market_cap": quote_data.get("market_cap", 0),
                "circulating_supply": crypto_data.get("circulating_supply", 0),
                "total_supply": crypto_data.get("total_supply", 0),
                "max_supply": crypto_data.get("max_supply", 0),
                "percent_change_1h": quote_data.get("percent_change_1h", 0),
                "percent_change_24h": quote_data.get("percent_change_24h", 0),
                "percent_change_7d": quote_data.get("percent_change_7d", 0),
                "last_updated": quote_data.get("last_updated", datetime.now().isoformat())
            }
            
            return price_data
        
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency price for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Failed to fetch cryptocurrency data: {str(e)}"
            }
    
    def get_crypto_listings(self, limit: int = 100, convert: str = "USD", sort: str = "market_cap") -> List[Dict[str, Any]]:
        """
        Get list of cryptocurrencies sorted by specified criteria
        
        Args:
            limit: Number of cryptocurrencies to return
            convert: Currency to convert prices to
            sort: Sort criteria (market_cap, volume_24h, percent_change_24h, etc.)
            
        Returns:
            List of cryptocurrency data
        """
        params = {
            "start": 1,
            "limit": min(limit, 5000),  # Ensure we don't exceed API limit
            "convert": convert,
            "sort": sort,
            "sort_dir": "desc"
        }
        
        try:
            response = self.get("cryptocurrency/listings/latest", params=params)
            
            if "data" not in response:
                logger.warning("Invalid response format from CoinMarketCap listings")
                return []
            
            results = []
            for crypto in response["data"]:
                quote_data = crypto.get("quote", {}).get(convert, {})
                
                results.append({
                    "id": crypto.get("id", 0),
                    "name": crypto.get("name", ""),
                    "symbol": crypto.get("symbol", ""),
                    "slug": crypto.get("slug", ""),
                    "rank": crypto.get("cmc_rank", 0),
                    "price": quote_data.get("price", 0),
                    "market_cap": quote_data.get("market_cap", 0),
                    "volume_24h": quote_data.get("volume_24h", 0),
                    "percent_change_24h": quote_data.get("percent_change_24h", 0),
                    "percent_change_7d": quote_data.get("percent_change_7d", 0),
                    "circulating_supply": crypto.get("circulating_supply", 0),
                    "total_supply": crypto.get("total_supply", 0),
                    "max_supply": crypto.get("max_supply", 0)
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency listings: {str(e)}")
            return []
    
    def search_crypto(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies
        
        Args:
            query: Search query
            
        Returns:
            List of matching cryptocurrencies
        """
        try:
            # Use the metadata endpoint to search
            response = self.get("cryptocurrency/info", {"slug": query})
            
            if "data" not in response:
                # Try again with symbol
                response = self.get("cryptocurrency/info", {"symbol": query.upper()})
                
                if "data" not in response:
                    # Still no match, return empty list
                    return []
            
            results = []
            for crypto_id, crypto_data in response["data"].items():
                results.append({
                    "id": int(crypto_id),
                    "name": crypto_data.get("name", ""),
                    "symbol": crypto_data.get("symbol", ""),
                    "slug": crypto_data.get("slug", ""),
                    "logo": crypto_data.get("logo", ""),
                    "description": crypto_data.get("description", ""),
                    "website": crypto_data.get("urls", {}).get("website", [])
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching cryptocurrencies with query '{query}': {str(e)}")
            return []
    
    def get_global_metrics(self, convert: str = "USD") -> Dict[str, Any]:
        """
        Get global cryptocurrency market metrics
        
        Args:
            convert: Currency to convert values to
            
        Returns:
            Dictionary with global market metrics
        """
        params = {
            "convert": convert
        }
        
        try:
            response = self.get("global-metrics/quotes/latest", params=params)
            
            if "data" not in response:
                logger.warning("Invalid response format from CoinMarketCap global metrics")
                return {"error": "invalid_response"}
            
            data = response["data"]
            quote_data = data.get("quote", {}).get(convert, {})
            
            metrics = {
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
                "total_cryptocurrencies": data.get("total_cryptocurrencies", 0),
                "active_exchanges": data.get("active_exchanges", 0),
                "total_exchanges": data.get("total_exchanges", 0),
                "btc_dominance": data.get("btc_dominance", 0),
                "eth_dominance": data.get("eth_dominance", 0),
                "total_market_cap": quote_data.get("total_market_cap", 0),
                "total_volume_24h": quote_data.get("total_volume_24h", 0),
                "altcoin_volume_24h": quote_data.get("altcoin_volume_24h", 0),
                "altcoin_market_cap": quote_data.get("altcoin_market_cap", 0),
                "last_updated": data.get("last_updated", datetime.now().isoformat())
            }
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error fetching global metrics: {str(e)}")
            return {"error": "api_error", "message": str(e)}
    
    def get_exchange_info(self, slug: str, convert: str = "USD") -> Dict[str, Any]:
        """
        Get information about a specific exchange
        
        Args:
            slug: Exchange slug (e.g., 'binance', 'coinbase')
            convert: Currency to convert values to
            
        Returns:
            Dictionary with exchange information
        """
        params = {
            "slug": slug,
            "convert": convert
        }
        
        try:
            response = self.get("exchange/info", params=params)
            
            if "data" not in response:
                logger.warning(f"Invalid response format from CoinMarketCap for exchange {slug}")
                return {
                    "slug": slug,
                    "error": "not_found",
                    "message": f"Could not find exchange data for {slug}"
                }
            
            # There should be only one exchange returned, get its ID
            exchange_id = list(response["data"].keys())[0]
            exchange_data = response["data"][exchange_id]
            
            return exchange_data
        
        except Exception as e:
            logger.error(f"Error fetching exchange info for {slug}: {str(e)}")
            return {
                "slug": slug,
                "error": "api_error",
                "message": f"Failed to fetch exchange data: {str(e)}"
            } 