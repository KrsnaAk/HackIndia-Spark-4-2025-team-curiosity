"""
Unified cryptocurrency API interface that handles multiple providers
"""

from typing import Dict, Any, Optional, List, Union
import logging
import re
import os

from app.utils.api.crypto.coingecko import CoinGeckoClient
from app.utils.api.crypto.binance import BinanceClient
from app.utils.api.crypto.coinmarketcap import CoinMarketCapClient
from app.utils.api.crypto.mock import MockCryptoClient

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
        # self.binance = BinanceClient()  # To be added later
        # self.coinmarketcap = CoinMarketCapClient(
        #     api_key=os.getenv("COINMARKETCAP_API_KEY")
        # )
        
        # Provider priority by function (can be customized based on reliability)
        self.provider_priority = {
            "price": ["coingecko", "mock"] if not use_mock else ["mock"],
            "details": ["coingecko", "mock"] if not use_mock else ["mock"],
            "historical": ["coingecko", "mock"] if not use_mock else ["mock"],
            "search": ["coingecko", "mock"] if not use_mock else ["mock"],
            "market": ["coingecko", "mock"] if not use_mock else ["mock"]
        }
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize cryptocurrency symbol
        
        Args:
            symbol: Raw symbol (e.g., '$BTC', 'btc', 'Bitcoin')
            
        Returns:
            Normalized symbol for API calls
        """
        # Remove $ prefix if present
        if symbol.startswith('$'):
            symbol = symbol[1:]
            
        # Convert to uppercase
        symbol = symbol.upper()
        
        # Handle special cases
        symbol_map = {
            "BITCOIN": "BTC",
            "ETHEREUM": "ETH",
            "LITECOIN": "LTC",
            "BITCOIN CASH": "BCH",
            "BINANCE COIN": "BNB",
            "CARDANO": "ADA",
            "POLKADOT": "DOT",
            "RIPPLE": "XRP",
            "DOGECOIN": "DOGE",
            "SOLANA": "SOL",
        }
        
        return symbol_map.get(symbol, symbol)
    
    def get_crypto_price(self, 
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
        
        # Determine provider order
        providers = self.provider_priority["price"].copy()
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
                    result = self.mock.get_crypto_price(symbol, convert)
                elif provider == "coingecko":
                    result = self.coingecko.get_crypto_price(symbol, convert)
                elif provider == "binance":
                    # Binance requires a trading pair
                    trading_pair = f"{symbol}{convert}"
                    result = self.binance.get_crypto_price(trading_pair)
                elif provider == "coinmarketcap":
                    result = self.coinmarketcap.get_crypto_price(symbol, convert)
                
                # Check if result contains error
                if not result or "error" in result:
                    errors.append(f"{provider}: {result.get('message') if result else 'No data'}")
                    continue
                
                # Add provider info to result
                result["provider"] = provider
                return result
                
            except Exception as e:
                logger.error(f"Error getting {symbol} price from {provider}: {str(e)}")
                errors.append(f"{provider}: {str(e)}")
        
        # All providers failed
        return {
            "symbol": symbol,
            "error": "all_providers_failed",
            "message": f"Failed to get price data from all providers",
            "details": errors
        }
    
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
            "binance": {
                "daily": "1d",
                "hourly": "1h",
                "minute": "1m",
                "15minute": "15m",
                "30minute": "30m",
                "4hour": "4h",
                "weekly": "1w"
            },
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
                elif provider == "binance":
                    # Binance requires a trading pair
                    trading_pair = f"{symbol}USDT"
                    provider_interval = interval_map["binance"].get(interval, "1d")
                    result = self.binance.get_historical_klines(trading_pair, provider_interval, limit=days)
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
            
            # If no mock or no results from mock, try Binance
            # Binance is the best source for trading pairs
            exchange_info = self.binance.get_exchange_info()
            
            if "symbols" not in exchange_info:
                return []
            
            pairs = []
            
            for symbol_info in exchange_info["symbols"]:
                base = symbol_info.get("baseAsset", "").upper()
                quote = symbol_info.get("quoteAsset", "").upper()
                
                # Apply filters if specified
                if base_symbol and base != base_symbol.upper():
                    continue
                    
                if quote_symbol and quote != quote_symbol.upper():
                    continue
                
                pairs.append({
                    "symbol": symbol_info.get("symbol", ""),
                    "base_symbol": base,
                    "quote_symbol": quote,
                    "status": symbol_info.get("status", ""),
                    "provider": "binance"
                })
            
            return pairs
            
        except Exception as e:
            logger.error(f"Error fetching trading pairs: {str(e)}")
            return [] 