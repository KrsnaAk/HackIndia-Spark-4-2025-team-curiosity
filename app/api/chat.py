from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import re
import logging

from app.knowledge_graph.manager import KnowledgeGraphManager
from app.utils.api.crypto import CryptoAPI
from app.utils.api.stock import StockMarketAPI
from app.utils.vector_db import VectorDatabase
from app.utils.web_search import WebSearchClient
from app.utils.gemini_client import GeminiClient

router = APIRouter()
kg_manager = KnowledgeGraphManager()
crypto_api = CryptoAPI()
stock_api = StockMarketAPI()
vector_db = VectorDatabase(collection_name="crypto_projects")
web_search = WebSearchClient()
gemini_client = GeminiClient()  # Initialize the Gemini client

# Populate the knowledge graph with crypto data
try:
    crypto_data = crypto_api.coingecko.funded_projects
    kg_manager.populate_from_crypto_data(crypto_data)
    logging.info(f"Populated Knowledge Graph with {len(crypto_data)} crypto projects")
except Exception as e:
    logging.error(f"Error populating Knowledge Graph: {str(e)}")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    filters: Optional[Dict[str, bool]] = None
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[Any] = None
    knowledge_graph: Dict[str, Any] = {}

# Helper function to detect greetings
def is_greeting(message: str) -> bool:
    greetings = ["hello", "hi", "hey", "greetings", "namaste", "howdy", "hola", 
                 "good morning", "good afternoon", "good evening", "what's up",
                 "ram ram", "radhe radhe"]
    message_lower = message.lower()
    return any(greeting in message_lower for greeting in greetings)

# Function to detect stock market queries
def is_stock_query(message: str) -> bool:
    """Detect if a message is asking about stock market information"""
    message_lower = message.lower()
    
    stock_terms = [
        "stock", "share", "equity", "market", "bse", "nse", "sensex", "nifty",
        "trading", "trader", "dividend", "ipo", "listing", "delist", "bull", "bear",
        "stock market", "share market", "stock price", "share price", "stock value"
    ]
    
    # Look for stock exchanges of India specifically
    indian_exchanges = ["bse", "nse", "sensex", "nifty", "indian stock", "india stock"]
    
    is_general_stock = any(term in message_lower for term in stock_terms)
    is_indian_stock = any(term in message_lower for term in indian_exchanges)
    
    return is_general_stock or is_indian_stock

# Function to detect loan-related queries
def is_loan_query(message: str) -> bool:
    """Detect if a message is asking about loans or financial borrowing"""
    message_lower = message.lower()
    
    # More specific loan-related phrases
    loan_phrases = [
        "tell me about loans",
        "what types of loans",
        "loan information",
        "loan details",
        "loan types",
        "loan options",
        "loan rates",
        "loan interest",
        "loan application",
        "how to get a loan",
        "loan eligibility",
        "loan requirements",
        "loan process",
        "loan calculator",
        "loan comparison"
    ]
    
    # Check for exact phrases first
    if any(phrase in message_lower for phrase in loan_phrases):
        return True
    
    # Then check for specific loan types
    loan_types = [
        "home loan",
        "car loan",
        "personal loan",
        "education loan",
        "student loan",
        "business loan",
        "mortgage loan",
        "auto loan",
        "gold loan",
        "property loan"
    ]
    
    # Must have both "loan" and a specific type
    if "loan" in message_lower and any(loan_type in message_lower for loan_type in loan_types):
        return True
    
    return False

# Function to extract stock symbol from message
def extract_stock_symbol(message: str) -> Optional[str]:
    """Extract stock symbol from a message"""
    # Check if it's actually a stock query
    if not is_stock_query(message):
        return None
    
    # Look for patterns like "price of RELIANCE" or "HDFC Bank stock"
    stock_regex_patterns = [
        r'price of ([A-Za-z0-9\.]+)',
        r'([A-Za-z0-9\.]+) stock',
        r'([A-Za-z0-9\.]+) share',
        r'([A-Za-z0-9\.]+) price',
        r'how is ([A-Za-z0-9\.]+) performing',
        r'buy ([A-Za-z0-9\.]+)',
        r'sell ([A-Za-z0-9\.]+)'
    ]
    
    message_lower = message.lower()
    for pattern in stock_regex_patterns:
        matches = re.findall(pattern, message_lower)
        if matches:
            # Don't consider common words as symbols
            common_words = ["the", "and", "for", "what", "how", "price", "much", "think", "about"]
            
            if matches[0].lower() not in common_words:
                return matches[0].upper()
    
    # If we get here, try to check for known Indian stocks
    known_indian_stocks = ["RELIANCE", "TCS", "HDFC", "INFY", "HDFCBANK", "ICICIBANK", "SBIN"]
    for stock in known_indian_stocks:
        if stock.lower() in message_lower:
            return stock
    
    return None

# Function to detect price prediction queries
def is_prediction_query(message: str) -> bool:
    """Detect if a message is asking for a price prediction"""
    message_lower = message.lower()
    
    # List of prediction-related keywords
    keywords = ["predict", "prediction", "future", "will", "increase", "decrease", 
               "drop", "rise", "fall", "grow", "expect", "forecast", "outlook", 
               "potential", "projections", "think", "opinion", "believe"]
    
    return any(keyword in message_lower for keyword in keywords)

# Function to detect investment suggestion queries
def is_investment_suggestion_query(message: str) -> bool:
    """Detect if a message is asking for investment suggestions or recommendations"""
    message_lower = message.lower()
    
    # Direct match for common investment suggestion phrases
    investment_phrases = [
        "tell me about investing in",
        "tell me about investment in",
        "tell me about investments in",
        "tell me 5 coins",
        "tell me five coins",
        "suggest me 5",
        "recommend 5",
        "advise on investing",
        "give me investment advice",
        "where should i invest",
        "what crypto should i buy",
        "best crypto to buy",
        "top blockchain projects",
        "best projects to invest"
    ]
    
    if any(phrase in message_lower for phrase in investment_phrases):
        return True
    
    # Look for investment suggestion phrases
    suggestion_phrases = [
        "suggest", "recommendation", "recommend", "advice", "advise",
        "what should i buy", "what to buy", "what to invest", "coins to invest",
        "tokens to invest", "should i invest", "good investment", "worth investing",
        "top coins", "best coins", "top crypto", "best crypto", "promising",
        "invest in", "investing in", "investment in", "buy crypto", "buy bitcoin",
        "good crypto", "top blockchain", "best blockchain", "top projects"
    ]
    
    return any(phrase in message_lower for phrase in suggestion_phrases)

# Function to detect if a message is asking for price information
def is_price_query(message: str) -> bool:
    """Detect if a message is specifically asking for price information"""
    message_lower = message.lower()
    
    # Look for price query phrases
    price_phrases = [
        "price of", "how much is", "current price", "trading at",
        "worth", "value of", "price for", "what is the price",
        "how much does", "cost", "what's the price"
    ]
    
    return any(phrase in message_lower for phrase in price_phrases)

# Function to extract crypto symbol from message
def extract_crypto_symbol(message: str) -> Optional[str]:
    """Extract cryptocurrency symbol from a message"""
    # Look for dollar sign followed by ticker
    crypto_price_regex = r'\$([A-Za-z0-9]{2,10})'
    crypto_matches = re.findall(crypto_price_regex, message)
    
    if crypto_matches:
        return crypto_matches[0].upper()
    
    # Only proceed with other extraction methods if this is actually a price query
    if not is_price_query(message):
        return None
    
    # Look for patterns like "price of BTC" or "how much is ETH worth"
    price_regex_patterns = [
        r'price of ([A-Za-z0-9]{2,10})',
        r'how much is ([A-Za-z0-9]{2,10})',
        r'what is ([A-Za-z0-9]{2,10}) trading at',
        r'current price of ([A-Za-z0-9]{2,10})',
        r'([A-Za-z0-9]{2,10}) price',
        r'value of ([A-Za-z0-9]{2,10})',
        r'worth of ([A-Za-z0-9]{2,10})',
        r'prediction for ([A-Za-z0-9]{2,10})',
        r'predict the price of ([A-Za-z0-9]{2,10})'
    ]
    
    message_lower = message.lower()
    for pattern in price_regex_patterns:
        matches = re.findall(pattern, message_lower)
        if matches:
            # Don't consider common words as symbols
            common_words = ["the", "and", "for", "what", "how", "price", "much", "think", "about", 
                          "will", "future", "value", "next", "year", "month", "worth", "prediction"]
            
            if matches[0].lower() not in common_words:
                return matches[0].upper()
    
    # Extract a potential cryptocurrency symbol (needs to be at least 2 characters)
    # Only do this if it's definitely a price query to avoid false matches
    if is_price_query(message):
        potential_symbols = re.findall(r'\b([A-Za-z]{2,10})\b', message)
        common_words = ["the", "and", "for", "what", "how", "price", "much", "think", "about", 
                       "will", "future", "value", "next", "year", "month", "worth", "prediction",
                       "predict", "forecast", "outlook", "potential", "opinion", "believe", "tell",
                       "me", "coins", "coin", "tokens", "token", "crypto", "cryptocurrency"]
        
        for potential in potential_symbols:
            if potential.lower() not in common_words:
                # Try to get price data for this potential symbol
                price_data = crypto_api.get_crypto_price(potential)
                if price_data and "error" not in price_data:
                    return potential.upper()
    
    return None

