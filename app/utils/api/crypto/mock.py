"""
Mock cryptocurrency API client for development and testing
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import random

from app.utils.api.base import BaseAPIClient

logger = logging.getLogger(__name__)

class MockCryptoClient(BaseAPIClient):
    """Mock cryptocurrency client that returns simulated data"""
    
    def __init__(self):
        """Initialize mock client"""
        super().__init__(
            base_url="https://mock-crypto-api.example",
            api_key="mock-api-key",
            api_name="mock_crypto"
        )
        
        # Mock data - cryptocurrency prices and details
        self.crypto_data = {
            "BTC": {
                "id": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "slug": "bitcoin",
                "price": 62500.0,
                "volume_24h": 32500000000.0,
                "market_cap": 1230000000000.0,
                "circulating_supply": 19700000,
                "total_supply": 21000000,
                "max_supply": 21000000,
                "percent_change_1h": 0.12,
                "percent_change_24h": -1.43,
                "percent_change_7d": 2.87,
                "last_updated": datetime.now().isoformat(),
                "description": "Bitcoin is the first and most well-known cryptocurrency, operating on a decentralized ledger technology called blockchain."
            },
            "ETH": {
                "id": 2,
                "name": "Ethereum",
                "symbol": "ETH",
                "slug": "ethereum",
                "price": 3350.0,
                "volume_24h": 18900000000.0,
                "market_cap": 402000000000.0,
                "circulating_supply": 120000000,
                "total_supply": 120000000,
                "max_supply": None,
                "percent_change_1h": 0.08,
                "percent_change_24h": -0.92,
                "percent_change_7d": 1.54,
                "last_updated": datetime.now().isoformat(),
                "description": "Ethereum is a decentralized blockchain platform that enables the creation of smart contracts and decentralized applications."
            },
            "SOL": {
                "id": 3,
                "name": "Solana",
                "symbol": "SOL",
                "slug": "solana",
                "price": 140.0,
                "volume_24h": 2900000000.0,
                "market_cap": 62800000000.0,
                "circulating_supply": 448000000,
                "total_supply": 535000000,
                "max_supply": None,
                "percent_change_1h": 0.23,
                "percent_change_24h": 2.17,
                "percent_change_7d": 5.34,
                "last_updated": datetime.now().isoformat(),
                "description": "Solana is a high-performance blockchain that supports smart contracts and decentralized applications with fast transaction speeds."
            },
            "DOGE": {
                "id": 4,
                "name": "Dogecoin",
                "symbol": "DOGE",
                "slug": "dogecoin",
                "price": 0.142,
                "volume_24h": 1800000000.0,
                "market_cap": 19200000000.0,
                "circulating_supply": 135000000000,
                "total_supply": 135000000000,
                "max_supply": None,
                "percent_change_1h": -0.15,
                "percent_change_24h": -2.34,
                "percent_change_7d": -0.78,
                "last_updated": datetime.now().isoformat(),
                "description": "Dogecoin is a cryptocurrency that started as a meme but gained popularity as a payment method and through celebrity endorsements."
            },
            "USDT": {
                "id": 5,
                "name": "Tether",
                "symbol": "USDT",
                "slug": "tether",
                "price": 1.0,
                "volume_24h": 76500000000.0,
                "market_cap": 89500000000.0,
                "circulating_supply": 89500000000,
                "total_supply": 89500000000,
                "max_supply": None,
                "percent_change_1h": 0.0,
                "percent_change_24h": 0.01,
                "percent_change_7d": 0.02,
                "last_updated": datetime.now().isoformat(),
                "description": "Tether is a stablecoin pegged to the US dollar, designed to maintain a 1:1 value with fiat currency."
            },
            "ALCH": {
                "id": 6,
                "name": "Alchemy Pay",
                "symbol": "ALCH",
                "slug": "alchemy-pay",
                "price": 0.019,
                "volume_24h": 42000000.0,
                "market_cap": 126000000.0,
                "circulating_supply": 6700000000,
                "total_supply": 10000000000,
                "max_supply": 10000000000,
                "percent_change_1h": 0.45,
                "percent_change_24h": -3.21,
                "percent_change_7d": -7.92,
                "last_updated": datetime.now().isoformat(),
                "description": "Alchemy Pay is a payment solution that bridges fiat and crypto economies, allowing businesses to accept both cryptocurrency and fiat payments."
            },
            "SHIB": {
                "id": 7,
                "name": "Shiba Inu",
                "symbol": "SHIB",
                "slug": "shiba-inu",
                "price": 0.00002245,
                "volume_24h": 950000000.0,
                "market_cap": 13300000000.0,
                "circulating_supply": 589000000000000,
                "total_supply": 589000000000000,
                "max_supply": None,
                "percent_change_1h": 0.32,
                "percent_change_24h": -1.86,
                "percent_change_7d": 2.43,
                "last_updated": datetime.now().isoformat(),
                "description": "Shiba Inu is a meme token that has evolved into a vibrant ecosystem with DEX and NFT capabilities."
            },
            "LINK": {
                "id": 8,
                "name": "Chainlink",
                "symbol": "LINK",
                "slug": "chainlink",
                "price": 14.75,
                "volume_24h": 680000000.0,
                "market_cap": 8900000000.0,
                "circulating_supply": 603000000,
                "total_supply": 1000000000,
                "max_supply": 1000000000,
                "percent_change_1h": 0.18,
                "percent_change_24h": -0.95,
                "percent_change_7d": 3.17,
                "last_updated": datetime.now().isoformat(),
                "description": "Chainlink is a decentralized oracle network that provides real-world data to smart contracts on the blockchain."
            }
        }
        
        # Mock market data
        self.market_data = {
            "active_cryptocurrencies": 8965,
            "total_cryptocurrencies": 25234,
            "active_exchanges": 752,
            "total_exchanges": 1843,
            "btc_dominance": 52.4,
            "eth_dominance": 18.7,
            "total_market_cap": 2350000000000.0,
            "total_volume_24h": 98500000000.0,
            "altcoin_volume_24h": 65000000000.0,
            "altcoin_market_cap": 1120000000000.0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Mock trading pairs
        self.trading_pairs = [
            {"symbol": "BTCUSDT", "base_symbol": "BTC", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "ETHUSDT", "base_symbol": "ETH", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "SOLUSDT", "base_symbol": "SOL", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "DOGEUSDT", "base_symbol": "DOGE", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "SHIBUSDT", "base_symbol": "SHIB", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "LINKUSDT", "base_symbol": "LINK", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "ALCHUSDT", "base_symbol": "ALCH", "quote_symbol": "USDT", "status": "TRADING"},
            {"symbol": "ETHBTC", "base_symbol": "ETH", "quote_symbol": "BTC", "status": "TRADING"},
            {"symbol": "SOLBTC", "base_symbol": "SOL", "quote_symbol": "BTC", "status": "TRADING"},
            {"symbol": "LINKBTC", "base_symbol": "LINK", "quote_symbol": "BTC", "status": "TRADING"}
        ]
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize cryptocurrency symbol"""
        if symbol.startswith('$'):
            symbol = symbol[1:]
        return symbol.upper()
    
    def get_crypto_price(self, symbol: str, convert: str = "USD") -> Dict[str, Any]:
        """
        Get cryptocurrency price (mock implementation)
        
        Args:
            symbol: Cryptocurrency symbol
            convert: Currency to convert price to
            
        Returns:
            Dictionary with price data
        """
        try:
            # Normalize the symbol
            symbol = self._normalize_symbol(symbol)
            
            # Check if we have data for this symbol
            if symbol in self.crypto_data:
                # Add slight randomness to prices for testing
                data = self.crypto_data[symbol].copy()
                
                # Slightly randomize the price for testing
                price_change = random.uniform(-0.5, 0.5) / 100  # ±0.5% random change
                data["price"] = data["price"] * (1 + price_change)
                
                return data
            else:
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find cryptocurrency data for {symbol}"
                }
                
        except Exception as e:
            logger.error(f"Error in mock get_crypto_price: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Mock API error: {str(e)}"
            }
    
    def get_crypto_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed cryptocurrency information (mock implementation)
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Dictionary with detailed info
        """
        try:
            # Normalize the symbol
            symbol = self._normalize_symbol(symbol)
            
            # Check if we have data for this symbol
            if symbol in self.crypto_data:
                data = self.crypto_data[symbol].copy()
                
                # Format data in a more detailed structure
                return {
                    "id": data["id"],
                    "name": data["name"],
                    "symbol": data["symbol"],
                    "description": data["description"],
                    "market_data": {
                        "current_price": {
                            "usd": data["price"]
                        },
                        "market_cap": {
                            "usd": data["market_cap"]
                        },
                        "total_volume": {
                            "usd": data["volume_24h"]
                        },
                        "circulating_supply": data["circulating_supply"],
                        "total_supply": data["total_supply"],
                        "max_supply": data["max_supply"]
                    },
                    "last_updated": data["last_updated"]
                }
            else:
                return {
                    "symbol": symbol,
                    "error": "not_found",
                    "message": f"Could not find cryptocurrency data for {symbol}"
                }
                
        except Exception as e:
            logger.error(f"Error in mock get_crypto_details: {str(e)}")
            return {
                "symbol": symbol,
                "error": "api_error",
                "message": f"Mock API error: {str(e)}"
            }
    
    def get_historical_data(self, symbol: str, days: int = 30, interval: str = "daily") -> List[Dict[str, Any]]:
        """
        Get historical price data (mock implementation)
        
        Args:
            symbol: Cryptocurrency symbol
            days: Number of days of data to retrieve
            interval: Data interval (daily, hourly, etc.)
            
        Returns:
            List of historical data points
        """
        try:
            # Normalize the symbol
            symbol = self._normalize_symbol(symbol)
            
            # Check if we have data for this symbol
            if symbol not in self.crypto_data:
                return []
                
            data = self.crypto_data[symbol]
            current_price = data["price"]
            result = []
            
            # Generate mock historical data
            now = datetime.now()
            
            # Determine time increment based on interval
            if interval == "daily":
                time_increment = timedelta(days=1)
            elif interval == "hourly":
                time_increment = timedelta(hours=1)
            else:
                time_increment = timedelta(days=1)  # Default to daily
            
            # Generate the data
            for i in range(days):
                # Calculate the timestamp
                timestamp = now - (time_increment * i)
                
                # Generate a realistic price with some randomness
                # More recent prices should be closer to the current price
                volatility = 0.02  # 2% daily volatility
                days_ago = i
                random_change = random.uniform(-volatility, volatility) * (days_ago ** 0.5)
                historical_price = current_price * (1 - (random_change))
                
                # Add the data point
                result.append({
                    "timestamp": timestamp.isoformat(),
                    "price": historical_price,
                    "volume_24h": data["volume_24h"] * random.uniform(0.7, 1.3),
                    "market_cap": historical_price * data["circulating_supply"]
                })
            
            return result
                
        except Exception as e:
            logger.error(f"Error in mock get_historical_data: {str(e)}")
            return []
    
    def search_crypto(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies (mock implementation)
        
        Args:
            query: Search query
            
        Returns:
            List of matching cryptocurrencies
        """
        try:
            query = query.upper()
            results = []
            
            # Search by symbol exact match
            for symbol, data in self.crypto_data.items():
                if query == symbol:
                    results.append({
                        "id": data["id"],
                        "name": data["name"],
                        "symbol": data["symbol"],
                        "slug": data["slug"],
                        "description": data["description"]
                    })
                    return results  # Exact symbol match, return immediately
            
            # Search by name or symbol contains query
            for symbol, data in self.crypto_data.items():
                if query in symbol or query.lower() in data["name"].lower() or query.lower() in data["slug"].lower():
                    results.append({
                        "id": data["id"],
                        "name": data["name"],
                        "symbol": data["symbol"],
                        "slug": data["slug"],
                        "description": data["description"]
                    })
            
            return results
                
        except Exception as e:
            logger.error(f"Error in mock search_crypto: {str(e)}")
            return []
    
    def get_global_metrics(self, convert: str = "USD") -> Dict[str, Any]:
        """
        Get global market metrics (mock implementation)
        
        Args:
            convert: Currency to convert values to
            
        Returns:
            Dictionary with global market data
        """
        try:
            # Return a copy of our mock market data
            return self.market_data.copy()
                
        except Exception as e:
            logger.error(f"Error in mock get_global_metrics: {str(e)}")
            return {
                "error": "api_error",
                "message": f"Mock API error: {str(e)}"
            }
    
    def get_trading_pairs(self, base_symbol: Optional[str] = None, quote_symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trading pairs (mock implementation)
        
        Args:
            base_symbol: Filter by base symbol
            quote_symbol: Filter by quote symbol
            
        Returns:
            List of trading pairs
        """
        try:
            results = []
            
            for pair in self.trading_pairs:
                # Apply filters if specified
                if base_symbol and pair["base_symbol"] != base_symbol.upper():
                    continue
                    
                if quote_symbol and pair["quote_symbol"] != quote_symbol.upper():
                    continue
                
                results.append(pair.copy())
            
            return results
                
        except Exception as e:
            logger.error(f"Error in mock get_trading_pairs: {str(e)}")
            return [] 