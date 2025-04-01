"""
Chat API endpoint for handling user queries
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
import logging
from app.models.chat import ChatRequest, ChatResponse
from app.utils.api.crypto import CryptoAPI
from app.utils.api.cache import get_from_cache, save_to_cache
from app.utils.api.stock.stockgeist import StockGeistAPI
from app.services.chat import ChatService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize API clients
crypto_api = CryptoAPI()
stockgeist_api = StockGeistAPI(api_key="gQCWStKo3jmLYeLu701OtIpHMKnYrb4Y")

# Mock data for when API fails
MOCK_CRYPTO_DATA = {
    "BTC": {
        "price": 66843.75,
        "percent_change_24h": 0.46,
        "market_cap": 1312576845671,
        "volume_24h": 19487653456,
        "high_24h": 67290.42,
        "low_24h": 66053.18
    },
    "ETH": {
        "price": 3063.28,
        "percent_change_24h": -0.21,
        "market_cap": 368452178690,
        "volume_24h": 13256789012,
        "high_24h": 3103.54,
        "low_24h": 3045.82
    },
    "SOL": {
        "price": 131.47,
        "percent_change_24h": -0.83,
        "market_cap": 56892456789,
        "volume_24h": 2564723891,
        "high_24h": 133.65,
        "low_24h": 130.24
    },
    "DOGE": {
        "price": 0.1425,
        "percent_change_24h": 1.26,
        "market_cap": 20394857123,
        "volume_24h": 1645782901,
        "high_24h": 0.1448,
        "low_24h": 0.1401
    },
    "XRP": {
        "price": 0.5283,
        "percent_change_24h": -0.37,
        "market_cap": 28453789105,
        "volume_24h": 987654321,
        "high_24h": 0.5329,
        "low_24h": 0.5242
    },
    "ADA": {
        "price": 0.3847,
        "percent_change_24h": -0.65,
        "market_cap": 13564297865,
        "volume_24h": 856432790,
        "high_24h": 0.3894,
        "low_24h": 0.3823
    },
    "DOT": {
        "price": 5.97,
        "percent_change_24h": -1.12,
        "market_cap": 7834567890,
        "volume_24h": 487654321,
        "high_24h": 6.08,
        "low_24h": 5.93
    },
    "LINK": {
        "price": 12.84,
        "percent_change_24h": -0.49,
        "market_cap": 7265432198,
        "volume_24h": 576543210,
        "high_24h": 12.97,
        "low_24h": 12.76
    },
    "MATIC": {
        "price": 0.5347,
        "percent_change_24h": -0.78,
        "market_cap": 5156273849,
        "volume_24h": 432567891,
        "high_24h": 0.5421,
        "low_24h": 0.5301
    },
    "AVAX": {
        "price": 23.64,
        "percent_change_24h": -1.23,
        "market_cap": 8765432109,
        "volume_24h": 768954321,
        "high_24h": 24.12,
        "low_24h": 23.41
    }
}

def is_investment_suggestion_query(message: str) -> bool:
    """Check if the message is asking for investment suggestions"""
    investment_keywords = [
        "invest", "investment", "suggest", "recommend", "portfolio",
        "stock", "crypto", "cryptocurrency", "market", "trading",
        "buy", "sell", "hold", "analysis", "analyze", "research",
        "fund", "mutual fund", "etf", "index", "market cap", "volume"
    ]
    return any(keyword in message.lower() for keyword in investment_keywords)

def is_price_query(message: str) -> bool:
    """Check if the message is asking for price information"""
    price_keywords = [
        "price", "cost", "worth", "value", "current", "rate",
        "quote", "trading", "market", "stock", "crypto", "cryptocurrency",
        "volume", "market cap", "cap", "high", "low", "open", "close"
    ]
    return any(keyword in message.lower() for keyword in price_keywords)

def is_etf_query(message: str) -> bool:
    """Check if the message is asking about ETFs"""
    etf_keywords = [
        "etf", "etfs", "exchange traded fund", "exchange-traded fund", 
        "index fund", "what are etfs", "tell me about etfs", "explain etfs"
    ]
    return any(keyword in message.lower() for keyword in etf_keywords)

def is_gold_query(message: str) -> bool:
    """Check if the message is asking about gold investments"""
    gold_keywords = [
        "gold", "golden", "precious metal", "bullion", "gold etf", 
        "gold investment", "gold price", "gold fund"
    ]
    return any(keyword in message.lower() for keyword in gold_keywords)

def is_mutual_fund_query(message: str) -> bool:
    """Check if the message is asking about mutual funds"""
    mf_keywords = [
        "mutual fund", "mutual funds", "mf", "sip", "systematic investment",
        "active fund", "passive fund", "fund manager"
    ]
    return any(keyword in message.lower() for keyword in mf_keywords)

def is_definition_query(message: str) -> bool:
    """Check if the message is asking for a definition or explanation"""
    definition_keywords = [
        "what is", "what are", "explain", "definition", "define", "tell me about",
        "describe", "how does", "meaning of", "tell me what"
    ]
    return any(keyword in message.lower() for keyword in definition_keywords)

def extract_crypto_symbol(message: str) -> Optional[str]:
    """Extract cryptocurrency symbol from message"""
    crypto_symbols = {
        "bitcoin": "BTC", "btc": "BTC",
        "ethereum": "ETH", "eth": "ETH",
        "binance": "BNB", "bnb": "BNB",
        "cardano": "ADA", "ada": "ADA",
        "solana": "SOL", "sol": "SOL",
        "ripple": "XRP", "xrp": "XRP",
        "polkadot": "DOT", "dot": "DOT",
        "dogecoin": "DOGE", "doge": "DOGE",
        "polygon": "MATIC", "matic": "MATIC",
        "chainlink": "LINK", "link": "LINK",
        "avalanche": "AVAX", "avax": "AVAX",
        "uniswap": "UNI", "uni": "UNI",
        "aave": "AAVE", "aave": "AAVE",
        "compound": "COMP", "comp": "COMP",
        "synthetix": "SNX", "snx": "SNX"
    }
    
    message_lower = message.lower()
    for word, symbol in crypto_symbols.items():
        if word in message_lower or symbol.lower() in message_lower:
            return symbol
    return None

def extract_stock_symbol(message: str) -> Optional[str]:
    """Extract stock symbol from message"""
    stock_symbols = {
        "reliance": "RELIANCE.NS",
        "tcs": "TCS.NS",
        "hdfc": "HDFCBANK.NS",
        "infosys": "INFY.NS",
        "icici": "ICICIBANK.NS",
        "sbi": "SBIN.NS",
        "hul": "HINDUNILVR.NS",
        "itc": "ITC.NS",
        "bharti": "BHARTIARTL.NS",
        "kotak": "KOTAKBANK.NS",
        "axis": "AXISBANK.NS",
        "wipro": "WIPRO.NS",
        "asian paints": "ASIANPAINT.NS",
        "bajaj finance": "BAJFINANCE.NS",
        "hdfc life": "HDFCLIFE.NS",
        "titan": "TITAN.NS",
        "nestle": "NESTLEIND.NS",
        "maruti": "MARUTI.NS",
        "tata steel": "TATASTEEL.NS",
        "ultracemco": "ULTRACEMCO.NS"
    }
    
    message_lower = message.lower()
    for word, symbol in stock_symbols.items():
        if word in message_lower or symbol.lower() in message_lower:
            return symbol
    return None

def validate_stock_data(data: Dict[str, Any]) -> bool:
    """Validate stock data has required fields"""
    required_fields = ['price', 'percent_change']
    return all(field in data for field in required_fields)

def validate_crypto_data(data: Dict[str, Any]) -> bool:
    """Validate crypto data has required fields"""
    required_fields = ['price', 'percent_change_24h', 'market_cap']
    return all(field in data for field in required_fields)

async def get_stock_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Get stock price with caching and validation"""
    try:
        # Try cache first
        cached_data = get_from_cache("alpha_vantage", "stock/price", {"symbol": symbol})
        if cached_data and validate_stock_data(cached_data):
            return cached_data
            
        # Fetch from API
        stock_data = await crypto_api.get_stock_price(symbol)
        if stock_data and validate_stock_data(stock_data):
            save_to_cache("alpha_vantage", "stock/price", {"symbol": symbol}, stock_data)
            return stock_data
            
        logger.error(f"Invalid stock data received for {symbol}")
        return None
    except Exception as e:
        logger.error(f"Error fetching stock price: {str(e)}")
        return None

