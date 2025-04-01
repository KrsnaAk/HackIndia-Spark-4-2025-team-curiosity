import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StockGeistAPI:
    """Client for interacting with StockGeist API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stockgeist.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information including price, sentiment, and trends"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/stock/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return None
    
    async def get_market_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market sentiment analysis for a stock"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sentiment/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching sentiment for {symbol}: {str(e)}")
            return None
    
    async def get_company_news(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get recent news and analysis for a company"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/news/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return None
    
    async def analyze_trends(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get technical analysis and trends for a stock"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/trends/{symbol}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error analyzing trends for {symbol}: {str(e)}")
            return None 