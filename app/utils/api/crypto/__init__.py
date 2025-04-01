"""
Unified cryptocurrency API interface that handles multiple providers
"""

from typing import Dict, Any, Optional, List, Union
import logging
import re
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv

from app.utils.api.crypto.coingecko import CoinGeckoClient
from app.utils.api.crypto.coinmarketcap import CoinMarketCapClient
from app.utils.api.crypto.mock import MockCryptoClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CryptoAPI:
    """
    Unified interface for cryptocurrency data
    
    Handles failover between different providers and normalizes responses
    """
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize all crypto API clients
        
        Args:
            use_mock: Whether to use mock data (useful for development)
        """
        # Create API clients
        self.mock = MockCryptoClient() if use_mock else None
        
        # Initialize real API clients
        self.coingecko = CoinGeckoClient()
        
        # Get CoinMarketCap API key from environment
        coinmarketcap_api_key = os.getenv("COINMARKETCAP_API_KEY", "")
        if not coinmarketcap_api_key:
            logger.warning("CoinMarketCap API key not found in environment variables. Mock data will be used.")
        
        self.coinmarketcap = CoinMarketCapClient(api_key=coinmarketcap_api_key)
        
        # Provider priority by function (can be customized based on reliability)
        self.provider_priority = {
            "price": ["coingecko", "coinmarketcap", "mock"] if not use_mock else ["mock"],
            "details": ["coingecko", "coinmarketcap", "mock"] if not use_mock else ["mock"],
            "historical": ["coingecko", "mock"] if not use_mock else ["mock"],
            "search": ["coingecko", "mock"] if not use_mock else ["mock"],
            "market": ["coingecko", "mock"] if not use_mock else ["mock"]
        }
        
        self.cg = CoinGeckoAPI()
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Mock data for fallback
        self.mock_data = {
            "BTC": {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price": 45000.0,
                "market_cap": 850000000000,
                "market_cap_rank": 1,
                "total_volume": 25000000000,
                "high_24h": 46000.0,
                "low_24h": 44000.0,
                "price_change_24h": 500.0,
                "price_change_percentage_24h": 1.1,
                "last_updated": datetime.now().isoformat()
            },
            "ETH": {
                "id": "ethereum",
                "symbol": "ETH",
                "name": "Ethereum",
                "current_price": 2500.0,
                "market_cap": 300000000000,
                "market_cap_rank": 2,
                "total_volume": 15000000000,
                "high_24h": 2600.0,
                "low_24h": 2400.0,
                "price_change_24h": 50.0,
                "price_change_percentage_24h": 2.0,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize cryptocurrency symbol with improved mapping
        
        Args:
            symbol: Raw symbol (e.g., '$BTC', 'btc', 'Bitcoin')
            
        Returns:
            Normalized symbol for API calls
        """
        # Remove $ prefix and whitespace
        symbol = symbol.strip()
        if symbol.startswith('$'):
            symbol = symbol[1:]
            
        # Convert to uppercase
        symbol = symbol.upper()
        
        # Handle special cases and common names
        symbol_map = {
            "BITCOIN": "BTC",
            "ETHEREUM": "ETH",
            "LITECOIN": "LTC",
            "BITCOIN CASH": "BCH",
            "CARDANO": "ADA",
            "POLKADOT": "DOT",
            "RIPPLE": "XRP",
            "DOGECOIN": "DOGE",
            "SOLANA": "SOL",
            "POLYGON": "MATIC",
            "CHAINLINK": "LINK",
            "AVALANCHE": "AVAX",
            "UNISWAP": "UNI",
            "TETHER": "USDT",
            "USD COIN": "USDC",
            "SHIBA INU": "SHIB",
            "WRAPPED BITCOIN": "WBTC",
            "COSMOS": "ATOM",
            "NEAR PROTOCOL": "NEAR"
        }
        
        return symbol_map.get(symbol, symbol)
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict]:
        """
        Get cryptocurrency data in a format compatible with the chat service
        """
        try:
            # Normalize symbol
            symbol = symbol.upper()
            
            # Check cache first
            if symbol in self.cache:
                cached_data, timestamp = self.cache[symbol]
                if datetime.now() - timestamp < self.cache_duration:
                    return cached_data

            # Try to get real data from CoinGecko
            try:
                # For BTC and ETH which we know are supported
                if symbol in ["BTC", "ETH"]:
                    coin_id = "bitcoin" if symbol == "BTC" else "ethereum"
                    
                    data = self.cg.get_price(ids=coin_id, 
                                           vs_currencies='usd',
                                           include_24hr_change=True,
                                           include_market_cap=True,
                                           include_24hr_vol=True)
                    
                    if data and coin_id in data:
                        crypto_data = {
                            "symbol": symbol,
                            "price": data[coin_id]["usd"],
                            "change_percent": data[coin_id].get("usd_24h_change", 0),
                            "volume": data[coin_id].get("usd_24h_vol", 0),
                            "market_cap": data[coin_id].get("usd_market_cap", 0),
                            "high_24h": 0,  # CoinGecko basic API doesn't provide this
                            "low_24h": 0,   # CoinGecko basic API doesn't provide this
                            "timestamp": datetime.now().isoformat()
                        }
                        self.cache[symbol] = (crypto_data, datetime.now())
                        return crypto_data
            except Exception as e:
                logger.warning(f"CoinGecko failed for {symbol}: {str(e)}")

            # Try CoinMarketCap as backup
            try:
                if hasattr(self.coinmarketcap, 'api_key') and self.coinmarketcap.api_key:
                    # CoinMarketCap client doesn't have async methods, so we're just calling it directly
                    data = self.coinmarketcap.get_crypto_price(symbol)
                    if data and "error" not in data:
                        crypto_data = {
                            "symbol": symbol,
                            "price": float(data.get("price", 0)),
                            "change_percent": float(data.get("percent_change_24h", 0)),
                            "volume": float(data.get("volume_24h", 0)),
                            "market_cap": float(data.get("market_cap", 0)),
                            "high_24h": float(data.get("high_24h", 0)),
                            "low_24h": float(data.get("low_24h", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                        self.cache[symbol] = (crypto_data, datetime.now())
                        return crypto_data
            except Exception as e:
                logger.warning(f"CoinMarketCap failed for {symbol}: {str(e)}")

            # If real data fails, use mock data
            if symbol in self.mock_data:
                logger.info(f"Using mock data for {symbol}")
                mock_data = self.mock_data[symbol]
                crypto_data = {
                    "symbol": mock_data["symbol"],
                    "price": mock_data["current_price"],
                    "change_percent": mock_data["price_change_percentage_24h"],
                    "volume": mock_data["total_volume"],
                    "market_cap": mock_data["market_cap"],
                    "high_24h": mock_data["high_24h"],
                    "low_24h": mock_data["low_24h"],
                    "timestamp": mock_data["last_updated"]
                }
                self.cache[symbol] = (crypto_data, datetime.now())
                return crypto_data

            return None

        except Exception as e:
            logger.error(f"Error getting crypto data for {symbol}: {str(e)}")
            return None
    
    async def get_crypto_price(self, 
                        symbol: str, 
                        convert: str = "USD", 
                        preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current cryptocurrency price from the best available provider
        
        Args:
            symbol: Cryptocurrency symbol
            convert: Currency to convert price to
            preferred_provider: Preferred provider to use (if available)
            
        Returns:
            Dictionary with price information
        """
        # Normalize symbol
        symbol = self._normalize_symbol(symbol)
        
        # Use mock data as fallback
        mock_data = self.mock.get_crypto_price(symbol, convert) if self.mock else None

        # Try preferred provider first if specified
        if preferred_provider and preferred_provider in self.provider_priority["price"]:
            try:
                # Move preferred provider to front
                providers = self.provider_priority["price"].copy()
                providers.remove(preferred_provider)
                providers.insert(0, preferred_provider)
                
                for provider in providers:
                    if provider == "mock" and self.mock:
                        result = self.mock.get_crypto_price(symbol, convert)
                    elif provider == "coingecko":
                        result = self.coingecko.get_crypto_price(symbol, convert)
                    elif provider == "coinmarketcap":
                        result = self.coinmarketcap.get_crypto_price(symbol, convert)
                    
                    # Check if result contains error
                    if not result or "error" in result:
                        continue
                    
                    # Add provider info to result
                    result["provider"] = provider
                    return result
                
            except Exception as e:
                logger.error(f"Error getting {symbol} price from {preferred_provider}: {str(e)}")
        
        # Try all available providers
        for provider in self.provider_priority["price"]:
            if provider == "mock" and self.mock:
                result = self.mock.get_crypto_price(symbol, convert)
            elif provider == "coingecko":
                result = self.coingecko.get_crypto_price(symbol, convert)
            elif provider == "coinmarketcap":
                result = self.coinmarketcap.get_crypto_price(symbol, convert)
            
            # Check if result is empty
            if not result:
                continue
            
            # Add provider info to result (as first element's metadata)
            if len(result) > 0 and isinstance(result[0], dict):
                result[0]["provider"] = provider
            
            return result
        
        # Fall back to mock data if all else fails
        if mock_data:
            mock_data["provider"] = "mock"
            return mock_data
            
        return None
    
    def get_crypto_details(self, 
                          symbol: str, 
                          preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol
            preferred_provider: Preferred provider to use (if available)
            
        Returns:
            Dictionary with detailed information
        """
        # Normalize symbol
        symbol = self._normalize_symbol(symbol)
        
        # Determine provider order
        providers = self.provider_priority["details"].copy()
        if preferred_provider and preferred_provider in providers:
            # Move preferred provider to front
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)
        
        result = None
        errors = []
        
        # Try each provider in order
        for provider in providers:
            try:
                if provider == "mock" and self.mock:
                    result = self.mock.get_crypto_details(symbol)
                elif provider == "coingecko":
                    result = self.coingecko.get_crypto_details(symbol)
                elif provider == "coinmarketcap":
                    # Search first to get ID, then get details
                    search_results = self.coinmarketcap.search_crypto(symbol)
                    if search_results:
                        # Use the first result
                        result = {
                            "id": search_results[0].get("id"),
                            "name": search_results[0].get("name"),
                            "symbol": search_results[0].get("symbol"),
                            "description": search_results[0].get("description", ""),
                            "links": {
                                "website": search_results[0].get("website", [])
                            }
                        }
                        # Add price data
                        price_data = self.coinmarketcap.get_crypto_price(symbol)
                        if price_data and "error" not in price_data:
                            result.update({
                                "market_data": {
                                    "current_price": {"usd": price_data.get("price", 0)},
                                    "market_cap": {"usd": price_data.get("market_cap", 0)},
                                    "total_volume": {"usd": price_data.get("volume_24h", 0)},
                                }
                            })
                
                # Check if result contains error
                if not result or "error" in result:
                    errors.append(f"{provider}: {result.get('message') if result else 'No data'}")
                    continue
                
                # Add provider info to result
                result["provider"] = provider
                return result
                
            except Exception as e:
                logger.error(f"Error getting {symbol} details from {provider}: {str(e)}")
                errors.append(f"{provider}: {str(e)}")
        
        # All providers failed
        return {
            "symbol": symbol,
            "error": "all_providers_failed",
            "message": f"Failed to get details from all providers",
            "details": errors
        }
    
    def get_historical_data(self, 
                           symbol: str, 
                           days: int = 30, 
                           interval: str = "daily",
                           preferred_provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get historical price data for a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol
            days: Number of days of history to retrieve
            interval: Data interval (e.g. 'daily', 'hourly')
            preferred_provider: Preferred provider to use (if available)
            
        Returns:
            List of historical data points
        """
        # Normalize symbol
        symbol = self._normalize_symbol(symbol)
        
        # Map standard intervals to provider-specific formats
        interval_map = {
            "coingecko": {
                "daily": "daily",
                "hourly": "hourly",
                "minute": "minute",
                "15minute": "minute",  # Not supported directly
                "30minute": "minute",  # Not supported directly
                "4hour": "hourly",     # Not supported directly
                "weekly": "daily"      # Not supported directly
            }
        }
        
        # Determine provider order
        providers = self.provider_priority["historical"].copy()
        if preferred_provider and preferred_provider in providers:
            # Move preferred provider to front
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)
        
        result = None
        errors = []
        
        # Try each provider in order
        for provider in providers:
            try:
                if provider == "mock" and self.mock:
                    result = self.mock.get_historical_data(symbol, days, interval)
                elif provider == "coingecko":
                    provider_interval = interval_map["coingecko"].get(interval, "daily")
                    result = self.coingecko.get_historical_data(symbol, days, provider_interval)
                elif provider == "coinmarketcap":
                    # CoinMarketCap historical data requires PRO subscription, skip for now
                    continue
                
                # Check if result is empty
                if not result:
                    errors.append(f"{provider}: No data")
                    continue
                
                # Add provider info to result (as first element's metadata)
                if len(result) > 0 and isinstance(result[0], dict):
                    result[0]["provider"] = provider
                
                return result
                
            except Exception as e:
                logger.error(f"Error getting {symbol} historical data from {provider}: {str(e)}")
                errors.append(f"{provider}: {str(e)}")
        
        # All providers failed
        return []
    
    def search_crypto(self, 
                     query: str, 
                     preferred_provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies
        
        Args:
            query: Search query
            preferred_provider: Preferred provider to use (if available)
            
        Returns:
            List of matching cryptocurrencies
        """
        # Determine provider order
        providers = self.provider_priority["search"].copy()
        if preferred_provider and preferred_provider in providers:
            # Move preferred provider to front
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)
        
        all_results = []
        errors = []
        seen_symbols = set()
        
        # Try each provider in order
        for provider in providers:
            try:
                provider_results = []
                
                if provider == "mock" and self.mock:
                    provider_results = self.mock.search_crypto(query)
                elif provider == "coingecko":
                    provider_results = self.coingecko.search_crypto(query)
                elif provider == "coinmarketcap":
                    provider_results = self.coinmarketcap.search_crypto(query)
                
                # Add provider info and deduplicate
                for result in provider_results:
                    symbol = result.get("symbol", "").upper()
                    if symbol and symbol not in seen_symbols:
                        seen_symbols.add(symbol)
                        result["provider"] = provider
                        all_results.append(result)
                
            except Exception as e:
                logger.error(f"Error searching for '{query}' from {provider}: {str(e)}")
                errors.append(f"{provider}: {str(e)}")
        
        return all_results
    
    def get_market_summary(self, 
                          convert: str = "USD", 
                          preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cryptocurrency market summary
        
        Args:
            convert: Currency to convert values to
            preferred_provider: Preferred provider to use (if available)
            
        Returns:
            Dictionary with market summary
        """
        # Determine provider order
        providers = self.provider_priority["market"].copy()
        if preferred_provider and preferred_provider in providers:
            # Move preferred provider to front
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)
        
        result = None
        errors = []
        
        # Try each provider in order
        for provider in providers:
            try:
                if provider == "mock" and self.mock:
                    result = self.mock.get_global_metrics(convert)
                elif provider == "coinmarketcap":
                    result = self.coinmarketcap.get_global_metrics(convert)
                elif provider == "coingecko":
                    # CoinGecko doesn't have a direct global metrics endpoint
                    # We can compose it from multiple endpoints
                    global_data = {}
                    
                    # Get top coins to calculate metrics
                    top_coins = self.coingecko.get_crypto_listings(limit=20, convert=convert)
                    
                    if top_coins:
                        # Calculate basic metrics
                        btc_market_cap = 0
                        eth_market_cap = 0
                        total_market_cap = 0
                        
                        for coin in top_coins:
                            if coin.get("symbol") == "BTC":
                                btc_market_cap = coin.get("market_cap", 0)
                            elif coin.get("symbol") == "ETH":
                                eth_market_cap = coin.get("market_cap", 0)
                            total_market_cap += coin.get("market_cap", 0)
                        
                        # Calculate dominance
                        btc_dominance = (btc_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
                        eth_dominance = (eth_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
                        
                        global_data = {
                            "active_cryptocurrencies": len(top_coins),
                            "btc_dominance": btc_dominance,
                            "eth_dominance": eth_dominance,
                            "total_market_cap": total_market_cap,
                            "last_updated": top_coins[0].get("last_updated") if top_coins else None
                        }
                        
                        result = global_data
                
                # Check if result contains error
                if not result or "error" in result:
                    errors.append(f"{provider}: {result.get('message') if result else 'No data'}")
                    continue
                
                # Add provider info to result
                result["provider"] = provider
                return result
                
            except Exception as e:
                logger.error(f"Error getting market summary from {provider}: {str(e)}")
                errors.append(f"{provider}: {str(e)}")
        
        # All providers failed
        return {
            "error": "all_providers_failed",
            "message": f"Failed to get market summary from all providers",
            "details": errors
        }
    
    def get_trading_pairs(self, 
                         base_symbol: Optional[str] = None, 
                         quote_symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available trading pairs
        
        Args:
            base_symbol: Filter by base symbol (e.g., 'BTC')
            quote_symbol: Filter by quote symbol (e.g., 'USD')
            
        Returns:
            List of trading pairs
        """
        try:
            # Try mock first if available
            if self.mock:
                pairs = self.mock.get_trading_pairs(base_symbol, quote_symbol)
                if pairs:
                    for pair in pairs:
                        pair["provider"] = "mock"
                    return pairs
            
            # If no mock or no results from mock, try CoinMarketCap
            # CoinMarketCap is the best source for trading pairs
            pairs = self.coinmarketcap.get_trading_pairs(base_symbol, quote_symbol)
            
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching trading pairs: {str(e)}")
            return []
    
    def get_price(self, symbol: str, convert: str = "USD") -> Dict[str, Any]:
        """
        Get current cryptocurrency price with improved error handling
        
        Args:
            symbol: Cryptocurrency symbol
            convert: Currency to convert price to
            
        Returns:
            Dictionary with price information or error details
        """
        try:
            # Normalize symbol
            symbol = self._normalize_symbol(symbol)
            
            # Try to get price data
            result = self.get_crypto_price(symbol, convert)
            
            # Check for errors
            if not result or "error" in result:
                return {
                    "error": "Failed to fetch price data",
                    "details": result.get("message", "Unknown error") if result else "No data returned"
                }
            
            # Format the response
            return {
                "price": float(result.get("price", 0)),
                "percent_change_24h": float(result.get("percent_change_24h", 0)),
                "market_cap": float(result.get("market_cap", 0)),
                "volume_24h": float(result.get("volume_24h", 0)),
                "symbol": symbol,
                "name": result.get("name", symbol),
                "provider": result.get("provider", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error in get_price for {symbol}: {str(e)}")
            return {
                "error": "Internal error",
                "details": str(e)
            }

    def _validate_crypto_price(self, data):
        """Validate crypto price data has required fields"""
        required_fields = ['price', 'percent_change_24h', 'market_cap']
        return all(field in data for field in required_fields) 