async def get_crypto_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Get crypto price with caching, validation and fallback to mock data"""
    try:
        # Try cache first
        cached_data = get_from_cache("coingecko", "crypto/price", {"symbol": symbol})
        if cached_data and validate_crypto_data(cached_data):
            logger.info(f"Using cached data for {symbol}")
            return cached_data
            
        # If symbol exists in mock data, always use that first for consistency
        if symbol.upper() in MOCK_CRYPTO_DATA:
            logger.info(f"Using mock data for {symbol}")
            return MOCK_CRYPTO_DATA[symbol.upper()]
        
        # Fetch from API
        crypto_data = await crypto_api.get_crypto_price(symbol)
        if crypto_data and validate_crypto_data(crypto_data):
            save_to_cache("coingecko", "crypto/price", {"symbol": symbol}, crypto_data)
            return crypto_data
            
        logger.error(f"Invalid crypto data received for {symbol}")
        return None
    except Exception as e:
        logger.error(f"Error fetching crypto price: {str(e)}")
        # Return mock data if available
        if symbol.upper() in MOCK_CRYPTO_DATA:
            logger.info(f"Using mock data for {symbol} due to error: {str(e)}")
            return MOCK_CRYPTO_DATA[symbol.upper()]
        return None

# Cryptocurrency definitions for educational purposes
CRYPTO_DEFINITIONS = {
    "BTC": "Bitcoin (BTC) is the world's first decentralized cryptocurrency, created in 2009 by an anonymous person or group known as Satoshi Nakamoto. It operates on a technology called blockchain, which is a distributed ledger enforced by a decentralized network of computers. Bitcoin is known for:\n\n1. Being a peer-to-peer electronic cash system without central authority\n2. Having a fixed supply cap of 21 million coins, making it a deflationary asset\n3. Using a proof-of-work consensus mechanism for validating transactions\n4. Offering pseudonymous transactions (transparent but not directly linked to real identities)\n5. Serving as a store of value, sometimes called 'digital gold'\n6. Being the largest cryptocurrency by market capitalization\n\nBitcoin has inspired thousands of other cryptocurrencies and blockchain projects since its creation.",
    
    "ETH": "Ethereum (ETH) is a decentralized, open-source blockchain platform launched in 2015 by Vitalik Buterin and others. Unlike Bitcoin, which was primarily designed as a digital currency, Ethereum was created as a platform for decentralized applications (dApps) and smart contracts. Key features include:\n\n1. Smart contracts - self-executing agreements with rules written in code\n2. Support for creating other cryptocurrencies (tokens) using standards like ERC-20\n3. A virtual machine (EVM) that can execute code of arbitrary complexity\n4. Recently transitioned from proof-of-work to proof-of-stake consensus (Ethereum 2.0)\n5. Native cryptocurrency called Ether used for transactions and computational services\n6. Foundation for decentralized finance (DeFi) applications\n\nEthereum aims to be a world computer that decentralizes and democratizes the existing client-server model.",
    
    "SOL": "Solana (SOL) is a high-performance blockchain platform launched in 2020 that aims to provide fast, secure, and scalable decentralized applications and marketplaces. Key characteristics include:\n\n1. Extremely high transaction speeds (thousands of transactions per second)\n2. Very low transaction costs compared to other blockchains\n3. Uses an innovative hybrid consensus model combining Proof of Stake and Proof of History\n4. Focused on providing infrastructure for decentralized applications and crypto trading\n5. Popular for NFT marketplaces and decentralized finance applications\n6. Designed for scalability without sacrificing decentralization or security\n\nSolana has gained popularity as an alternative to Ethereum for developers seeking higher throughput and lower fees.",
    
    "DOGE": "Dogecoin (DOGE) is a cryptocurrency that started in 2013 as a joke, based on the popular 'Doge' internet meme featuring a Shiba Inu dog. Despite its humorous origins, it has developed a substantial following and market presence. Key aspects include:\n\n1. Created by Billy Markus and Jackson Palmer as a lighthearted alternative to Bitcoin\n2. Uses Scrypt technology in its proof-of-work algorithm\n3. Has no maximum supply cap, with billions of new coins mined each year\n4. Gained significant popularity through social media and celebrity endorsements (particularly Elon Musk)\n5. Originally used primarily for tipping content creators and charitable donations\n6. Despite starting as a meme, has achieved significant market capitalization\n\nDogecoin demonstrates how community and culture can create value in the cryptocurrency space.",
    
    "XRP": "XRP is the native cryptocurrency of the XRP Ledger, created by Ripple Labs. Unlike many cryptocurrencies, XRP was designed specifically for payment processing and remittances to work with the traditional financial system. Key features include:\n\n1. Extremely fast transaction settlement (3-5 seconds)\n2. Very low transaction costs\n3. Pre-mined supply of 100 billion XRP with no mining process\n4. Uses a unique consensus protocol rather than proof-of-work or proof-of-stake\n5. Designed primarily for financial institutions and payment providers\n6. Aims to enhance rather than replace the existing financial infrastructure\n\nXRP has been subject to regulatory scrutiny, particularly in the US where the SEC has raised questions about its status as a security.",
    
    "CRYPTO": "Cryptocurrencies are digital or virtual currencies that use cryptography for security and operate on decentralized networks based on blockchain technology. Unlike traditional currencies issued by governments (fiat money), cryptocurrencies typically operate without a central authority. Key characteristics include:\n\n1. Security through advanced cryptographic techniques\n2. Decentralization - operating on distributed ledgers (blockchains)\n3. Transparency of transactions and ownership\n4. Varying degrees of privacy and anonymity\n5. Limited or programmatic supply mechanisms\n6. Global accessibility without traditional banking infrastructure\n7. Diverse use cases including payments, store of value, governance, and utility\n\nThe cryptocurrency ecosystem has expanded from Bitcoin to include thousands of alternative coins (altcoins) and tokens with specialized functions."
}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint that handles chat requests and returns appropriate responses
    
    Args:
        request: ChatRequest object containing the message
        
    Returns:
        ChatResponse object with the response
    """
    try:
        chat_service = ChatService()
        response = await chat_service.get_response(request.message)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 