# Function to get finance-related response
def get_finance_response(message: str, active_categories: List[str]) -> str:
    # Check for specific financial topics
    message_lower = message.lower()
    
    # Check intent classification first (prioritize in this order)
    is_investment = is_investment_suggestion_query(message)
    is_prediction = is_prediction_query(message)
    is_price = is_price_query(message)
    
    # Investment suggestions take highest priority
    if is_investment:
        # Check for blockchain-specific investment queries
        if any(term in message_lower for term in ["blockchain", "crypto", "token", "web3", "defi"]):
            return (
                "When considering blockchain and crypto investments, it's important to diversify and research thoroughly. Here are 5 notable projects across different sectors:\n\n"
                "1. Bitcoin (BTC): The original cryptocurrency with the largest market cap and institutional adoption\n"
                "2. Ethereum (ETH): Leading smart contract platform with the largest ecosystem of dApps and DeFi\n"
                "3. Solana (SOL): High-performance Layer 1 blockchain known for speed and low transaction costs\n"
                "4. Chainlink (LINK): Oracle network connecting blockchains to real-world data\n"
                "5. Polygon (MATIC): Ethereum scaling solution with growing ecosystem and institutional partnerships\n\n"
                "Always conduct your own research, understand the risks, and never invest more than you can afford to lose. Cryptocurrency investments are highly volatile and speculative."
            )
        # General investment advice
        return (
            "When considering crypto investments, it's important to diversify and research thoroughly. Here are 5 notable projects across different sectors:\n\n"
            "1. Bitcoin (BTC): The original cryptocurrency with the largest market cap and institutional adoption\n"
            "2. Ethereum (ETH): Leading smart contract platform with the largest ecosystem of dApps and DeFi\n"
            "3. Solana (SOL): High-performance Layer 1 blockchain known for speed and low transaction costs\n"
            "4. Chainlink (LINK): Oracle network connecting blockchains to real-world data\n"
            "5. Polygon (MATIC): Ethereum scaling solution with growing ecosystem and institutional partnerships\n\n"
            "Always conduct your own research, understand the risks, and never invest more than you can afford to lose. Cryptocurrency investments are highly volatile and speculative."
        )
    
    # Check for project information or emerging tech queries
    for tech_keyword in ["agi", "layer", "new crypto", "web3", "funded", "funding", 
                         "emerging tech", "blockchain tech", "crypto project", "blockchain project",
                         "web3 project", "crypto company", "blockchain company", "crypto startup"]:
        if tech_keyword in message_lower:
            # Look for specific project mentions
            project_pattern = r'\b([A-Za-z]{2,10})\b'
            project_matches = re.findall(project_pattern, message)
            
            for potential_symbol in project_matches:
                if len(potential_symbol) >= 2 and potential_symbol.upper() != "AGI" and potential_symbol.lower() not in ["the", "new", "for", "web", "and", "what", "are", "how", "about", "tell", "me"]:
                    # Try to get project info
                    project_info = crypto_api.coingecko.get_project_info(potential_symbol)
                    if project_info.get("found", False):
                        name = project_info.get("name", potential_symbol)
                        description = project_info.get("description", "")
                        category = project_info.get("category", "")
                        funding = project_info.get("funding", "")
                        mcap = project_info.get("mcap", "")
                        
                        return (
                            f"{name} ({potential_symbol}) is a {category} project. {description}\n\n"
                            f"Funding: {funding}\nMarket Cap: {mcap}"
                        )
            
            # If no specific project found, check if asking about a category
            for category in ["agi", "layer 1", "layer 2", "defi", "web3", "identity", "oracle", "nft"]:
                if category in message_lower:
                    if category == "agi":
                        return (
                            "Artificial General Intelligence (AGI) in the crypto space refers to projects building decentralized AI networks. "
                            "Major AGI crypto projects include:\n\n"
                            "- SingularityNET (AGIX): A decentralized marketplace for AI services\n"
                            "- Fetch.ai (FET): Autonomous agent platform for decentralized machine learning\n"
                            "- Ocean Protocol (OCEAN): Decentralized data exchange protocol for AI datasets\n\n"
                            "These projects aim to create decentralized networks for AI development, ensuring AI remains accessible, transparent and not controlled by a few corporations."
                        )
                    elif "layer" in category:
                        layer_num = "1" if "1" in category else "2"
                        if layer_num == "1":
                            return (
                                "Layer 1 blockchains are base networks like Ethereum, Solana, and Aptos that process and finalize transactions on their own blockchain. "
                                "Recent well-funded Layer 1 projects include:\n\n"
                                "- Sui (SUI): $300M+ funding, focuses on horizontal scaling and high throughput\n"
                                "- Aptos (APT): $350M funding, developed by former Meta employees using Move language\n"
                                "- ZetaChain (ZETA): $30M funding, enables native omnichain applications\n"
                                "- Sei Network (SEI): $30M funding, specialized for trading with parallel execution\n\n"
                                "These new L1s typically focus on scalability, lower fees, and developer-friendly environments."
                            )
                        else:
                            return (
                                "Layer 2 solutions are scaling technologies built on top of Layer 1 blockchains like Ethereum. "
                                "Well-funded Layer 2 projects include:\n\n"
                                "- Arbitrum (ARB): $177M funding, optimistic rollup with widespread adoption\n"
                                "- Base: Coinbase-backed L2 built on OP Stack focusing on mainstream adoption\n"
                                "- Starknet: ZK-rollup with $75M+ funding from Paradigm and others\n"
                                "- zkSync: ZK-rollup with $175M funding, focusing on user and developer experience\n\n"
                                "Layer 2s provide faster transactions and lower fees while inheriting the security of the underlying L1 blockchain."
                            )
            
            # General response about emerging crypto/web3 projects
            return (
                "The crypto/web3 space has several well-funded emerging projects across different categories:\n\n"
                "AGI/AI: SingularityNET (AGIX), Fetch.ai (FET), Ocean Protocol (OCEAN)\n"
                "Layer 1: Sui (SUI), Aptos (APT), ZetaChain (ZETA), Sei Network (SEI)\n"
                "Layer 2: Arbitrum (ARB), Base, Starknet, zkSync\n"
                "DeFi: Pendle Finance (PENDLE), GMX (GMX), dYdX (DYDX)\n"
                "Identity: Worldcoin (WLD), Lit Protocol (LIT)\n"
                "Web3 Infrastructure: Render Network (RNDR), Pyth Network (PYTH)\n\n"
                "Most of these projects have secured funding of $5 million or more, with some raising hundreds of millions from venture capital firms."
            )
    
    # Handle cryptocurrency price or prediction queries
    symbol = extract_crypto_symbol(message)
    if symbol:
        try:
            price_data = crypto_api.get_crypto_price(symbol)
            
            if price_data and "error" not in price_data:
                # Format price with appropriate decimals
                price = price_data.get("price", 0)
                price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
                
                percent_change = price_data.get("percent_change_24h", 0)
                change_str = f"increase of {abs(percent_change):.2f}%" if percent_change >= 0 else f"decrease of {abs(percent_change):.2f}%"
                
                market_cap = price_data.get("market_cap", 0)
                market_cap_str = f"${market_cap/1_000_000_000:.2f} billion" if market_cap >= 1_000_000_000 else f"${market_cap/1_000_000:.2f} million"
                
                name = price_data.get("name", symbol)
                
                # If this is a prediction query, provide a responsible answer
                if is_prediction or any(kw in message_lower for kw in ["predict", "prediction", "future price", "will be worth"]):
                    return (
                        f"Making specific price predictions for cryptocurrencies over long timeframes isn't reliable due to market "
                        f"volatility, regulatory changes, technological developments, and other unpredictable factors. Instead of "
                        f"focusing on price predictions, consider evaluating the project's technology, adoption metrics, team, and "
                        f"long-term viability. The current price of {name} ({symbol}) is {price_str}. Remember that all investments "
                        f"should be based on thorough research and aligned with your financial goals and risk tolerance."
                    )
                else:
                    # Just provide current price information
                    return (
                        f"The current price of {name} ({symbol}) is {price_str}, showing a 24-hour {change_str} "
                        f"with a market cap of {market_cap_str}. (Data may be delayed)"
                    )
            else:
                return f"I couldn't find price information for {symbol}. Please check if the cryptocurrency symbol is correct."
        except Exception as e:
            logging.error(f"Error fetching crypto price: {str(e)}")
            return "I encountered an error while fetching cryptocurrency price data. Please try again later."
    
    # Basic dictionary of finance topics and responses
    finance_topics = {
        "stock": "Stocks represent ownership in a company and can be bought and sold on stock exchanges. They offer potential for capital appreciation and dividend income, but come with market risk.",
        "bond": "Bonds are debt securities that companies or governments issue to raise capital. They typically pay fixed interest and return the principal at maturity, making them generally less risky than stocks.",
        "mutual fund": "Mutual funds pool money from multiple investors to purchase a diversified portfolio of stocks, bonds, or other securities, managed by investment professionals.",
        "etf": "Exchange-Traded Funds (ETFs) are similar to mutual funds but trade on exchanges like stocks. They offer diversification, lower expense ratios, and intraday trading.",
        "investment": "Investment refers to allocating resources (such as money) with the expectation of generating income or profit over time through various vehicles like stocks, bonds, real estate, or businesses.",
        "retirement": "Retirement planning involves strategies to ensure financial security during retirement years, including pension plans, 401(k)s, IRAs, and other investment vehicles.",
        "crypto": "Cryptocurrency is a digital or virtual currency secured by cryptography, making it difficult to counterfeit. Bitcoin, Ethereum, and others operate on decentralized networks using blockchain technology.",
        "bitcoin": "Bitcoin is the first and most well-known cryptocurrency, created in 2009. It operates on a decentralized network without a central authority and has a fixed supply of 21 million coins.",
        "inflation": "Inflation is the rate at which the general level of prices for goods and services rises, causing purchasing power to fall. Central banks typically target low and stable inflation.",
        "interest rate": "Interest rates represent the cost of borrowing money or the return for lending it. They affect everything from mortgages and loans to savings accounts and bond yields.",
        "mortgage": "A mortgage is a loan used to purchase real estate where the property serves as collateral. They typically have 15-30 year terms with fixed or adjustable interest rates.",
        "credit score": "A credit score is a numerical representation of your creditworthiness based on your credit history. Higher scores typically result in better loan terms and interest rates.",
        "budget": "Budgeting is the process of creating a plan for how to spend and save money, helping you track expenses, reduce debt, and achieve financial goals.",
        "tax": "Taxes are mandatory contributions levied by governments on income, property, goods, or services to fund public services and government operations.",
        "diversification": "Diversification is an investment strategy that combines different assets to reduce risk, following the principle of not putting all your eggs in one basket.",
        "portfolio": "An investment portfolio is a collection of financial assets like stocks, bonds, cash, and alternatives, designed to achieve specific financial goals with an appropriate risk level.",
        "asset": "In finance, an asset is anything of value that can be owned or controlled to produce positive economic value, such as cash, securities, inventory, or property.",
        "liability": "A liability is a financial obligation or debt owed to another party, such as loans, mortgages, or accounts payable.",
        "dividend": "Dividends are portions of a company's earnings distributed to shareholders, typically in cash or additional shares, representing a return on investment.",
        "capital gain": "A capital gain occurs when you sell an investment for more than you paid for it. These gains may be subject to capital gains tax.",
        "ira": "An Individual Retirement Account (IRA) is a tax-advantaged investment account designed to help you save for retirement with either pre-tax (Traditional) or after-tax (Roth) contributions.",
        "401k": "A 401(k) is an employer-sponsored retirement plan that allows employees to contribute a portion of their wages on a pre-tax basis, often with employer matching contributions.",
        "risk": "In finance, risk refers to the possibility that an investment's actual return will differ from the expected return, potentially resulting in loss of principal.",
        "market": "Financial markets are venues where buyers and sellers trade financial assets such as stocks, bonds, commodities, currencies, and derivatives.",
        "bear market": "A bear market is characterized by falling securities prices (typically 20% or more) and widespread pessimism, often during economic downturns.",
        "bull market": "A bull market features rising securities prices and investor optimism, typically during periods of economic expansion.",
        "hedge fund": "Hedge funds are alternative investments that use pooled funds and employ various strategies to earn active returns for their investors, often with higher fees.",
        "private equity": "Private equity involves investing directly in private companies or buyouts of public companies, with capital not listed on public exchanges.",
        "ipo": "An Initial Public Offering (IPO) is the process of offering shares of a private corporation to the public for the first time, allowing companies to raise capital.",
        "reit": "Real Estate Investment Trusts (REITs) are companies that own, operate, or finance income-generating real estate, offering investors regular income streams and long-term capital appreciation.",
        "commodity": "Commodities are basic goods used in commerce that are interchangeable with other goods of the same type, such as gold, oil, natural gas, and agricultural products.",
        "forex": "The foreign exchange (forex) market is where currencies are traded, representing the world's largest and most liquid financial market.",
        "option": "Options are financial derivatives that give buyers the right, but not the obligation, to buy or sell an underlying asset at a specified price within a specific time period.",
        "futures": "Futures contracts obligate the buyer to purchase and the seller to sell an asset at a predetermined future date and price, commonly used for commodities and financial instruments.",
        "liquidity": "Liquidity refers to how quickly an asset can be converted to cash without affecting its market price, with cash being the most liquid asset.",
        "leverage": "Financial leverage involves using borrowed capital to increase the potential return of an investment, magnifying both gains and losses.",
        "arbitrage": "Arbitrage is the practice of taking advantage of price differences in different markets for the same asset, buying in one market and selling in another for profit.",
        "roi": "Return on Investment (ROI) measures the performance of an investment by dividing the profit by the cost, expressed as a percentage.",
        "yield": "Yield is the income returned on an investment, such as interest or dividends, expressed as a percentage based on the investment's cost or market value.",
    }
    
    # Check for exact matches or keywords in the message
    for topic, response in finance_topics.items():
        if topic in message_lower or (len(topic.split()) > 1 and all(word in message_lower for word in topic.split())):
            return response
            
    # Check for specific categories
    if "category" in message_lower or "filter" in message_lower:
        return "You can filter financial information by categories like investments, banking, market, and risk using the sidebar filters."
    
    # Default finance response for general finance queries
    return "I can help you with various finance topics like investments, stocks, bonds, retirement planning, budgeting, taxes, and more. Could you please specify what financial information you're looking for?"

