# Stock Market API Module

from app.utils.api.stock.alpha_vantage import AlphaVantageClient
from app.utils.api.stock.yahoo_finance import YahooFinanceClient
from app.utils.api.stock.nse_india import NSEIndiaClient

from typing import Dict, Any, List, Optional, Literal
import logging

logger = logging.getLogger(__name__)

class StockMarketAPI:
    """
    Unified interface for stock market data APIs
    Handles failover between different providers and data normalization
    """
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageClient()
        self.yahoo_finance = YahooFinanceClient()
        self.nse_india = NSEIndiaClient()
        
    def get_stock_price(self, symbol: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current stock price from the preferred provider with failover
        
        Args:
            symbol: Stock symbol
            provider: Optional preferred provider ('alpha_vantage', 'yahoo_finance', 'nse_india')
            
        Returns:
            Normalized stock price data
        """
        # Identify if this is an Indian stock (NSE/BSE)
        is_indian_stock = symbol.endswith('.NS') or symbol.endswith('.BO')
        
        # Define provider order based on inputs
        providers = []
        
        if provider:
            # If specific provider requested, try it first
            providers.append(provider)
        
        if is_indian_stock and 'nse_india' not in providers:
            providers.append('nse_india')
        
        # Add remaining providers for failover
        for p in ['yahoo_finance', 'alpha_vantage', 'nse_india']:
            if p not in providers:
                providers.append(p)
        
        # Try each provider in order
        for provider_name in providers:
            try:
                if provider_name == 'alpha_vantage':
                    data = self.alpha_vantage.get_stock_price(symbol)
                elif provider_name == 'yahoo_finance':
                    data = self.yahoo_finance.get_stock_price(symbol)
                elif provider_name == 'nse_india':
                    # For NSE India, we need to remove any exchange suffix
                    clean_symbol = symbol.split('.')[0]
                    data = self.nse_india.get_stock_price(clean_symbol)
                else:
                    continue
                
                # If valid data returned (no error), add provider info and return
                if data and 'error' not in data:
                    data['provider'] = provider_name
                    return data
                    
            except Exception as e:
                logger.warning(f"Error from {provider_name} for {symbol}: {str(e)}")
                continue
        
        # If all providers failed, return error
        return {
            "symbol": symbol,
            "error": "not_found",
            "message": f"Could not find stock data for {symbol} from any provider"
        }
    
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
                    data = self.yahoo_finance.get_historical_data(
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
                    provider_results = self.yahoo_finance.search_stocks(query)
                elif provider_name == 'nse_india':
                    provider_results = self.nse_india.search_stocks(query)
                
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
            yahoo_indices = self.yahoo_finance.get_market_summary()
            for index in yahoo_indices:
                index['provider'] = 'yahoo_finance'
                summary['indices'].append(index)
                summary['global_indices'].append(index)
        except Exception as e:
            logger.warning(f"Error getting market summary from Yahoo Finance: {str(e)}")
        
        # Get Indian market data from NSE
        try:
            nse_indices = self.nse_india.get_indices()
            for index in nse_indices:
                index['provider'] = 'nse_india'
                summary['indices'].append(index)
                summary['indian_indices'].append(index)
                
            nse_gainers_losers = self.nse_india.get_top_gainers_losers()
            for gainer in nse_gainers_losers.get('gainers', []):
                gainer['provider'] = 'nse_india'
                summary['gainers'].append(gainer)
                
            for loser in nse_gainers_losers.get('losers', []):
                loser['provider'] = 'nse_india'
                summary['losers'].append(loser)
                
            market_status = self.nse_india.get_market_status()
            if 'error' not in market_status:
                summary['market_status']['nse'] = market_status
        except Exception as e:
            logger.warning(f"Error getting market data from NSE India: {str(e)}")
        
        return summary 