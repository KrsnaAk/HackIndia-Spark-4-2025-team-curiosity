# Stock Market API Module

from app.utils.api.stock.alpha_vantage import AlphaVantageClient
from app.utils.api.stock.yahoo_finance import YahooFinanceClient
from app.utils.api.stock.nse_india import NSEIndiaClient
from app.utils.api.stock.finnhub import FinnhubAPI

from typing import Dict, Any, List, Optional, Literal
import logging
import aiohttp
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class StockMarketAPI:
    """
    Unified API client for stock market data from multiple providers
    """
    def __init__(self):
        self.nse = NSEIndiaClient()
        self.yahoo = YahooFinanceClient()
        self.alpha_vantage = AlphaVantageClient(api_key=os.getenv("ALPHA_VANTAGE_API_KEY"))
        self.finnhub = FinnhubAPI(api_key=os.getenv("FINNHUB_API_KEY"))
        self.base_url = "https://api.polygon.io/v2"
        self.api_key = "YOUR_POLYGON_API_KEY"  # Replace with actual API key
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock price data, trying multiple providers in sequence
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT', 'RELIANCE.NS')
            
        Returns:
            Dict containing stock price data
        """
        # Try Finnhub first (best real-time data)
        try:
            data = await self.finnhub.get_stock_price(symbol)
            if data and "error" not in data:
                return data
            logger.warning(f"Finnhub failed for {symbol}, trying NSE India")
        except Exception as e:
            logger.warning(f"Finnhub error for {symbol}: {str(e)}")
        
        # Try NSE India for Indian stocks
        if ".NS" in symbol or any(indian in symbol.upper() for indian in ["NSE:", "BSE:", "RELIANCE", "TCS", "INFY"]):
            try:
                data = self.nse.get_stock_price(symbol)
                if data and "error" not in data:
                    return data
                logger.warning(f"NSE India failed for {symbol}, trying Yahoo Finance")
            except Exception as e:
                logger.warning(f"NSE India error for {symbol}: {str(e)}")
        
        # Try Yahoo Finance
        try:
            data = self.yahoo.get_stock_price(symbol)
            if data and "error" not in data:
                return data
            logger.warning(f"Yahoo Finance failed for {symbol}, trying Alpha Vantage")
        except Exception as e:
            logger.warning(f"Yahoo Finance error for {symbol}: {str(e)}")
        
        # Try Alpha Vantage as last resort
        try:
            data = self.alpha_vantage.get_stock_price(symbol)
            if data and "error" not in data:
                return data
            logger.warning(f"Alpha Vantage failed for {symbol}")
        except Exception as e:
            logger.warning(f"Alpha Vantage error for {symbol}: {str(e)}")
        
        return {"error": f"Could not fetch stock price for {symbol} from any provider"}
    
    async def search_symbol(self, query: str) -> Optional[str]:
        """
        Search for a stock symbol across providers
        
        Args:
            query: Search query (company name or symbol)
            
        Returns:
            Best matching symbol or None if not found
        """
        # Try Finnhub first
        try:
            symbol = await self.finnhub.search_symbol(query)
            if symbol:
                return symbol
        except Exception:
            pass
        
        # Try other providers if Finnhub fails
        for provider in [self.yahoo, self.alpha_vantage, self.nse]:
            try:
                symbol = await provider.search_symbol(query)
                if symbol:
                    return symbol
            except Exception:
                continue
        
        return None
    
    def get_historical_data(self, 
                          symbol: str, 
                          interval: str = "daily", 
                          period: str = "1mo", 
                          provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical price data with failover between providers
        
        Args:
            symbol: Stock symbol
            interval: Time interval ('daily', 'weekly', 'monthly')
            period: Time period ('1mo', '3mo', '6mo', '1y', '5y')
            provider: Optional preferred provider
            
        Returns:
            Historical price data
        """
        # Map standard intervals to provider-specific formats
        interval_map = {
            # format: [alpha_vantage, yahoo_finance]
            "daily": ["daily", "1d"],
            "weekly": ["weekly", "1wk"],
            "monthly": ["monthly", "1mo"]
        }
        
        # Map standard periods to yahoo_finance format
        period_map = {
            "1mo": "1mo",
            "3mo": "3mo",
            "6mo": "6mo",
            "1y": "1y",
            "5y": "5y",
            "max": "max"
        }
        
        # Determine if Indian stock
        is_indian_stock = symbol.endswith('.NS') or symbol.endswith('.BO')
        
        # Define provider order
        providers = []
        
        if provider:
            providers.append(provider)
            
        if is_indian_stock and 'nse_india' not in providers:
            providers.append('nse_india')
            
        for p in ['yahoo_finance', 'alpha_vantage']:
            if p not in providers:
                providers.append(p)
        
        # Try each provider
        for provider_name in providers:
            try:
                if provider_name == 'alpha_vantage':
                    data = self.alpha_vantage.get_historical_data(
                        symbol,
                        interval=interval_map.get(interval, ["daily"])[0],
                        output_size="full" if period in ["5y", "max"] else "compact"
                    )
                elif provider_name == 'yahoo_finance':
                    data = self.yahoo.get_historical_data(
                        symbol,
                        interval=interval_map.get(interval, ["", "1d"])[1],
                        range_period=period_map.get(period, "1mo")
                    )
                else:
                    # NSE India doesn't have a comparable historical data API
                    continue
                
                if data and 'error' not in data:
                    data['provider'] = provider_name
                    return data
                    
            except Exception as e:
                logger.warning(f"Error getting historical data from {provider_name} for {symbol}: {str(e)}")
                continue
        
        # If all providers failed, return error
        return {
            "symbol": symbol,
            "error": "not_found",
            "message": f"Could not find historical data for {symbol} from any provider"
        }
    
    def search_stocks(self, query: str, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for stocks across all providers
        
        Args:
            query: Search query
            provider: Optional preferred provider
            
        Returns:
            Combined list of matching stocks
        """
        results = []
        seen_symbols = set()
        
        # Define provider order
        providers = []
        
        if provider:
            providers.append(provider)
            
        for p in ['yahoo_finance', 'alpha_vantage', 'nse_india']:
            if p not in providers:
                providers.append(p)
        
        # Try each provider
        for provider_name in providers:
            try:
                provider_results = []
                
                if provider_name == 'alpha_vantage':
                    provider_results = self.alpha_vantage.search_stocks(query)
                elif provider_name == 'yahoo_finance':
                    provider_results = self.yahoo.search_stocks(query)
                elif provider_name == 'nse_india':
                    provider_results = self.nse.search_stocks(query)
                
                # Add provider info and deduplicate
                for item in provider_results:
                    if item.get('symbol') not in seen_symbols:
                        item['provider'] = provider_name
                        results.append(item)
                        seen_symbols.add(item.get('symbol'))
                    
            except Exception as e:
                logger.warning(f"Error searching stocks from {provider_name}: {str(e)}")
                continue
        
        return results
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get a combined market summary from all providers
        
        Returns:
            Dictionary with market indices, top gainers/losers, etc.
        """
        summary = {
            "indices": [],
            "global_indices": [],
            "indian_indices": [],
            "gainers": [],
            "losers": [],
            "market_status": {}
        }
        
        # Get indices from Yahoo Finance
        try:
            yahoo_indices = self.yahoo.get_market_summary()
            for index in yahoo_indices:
                index['provider'] = 'yahoo_finance'
                summary['indices'].append(index)
                summary['global_indices'].append(index)
        except Exception as e:
            logger.warning(f"Error getting market summary from Yahoo Finance: {str(e)}")
        
        # Get Indian market data from NSE
        try:
            nse_indices = self.nse.get_indices()
            for index in nse_indices:
                index['provider'] = 'nse_india'
                summary['indices'].append(index)
                summary['indian_indices'].append(index)
                
            nse_gainers_losers = self.nse.get_top_gainers_losers()
            for gainer in nse_gainers_losers.get('gainers', []):
                gainer['provider'] = 'nse_india'
                summary['gainers'].append(gainer)
                
            for loser in nse_gainers_losers.get('losers', []):
                loser['provider'] = 'nse_india'
                summary['losers'].append(loser)
                
            market_status = self.nse.get_market_status()
            if 'error' not in market_status:
                summary['market_status']['nse'] = market_status
        except Exception as e:
            logger.warning(f"Error getting market data from NSE India: {str(e)}")
        
        return summary 

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get stock data in a format compatible with the chat service
        """
        try:
            # Check cache first
            if symbol in self.cache:
                cached_data, timestamp = self.cache[symbol]
                if datetime.now() - timestamp < self.cache_duration:
                    return cached_data

            # Try Alpha Vantage first
            try:
                data = await self.alpha_vantage.get_stock_price_async(symbol)
                if data and "error" not in data:
                    stock_data = {
                        "symbol": symbol,
                        "price": float(data.get("price", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                        "volume": int(data.get("volume", 0)),
                        "high": float(data.get("high", 0) if "high" in data else 0),
                        "low": float(data.get("low", 0) if "low" in data else 0),
                        "open": float(data.get("open", 0) if "open" in data else 0),
                        "close": float(data.get("price", 0)),  # Use price as close if not available
                        "timestamp": data.get("timestamp", datetime.now().isoformat())
                    }
                    self.cache[symbol] = (stock_data, datetime.now())
                    return stock_data
            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {symbol}: {str(e)}")

            # Try Finnhub as backup
            try:
                data = await self.finnhub.get_stock_price(symbol)
                if data and "error" not in data:
                    stock_data = {
                        "symbol": symbol,
                        "price": float(data.get("price", 0) if "price" in data else data.get("c", 0)),  # Current price
                        "change_percent": float(data.get("change_percent", 0) if "change_percent" in data else data.get("dp", 0)),  # Daily percent change
                        "volume": int(data.get("volume", 0) if "volume" in data else data.get("v", 0)),  # Volume
                        "high": float(data.get("high", 0) if "high" in data else data.get("h", 0)),  # High
                        "low": float(data.get("low", 0) if "low" in data else data.get("l", 0)),  # Low
                        "open": float(data.get("open", 0) if "open" in data else data.get("o", 0)),  # Open
                        "close": float(data.get("close", 0) if "close" in data else data.get("c", 0)),  # Close
                        "timestamp": datetime.now().isoformat()
                    }
                    self.cache[symbol] = (stock_data, datetime.now())
                    return stock_data
            except Exception as e:
                logger.warning(f"Finnhub failed for {symbol}: {str(e)}")

            # Try Yahoo Finance as last resort
            try:
                data = await self.yahoo.get_stock_price_async(symbol)
                if data and "error" not in data:
                    stock_data = {
                        "symbol": symbol,
                        "price": float(data.get("price", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                        "volume": int(data.get("volume", 0)),
                        "high": float(data.get("high", 0)),
                        "low": float(data.get("low", 0)),
                        "open": float(data.get("open", 0)),
                        "close": float(data.get("close", 0)),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.cache[symbol] = (stock_data, datetime.now())
                    return stock_data
            except Exception as e:
                logger.warning(f"Yahoo Finance failed for {symbol}: {str(e)}")
                
            # Try NSE India for Indian stocks
            if ".NS" in symbol or any(indian in symbol.upper() for indian in ["NSE:", "BSE:", "RELIANCE", "TCS", "INFY"]):
                try:
                    data = await self.nse.get_stock_price_async(symbol)
                    if data and "error" not in data:
                        stock_data = {
                            "symbol": symbol,
                            "price": float(data.get("price", 0)),
                            "change_percent": float(data.get("change_percent", 0)),
                            "volume": int(data.get("volume", 0)),
                            "high": float(data.get("high", 0)),
                            "low": float(data.get("low", 0)),
                            "open": float(data.get("open", 0)),
                            "close": float(data.get("price", 0)),  # Use price as close if not available
                            "timestamp": data.get("timestamp", datetime.now().isoformat())
                        }
                        self.cache[symbol] = (stock_data, datetime.now())
                        return stock_data
                except Exception as e:
                    logger.warning(f"NSE India failed for {symbol}: {str(e)}")

            # If all APIs fail, return mock data for testing purposes
            logger.info(f"Using mock data for {symbol} as all API calls failed")
            mock_data = {
                "symbol": symbol,
                "price": 100.0 if symbol == "AAPL" else 200.0 if symbol == "MSFT" else 50.0 if symbol == "BTC" else 3000.0,
                "change_percent": 1.5,
                "volume": 1000000,
                "high": 105.0,
                "low": 95.0,
                "open": 97.0,
                "close": 100.0,
                "timestamp": datetime.now().isoformat(),
                "note": "MOCK DATA - APIs unavailable"
            }
            self.cache[symbol] = (mock_data, datetime.now())
            return mock_data

        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            return None

class StockAPI(StockMarketAPI):
    """
    Simplified API client for the chat service
    """
    def __init__(self):
        """Initialize StockAPI with proper API keys from environment variables"""
        super().__init__()
        
        # Log API key status
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        
        if not alpha_vantage_key:
            logger.warning("Alpha Vantage API key not found in environment variables")
        
        if not finnhub_key:
            logger.warning("Finnhub API key not found in environment variables")
        
        # Ensure polygon API key is properly set
        self.api_key = os.getenv("POLYGON_API_KEY", "")
        if not self.api_key or self.api_key == "YOUR_POLYGON_API_KEY":
            logger.warning("Polygon API key not found or placeholder used, some functionality may be limited") 