# Function to detect if a message is asking about a specific crypto project
def is_project_query(message: str) -> Optional[str]:
    """Detect if a message is asking about a specific crypto project and return the project name"""
    message_lower = message.lower()
    
    # Common crypto project names (not tickers)
    project_names = {
        "singularitynet": "AGIX",
        "singularity net": "AGIX",
        "singularity": "AGIX",
        "fetch.ai": "FET", 
        "fetchai": "FET",
        "fetch ai": "FET",
        "fetch": "FET",
        "ocean protocol": "OCEAN",
        "ocean": "OCEAN",
        "sui": "SUI",
        "aptos": "APT",
        "zetachain": "ZETA",
        "zeta chain": "ZETA",
        "worldcoin": "WORLDCOIN",
        "lit protocol": "LIT",
        "lit": "LIT",
        "render network": "RENDER",
        "render": "RENDER",
        "arbitrum": "ARB",
        "base": "BASE",
        "pendle": "PENDLE",
        "mask network": "MASK",
        "mask": "MASK",
        "pyth": "PYTH",
        "pyth network": "PYTH"
    }
    
    # Check for project names in the message
    for project, symbol in project_names.items():
        if project in message_lower:
            return symbol
    
    # Look for specific patterns indicating a project query
    project_query_phrases = [
        "tell me about",
        "what is",
        "who is",
        "information on",
        "details about",
        "learn about",
        "explain"
    ]
    
    if any(phrase in message_lower for phrase in project_query_phrases):
        # Extract potential project names
        words = message_lower.split()
        for project, symbol in project_names.items():
            project_words = project.split()
            if len(project_words) == 1:  # Single word project names
                if project_words[0] in words:
                    return symbol
    
    return None

