"""
Chat service for handling chat interactions
"""
import logging
from typing import Optional, Dict, Any, List, Union
from app.models.chat import ChatResponse
from app.utils.api.stock import StockAPI
from app.utils.api.crypto import CryptoAPI
import json
import re
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for handling chat interactions
    """
    def __init__(self):
        self.stock_api = StockAPI()
        self.crypto_api = CryptoAPI()
        
        # Knowledge base for stocks and cryptocurrencies
        self.knowledge_base = {
            "stocks": {
                "AAPL": {
                    "name": "Apple Inc.",
                    "sector": "Technology",
                    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Dividend Yield", "52-Week Range"]
                },
                "MSFT": {
                    "name": "Microsoft Corporation",
                    "sector": "Technology",
                    "description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Dividend Yield", "52-Week Range"]
                }
            },
            "crypto": {
                "BTC": {
                    "name": "Bitcoin",
                    "founder": "Satoshi Nakamoto",
                    "founded": "2009",
                    "description": "Bitcoin is a decentralized digital currency, without a central bank or single administrator.",
                    "features": ["Decentralized", "Limited Supply (21 million)", "Blockchain-based", "Peer-to-peer"]
                },
                "ETH": {
                    "name": "Ethereum",
                    "founder": "Vitalik Buterin",
                    "founded": "2015",
                    "description": "Ethereum is a decentralized, open-source blockchain with smart contract functionality.",
                    "features": ["Smart Contracts", "Decentralized Applications (DApps)", "ERC-20 Tokens", "Proof of Stake"]
                }
            }
        }

    def _get_knowledge_graph(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """
        Get knowledge graph data for a symbol
        
        Args:
            symbol: Stock or crypto symbol
            data_type: 'stock' or 'crypto'
            
        Returns:
            Dictionary with knowledge graph data
        """
        if data_type == 'stock':
            if symbol in self.knowledge_base["stocks"]:
                return self.knowledge_base["stocks"][symbol]
            
            # General stock market knowledge
            return {
                "name": f"{symbol} Stock",
                "type": "Stock",
                "description": "A stock represents ownership in a publicly-traded company."
            }
            
        elif data_type == 'crypto':
            if symbol in self.knowledge_base["crypto"]:
                return self.knowledge_base["crypto"][symbol]
            
            # General crypto knowledge
            return {
                "name": f"{symbol} Cryptocurrency",
                "type": "Cryptocurrency",
                "description": "A cryptocurrency is a digital or virtual currency that is secured by cryptography."
            }
            
        return {}

    async def get_response(self, message: str) -> ChatResponse:
        """
        Get response to a chat message
        
        Args:
            message: User message
            
        Returns:
            ChatResponse with appropriate response
        """
        try:
            # Convert to lowercase for easier matching
            message_lower = message.lower()
            
            # Handle greetings
            if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
                return ChatResponse(
                    response="👋 Hello! I'm your AI financial assistant. I can help with stock prices, crypto trends, mutual funds, and investment advice. What would you like to know about today?",
                    additional_data=None
                )
            
            # Handle help requests
            if any(help_term in message_lower for help_term in ["help", "what can you do", "capabilities"]):
                help_text = """
                I can assist you with:
                
                📈 Stock prices and information (e.g., "What's the price of Apple stock?")
                🪙 Cryptocurrency trends (e.g., "Show me Bitcoin price")
                💰 Mutual funds and ETFs information (e.g., "Tell me about index funds")
                💼 Investment suggestions (e.g., "How should I invest for retirement?")
                📊 Market insights and analysis (e.g., "How is the tech sector performing?")
                
                How can I help you today?
                """
                return ChatResponse(
                    response=help_text.strip(),
                    additional_data=None
                )
            
            # Handle stock queries
            stock_pattern = r'(?:price|stock|share|ticker)\s+(?:of|for)?\s*([A-Za-z\s]+)'
            stock_match = re.search(stock_pattern, message_lower)
            
            if "stock" in message_lower or "price" in message_lower or stock_match:
                # Extract stock symbol
                symbol = None
                
                # First check if there's a direct company mention
                company_mapping = {
                    "tesla": "TSLA",
                    "apple": "AAPL",
                    "microsoft": "MSFT",
                    "google": "GOOGL",
                    "amazon": "AMZN",
                    "meta": "META",
                    "facebook": "META",
                    "nvidia": "NVDA",
                    "netflix": "NFLX",
                    "ibm": "IBM",
                    "oracle": "ORCL",
                    "intel": "INTC",
                    "amd": "AMD",
                    "reliance": "RELIANCE", # Indian company
                    "tcs": "TCS",           # Indian company
                    "infosys": "INFY",      # Indian company
                    "walmart": "WMT",
                    "boeing": "BA",
                    "ford": "F",
                    "tesla motors": "TSLA",
                    "general motors": "GM",
                    "goldman sachs": "GS",
                    "jp morgan": "JPM",
                    "jpmorgan": "JPM",
                    "jp morgan chase": "JPM",
                    "bank of america": "BAC",
                    "stocks": "SPY" # Default to S&P 500 ETF for general stock queries
                }
                
                for company, ticker in company_mapping.items():
                    if company in message_lower:
                        symbol = ticker
                        break
                
                # If no company matched, check for a stock pattern match
                if not symbol and stock_match:
                    potential_symbol = stock_match.group(1).strip().upper()
                    # If multi-word, we'll try to map it
                    if " " in potential_symbol:
                        if "nvidia" in potential_symbol.lower():
                            symbol = "NVDA"
                        elif "tesla" in potential_symbol.lower():
                            symbol = "TSLA"
                        # Add more mappings as needed
                    else:
                        symbol = potential_symbol
                
                # Try to find uppercase ticker symbols if nothing else worked
                if not symbol:
                    # Look for uppercase words that might be stock symbols
                    for word in message.split():
                        if word.isupper() and len(word) <= 5:
                            symbol = word
                            break
                
                if symbol:
                    # Get stock data
                    stock_data = await self.stock_api.get_stock_data(symbol)
                    
                    if stock_data:
                        # Get knowledge graph data
                        knowledge_graph = self._get_knowledge_graph(symbol, 'stock')
                        
                        response = f"📈 **{symbol}** stock is currently trading at ${stock_data['price']:.2f}, "
                        if stock_data.get('change_percent', 0) >= 0:
                            response += f"📈 up {abs(stock_data['change_percent']):.2f}% today."
                        else:
                            response += f"📉 down {abs(stock_data['change_percent']):.2f}% today."
                            
                        response += f"\n\n💰 **Volume**: {stock_data.get('volume', 0):,}"
                        
                        if knowledge_graph.get('name'):
                            response += f"\n\n🏢 **Company**: {knowledge_graph.get('name')}"
                        
                        if knowledge_graph.get('sector'):
                            response += f"\n🔍 **Sector**: {knowledge_graph.get('sector')}"
                            
                        if knowledge_graph.get('description'):
                            response += f"\n\n📋 {knowledge_graph.get('description')}"
                        
                        return ChatResponse(
                            response=response,
                            additional_data={"type": "stock", "data": stock_data},
                            knowledge_graph=knowledge_graph
                        )
                    else:
                        return ChatResponse(
                            response=f"I couldn't find data for the stock symbol {symbol}. Please check if it's a valid symbol and try again.",
                            additional_data={"type": "error", "symbol": symbol}
                        )
            
            # Handle cryptocurrency queries
            crypto_pattern = r'(?:price|value|crypto|cryptocurrency)\s+(?:of|for)?\s*([A-Za-z\s]+)'
            crypto_match = re.search(crypto_pattern, message_lower)
            
            # List of known cryptocurrencies and their symbols
            crypto_mapping = {
                "bitcoin": "BTC",
                "btc": "BTC",
                "ethereum": "ETH",
                "eth": "ETH",
                "ripple": "XRP", 
                "xrp": "XRP",
                "cardano": "ADA",
                "ada": "ADA",
                "solana": "SOL",
                "sol": "SOL",
                "dogecoin": "DOGE",
                "doge": "DOGE",
                "shiba inu": "SHIB",
                "shib": "SHIB",
                "tether": "USDT",
                "usdt": "USDT",
                "bnb": "BNB",
                "usd coin": "USDC",
                "usdc": "USDC",
                "litecoin": "LTC",
                "ltc": "LTC",
                "arbitrum": "ARB",
                "arb": "ARB"
            }
            
            # Check if message contains any known cryptocurrency
            symbol = None
            for crypto_name, crypto_symbol in crypto_mapping.items():
                if crypto_name in message_lower:
                    symbol = crypto_symbol
                    break
                    
            # If a pattern match exists and no symbol found yet, check the match
            if not symbol and crypto_match:
                potential_crypto = crypto_match.group(1).strip().lower()
                # Try to find the crypto in our mapping
                for crypto_name, crypto_symbol in crypto_mapping.items():
                    if crypto_name in potential_crypto:
                        symbol = crypto_symbol
                        break
            
            if symbol or "crypto" in message_lower:
                # If we have a symbol or explicit crypto mention
                if symbol:
                    # Get crypto data
                    crypto_data = await self.crypto_api.get_crypto_data(symbol)
                    
                    if crypto_data:
                        # Get knowledge graph data
                        knowledge_graph = self._get_knowledge_graph(symbol, 'crypto')
                        
                        response = f"🪙 **{knowledge_graph.get('name', symbol)}** is currently valued at ${crypto_data['price']:.2f}, "
                        if crypto_data.get('change_percent', 0) >= 0:
                            response += f"📈 up {abs(crypto_data['change_percent']):.2f}% in the last 24 hours."
                        else:
                            response += f"📉 down {abs(crypto_data['change_percent']):.2f}% in the last 24 hours."
                            
                        if knowledge_graph.get('description'):
                            response += f"\n\n📋 {knowledge_graph.get('description')}"
                            
                        if knowledge_graph.get('features'):
                            response += "\n\n✨ **Key features**:"
                            for feature in knowledge_graph.get('features', []):
                                response += f"\n• {feature}"
                        
                        return ChatResponse(
                            response=response,
                            additional_data=None
                        )
                    else:
                        return ChatResponse(
                            response=f"❌ I couldn't find current data for {symbol}. Please try again later.",
                            additional_data=None
                        )
                else:
                    # General crypto response when "crypto" is mentioned but no specific coin
                    return ChatResponse(
                        response="🪙 I can provide information about various cryptocurrencies like Bitcoin (BTC), Ethereum (ETH), and more. Which specific cryptocurrency would you like to know about?",
                        additional_data=None
                    )
            
            # Handle mutual funds queries
            if "mutual fund" in message_lower or "funds" in message_lower or "etf" in message_lower:
                response = """
                💰 **Mutual Funds Overview**
                
                Mutual funds are investment vehicles managed by professionals that pool money from multiple investors to purchase a diversified portfolio of stocks, bonds, or other securities.
                
                **Types of mutual funds include:**
                
                📊 **Equity Funds**: Invest primarily in stocks
                🔒 **Bond Funds**: Invest primarily in bonds and other debt securities
                📈 **Index Funds**: Track a specific market index like the S&P 500
                ⚖️ **Balanced Funds**: Invest in a mix of stocks, bonds, and other securities
                💵 **Money Market Funds**: Invest in short-term, low-risk securities
                
                **Key considerations when choosing mutual funds:**
                • 💲 Expense ratio (lower is generally better)
                • 📋 Fund performance history (though past performance doesn't guarantee future results)
                • 👨‍💼 Fund manager experience
                • 🔄 Investment strategy and risk level
                
                Would you like more specific information about a particular type of mutual fund?
                """
                
                return ChatResponse(
                    response=response.strip(),
                    additional_data=None
                )
            
            # Handle investment advice
            if "invest" in message_lower or "retirement" in message_lower or "portfolio" in message_lower:
                response = """
                💼 **Investment Principles**
                
                Here are some general investment principles to consider:
                
                🧩 **Diversification**: Spread investments across different asset classes to reduce risk
                ⏳ **Time horizon**: Longer time horizons generally allow for taking more risk
                📊 **Risk tolerance**: Understand your personal comfort level with investment volatility
                💵 **Dollar-cost averaging**: Invest regularly regardless of market conditions
                📝 **Tax efficiency**: Consider tax implications of investment decisions
                
                **A common starting portfolio might include:**
                • 📈 60-70% stocks (domestic and international)
                • 🔒 20-30% bonds
                • 💰 5-10% alternatives/cash
                
                Remember that investment advice should be personalized to your specific financial situation, goals, and risk tolerance. Consider consulting with a financial advisor for personalized guidance.
                """
                
                return ChatResponse(
                    response=response.strip(),
                    additional_data=None
                )
            
            # Default response for unrecognized queries
            return ChatResponse(
                response="❓ I'm not sure how to respond to that question. I can help with stock prices, cryptocurrency trends, mutual funds, and investment advice. Could you please ask about one of these topics?",
                additional_data=None
            )
            
        except Exception as e:
            # Log the error
            logger.error(f"Error generating response: {str(e)}")
            
            # Return a friendly error message
            return ChatResponse(
                response="⚠️ I'm sorry, but I encountered an error while processing your request. Please try again or ask a different question.",
                additional_data=None
            ) 