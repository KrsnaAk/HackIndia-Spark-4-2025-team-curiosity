"""
Chat service for handling chat interactions
"""
import logging
from typing import Optional, Dict, Any, List, Union
from app.models.chat import ChatResponse
from app.utils.api.stock import StockAPI
from app.utils.api.crypto import CryptoAPI
from app.utils.ai_service import AIService
from app.services.reasoning_service import ReasoningService
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
        self.ai_service = AIService()
        self.reasoning_service = ReasoningService()
        self.use_ai_fallback = os.getenv("USE_AI_FALLBACK", "true").lower() == "true"
        
        # Knowledge base for stocks and cryptocurrencies
        self.knowledge_base = {
            "stocks": {
                "AAPL": {
                    "name": "Apple Inc.",
                    "sector": "Technology",
                    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Dividend Yield", "52-Week Range"],
                    "fundamentals": {
                        "pe_ratio": "28.5",
                        "market_cap": "$2.87T",
                        "revenue": "$394.33B (TTM)",
                        "eps": "$6.42"
                    }
                },
                "MSFT": {
                    "name": "Microsoft Corporation",
                    "sector": "Technology",
                    "description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Dividend Yield", "52-Week Range"],
                    "fundamentals": {
                        "pe_ratio": "36.2",
                        "market_cap": "$3.01T",
                        "revenue": "$211.92B (TTM)",
                        "eps": "$11.14"
                    }
                },
                "TSLA": {
                    "name": "Tesla, Inc.",
                    "sector": "Automotive",
                    "description": "Tesla, Inc. designs, manufactures, and sells electric vehicles, energy generation and storage systems worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Revenue Growth", "Debt-to-Equity"],
                    "fundamentals": {
                        "pe_ratio": "47.3",
                        "market_cap": "$586.42B",
                        "revenue": "$96.77B (TTM)",
                        "eps": "$4.30"
                    }
                },
                "NVDA": {
                    "name": "NVIDIA Corporation",
                    "sector": "Technology",
                    "description": "NVIDIA Corporation designs and manufactures computer graphics processors, chipsets, and related software for gaming, professional visualization, data center, and automotive markets.",
                    "metrics": ["PE Ratio", "Market Cap", "Revenue Growth", "Gross Margin"],
                    "fundamentals": {
                        "pe_ratio": "65.7",
                        "market_cap": "$2.31T",
                        "revenue": "$60.92B (TTM)",
                        "eps": "$12.96"
                    }
                },
                "AMZN": {
                    "name": "Amazon.com, Inc.",
                    "sector": "Consumer Cyclical",
                    "description": "Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions through online and physical stores worldwide.",
                    "metrics": ["PE Ratio", "Market Cap", "Revenue Growth", "Operating Margin"],
                    "fundamentals": {
                        "pe_ratio": "42.8",
                        "market_cap": "$1.85T",
                        "revenue": "$574.78B (TTM)",
                        "eps": "$4.73"
                    }
                },
                "GOOGL": {
                    "name": "Alphabet Inc.",
                    "sector": "Communication Services",
                    "description": "Alphabet Inc. provides various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.",
                    "metrics": ["PE Ratio", "Market Cap", "Revenue Growth", "Operating Margin"],
                    "fundamentals": {
                        "pe_ratio": "25.1",
                        "market_cap": "$2.01T",
                        "revenue": "$307.39B (TTM)",
                        "eps": "$6.90"
                    }
                }
            },
            "crypto": {
                "BTC": {
                    "name": "Bitcoin",
                    "founder": "Satoshi Nakamoto",
                    "founded": "2009",
                    "description": "Bitcoin is a decentralized digital currency, without a central bank or single administrator.",
                    "features": ["Decentralized", "Limited Supply (21 million)", "Blockchain-based", "Peer-to-peer"],
                    "fundamentals": {
                        "market_cap": "$1.2T",
                        "circulating_supply": "19.5M BTC",
                        "max_supply": "21M BTC",
                        "24h_volume": "$32.5B"
                    }
                },
                "ETH": {
                    "name": "Ethereum",
                    "founder": "Vitalik Buterin",
                    "founded": "2015",
                    "description": "Ethereum is a decentralized, open-source blockchain with smart contract functionality.",
                    "features": ["Smart Contracts", "Decentralized Applications (DApps)", "ERC-20 Tokens", "Proof of Stake"],
                    "fundamentals": {
                        "market_cap": "$345B",
                        "circulating_supply": "120M ETH",
                        "max_supply": "Unlimited",
                        "24h_volume": "$15.7B"
                    }
                },
                "ARB": {
                    "name": "Arbitrum",
                    "founder": "Offchain Labs",
                    "founded": "2021",
                    "description": "Arbitrum is a layer 2 scaling solution for Ethereum that increases throughput and reduces costs while maintaining security.",
                    "features": ["Layer 2 Scaling", "EVM Compatible", "Optimistic Rollups", "Low Transaction Fees"],
                    "fundamentals": {
                        "market_cap": "$1.8B",
                        "circulating_supply": "2.8B ARB",
                        "max_supply": "10B ARB",
                        "24h_volume": "$520M"
                    }
                }
            },
            "financial_terms": {
                "pe_ratio": {
                    "name": "Price-to-Earnings Ratio (P/E)",
                    "description": "The price-to-earnings ratio measures a company's current share price relative to its earnings per share (EPS). A high P/E could mean a stock is overvalued, or investors are expecting high growth rates in the future.",
                    "calculation": "Share Price / Earnings Per Share",
                    "example": "If a company's stock is trading at $100 per share and its EPS is $10, then its P/E ratio is 10."
                },
                "market_cap": {
                    "name": "Market Capitalization",
                    "description": "The total value of a company's outstanding shares of stock, calculated by multiplying the stock's current market price by the total number of outstanding shares.",
                    "calculation": "Share Price × Total Number of Outstanding Shares",
                    "example": "If a company has 10 million shares outstanding at $50 per share, its market cap is $500 million."
                },
                "eps": {
                    "name": "Earnings Per Share (EPS)",
                    "description": "The portion of a company's profit allocated to each outstanding share of common stock. It serves as an indicator of a company's profitability.",
                    "calculation": "Net Income / Number of Outstanding Shares",
                    "example": "If a company earns $10 million and has 2 million shares outstanding, its EPS is $5."
                },
                "rsi": {
                    "name": "Relative Strength Index (RSI)",
                    "description": "A momentum oscillator that measures the speed and change of price movements. The RSI ranges from 0 to 100 and is considered overbought when above 70 and oversold when below 30.",
                    "calculation": "RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss",
                    "example": "An RSI of 80 suggests a stock may be overbought and due for a price correction."
                },
                "dividend_yield": {
                    "name": "Dividend Yield",
                    "description": "A financial ratio that shows how much a company pays out in dividends each year relative to its stock price.",
                    "calculation": "(Annual Dividends per Share / Price per Share) × 100%",
                    "example": "If a stock pays annual dividends of $2 and is trading at $50, its dividend yield is 4%."
                },
                "blue_chip": {
                    "name": "Blue-Chip Stocks",
                    "description": "Shares of large, well-established, and financially sound companies with a history of reliable performance and often dividend payments.",
                    "examples": "Companies like Apple (AAPL), Microsoft (MSFT), Johnson & Johnson (JNJ), and Coca-Cola (KO)."
                },
                "tokenized_stocks": {
                    "name": "Tokenized Stocks",
                    "description": "Digital tokens that represent traditional securities like stocks on a blockchain. They allow for fractional ownership and 24/7 trading without the need for traditional market intermediaries.",
                    "benefits": "Fractional ownership, global accessibility, reduced settlement times, and potentially lower fees.",
                    "platforms": "Coinbase, Kraken, DeFi protocols like Synthetix, Mirror Protocol"
                }
            },
            "portfolio_advice": {
                "diversification": {
                    "name": "Portfolio Diversification",
                    "description": "The practice of spreading investments across various asset classes to reduce risk.",
                    "principles": [
                        "Invest across different asset classes (stocks, bonds, real estate, commodities)",
                        "Diversify within asset classes (different sectors, market caps, geographic regions)",
                        "Consider correlation between assets",
                        "Rebalance periodically"
                    ]
                },
                "long_term": {
                    "name": "Long-Term Investment Strategy",
                    "description": "Investing with a time horizon of 5+ years, focusing on fundamental value rather than short-term price movements.",
                    "recommendations": [
                        "Focus on companies with strong competitive advantages",
                        "Consider dollar-cost averaging",
                        "Reinvest dividends",
                        "Minimize trading and tax costs"
                    ],
                    "example_portfolio": "60% broad market index funds, 20% international stocks, 15% bonds, 5% alternatives"
                },
                "blue_chips": {
                    "name": "Blue-Chip Investment Strategy",
                    "description": "Focusing on large, established companies with a history of reliable performance.",
                    "examples": [
                        "Microsoft (MSFT)",
                        "Apple (AAPL)",
                        "Johnson & Johnson (JNJ)",
                        "Procter & Gamble (PG)",
                        "Berkshire Hathaway (BRK.B)"
                    ]
                }
            },
            "financial_concepts": {
                "assets_liabilities": {
                    "name": "Assets vs. Liabilities",
                    "description": "In finance, assets and liabilities are fundamental components of a balance sheet and represent the financial position of an entity.",
                    "assets": {
                        "definition": "Things of value that you own or control, which can provide future economic benefits.",
                        "examples": [
                            "Cash and cash equivalents",
                            "Investments (stocks, bonds, mutual funds)",
                            "Real estate (home, land, rental properties)",
                            "Vehicles",
                            "Business interests",
                            "Personal possessions with significant value"
                        ]
                    },
                    "liabilities": {
                        "definition": "Financial obligations or debts that you owe to others.",
                        "examples": [
                            "Mortgage loans",
                            "Credit card debt",
                            "Student loans",
                            "Auto loans",
                            "Personal loans",
                            "Unpaid bills"
                        ]
                    },
                    "key_differences": [
                        "Assets increase your net worth, liabilities decrease it",
                        "Assets typically generate income or appreciate in value, while liabilities often cost money (interest)",
                        "Financial health is measured by comparing assets to liabilities (net worth)"
                    ]
                },
                "financial_markets": {
                    "name": "Types of Financial Markets",
                    "description": "Financial markets are platforms where buyers and sellers engage in the exchange of financial assets such as stocks, bonds, currencies, and derivatives.",
                    "types": [
                        {
                            "name": "Stock Markets",
                            "description": "Markets where shares of publicly-held companies are issued and traded.",
                            "examples": "NYSE, NASDAQ, LSE, Tokyo Stock Exchange"
                        },
                        {
                            "name": "Bond Markets",
                            "description": "Markets where debt securities are issued and traded.",
                            "examples": "Government bonds, corporate bonds, municipal bonds"
                        },
                        {
                            "name": "Money Markets",
                            "description": "Markets for short-term, high-liquidity debt securities.",
                            "examples": "Treasury bills, commercial paper, certificates of deposit"
                        },
                        {
                            "name": "Forex Markets",
                            "description": "Markets where currencies are traded.",
                            "examples": "EUR/USD, GBP/JPY, USD/CAD currency pairs"
                        },
                        {
                            "name": "Derivative Markets",
                            "description": "Markets for derivative instruments whose value is derived from underlying assets.",
                            "examples": "Options, futures, swaps, forwards"
                        },
                        {
                            "name": "Commodity Markets",
                            "description": "Markets where raw or primary products are exchanged.",
                            "examples": "Gold, silver, crude oil, natural gas, agricultural products"
                        },
                        {
                            "name": "Cryptocurrency Markets",
                            "description": "Digital or virtual currency markets that operate using blockchain technology.",
                            "examples": "Bitcoin (BTC), Ethereum (ETH), exchanges like Coinbase, Kraken"
                        }
                    ],
                    "classifications": {
                        "primary_vs_secondary": "Primary markets deal with new issues of securities, while secondary markets involve trading existing securities.",
                        "cash_vs_derivative": "Cash markets involve immediate delivery of assets, while derivative markets involve contracts based on underlying assets.",
                        "exchange_vs_otc": "Exchange-traded markets have centralized trading venues, while over-the-counter (OTC) markets are decentralized."
                    }
                },
                "risk_return": {
                    "name": "Risk and Return",
                    "description": "The relationship between the potential return on an investment and the risk level involved.",
                    "types_of_risk": [
                        {
                            "name": "Market Risk",
                            "description": "Risk of investments declining due to economic developments or other events that affect the entire market."
                        },
                        {
                            "name": "Credit Risk",
                            "description": "Risk of loss from a borrower failing to repay a loan or meet contractual obligations."
                        },
                        {
                            "name": "Liquidity Risk",
                            "description": "Risk of not being able to quickly buy or sell an investment at a fair price."
                        },
                        {
                            "name": "Inflation Risk",
                            "description": "Risk that the purchasing power of your investments will decrease due to inflation."
                        }
                    ],
                    "risk_return_spectrum": [
                        "Low risk, low return: Cash, treasury bonds, money market funds",
                        "Medium risk, medium return: Corporate bonds, dividend stocks, real estate",
                        "High risk, high potential return: Growth stocks, emerging markets, venture capital"
                    ],
                    "key_principles": [
                        "Higher potential returns generally come with higher risk",
                        "Diversification can help manage risk while pursuing returns",
                        "Time horizon affects optimal risk level (longer horizons can typically handle more risk)"
                    ]
                },
                "interest_rates": {
                    "name": "Interest Rates",
                    "description": "The amount a lender charges a borrower for the use of assets, expressed as a percentage of the principal.",
                    "types": [
                        {
                            "name": "Simple Interest",
                            "description": "Interest calculated only on the initial principal.",
                            "formula": "Interest = Principal × Rate × Time"
                        },
                        {
                            "name": "Compound Interest",
                            "description": "Interest calculated on both the initial principal and accumulated interest over time.",
                            "formula": "A = P(1 + r)^t where A is final amount, P is principal, r is rate, and t is time"
                        }
                    ],
                    "factors_affecting": [
                        "Central bank policies",
                        "Inflation rates",
                        "Economic growth",
                        "Supply and demand for credit",
                        "Term length of the loan or investment"
                    ],
                    "impact": {
                        "borrowers": "Higher rates increase borrowing costs for loans, mortgages, credit cards",
                        "savers": "Higher rates benefit savers through better returns on savings accounts and CDs",
                        "investors": "Interest rate changes affect bond prices, stock valuations, and real estate markets"
                    }
                },
                "stock_vs_crypto": {
                    "name": "Stocks vs Cryptocurrencies",
                    "description": "A comparison between traditional stocks and cryptocurrencies as investment vehicles.",
                    "stocks": {
                        "definition": "Stocks represent ownership shares in a publicly-traded company.",
                        "characteristics": [
                            "Regulated by government agencies (SEC in the US)",
                            "Traded on established exchanges with set hours (9:30am-4pm EST in US)",
                            "Represent partial ownership in a company",
                            "Value derived from company performance, earnings, and growth prospects",
                            "Often pay dividends to shareholders",
                            "Typically less volatile than cryptocurrencies",
                            "Longer historical performance data (decades or centuries)",
                            "More established valuation methods (P/E ratio, EPS, etc.)"
                        ]
                    },
                    "cryptocurrencies": {
                        "definition": "Cryptocurrencies are digital or virtual currencies that use cryptography for security and operate on decentralized networks based on blockchain technology.",
                        "characteristics": [
                            "Largely unregulated or with emerging regulations",
                            "Traded 24/7 globally on crypto exchanges",
                            "Represent digital assets (currency, utility, security tokens)",
                            "Value derived from utility, adoption, scarcity, and speculation",
                            "Some offer staking rewards or governance rights",
                            "Generally more volatile than traditional stocks",
                            "Relatively new asset class (since 2009 with Bitcoin)",
                            "Evolving valuation methods (network effects, on-chain metrics)"
                        ]
                    },
                    "key_differences": [
                        "Regulatory oversight: Stocks are heavily regulated; cryptocurrencies have varying levels of regulation",
                        "Trading hours: Stocks have fixed trading hours; cryptocurrencies trade 24/7",
                        "Volatility: Cryptocurrencies typically experience higher price volatility",
                        "Ownership: Stocks represent company ownership; cryptocurrencies represent various digital assets",
                        "Maturity: Stock markets are established and mature; crypto markets are newer and evolving",
                        "Accessibility: Cryptocurrencies often have lower barriers to entry for global investors"
                    ]
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
            Dictionary with knowledge graph data including nodes and edges
        """
        if data_type == 'stock':
            if symbol in self.knowledge_base["stocks"]:
                data = self.knowledge_base["stocks"][symbol]
                nodes = [
                    {"id": symbol, "label": data["name"], "type": "stock"},
                    {"id": "sector", "label": data["sector"], "type": "sector"},
                    {"id": "description", "label": data["description"], "type": "description"}
                ]
                edges = [
                    {"source": symbol, "target": "sector", "type": "belongs_to"},
                    {"source": symbol, "target": "description", "type": "has_description"}
                ]
                
                # Add fundamentals as nodes
                if "fundamentals" in data:
                    for key, value in data["fundamentals"].items():
                        node_id = f"fundamental_{key}"
                        nodes.append({"id": node_id, "label": f"{key}: {value}", "type": "fundamental"})
                        edges.append({"source": symbol, "target": node_id, "type": "has_fundamental"})
                
                return {
                    "data": data,
                    "nodes": nodes,
                    "edges": edges
                }
            
            # General stock market knowledge
            return {
                "data": {
                    "name": f"{symbol} Stock",
                    "type": "Stock",
                    "description": "A stock represents ownership in a publicly-traded company."
                },
                "nodes": [
                    {"id": symbol, "label": f"{symbol} Stock", "type": "stock"},
                    {"id": "description", "label": "A stock represents ownership in a publicly-traded company.", "type": "description"}
                ],
                "edges": [
                    {"source": symbol, "target": "description", "type": "has_description"}
                ]
            }
            
        elif data_type == 'crypto':
            if symbol in self.knowledge_base["crypto"]:
                data = self.knowledge_base["crypto"][symbol]
                nodes = [
                    {"id": symbol, "label": data["name"], "type": "crypto"},
                    {"id": "founder", "label": data["founder"], "type": "person"},
                    {"id": "description", "label": data["description"], "type": "description"}
                ]
                edges = [
                    {"source": symbol, "target": "founder", "type": "founded_by"},
                    {"source": symbol, "target": "description", "type": "has_description"}
                ]
                
                # Add features as nodes
                for i, feature in enumerate(data["features"]):
                    feature_id = f"feature_{i}"
                    nodes.append({"id": feature_id, "label": feature, "type": "feature"})
                    edges.append({"source": symbol, "target": feature_id, "type": "has_feature"})
                
                # Add fundamentals as nodes
                if "fundamentals" in data:
                    for key, value in data["fundamentals"].items():
                        node_id = f"fundamental_{key}"
                        nodes.append({"id": node_id, "label": f"{key}: {value}", "type": "fundamental"})
                        edges.append({"source": symbol, "target": node_id, "type": "has_fundamental"})
                
                return {
                    "data": data,
                    "nodes": nodes,
                    "edges": edges
                }
            
            # General crypto knowledge
            return {
                "data": {
                    "name": f"{symbol} Cryptocurrency",
                    "type": "Cryptocurrency",
                    "description": "A cryptocurrency is a digital or virtual currency that is secured by cryptography."
                },
                "nodes": [
                    {"id": symbol, "label": f"{symbol} Cryptocurrency", "type": "crypto"},
                    {"id": "description", "label": "A cryptocurrency is a digital or virtual currency that is secured by cryptography.", "type": "description"}
                ],
                "edges": [
                    {"source": symbol, "target": "description", "type": "has_description"}
                ]
            }
            
        return {
            "data": {},
            "nodes": [],
            "edges": []
        }

    # Use MeTTa-based reasoning for financial queries that need inference
    async def reason_about_query(self, message: str) -> Optional[ChatResponse]:
        """
        Reason about a query using MeTTa symbolic reasoning
        
        Args:
            message: User's message
            
        Returns:
            ChatResponse with reasoning or None if no reasoning available
        """
        # Keywords that suggest the need for causal reasoning
        reasoning_keywords = [
            "why", "how", "explain", "reason", "cause", "effect", "impact", 
            "influence", "relationship", "correlation", "leads to", "results in",
            "what happens when", "what happens if", "what occurs when", "predict"
        ]
        
        # Check if the query contains reasoning keywords
        if any(keyword in message.lower() for keyword in reasoning_keywords):
            try:
                # Use MeTTa reasoning service to infer an answer
                reasoning_result = await self.reasoning_service.infer(message)
                
                if reasoning_result["success"] and reasoning_result.get("response"):
                    return ChatResponse(
                        response=reasoning_result["response"],
                        additional_data={"reasoning": reasoning_result["reasoning"]},
                        knowledge_graph=reasoning_result.get("knowledge_graph")
                    )
                else:
                    # Fallback to AI service for complex queries
                    context = "You are a financial expert. Please provide a detailed explanation for this query."
                    try:
                        ai_response = await self.ai_service.get_ai_response(message, context)
                        return ChatResponse(
                            response=ai_response,
                            additional_data={"type": "ai_generated"}
                        )
                    except Exception as e:
                        logger.error(f"Error in AI fallback: {str(e)}")
                        return ChatResponse(
                            response="I apologize, but I need more information to provide a complete answer. Could you please provide more details or rephrase your question?",
                            additional_data=None
                        )
            except Exception as e:
                logger.error(f"Error in MeTTa reasoning: {str(e)}")
                # Fallback to a generic response
                return ChatResponse(
                    response="I apologize, but I'm having trouble processing your request. Could you please rephrase your question or try a different query?",
                    additional_data=None
                )
        
        return None
    
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
            
            # Try symbolic reasoning for complex queries first
            try:
                reasoning_response = await self.reason_about_query(message)
                if reasoning_response:
                    return reasoning_response
            except Exception as e:
                logger.error(f"Error in reasoning service: {str(e)}")
                # Continue with other message handling methods
            
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
                📚 Financial education (e.g., "What's the difference between assets and liabilities?")
                🏦 Financial markets (e.g., "What are the types of financial markets?")
                
                How can I help you today?
                """
                return ChatResponse(
                    response=help_text.strip(),
                    additional_data=None
                )
            
            # Handle assets vs liabilities queries
            if (("assets" in message_lower and "liabilities" in message_lower) or 
                ("asset" in message_lower and "liability" in message_lower) or
                ("difference between assets" in message_lower)):
                
                assets_liabilities = self.knowledge_base["financial_concepts"]["assets_liabilities"]
                
                response = f"📚 {assets_liabilities['name']}\n\n"
                response += f"{assets_liabilities['description']}\n\n"
                
                response += f"📈 Assets: {assets_liabilities['assets']['definition']}\n\n"
                response += "Examples of assets:\n"
                for example in assets_liabilities['assets']['examples']:
                    response += f"• {example}\n"
                
                response += f"\n📉 Liabilities: {assets_liabilities['liabilities']['definition']}\n\n"
                response += "Examples of liabilities:\n"
                for example in assets_liabilities['liabilities']['examples']:
                    response += f"• {example}\n"
                
                response += "\nKey Differences:\n"
                for difference in assets_liabilities['key_differences']:
                    response += f"• {difference}\n"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle financial markets queries
            if "financial markets" in message_lower or "types of markets" in message_lower or "market types" in message_lower or "types of financial markets" in message_lower:
                financial_markets = self.knowledge_base["financial_concepts"]["financial_markets"]
                
                response = f"🌐 {financial_markets['name']}\n\n"
                response += f"{financial_markets['description']}\n\n"
                
                response += "Major Types of Financial Markets:\n\n"
                
                for market_type in financial_markets['types']:
                    response += f"{market_type['name']}: {market_type['description']}\n"
                    response += f"  Examples: {market_type['examples']}\n\n"
                
                response += "Market Classifications:\n"
                response += f"• Primary vs. Secondary Markets: {financial_markets['classifications']['primary_vs_secondary']}\n"
                response += f"• Cash vs. Derivative Markets: {financial_markets['classifications']['cash_vs_derivative']}\n"
                response += f"• Exchange-Traded vs. OTC Markets: {financial_markets['classifications']['exchange_vs_otc']}"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )

            # Handle risk and return queries
            if "risk" in message_lower and ("return" in message_lower or "reward" in message_lower):
                risk_return = self.knowledge_base["financial_concepts"]["risk_return"]
                
                response = f"⚖️ {risk_return['name']}\n\n"
                response += f"{risk_return['description']}\n\n"
                
                response += "Types of Investment Risk:\n"
                for risk_type in risk_return['types_of_risk']:
                    response += f"• {risk_type['name']}: {risk_type['description']}\n"
                
                response += "\nRisk-Return Spectrum:\n"
                for item in risk_return['risk_return_spectrum']:
                    response += f"• {item}\n"
                
                response += "\nKey Principles:\n"
                for principle in risk_return['key_principles']:
                    response += f"• {principle}\n"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
                
            # Handle interest rate queries
            if "interest rate" in message_lower or "interest rates" in message_lower:
                interest_rates = self.knowledge_base["financial_concepts"]["interest_rates"]
                
                response = f"💰 {interest_rates['name']}\n\n"
                response += f"{interest_rates['description']}\n\n"
                
                response += "Types of Interest:\n"
                for interest_type in interest_rates['types']:
                    response += f"• {interest_type['name']}: {interest_type['description']}\n"
                    response += f"  Formula: {interest_type['formula']}\n"
                
                response += "\nFactors Affecting Interest Rates:\n"
                for factor in interest_rates['factors_affecting']:
                    response += f"• {factor}\n"
                
                response += "\nImpact of Interest Rates:\n"
                response += f"• For Borrowers: {interest_rates['impact']['borrowers']}\n"
                response += f"• For Savers: {interest_rates['impact']['savers']}\n"
                response += f"• For Investors: {interest_rates['impact']['investors']}"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle stock vs crypto comparison queries
            if (("stock" in message_lower and "crypto" in message_lower) or 
                ("difference between stock" in message_lower and "crypto" in message_lower) or
                ("stocks vs" in message_lower and "crypto" in message_lower) or
                ("stocks versus" in message_lower and "crypto" in message_lower) or
                ("compare stocks" in message_lower and "crypto" in message_lower)):
                
                stock_vs_crypto = self.knowledge_base["financial_concepts"]["stock_vs_crypto"]
                
                response = f"🔄 {stock_vs_crypto['name']}\n\n"
                response += f"{stock_vs_crypto['description']}\n\n"
                
                response += f"📈 Stocks: {stock_vs_crypto['stocks']['definition']}\n\n"
                response += "Characteristics of Stocks:\n"
                for characteristic in stock_vs_crypto['stocks']['characteristics']:
                    response += f"• {characteristic}\n"
                
                response += f"\n🪙 Cryptocurrencies: {stock_vs_crypto['cryptocurrencies']['definition']}\n\n"
                response += "Characteristics of Cryptocurrencies:\n"
                for characteristic in stock_vs_crypto['cryptocurrencies']['characteristics']:
                    response += f"• {characteristic}\n"
                
                response += "\nKey Differences:\n"
                for difference in stock_vs_crypto['key_differences']:
                    response += f"• {difference}\n"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle cryptocurrency queries first (before stock queries)
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
            
            # Check if message contains any known cryptocurrency or matches crypto pattern
            symbol = None
            is_crypto = False
            
            # First check for exact matches in crypto mapping
            for crypto_name, crypto_symbol in crypto_mapping.items():
                if crypto_name in message_lower:
                    symbol = crypto_symbol
                    is_crypto = True
                    break
                    
            # If a pattern match exists and no symbol found yet, check the match
            if not symbol and crypto_match:
                potential_crypto = crypto_match.group(1).strip().lower()
                # Try to find the crypto in our mapping
                for crypto_name, crypto_symbol in crypto_mapping.items():
                    if crypto_name in potential_crypto:
                        symbol = crypto_symbol
                        is_crypto = True
                        break
            
            # Check for standalone crypto symbols
            if not symbol:
                words = message_lower.split()
                for word in words:
                    word = word.strip(".,?! ").upper()
                    if word in [sym.upper() for sym in crypto_mapping.values()]:
                        symbol = word
                        is_crypto = True
                        break
            
            if is_crypto or "crypto" in message_lower or symbol in crypto_mapping.values():
                # Handle cryptocurrency query
                if symbol:
                    # Get crypto data
                    crypto_data = await self.crypto_api.get_crypto_data(symbol)
                    
                    if crypto_data:
                        # Get knowledge graph data
                        knowledge_graph = self._get_knowledge_graph(symbol, 'crypto')
                        
                        response = f"🪙 {knowledge_graph.get('data', {}).get('name', symbol)} ({symbol})\n\n"
                        response += f"💰 Current Price: ${crypto_data['price']:.2f}"
                        
                        # Add change information
                        if crypto_data.get('change_percent', 0) >= 0:
                            response += f" | 📈 +{abs(crypto_data['change_percent']):.2f}% (24h)"
                        else:
                            response += f" | 📉 -{abs(crypto_data['change_percent']):.2f}% (24h)"
                        
                        # Add trading information
                        response += f"\n\nTrading Information:"
                        response += f"\n• 📊 Volume (24h): ${crypto_data.get('volume', 0):,.2f}"
                        if crypto_data.get('high_24h', 0) > 0:
                            response += f"\n• ⬆️ 24h High: ${crypto_data.get('high_24h', 0):.2f}"
                        if crypto_data.get('low_24h', 0) > 0:
                            response += f"\n• ⬇️ 24h Low: ${crypto_data.get('low_24h', 0):.2f}"
                        if crypto_data.get('market_cap', 0) > 0:
                            response += f"\n• 💼 Market Cap: ${crypto_data.get('market_cap', 0):,.2f}"
                        
                        # Add fundamentals if available
                        if knowledge_graph.get('data', {}).get('fundamentals'):
                            response += f"\n\nFundamentals:"
                            fundamentals = knowledge_graph.get('data', {}).get('fundamentals', {})
                            if 'circulating_supply' in fundamentals:
                                response += f"\n• 📈 Circulating Supply: {fundamentals.get('circulating_supply')}"
                            if 'max_supply' in fundamentals:
                                response += f"\n• 🔝 Max Supply: {fundamentals.get('max_supply')}"
                            if '24h_volume' in fundamentals:
                                response += f"\n• 📈 24h Volume: {fundamentals.get('24h_volume')}"
                        
                        # Add description
                        if knowledge_graph.get('data', {}).get('description'):
                            response += f"\n\n📋 About: {knowledge_graph.get('data', {}).get('description')}"
                            
                        # Add features
                        if knowledge_graph.get('data', {}).get('features'):
                            response += "\n\n✨ Key Features:"
                            for feature in knowledge_graph.get('data', {}).get('features', []):
                                response += f"\n• {feature}"
                        
                        return ChatResponse(
                            response=response,
                            additional_data={"type": "crypto", "data": crypto_data},
                            knowledge_graph=knowledge_graph
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
            
            # Handle stock queries (only if not a crypto query)
            stock_pattern = r'(?:price|stock|share|ticker)\s+(?:of|for)?\s*([A-Za-z\s]+)'
            stock_match = re.search(stock_pattern, message_lower)
            
            if ("stock" in message_lower or "price" in message_lower or stock_match) and not is_crypto:
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
                        
                        response = f"📈 {knowledge_graph.get('data', {}).get('name', symbol)} ({symbol})\n\n"
                        response += f"💰 Current Price: ${stock_data['price']:.2f}"
                        
                        # Add change information
                        if stock_data.get('change_percent', 0) >= 0:
                            response += f" | 📈 +{abs(stock_data['change_percent']):.2f}% today"
                        else:
                            response += f" | 📉 -{abs(stock_data['change_percent']):.2f}% today"
                        
                        # Add trading information
                        response += f"\n\nTrading Information:"
                        response += f"\n• 📊 Volume: {stock_data.get('volume', 0):,}"
                        if stock_data.get('high', 0) > 0:
                            response += f"\n• ⬆️ Today's High: ${stock_data.get('high', 0):.2f}"
                        if stock_data.get('low', 0) > 0:
                            response += f"\n• ⬇️ Today's Low: ${stock_data.get('low', 0):.2f}"
                        if stock_data.get('open', 0) > 0:
                            response += f"\n• 🔓 Open: ${stock_data.get('open', 0):.2f}"
                        
                        # Add fundamentals if available
                        if knowledge_graph.get('data', {}).get('fundamentals'):
                            response += f"\n\nFundamentals:"
                            fundamentals = knowledge_graph.get('data', {}).get('fundamentals', {})
                            if 'pe_ratio' in fundamentals:
                                response += f"\n• 📊 P/E Ratio: {fundamentals.get('pe_ratio')}"
                            if 'market_cap' in fundamentals:
                                response += f"\n• 💼 Market Cap: {fundamentals.get('market_cap')}"
                            if 'eps' in fundamentals:
                                response += f"\n• 💵 EPS: {fundamentals.get('eps')}"
                            if 'revenue' in fundamentals:
                                response += f"\n• 💰 Revenue: {fundamentals.get('revenue')}"
                        
                        # Add company information
                        if knowledge_graph.get('data', {}).get('sector'):
                            response += f"\n\n🏭 Sector: {knowledge_graph.get('data', {}).get('sector')}"
                            
                        if knowledge_graph.get('data', {}).get('description'):
                            response += f"\n\n📋 About: {knowledge_graph.get('data', {}).get('description')}"
                        
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
            
            # Handle mutual funds queries
            if "mutual fund" in message_lower or "funds" in message_lower or "etf" in message_lower:
                response = """
                💰 Mutual Funds Overview
                
                Mutual funds are investment vehicles managed by professionals that pool money from multiple investors to purchase a diversified portfolio of stocks, bonds, or other securities.
                
                Types of mutual funds include:
                
                📊 Equity Funds: Invest primarily in stocks
                🔒 Bond Funds: Invest primarily in bonds and other debt securities
                📈 Index Funds: Track a specific market index like the S&P 500
                ⚖️ Balanced Funds: Invest in a mix of stocks, bonds, and other securities
                💵 Money Market Funds: Invest in short-term, low-risk securities
                
                Key considerations when choosing mutual funds:
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
                💼 Investment Principles
                
                Here are some general investment principles to consider:
                
                🧩 Diversification: Spread investments across different asset classes to reduce risk
                ⏳ Time horizon: Longer time horizons generally allow for taking more risk
                📊 Risk tolerance: Understand your personal comfort level with investment volatility
                💵 Dollar-cost averaging: Invest regularly regardless of market conditions
                📝 Tax efficiency: Consider tax implications of investment decisions
                
                A common starting portfolio might include:
                • 📈 60-70% stocks (domestic and international)
                • 🔒 20-30% bonds
                • 💰 5-10% alternatives/cash
                
                Remember that investment advice should be personalized to your specific financial situation, goals, and risk tolerance. Consider consulting with a financial advisor for personalized guidance.
                """
                
                return ChatResponse(
                    response=response.strip(),
                    additional_data=None
                )
            
            # Handle PE ratio and other fundamental metrics queries
            if "p/e" in message_lower or "pe ratio" in message_lower or "price to earnings" in message_lower:
                # Extract stock symbol
                symbol = None
                for company, ticker in company_mapping.items():
                    if company in message_lower:
                        symbol = ticker
                        break
                
                # Try to find uppercase ticker symbols if nothing else worked
                if not symbol:
                    for word in message.split():
                        if word.strip("()").isupper() and len(word.strip("()")) <= 5:
                            symbol = word.strip("()")
                            break
                
                if symbol:
                    # Get knowledge graph data
                    knowledge_graph = self._get_knowledge_graph(symbol, 'stock')
                    
                    if knowledge_graph.get('data', {}).get('fundamentals') and "pe_ratio" in knowledge_graph.get('data', {}).get('fundamentals'):
                        pe_term_info = self.knowledge_base["financial_terms"]["pe_ratio"]
                        
                        response = f"🔍 The P/E ratio for {knowledge_graph.get('data', {}).get('name', symbol)} is {knowledge_graph.get('data', {}).get('fundamentals', {}).get('pe_ratio')}.\n\n"
                        response += f"📊 Other key metrics:\n"
                        response += f"• Market Cap: {knowledge_graph.get('data', {}).get('fundamentals', {}).get('market_cap', 'N/A')}\n"
                        response += f"• Revenue: {knowledge_graph.get('data', {}).get('fundamentals', {}).get('revenue', 'N/A')}\n"
                        response += f"• EPS: {knowledge_graph.get('data', {}).get('fundamentals', {}).get('eps', 'N/A')}\n\n"
                        
                        response += f"ℹ️ About P/E Ratio: {pe_term_info['description']}\n"
                        response += f"📝 Calculation: {pe_term_info['calculation']}"
                        
                        return ChatResponse(
                            response=response,
                            additional_data=None
                        )
                
                # Generic P/E ratio explanation
                pe_term_info = self.knowledge_base["financial_terms"]["pe_ratio"]
                response = f"📊 Price-to-Earnings (P/E) Ratio\n\n"
                response += f"{pe_term_info['description']}\n\n"
                response += f"📝 How it's calculated: {pe_term_info['calculation']}\n\n"
                response += f"💡 Example: {pe_term_info['example']}\n\n"
                response += "To get the P/E ratio for a specific stock, please ask something like 'What is the P/E ratio of Apple?'"
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle RSI and technical analysis queries
            if "rsi" in message_lower or "relative strength index" in message_lower or "overbought" in message_lower or "oversold" in message_lower:
                rsi_info = self.knowledge_base["financial_terms"]["rsi"]
                
                response = f"📈 Relative Strength Index (RSI)\n\n"
                response += f"{rsi_info['description']}\n\n"
                response += f"📝 How it's calculated: {rsi_info['calculation']}\n\n"
                response += f"💡 Example: {rsi_info['example']}\n\n"
                response += "RSI is typically used as a tool for technical analysis to identify overbought or oversold conditions in a market."
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle tokenized stocks and Web3 queries
            if "tokenized stocks" in message_lower or "web3" in message_lower or "blockchain" in message_lower:
                if "tokenized stocks" in message_lower:
                    tokenized_info = self.knowledge_base["financial_terms"]["tokenized_stocks"]
                    
                    response = f"🪙 Tokenized Stocks\n\n"
                    response += f"{tokenized_info['description']}\n\n"
                    response += f"✅ Benefits:\n{tokenized_info['benefits']}\n\n"
                    response += f"🏢 Platforms offering tokenized stocks:\n{tokenized_info['platforms']}\n\n"
                    response += "Note: Regulations around tokenized stocks vary by jurisdiction. Always do your own research and consult with a financial advisor before investing."
                    
                    return ChatResponse(
                        response=response,
                        additional_data=None
                    )
                else:
                    response = f"🔗 Blockchain and Traditional Finance\n\n"
                    response += "Blockchain technology is revolutionizing traditional finance in several ways:\n\n"
                    response += "• Tokenized Securities: Digital representations of traditional assets like stocks and bonds\n"
                    response += "• 24/7 Trading: Unlike traditional markets with fixed hours\n"
                    response += "• Fractional Ownership: Making expensive assets accessible to more investors\n"
                    response += "• Reduced Settlement Times: Near-instant settlement versus T+2 in traditional markets\n"
                    response += "• Automated Compliance: Using smart contracts to enforce regulatory requirements\n\n"
                    response += "Several platforms now offer blockchain-based trading of traditional financial assets, though regulatory frameworks are still evolving."
                    
                    return ChatResponse(
                        response=response,
                        additional_data=None
                    )
            
            # Handle blue-chip stocks queries
            if "blue chip" in message_lower or "blue-chip" in message_lower:
                blue_chip_info = self.knowledge_base["portfolio_advice"]["blue_chips"]
                
                response = f"🏆 Blue-Chip Stocks\n\n"
                response += f"{blue_chip_info['description']}\n\n"
                response += "Examples of blue-chip stocks:\n"
                for stock in blue_chip_info['examples']:
                    response += f"• {stock}\n"
                response += "\nBlue-chip stocks are often considered core holdings in a long-term investment portfolio due to their stability and history of reliable performance."
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Handle portfolio diversification queries
            if "diversify" in message_lower or "diversification" in message_lower or "portfolio" in message_lower:
                diversification_info = self.knowledge_base["portfolio_advice"]["diversification"]
                
                response = f"🧩 Portfolio Diversification\n\n"
                response += f"{diversification_info['description']}\n\n"
                response += "Key principles of diversification:\n"
                for principle in diversification_info['principles']:
                    response += f"• {principle}\n"
                response += "\nA well-diversified portfolio aims to maximize returns while minimizing risk by spreading investments across assets that respond differently to market events."
                
                return ChatResponse(
                    response=response,
                    additional_data=None
                )
            
            # Default response for unrecognized queries
            if self.use_ai_fallback:
                try:
                    # Create context with relevant financial concepts
                    context = "You are a financial assistant helping with questions about finance, investments, stocks, and cryptocurrencies."
                    
                    # Get AI response
                    ai_response = await self.ai_service.get_ai_response(message, context)
                    
                    return ChatResponse(
                        response=ai_response,
                        additional_data={"type": "ai_generated"}
                    )
                except Exception as e:
                    logger.error(f"Error getting AI response: {str(e)}")
                    # Fall back to default response if AI fails
                    return ChatResponse(
                        response="❓ I'm not sure how to respond to that question. I can help with stock prices, cryptocurrency trends, mutual funds, investment advice, and general financial concepts. Could you please rephrase your question?",
                        additional_data=None
                    )
            else:
                return ChatResponse(
                    response="❓ I'm not sure how to respond to that question. I can help with stock prices, cryptocurrency trends, mutual funds, investment advice, and general financial concepts. Could you please rephrase your question?",
                    additional_data=None
                )
            
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return ChatResponse(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                additional_data=None
            ) 