# Function to detect if a message is asking about Indian investments
def is_indian_investment_query(message: str) -> bool:
    """Detect if a message is asking about Indian investment options"""
    message_lower = message.lower()
    
    # Keywords related to Indian investments
    indian_investment_keywords = [
        "india", "indian", "market", "invest", "investment", "financial", "plan",
        "mutual fund", "nps", "ppf", "fd", "fixed deposit", "equity", "stock", "share",
        "real estate", "property", "gold", "bond", "debenture", "ulip", "insurance",
        "saving", "retirement", "pension", "tax saving", "elss", "sukanya", "senior citizen",
        "scheme", "portfolio", "asset allocation", "returns", "yield", "interest rate",
        "inr", "rupee", "lakh", "crore", "nse", "bse", "where should i invest"
    ]
    
    return any(keyword in message_lower for keyword in indian_investment_keywords)

# Function to get Indian investment recommendations
def get_indian_investment_recommendations(message: str) -> str:
    """Provide recommendations for Indian investment options based on the message"""
    message_lower = message.lower()
    
    # Check for specific interest in investment types
    
    # Comprehensive investment plan
    if any(phrase in message_lower for phrase in ["all", "detail", "comprehensive", "full", "complete", "financial plan", "investment plan", "where should i invest", "best investment"]):
        return (
            "Here are the best investment options available in the Indian market:\n\n"
            "1. Equity Investments (12-15% long-term returns):\n"
            "   - Direct Stocks: Individual company shares through NSE/BSE\n"
            "   - Mutual Funds: Large cap (12-15%), Mid cap (15-18%), Small cap (high risk/reward)\n"
            "   - ELSS Funds: Equity Linked Savings Scheme with 3-year lock-in and 80C tax benefits\n\n"
            "2. Fixed Income (5-9% returns):\n"
            "   - Fixed Deposits: Bank FDs (5.5-7%), Corporate FDs (7-9%)\n"
            "   - Government Securities: G-Secs, T-Bills (7-7.5%)\n"
            "   - Public Provident Fund (PPF): 7.1% tax-free returns, 15-year lock-in\n"
            "   - National Savings Certificate (NSC): 7% returns, 5-year lock-in\n\n"
            "3. Gold Investments (8-10% long-term returns):\n"
            "   - Sovereign Gold Bonds: 2.5% annual interest + gold price appreciation\n"
            "   - Gold ETFs: No making charges, high liquidity\n"
            "   - Digital Gold: Low entry barrier (₹10)\n\n"
            "4. Real Estate (8-12% returns):\n"
            "   - Residential/Commercial Properties: Direct ownership\n"
            "   - REITs: Real Estate Investment Trusts (8-10% annual yields)\n"
            "   - Fractional Ownership: Commercial property investment platforms\n\n"
            "5. Retirement-focused Options:\n"
            "   - National Pension System (NPS): Additional tax benefits under 80CCD(1B)\n"
            "   - Atal Pension Yojana: For unorganized sector workers\n\n"
            "6. Insurance-linked Investment:\n"
            "   - ULIPs: Unit Linked Insurance Plans with market-linked returns\n"
            "   - Traditional Plans: Endowment, money-back policies (5-6% returns)\n\n"
            "7. Small Saving Schemes (Government-backed):\n"
            "   - Sukanya Samriddhi Yojana: 7.6% for girl child education\n"
            "   - Senior Citizens Savings Scheme: 8.2% for seniors\n"
            "   - Post Office Monthly Income Scheme: 7.4% with monthly payouts\n\n"
            "8. Alternative Investments (Higher risk):\n"
            "   - P2P Lending: 10-14% returns through platforms like LendenClub\n"
            "   - Startup Investments: Through angel networks, platforms\n"
            "   - Invoice Discounting: 12-14% returns through platforms like KredX\n\n"
            "For optimal allocation, consider the 50-30-20 rule: 50% in equity for growth (adjust based on age), 30% in fixed income for stability, and 20% in gold/alternative investments for diversification."
        )
    
    # Equity-focused query
    if any(phrase in message_lower for phrase in ["equity", "stock", "share", "mutual fund", "market", "nse", "bse", "sensex", "nifty"]):
        return (
            "For equity investments in India, consider these options:\n\n"
            "1. Direct Stocks: Investing directly in companies listed on NSE/BSE\n"
            "   - Pros: No expense ratio, potential for high returns (15-20%+)\n"
            "   - Cons: Requires research, monitoring, higher risk\n"
            "   - Best for: Experienced investors with time for research\n\n"
            "2. Mutual Funds:\n"
            "   - Large Cap Funds: Stable returns (12-15%) with lower risk (e.g., HDFC Top 100, Axis Bluechip)\n"
            "   - Mid Cap Funds: Higher growth potential (15-18%) with moderate risk (e.g., Kotak Emerging Equity)\n"
            "   - Small Cap Funds: Highest growth potential (18-22%) but higher volatility (e.g., SBI Small Cap)\n"
            "   - Index Funds: Low-cost funds tracking indexes like Nifty 50 (e.g., UTI Nifty Index Fund)\n"
            "   - ELSS Funds: Tax-saving equity funds with 3-year lock-in (e.g., Axis Long Term Equity)\n\n"
            "3. ETFs (Exchange Traded Funds):\n"
            "   - Nifty ETFs: Track Nifty 50 with very low expense ratios\n"
            "   - Sectoral ETFs: Focus on specific sectors like banking, IT\n\n"
            "Current outlook: Indian equity markets have shown strong performance with Nifty 50 delivering ~15% CAGR over the past 10 years. For long-term wealth creation (7+ years), maintaining 50-70% allocation to equity is recommended based on your risk appetite and age."
        )
    
    # Fixed income / debt query
    if any(phrase in message_lower for phrase in ["fixed", "debt", "fd", "deposit", "bond", "interest", "income", "ppf", "provident", "safe", "guaranteed"]):
        return (
            "Fixed income investment options in India offer stability and regular income:\n\n"
            "1. Bank Fixed Deposits (FDs):\n"
            "   - Returns: 5.5-7% depending on tenure and bank\n"
            "   - Top rates: Small finance banks offer up to 7.5-8%\n"
            "   - Safety: Insured up to ₹5 lakhs by DICGC\n"
            "   - Taxation: Interest taxed at income tax slab rate\n\n"
            "2. Government Schemes:\n"
            "   - Public Provident Fund (PPF): 7.1%, tax-free, 15-year lock-in, ₹1.5 lakh annual limit\n"
            "   - National Savings Certificate (NSC): 7%, 5-year lock-in, 80C tax benefit\n"
            "   - Senior Citizens Savings Scheme: 8.2% for seniors above 60, 5-year tenure\n"
            "   - Post Office Monthly Income Scheme: 7.4%, monthly payouts, 5-year tenure\n\n"
            "3. Government Securities (G-Secs):\n"
            "   - Directly through RBI Retail Direct platform\n"
            "   - Returns: 7-7.5% for 10-year government bonds\n"
            "   - Sovereign guarantee (safest)\n\n"
            "4. Corporate Bonds and Debentures:\n"
            "   - Returns: 7-9% depending on company rating\n"
            "   - Available through bond platforms like Goldenpi, BondsIndia\n"
            "   - Higher risk than government securities but better returns\n\n"
            "5. Debt Mutual Funds:\n"
            "   - Liquid Funds: 6-6.5%, high liquidity, low risk\n"
            "   - Short-term Debt Funds: 7-8%, for 1-3 year horizon\n"
            "   - Corporate Bond Funds: 7.5-8.5%, invest primarily in AA+ rated bonds\n"
            "   - Taxation advantage: Indexation benefit on holds over 3 years\n\n"
            "Current outlook: With RBI maintaining high interest rates, fixed income investments are offering attractive returns. Consider laddering your fixed deposits or bonds (spreading across different maturities) to optimize returns and maintain liquidity."
        )
    
    # Real estate query
    if any(phrase in message_lower for phrase in ["real estate", "property", "house", "apartment", "commercial", "reit", "rent"]):
        return (
            "Real estate investment options in India:\n\n"
            "1. Residential Property:\n"
            "   - Current yields: 2-3% rental yield in major cities\n"
            "   - Capital appreciation: 5-8% annually depending on location\n"
            "   - High ticket size (₹30 lakhs - ₹2 crores+)\n"
            "   - Best locations: Pune, Bengaluru, and Hyderabad have shown consistent growth\n\n"
            "2. Commercial Property:\n"
            "   - Higher yields: 6-10% rental yields\n"
            "   - Stable tenants with longer lease terms (3-9 years)\n"
            "   - Higher ticket size (₹1 crore+)\n\n"
            "3. REITs (Real Estate Investment Trusts):\n"
            "   - More accessible (starting ₹10,000-15,000)\n"
            "   - Current yield: 7-9% annually\n"
            "   - Listed REITs: Embassy Office Parks, Mindspace Business Parks, Brookfield India\n"
            "   - Liquidity through stock exchange trading\n\n"
            "4. Fractional Ownership Platforms:\n"
            "   - Invest in premium properties with lower capital (₹10-25 lakhs)\n"
            "   - Expected returns: 8-12% (rental yield + appreciation)\n"
            "   - Platforms: PropertyShare, hBits, Strata\n\n"
            "5. Real Estate Funds:\n"
            "   - Professionally managed, high minimum investment (₹50 lakhs+)\n"
            "   - Expected returns: 12-18% IRR\n"
            "   - For accredited/high net worth investors\n\n"
            "Current outlook: Post-pandemic, commercial real estate is recovering strongly, with REITs offering an accessible entry point. Residential real estate prices are rising after years of stagnation, with premium properties showing better appreciation. Consider REITs for beginner investors and direct ownership for long-term wealth creation if you have significant capital."
        )
    
    # Gold investment query
    if any(phrase in message_lower for phrase in ["gold", "sovereign gold bond", "sgb", "digital gold", "bullion", "jewelry", "precious metal"]):
        return (
            "Gold investment options in India:\n\n"
            "1. Sovereign Gold Bonds (SGBs):\n"
            "   - Best option for long-term investors\n"
            "   - 2.5% annual interest + gold price appreciation\n"
            "   - Tax benefits: Tax-free capital gains if held till maturity (8 years)\n"
            "   - Issued by RBI with government guarantee\n"
            "   - Available through banks, post offices, and stock brokers\n\n"
            "2. Gold ETFs (Exchange Traded Funds):\n"
            "   - Trade on stock exchanges like shares\n"
            "   - High liquidity, no storage concerns\n"
            "   - No making charges (unlike physical gold)\n"
            "   - Small expense ratio (0.5-1%)\n"
            "   - Popular options: Nippon India Gold ETF, SBI Gold ETF\n\n"
            "3. Digital Gold:\n"
            "   - Start with as little as ₹10\n"
            "   - Platforms: Paytm, PhonePe, Google Pay partner with MMTC-PAMP or SafeGold\n"
            "   - Option to convert to physical gold\n"
            "   - Convenient but slightly higher charges\n\n"
            "4. Gold Mutual Funds:\n"
            "   - Invest in gold ETFs\n"
            "   - Systematic Investment Plan (SIP) option available\n"
            "   - Slightly higher expense ratio than direct ETFs\n\n"
            "5. Physical Gold:\n"
            "   - Jewelry: High making charges (10-25%), emotional value\n"
            "   - Coins/Bars: Lower making charges (5-10%), from banks or jewelers\n"
            "   - Storage and insurance concerns\n\n"
            "Current outlook: Gold has historically delivered 8-10% CAGR over the long term and serves as a hedge against inflation and economic uncertainty. Recommended allocation is 10-15% of your investment portfolio. SGBs are currently the most tax-efficient and rewarding way to invest in gold for the long term."
        )
    
    # Tax-saving/ELSS query
    if any(phrase in message_lower for phrase in ["tax saving", "tax benefit", "80c", "elss", "tax", "save tax"]):
        return (
            "Tax-saving investment options in India (Section 80C and beyond):\n\n"
            "1. ELSS (Equity Linked Savings Scheme):\n"
            "   - Mutual funds with 3-year lock-in (shortest among tax-saving instruments)\n"
            "   - Potential returns: 12-15% long-term CAGR\n"
            "   - Tax deduction up to ₹1.5 lakhs under Section 80C\n"
            "   - Top performers: Axis Long Term Equity, Parag Parikh Tax Saver, Quant Tax Plan\n\n"
            "2. Public Provident Fund (PPF):\n"
            "   - 7.1% tax-free returns with 15-year lock-in (partial withdrawal allowed after 7 years)\n"
            "   - Completely tax-free (EEE - exempt-exempt-exempt)\n"
            "   - Up to ₹1.5 lakhs deduction under Section 80C\n"
            "   - Sovereign guarantee (extremely safe)\n\n"
            "3. National Pension System (NPS):\n"
            "   - Additional ₹50,000 deduction under 80CCD(1B) beyond 80C limit\n"
            "   - Potential returns: 9-12% based on asset allocation\n"
            "   - Low cost but locked until retirement (partial withdrawal allowed for specific needs)\n\n"
            "4. Tax-Saving Fixed Deposits:\n"
            "   - 5-year lock-in period\n"
            "   - Current rates: 6.5-7% depending on the bank\n"
            "   - Section 80C benefit up to ₹1.5 lakhs\n"
            "   - Interest taxable at income tax slab rate\n\n"
            "5. National Savings Certificate (NSC):\n"
            "   - 7% returns with 5-year maturity\n"
            "   - Section 80C benefit up to ₹1.5 lakhs\n"
            "   - Interest reinvested and qualifies for deduction each year\n\n"
            "6. Unit Linked Insurance Plans (ULIPs):\n"
            "   - Insurance + Investment with 5-year lock-in\n"
            "   - Market-linked returns (8-12% potentially)\n"
            "   - Tax-free maturity under Section 10(10D) if conditions met\n\n"
            "7. Sukanya Samriddhi Yojana (for girl child):\n"
            "   - 7.6% tax-free returns\n"
            "   - For daughters under 10 years of age\n"
            "   - 21-year lock-in (partial withdrawal allowed for education after 18)\n\n"
            "Recommendation: Diversify your tax-saving investments. For higher returns, allocate more to ELSS funds. For safety, consider PPF. If you've exhausted your 80C limit, utilize NPS for additional tax benefits."
        )
    
    # Retirement planning query
    if any(phrase in message_lower for phrase in ["retirement", "pension", "nps", "old age", "senior"]):
        return (
            "Retirement planning options in India:\n\n"
            "1. National Pension System (NPS):\n"
            "   - Government-backed retirement scheme\n"
            "   - Tax benefits: 80C deduction + additional ₹50,000 under 80CCD(1B)\n"
            "   - Asset allocation options: Auto (lifecycle based), Aggressive (max 75% equity), Moderate, Conservative\n"
            "   - Historical returns: Equity plans (9-12%), Corporate Debt (9-10%), Government Securities (8-9%)\n"
            "   - Partial withdrawal allowed for specific needs, 60% taxable at maturity\n\n"
            "2. Employees' Provident Fund (EPF):\n"
            "   - For salaried employees\n"
            "   - Current interest rate: 8.15%\n"
            "   - Tax-free returns if within limits\n"
            "   - Employer also contributes an equal amount\n\n"
            "3. Public Provident Fund (PPF):\n"
            "   - 7.1% tax-free returns\n"
            "   - 15-year tenure (extendable)\n"
            "   - Complete EEE status (tax-free at all stages)\n"
            "   - Annual investment limit: ₹1.5 lakhs\n\n"
            "4. Systematic Investment Plans (SIPs) in Mutual Funds:\n"
            "   - Long-term equity investments for wealth creation\n"
            "   - Potential returns: 12-15% CAGR over long periods\n"
            "   - Recommended funds for retirement: Index funds, Balanced Advantage Funds, Multi-cap Funds\n\n"
            "5. Atal Pension Yojana:\n"
            "   - For unorganized sector workers\n"
            "   - Guaranteed pension of ₹1,000-5,000 per month after 60\n"
            "   - Government co-contribution for eligible subscribers\n\n"
            "6. Senior Citizens Saving Scheme (after retirement):\n"
            "   - 8.2% interest rate paid quarterly\n"
            "   - 5-year tenure (extendable once)\n"
            "   - Maximum investment: ₹15 lakhs\n\n"
            "7. Pradhan Mantri Vaya Vandana Yojana:\n"
            "   - For seniors above 60\n"
            "   - Guaranteed pension of 7.4% per annum\n"
            "   - 10-year policy term\n\n"
            "Retirement planning strategy: Follow the 'multiply by 25' rule - your retirement corpus should be at least 25 times your annual expenses. For a monthly expense of ₹50,000, aim for a corpus of at least ₹1.5 crores. Start early and increase allocation as you age."
        )
    
    # Default investment advice for Indian market
    return (
        "For investments in the Indian market, here are the best options based on your goals:\n\n"
        "1. Short-term goals (1-3 years):\n"
        "   - Bank FDs: 5.5-7% returns\n"
        "   - Short-term debt funds: 7-8% potential returns\n"
        "   - Liquid funds: 6-6.5% with high liquidity\n\n"
        "2. Medium-term goals (3-7 years):\n"
        "   - Corporate bonds: 7-9% returns\n"
        "   - Balanced/Hybrid mutual funds: 9-11% potential returns\n"
        "   - Government securities: 7-7.5% with sovereign guarantee\n\n"
        "3. Long-term goals (7+ years):\n"
        "   - Equity mutual funds: 12-15% historical returns\n"
        "   - NPS: 9-12% with tax benefits\n"
        "   - PPF: 7.1% tax-free returns\n"
        "   - Real Estate: 8-12% including rental yields and appreciation\n\n"
        "4. Tax-saving investments (80C - ₹1.5 lakh limit):\n"
        "   - ELSS funds: 12-15% potential returns with 3-year lock-in\n"
        "   - PPF: 7.1% tax-free with 15-year lock-in\n"
        "   - Tax-saving FDs: 6.5-7% with 5-year lock-in\n\n"
        "For optimal allocation, follow the 100-minus-age rule for equity exposure: If you're 30 years old, allocate approximately 70% to equity and 30% to debt and alternatives."
    )

