"""
CoinGecko API client for cryptocurrency data
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import time
import requests
import os
import asyncio

from app.utils.api.base import BaseAPIClient

logger = logging.getLogger(__name__)

class CoinGeckoClient(BaseAPIClient):
    """
    CoinGecko API client for cryptocurrency data
    Free tier with rate limits - handle appropriately
    """
    
    def __init__(self):
        """Initialize the CoinGecko API client"""
        base_url = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
        super().__init__(
            base_url=base_url,
            api_key=None,  # CoinGecko free tier doesn't require an API key
            api_name="coingecko"
        )
        # Common cryptocurrency symbol to CoinGecko ID mapping
        self.symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "USDC": "usd-coin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOGE": "dogecoin",
            "TRX": "tron",
            "LINK": "chainlink",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "TON": "the-open-network",
            "SHIB": "shiba-inu",
            "LTC": "litecoin",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "XLM": "stellar",
            "BCH": "bitcoin-cash",
            "NEAR": "near",
            "INJ": "injective-protocol",
            "APT": "aptos",
            "XMR": "monero",
            "OP": "optimism",
            "ICP": "internet-computer",
            "FIL": "filecoin",
            "VET": "vechain",
            "MNT": "mantle",
            "HBAR": "hedera-hashgraph",
            "ALCH": "alchemy-pay",
            "DAI": "dai",
            "OKB": "okb"
        }
        
        # Database of funded crypto/web3 projects and emerging technologies
        self.funded_projects = {
            # AGI/AI Projects
            "AGIX": {
                "name": "SingularityNET",
                "category": "AGI",
                "funding": "$36M ICO",
                "mcap": "$800M",
                "description": "Decentralized marketplace for AI services, aiming to become the key protocol for networking AI systems together into emergent AGI."
            },
            "FET": {
                "name": "Fetch.ai",
                "category": "AGI",
                "funding": "$24M",
                "mcap": "$1.1B",
                "description": "Decentralized machine learning platform building an open, permissionless, decentralized machine learning network to enable smart infrastructure built around a decentralized digital economy."
            },
            "OCEAN": {
                "name": "Ocean Protocol",
                "category": "AGI",
                "funding": "$32M",
                "mcap": "$330M",
                "description": "Decentralized data exchange protocol to unlock data for AI. Allows data to be shared while preserving privacy and control."
            }
        }
        
        # Track API calls to respect rate limits
        self.last_api_call = 0
        self.min_call_interval = 6  # seconds between calls for free tier
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_call_interval:
            # Sleep to respect rate limit
            sleep_time = self.min_call_interval - time_since_last_call
            logger.debug(f"Rate limiting - sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def _get_coin_id(self, symbol: str) -> str:
        """Get CoinGecko coin ID from symbol"""
        symbol = symbol.upper()
        if symbol in self.symbol_to_id:
            return self.symbol_to_id[symbol]
        
        # Try to search for the coin if not in mapping
        try:
            self._respect_rate_limit()
            response = requests.get(f"{self.base_url}/coins/list")
            if response.status_code == 200:
                coins = response.json()
                for coin in coins:
                    if coin.get('symbol', '').upper() == symbol:
                        return coin.get('id')
            
            logger.warning(f"Could not find CoinGecko ID for {symbol}")
            return symbol.lower()  # fallback
        except Exception as e:
            logger.error(f"Error finding coin ID: {str(e)}")
            return symbol.lower()  # fallback
    
    def get_crypto_price(self, symbol: str, currency: str = "USD") -> Optional[Dict[str, Any]]:
        """
        Get current price for a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC)
            currency: Currency to get price in (e.g., USD)
            
        Returns:
            Dictionary with price data or None if not found
        """
        try:
            coin_id = self._get_coin_id(symbol)
            self._respect_rate_limit()
            
            # Get market data for more comprehensive information
            url = f"{self.base_url}/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
            logger.debug(f"Fetching data from {url}")
            
            response = requests.get(url)
            
            # Check for errors
            if response.status_code == 429:
                logger.warning(f"Rate limit exceeded for CoinGecko API")
                raise Exception("Rate limit exceeded")
            
            if response.status_code != 200:
                logger.error(f"HTTP error from coingecko: HTTP {response.status_code}")
                raise Exception(f"API request failed: HTTP {response.status_code}")
            
            data = response.json()
            
            if not data or "market_data" not in data:
                logger.error(f"Invalid response from coingecko/coins/{coin_id}: {data}")
                raise Exception("API request failed: Invalid response format")
            
            market_data = data["market_data"]
            currency = currency.lower()
            
            # Construct result
            result = {
                "symbol": symbol.upper(),
                "name": data.get("name", symbol.upper()),
                "price": market_data["current_price"].get(currency, 0),
                "market_cap": market_data["market_cap"].get(currency, 0),
                "percent_change_24h": market_data["price_change_percentage_24h"] or 0,
                "volume_24h": market_data["total_volume"].get(currency, 0)
            }
            
            # Add high and low if available
            if "high_24h" in market_data and "low_24h" in market_data:
                result["high_24h"] = market_data["high_24h"].get(currency, 0)
                result["low_24h"] = market_data["low_24h"].get(currency, 0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency details for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 7, interval: str = "daily", currency: str = "usd") -> Optional[Dict[str, Any]]:
        """
        Get historical price data for a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC)
            days: Number of days of data to retrieve (1, 7, 14, 30, 90, etc.)
            interval: Data interval (daily, hourly)
            currency: Currency for price data (USD, EUR, etc.)
            
        Returns:
            Dictionary with historical data or None if error
        """
        try:
            coin_id = self._get_coin_id(symbol)
            self._respect_rate_limit()
            
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": currency.lower(),
                "days": days,
                "interval": "daily" if interval == "daily" else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = requests.get(url, params=params)
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"HTTP error from coingecko: HTTP {response.status_code}")
                raise Exception(f"API request failed: HTTP {response.status_code}")
            
            data = response.json()
            
            if not data or "prices" not in data:
                logger.error(f"Invalid response from coingecko/coins/{coin_id}/market_chart: {data}")
                raise Exception("API request failed: Invalid response format")
            
            # Format the data for easier consumption
            prices = []
            timestamps = []
            for price_data in data["prices"]:
                timestamp, price = price_data
                timestamps.append(timestamp)
                prices.append(price)
            
            volumes = []
            for volume_data in data.get("total_volumes", []):
                _, volume = volume_data
                volumes.append(volume)
            
            market_caps = []
            for market_cap_data in data.get("market_caps", []):
                _, market_cap = market_cap_data
                market_caps.append(market_cap)
            
            return {
                "symbol": symbol,
                "timestamps": timestamps,
                "prices": prices,
                "volumes": volumes,
                "market_caps": market_caps
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def search_cryptocurrency(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies by name or symbol
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching cryptocurrencies
        """
        try:
            self._respect_rate_limit()
            
            response = requests.get(f"{self.base_url}/search?query={query}")
            
            if response.status_code != 200:
                logger.error(f"HTTP error from coingecko: HTTP {response.status_code}")
                return []
            
            data = response.json()
            
            if not data or "coins" not in data:
                return []
            
            coins = data["coins"][:limit]
            
            results = []
            for coin in coins:
                results.append({
                    "id": coin.get("id", ""),
                    "name": coin.get("name", ""),
                    "symbol": coin.get("symbol", "").upper(),
                    "market_cap_rank": coin.get("market_cap_rank", 0),
                    "thumb": coin.get("thumb", ""),
                    "provider": "coingecko"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching for cryptocurrencies: {str(e)}")
            return []
    
    def get_crypto_details(self, crypto_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a cryptocurrency
        
        Args:
            crypto_id: CoinGecko cryptocurrency ID
            
        Returns:
            Dictionary with detailed information
        """
        try:
            response = self.get(f"coins/{crypto_id}", {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false"
            })
            
            if "id" not in response:
                logger.warning(f"Invalid response format from CoinGecko details for {crypto_id}")
                return {
                    "id": crypto_id,
                    "error": "not_found",
                    "message": f"Could not find details for {crypto_id}"
                }
            
            # Extract relevant information
            market_data = response.get("market_data", {})
            
            crypto_details = {
                "id": response.get("id", ""),
                "symbol": response.get("symbol", "").upper(),
                "name": response.get("name", ""),
                "description": response.get("description", {}).get("en", ""),
                "image": response.get("image", {}).get("large", ""),
                "current_price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "market_cap_rank": market_data.get("market_cap_rank", 0),
                "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "price_change_percentage_24h": market_data.get("price_change_percentage_24h", 0),
                "market_cap_change_24h": market_data.get("market_cap_change_24h", 0),
                "market_cap_change_percentage_24h": market_data.get("market_cap_change_percentage_24h", 0),
                "circulating_supply": market_data.get("circulating_supply", 0),
                "total_supply": market_data.get("total_supply", 0),
                "max_supply": market_data.get("max_supply", 0),
                "ath": market_data.get("ath", {}).get("usd", 0),
                "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd", 0),
                "ath_date": market_data.get("ath_date", {}).get("usd", ""),
                "atl": market_data.get("atl", {}).get("usd", 0),
                "atl_change_percentage": market_data.get("atl_change_percentage", {}).get("usd", 0),
                "atl_date": market_data.get("atl_date", {}).get("usd", ""),
                "last_updated": market_data.get("last_updated", datetime.now().isoformat())
            }
            
            # Add community data if available
            community_data = response.get("community_data", {})
            if community_data:
                crypto_details["community_data"] = {
                    "twitter_followers": community_data.get("twitter_followers", 0),
                    "reddit_subscribers": community_data.get("reddit_subscribers", 0),
                    "telegram_channel_user_count": community_data.get("telegram_channel_user_count", 0),
                }
            
            return crypto_details
        
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency details for {crypto_id}: {str(e)}")
            return {
                "id": crypto_id,
                "error": "api_error",
                "message": f"Failed to fetch cryptocurrency details: {str(e)}"
            }
    
    def get_trending_coins(self) -> List[Dict[str, Any]]:
        """
        Get trending cryptocurrencies
        
        Returns:
            List of trending cryptocurrencies
        """
        try:
            response = self.get("search/trending", {})
            
            if "coins" not in response:
                logger.warning("Invalid response format from CoinGecko trending")
                return []
            
            results = []
            for item in response.get("coins", []):
                coin = item.get("item", {})
                results.append({
                    "id": coin.get("id", ""),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name", ""),
                    "market_cap_rank": coin.get("market_cap_rank", 0),
                    "thumb": coin.get("thumb", ""),
                    "large": coin.get("large", ""),
                    "score": coin.get("score", 0)
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error fetching trending cryptocurrencies: {str(e)}")
            return []
            
    def get_project_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get information about a well-funded crypto/web3 project
        
        Args:
            symbol: Project symbol/ticker (e.g., 'FET', 'ZETA', 'WORLDCOIN')
            
        Returns:
            Dictionary with project information or None if not found
        """
        symbol = symbol.upper()
        
        # Check if it's in our database of funded projects
        if symbol in self.funded_projects:
            return {
                "symbol": symbol,
                "found": True,
                "source": "internal_db",
                **self.funded_projects[symbol]
            }
            
        # If not in our database, try to get price and add a note
        price_data = self.get_crypto_price(symbol)
        if price_data and "error" not in price_data:
            return {
                "symbol": symbol,
                "name": price_data.get("name", symbol),
                "found": True,
                "source": "price_data",
                "price": price_data.get("price", 0),
                "market_cap": price_data.get("market_cap", 0),
                "note": "This project is not in our curated list of well-funded crypto/web3 projects or emerging technologies."
            }
            
        return {
            "symbol": symbol,
            "found": False,
            "message": f"Could not find information about {symbol}. It may not be a well-known or well-funded crypto/web3 project."
        }
        
    def get_projects_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get crypto/web3 projects by category
        
        Args:
            category: Category to filter by (e.g., 'AGI', 'Layer 1', 'Layer 2', 'DeFi')
            
        Returns:
            List of projects in the specified category
        """
        results = []
        category = category.lower()
        
        for symbol, data in self.funded_projects.items():
            if category in data.get("category", "").lower():
                results.append({
                    "symbol": symbol,
                    **data
                })
                
        return results 