# Function to detect detailed financial queries for Indian market
def is_detailed_financial_query(message: str) -> bool:
    """Detect if a message is asking for detailed information about Indian financial concepts"""
    message_lower = message.lower()
    
    # Keywords related to detailed financial queries
    detailed_query_keywords = [
        "explain in detail", "detailed", "depth", "comprehensive", "elaborate", 
        "loan details", "tax implications", "financial planning", "provide details",
        "details about", "explain how", "step by step", "process", "procedure",
        "eligibility", "rules", "regulations", "requirements", "calculation",
        "formula", "method", "approach", "system", "framework"
    ]
    
    # Return True if any of the keywords are present in the message
    return any(keyword in message_lower for keyword in detailed_query_keywords)

# Function to detect tax-related queries
def is_tax_query(message: str) -> bool:
    """Detect if a message is asking about taxes in India"""
    message_lower = message.lower()
    
    # Keywords related to taxes
    tax_keywords = [
        "tax", "taxation", "income tax", "gst", "goods and services tax", "tds",
        "tax deducted at source", "capital gains", "tax saving", "tax exemption",
        "tax deduction", "tax benefit", "tax slab", "tax rate", "tax filing",
        "itr", "income tax return", "tax planning", "tax calculator", "tax regime",
        "80c", "80d", "huf", "house rent allowance", "hra", "tcs", "tds return",
        "tax audit", "advance tax", "self assessment tax", "form 16", "tax credit"
    ]
    
    return any(keyword in message_lower for keyword in tax_keywords)

# Function to get detailed financial information using Gemini
def get_detailed_financial_information(message: str) -> str:
    """Get detailed information about financial topics using Gemini"""
    try:
        # Categorize the query
        categorization = gemini_client.categorize_financial_query(message)
        category = categorization.get("category", "General Financial Planning")
        specific_topic = categorization.get("specific_topic", message)
        
        # Generate response based on category
        if category == "Loan":
            return gemini_client.get_loan_information(specific_topic)
        elif category == "Tax":
            return gemini_client.get_tax_information(specific_topic)
        else:
            return gemini_client.get_indian_financial_advice(specific_topic, context=message)
    
    except Exception as e:
        logging.error(f"Error getting detailed financial information: {str(e)}")
        return (
            "I'm unable to provide detailed information at the moment. "
            "Please try rephrasing your question or ask about a different financial topic."
        )

# Function to detect if query is about crypto trading
def is_trading_query(message: str) -> bool:
    """Detect if a message is asking about cryptocurrency trading mechanisms"""
    message_lower = message.lower()
    
    # Keywords related to crypto trading
    trading_keywords = [
        "futures trading", "p2p trading", "spot trading", "margin trading", 
        "futures", "p2p", "derivatives", "perpetual", "swap", "leverage", 
        "margin", "binance", "bybit", "okx", "exchange", "trading", "trade", 
        "hedging", "liquidation", "short", "long", "grid trading", "funding rate",
        "options trading", "dex", "decentralized exchange", "amm", "limit order"
    ]
    
    return any(keyword in message_lower for keyword in trading_keywords)

# Function to detect if a message is asking about relationships between projects
def is_relationship_query(message: str) -> bool:
    """Detect if a message is asking about relationships between projects"""
    message_lower = message.lower()
    
    # Keywords related to relationships
    relationship_keywords = [
        "relationship", "connected to", "connection", "compared to", "versus", "vs", 
        "similar to", "different from", "difference between", "related to", "competitor",
        "works with", "built on", "ecosystem", "network", "compatible", "integration",
        "partnership", "backed by", "invested in", "relation", "compared with",
        "whats the connection", "how are they related", "how do they compare"
    ]
    
    return any(keyword in message_lower for keyword in relationship_keywords)

def get_project_details(project_name: str) -> str:
    """Get detailed information about a crypto project"""
    try:
        # Search for the project
        search_results = crypto_api.search_crypto(project_name)
        if not search_results:
            return f"I couldn't find information about {project_name}. Please check the spelling or try a different project name."

        # Get the first matching project
        project = search_results[0]
        symbol = project.get('symbol', '').upper()
        
        # Get current price and market data
        price_data = crypto_api.get_crypto_price(symbol)
        details = crypto_api.get_crypto_details(symbol)
        
        # Format the response
        response = f"Here's detailed information about {project.get('name', project_name)} ({symbol}):\n\n"
        
        # Price Information
        if price_data and 'error' not in price_data:
            response += "Current Market Data:\n"
            response += f"- Price: ${price_data.get('price', 'N/A')}\n"
            response += f"- 24h Change: {price_data.get('percent_change_24h', 'N/A')}%\n"
            response += f"- Market Cap: ${price_data.get('market_cap', 'N/A'):,.2f}\n"
            response += f"- 24h Volume: ${price_data.get('volume_24h', 'N/A'):,.2f}\n\n"
        
        # Project Details
        if details and 'error' not in details:
            response += "Project Details:\n"
            response += f"- Category: {details.get('category', 'N/A')}\n"
            response += f"- Description: {details.get('description', 'N/A')}\n"
            response += f"- Website: {details.get('website', 'N/A')}\n"
            response += f"- GitHub: {details.get('github', 'N/A')}\n"
            response += f"- Twitter: {details.get('twitter', 'N/A')}\n\n"
            
            # Technical Details
            if 'technical_details' in details:
                tech = details['technical_details']
                response += "Technical Details:\n"
                response += f"- Consensus: {tech.get('consensus', 'N/A')}\n"
                response += f"- Block Time: {tech.get('block_time', 'N/A')}\n"
                response += f"- TPS: {tech.get('tps', 'N/A')}\n"
                response += f"- Layer: {tech.get('layer', 'N/A')}\n\n"
            
            # Tokenomics
            if 'tokenomics' in details:
                token = details['tokenomics']
                response += "Tokenomics:\n"
                response += f"- Total Supply: {token.get('total_supply', 'N/A')}\n"
                response += f"- Circulating Supply: {token.get('circulating_supply', 'N/A')}\n"
                response += f"- Max Supply: {token.get('max_supply', 'N/A')}\n"
                response += f"- Inflation Rate: {token.get('inflation_rate', 'N/A')}\n\n"
        
        # Add disclaimer
        response += "Disclaimer: This information is for educational purposes only. Always do your own research before making investment decisions."
        
        return response
        
    except Exception as e:
        logging.error(f"Error getting project details for {project_name}: {str(e)}")
        return f"I encountered an error while fetching information about {project_name}. Please try again later."

@router.post("/")
async def chat(request: ChatRequest):
    message = request.message
    filters = request.filters
    history = request.history or []
    
    try:
        # Log the incoming message
        logging.info(f"Processing message: {message}")
        
        # Check for greeting
        if is_greeting(message) and len(message.split()) < 5:
            return ChatResponse(
                response="Hello! I'm your finance assistant. How can I help with your financial questions today?"
            )
        
        # Check for stock market query
        if is_stock_query(message):
            stock_symbol = extract_stock_symbol(message)
            if stock_symbol:
                try:
                    # First try NSE for Indian stocks
                    stock_data = stock_api.get_stock_price(stock_symbol, provider="nse_india")
                    if "error" not in stock_data and stock_data.get("price"):
                        # Format Indian stock data response
                        return ChatResponse(
                            response=f"Here is the current information for {stock_symbol} on NSE India:\n\n"
                                    f"Price: ₹{stock_data.get('price', 'N/A')}\n"
                                    f"Change: {stock_data.get('change', 'N/A')} ({stock_data.get('change_percent', 'N/A')}%)\n"
                                    f"Day High: ₹{stock_data.get('day_high', 'N/A')}\n"
                                    f"Day Low: ₹{stock_data.get('day_low', 'N/A')}\n"
                                    f"52 Week High: ₹{stock_data.get('year_high', 'N/A')}\n"
                                    f"52 Week Low: ₹{stock_data.get('year_low', 'N/A')}\n"
                                    f"Volume: {stock_data.get('volume', 'N/A')}\n",
                            data=stock_data
                        )
                except Exception as e:
                    logging.error(f"Error fetching stock data for {stock_symbol}: {str(e)}")
                    # Continue with general stock market response if API calls fail
            
            # General stock market query
            if "best stocks" in message.lower() or "top stocks" in message.lower() or "stock recommendations" in message.lower():
                if "india" in message.lower() or "indian" in message.lower() or "nse" in message.lower() or "bse" in message.lower():
                    return ChatResponse(
                        response="Here are some of the top-performing stocks on the Indian market:\n\n"
                                "1. **Reliance Industries (RELIANCE)** - India's largest conglomerate with interests in petrochemicals, oil and gas, telecom, and retail\n"
                                "2. **Tata Consultancy Services (TCS)** - India's largest IT services company\n"
                                "3. **HDFC Bank (HDFCBANK)** - One of India's leading private sector banks\n"
                                "4. **Infosys (INFY)** - Global IT consulting and services company\n"
                                "5. **State Bank of India (SBIN)** - India's largest public sector bank\n\n"
                                "Remember that stock performance changes frequently, and you should conduct your own research or consult with a financial advisor before making investment decisions."
                    )
                else:
                    return ChatResponse(
                        response="Here are some widely-tracked stocks in the global market:\n\n"
                                "1. **Apple (AAPL)** - Consumer electronics and technology services\n"
                                "2. **Microsoft (MSFT)** - Software, cloud computing, and technology services\n" 
                                "3. **Amazon (AMZN)** - E-commerce, cloud computing, and digital streaming\n"
                                "4. **Alphabet/Google (GOOGL)** - Internet services and products\n"
                                "5. **Tesla (TSLA)** - Electric vehicles and clean energy\n\n"
                                "Remember that stock performance changes frequently, and you should conduct your own research or consult with a financial advisor before making investment decisions."
                    )
            
            # Use stock market fallback for general stock market queries
            is_indian_stock_query = "india" in message.lower() or "indian" in message.lower() or "nse" in message.lower() or "bse" in message.lower() or "sensex" in message.lower() or "nifty" in message.lower()
            return ChatResponse(
                response=gemini_client.get_stock_market_fallback(is_indian=is_indian_stock_query)
            )
        
        # Check for loan query
        if is_loan_query(message):
            if "home loan" in message.lower() or "housing loan" in message.lower() or "mortgage" in message.lower():
                if "india" in message.lower() or "indian" in message.lower():
                    return ChatResponse(
                        response="# Home Loans in India\n\n"
                                "Home loans in India typically have the following characteristics:\n\n"
                                "**Interest Rates:** Currently ranging from 8.50% to 10.50% p.a.\n\n"
                                "**Loan Tenure:** Up to 30 years\n\n"
                                "**Loan-to-Value Ratio:** Up to 80-90% of the property value\n\n"
                                "**Top Lenders:**\n"
                                "- State Bank of India (SBI)\n"
                                "- HDFC Limited\n"
                                "- ICICI Bank\n"
                                "- Axis Bank\n"
                                "- LIC Housing Finance\n\n"
                                "**Required Documents:**\n"
                                "- Identity proof (Aadhar, PAN, Passport)\n"
                                "- Address proof\n"
                                "- Income documents (salary slips or ITR)\n"
                                "- Property documents\n\n"
                                "**Tax Benefits:** Under Section 80C for principal repayment (up to ₹1.5 lakh) and Section 24(b) for interest payment (up to ₹2 lakh for self-occupied properties)\n\n"
                                "**Eligibility:** Typically requires a good credit score (700+), stable income, and employment history\n\n"
                                "**Processing Fees:** Usually 0.5% to 1% of the loan amount\n\n"
                                "Would you like more specific information about any aspect of home loans in India?"
                    )
                else:
                    return ChatResponse(
                        response="# Home Loans/Mortgages\n\n"
                                "Home loans or mortgages are long-term loans for purchasing or refinancing a home. Here are the key aspects:\n\n"
                                "**Types of Mortgages:**\n"
                                "- Fixed-rate mortgages: Interest rate remains the same throughout the loan term\n"
                                "- Adjustable-rate mortgages (ARMs): Interest rate adjusts periodically based on market conditions\n"
                                "- FHA loans: Government-backed loans with lower down payment requirements\n"
                                "- VA loans: For veterans and service members\n"
                                "- USDA loans: For rural homebuyers\n\n"
                                "**Typical Terms:**\n"
                                "- Down payment: 3% to 20% of the home's value\n"
                                "- Loan terms: 15, 20, or 30 years (30 years being most common)\n"
                                "- Interest rates: Vary based on market conditions, credit score, and loan type\n\n"
                                "**Eligibility Factors:**\n"
                                "- Credit score (typically 620+ for conventional loans)\n"
                                "- Debt-to-income ratio (typically below 43%)\n"
                                "- Employment history and income stability\n"
                                "- Down payment amount\n\n"
                                "Would you like more specific information about mortgage rates, the application process, or refinancing options?"
                    )
            
            if "personal loan" in message.lower():
                if "india" in message.lower() or "indian" in message.lower():
                    return ChatResponse(
                        response="# Personal Loans in India\n\n"
                                "Personal loans in India typically have the following characteristics:\n\n"
                                "**Interest Rates:** Generally between 10.5% to 24% p.a.\n\n"
                                "**Loan Amount:** Usually ranges from ₹10,000 to ₹40 lakh\n\n"
                                "**Loan Tenure:** Usually 1 to 5 years\n\n"
                                "**Top Lenders:**\n"
                                "- HDFC Bank\n"
                                "- SBI\n"
                                "- ICICI Bank\n"
                                "- Bajaj Finserv\n"
                                "- Axis Bank\n\n"
                                "**Required Documents:**\n"
                                "- Identity proof (Aadhar, PAN, Passport)\n"
                                "- Address proof\n"
                                "- Income documents (salary slips or ITR)\n"
                                "- Bank statements (usually for the last 3-6 months)\n\n"
                                "**Eligibility:**\n"
                                "- Minimum age: 21 years\n"
                                "- Maximum age: 60-65 years (at loan maturity)\n"
                                "- Minimum income: Varies by lender and location (typically ₹15,000 to ₹25,000 per month)\n"
                                "- Credit score: Usually 700+ for competitive rates\n\n"
                                "**Processing Fees:** Usually 1% to 3% of the loan amount\n\n"
                                "Would you like more specific information about any aspect of personal loans in India?"
                    )
                else:
                    return ChatResponse(
                        response="# Personal Loans\n\n"
                                "Personal loans are unsecured loans that can be used for almost any purpose. Here are the key aspects:\n\n"
                                "**Loan Characteristics:**\n"
                                "- Unsecured (no collateral required)\n"
                                "- Fixed interest rates (typically 5% to 36% APR)\n"
                                "- Fixed monthly payments\n"
                                "- Loan terms usually 2 to 7 years\n"
                                "- Loan amounts typically from $1,000 to $50,000\n\n"
                                "**Common Uses:**\n"
                                "- Debt consolidation\n"
                                "- Home improvements\n"
                                "- Medical expenses\n"
                                "- Large purchases\n"
                                "- Emergency expenses\n\n"
                                "**Eligibility Factors:**\n"
                                "- Credit score (typically 580+ for consideration, 700+ for best rates)\n"
                                "- Debt-to-income ratio\n"
                                "- Income and employment history\n"
                                "- Credit history\n\n"
                                "Would you like more specific information about getting a personal loan, comparing lenders, or calculating payments?"
                    )
            
            # General loan query
            return ChatResponse(
                response="# Types of Loans\n\n"
                        "Loans are financial products that allow individuals and businesses to borrow money for various purposes. Here are the main types of loans available:\n\n"
                        "**Secured Loans:**\n"
                        "- Home loans/Mortgages\n"
                        "- Auto loans\n"
                        "- Gold loans\n"
                        "- Loan against property\n"
                        "- Loan against securities\n\n"
                        "**Unsecured Loans:**\n"
                        "- Personal loans\n"
                        "- Credit cards\n"
                        "- Education loans\n"
                        "- Payday loans\n\n"
                        "**Business Loans:**\n"
                        "- Term loans\n"
                        "- Working capital loans\n"
                        "- Equipment financing\n"
                        "- Business line of credit\n\n"
                        "Would you like specific information about any of these loan types, including interest rates, eligibility criteria, or the application process?"
            )
        
        # Check for specific cryptocurrency symbol
        crypto_symbol = extract_crypto_symbol(message)
        if crypto_symbol:
            # Get crypto price and details
            price_data = crypto_api.get_crypto_price(crypto_symbol)
            if price_data and "error" not in price_data:
                price = price_data.get("price", "N/A")
                change_24h = price_data.get("percent_change_24h", "N/A")
                market_cap = price_data.get("market_cap", "N/A")
                volume_24h = price_data.get("volume_24h", "N/A")
                
                # Format the response
                if isinstance(change_24h, (int, float)):
                    change_sign = "+" if change_24h > 0 else ""
                    change_formatted = f"{change_sign}{change_24h:.2f}%"
                else:
                    change_formatted = "N/A"
                    
                if isinstance(market_cap, (int, float)) and market_cap > 1000000:
                    market_cap_formatted = f"${market_cap/1000000:.2f}M"
                else:
                    market_cap_formatted = f"${market_cap}" if isinstance(market_cap, (int, float)) else "N/A"
                    
                if isinstance(volume_24h, (int, float)) and volume_24h > 1000000:
                    volume_formatted = f"${volume_24h/1000000:.2f}M"
                else:
                    volume_formatted = f"${volume_24h}" if isinstance(volume_24h, (int, float)) else "N/A"
                
                response_text = f"{crypto_symbol} current price: ${price}\n"
                response_text += f"24h change: {change_formatted}\n"
                response_text += f"Market cap: {market_cap_formatted}\n"
                response_text += f"24h volume: {volume_formatted}\n"
                
                # Check for project info
                logging.info(f"Project symbol detected: {crypto_symbol}")
                project_info = None
                
                # Try to find project info from database
                try:
                    if crypto_api.coingecko.funded_projects and crypto_symbol in crypto_api.coingecko.funded_projects:
                        project_info = crypto_api.coingecko.funded_projects[crypto_symbol]
                        logging.info(f"Project info: {project_info}")
                        
                        # Add project details to response
                        if project_info:
                            response_text += f"\n{project_info.get('name', crypto_symbol)} is a {project_info.get('category', 'crypto')} project. "
                            if project_info.get('description'):
                                response_text += f"{project_info['description']}\n\n"
                            if project_info.get('funding'):
                                response_text += f"Funding: {project_info['funding']}\n"
                            if project_info.get('mcap'):
                                response_text += f"Market Cap: {project_info['mcap']}"
                except Exception as e:
                    logging.error(f"Error fetching project info: {str(e)}")
                
                return ChatResponse(
                    response=response_text,
                    data={"symbol": crypto_symbol, "price": price, "project_info": project_info}
                )
        
        # For relationship queries, use appropriate prompt engineering
        is_relationship = "relationship" in message.lower() or "compare" in message.lower() or "vs" in message.lower() or "versus" in message.lower() or "difference between" in message.lower()
        
        # Handle trading-related queries with specialized fallback
        if "futures trading" in message.lower() or "p2p trading" in message.lower() or "margin trading" in message.lower() or "crypto trading" in message.lower():
            try:
                response = gemini_client.generate_response(message)
                # Use KG if available, otherwise return direct response
                return ChatResponse(
                    response=response,
                    knowledge_graph={"relationship_query": is_relationship}
                )
            except Exception as e:
                logging.error(f"Error generating trading response: {str(e)}")
                # Fallback response for crypto trading
                return ChatResponse(
                    response=gemini_client.get_crypto_trading_fallback()
                )
        
        # Process with Graph RAG if needed
        if is_relationship:
            prompt = f"The user query focuses on relationship or comparison: {message}. Please analyze the similarities, differences, and relationships between the entities mentioned in the query."
            try:
                response = gemini_client.generate_response(prompt)
                return ChatResponse(
                    response=response,
                    knowledge_graph={"relationship_query": True}
                )
            except Exception as e:
                logging.error(f"Error generating relationship response: {str(e)}")
                # Continue with normal processing
        
        # Check for project-specific queries
        if "tell me about" in message.lower() or "what is" in message.lower() or "information about" in message.lower():
            # Extract project name
            project_name = None
            if "tell me about" in message.lower():
                project_name = message.lower().split("tell me about")[1].strip()
            elif "what is" in message.lower():
                project_name = message.lower().split("what is")[1].strip()
            elif "information about" in message.lower():
                project_name = message.lower().split("information about")[1].strip()
                
            if project_name:
                return ChatResponse(
                    response=get_project_details(project_name)
                )
        
        # Default to general LLM response
        try:
            response = gemini_client.generate_response(message)
            return ChatResponse(
                response=response,
                knowledge_graph={"enhanced_context": True if not is_relationship else False}
            )
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return ChatResponse(
                response="I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            )
    
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Populate the vector database with project information
def populate_vector_db():
    """
    Populate the vector database with project information from the funded_projects dictionary
    """
    try:
        # Check if the database already has documents
        if vector_db.documents:
            logging.info(f"Vector database already contains {len(vector_db.documents)} documents")
            return
        
        # Get the funded projects from the CoinGecko client
        funded_projects = crypto_api.coingecko.funded_projects
        
        # Prepare texts and metadata for vector database
        texts = []
        metadatas = []
        
        for symbol, project_data in funded_projects.items():
            # Create a detailed text description for the project
            project_text = f"{project_data.get('name', symbol)} ({symbol}) is a {project_data.get('category', 'crypto')} project. "
            project_text += project_data.get('description', '')
            project_text += f"\nFunding: {project_data.get('funding', 'Unknown')}"
            project_text += f"\nMarket Cap: {project_data.get('mcap', 'Unknown')}"
            
            # Add the text and metadata
            texts.append(project_text)
            metadatas.append({
                'symbol': symbol,
                'name': project_data.get('name', symbol),
                'category': project_data.get('category', 'crypto'),
                'token': project_data.get('token', symbol)
            })
        
        # Add to vector database
        vector_db.add_documents(texts, metadatas)
        logging.info(f"Added {len(texts)} projects to the vector database")
    except Exception as e:
        logging.error(f"Error populating vector database: {str(e)}")

# Call the function to populate the database
populate_vector_db() 