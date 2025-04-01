## Overview

A *Financial Assistant with MeTTa Reasoning* leverages Meta-Type-Theoretic Architecture (MeTTa) to process financial data, analyze trends, and provide intelligent investment recommendations. By utilizing symbolic reasoning and pattern recognition, it enhances decision-making in portfolio management, risk assessment, and personalized financial planning.

## Features
- **Real-time Financial Data**: Access up-to-date information on stocks, cryptocurrencies, and market indices
- **Intelligent Query Processing**: Natural language understanding for complex financial questions
- **Personalized Investment Insights**: Tailored recommendations based on user preferences
- **Market Sentiment Analysis**: Gauge market sentiment through news and social media analysis
- **Historical Data Visualization**: View historical performance of financial instruments
- **Multi-source Data Integration**: Combines data from various financial APIs for comprehensive insights

## Technology Stack
- **Backend**: FastAPI (Python)
- **AI/ML**: OpenAI API, scikit-learn, sentence-transformers
- **Data Processing**: Pandas, NumPy
- **API Integration**: 
  - CoinMarketCap (cryptocurrency data)
  - Alpha Vantage (stock market data)
  - Finnhub (financial market data)
  - StockGeist (market sentiment)
- **Caching**: Custom caching system with configurable TTL
- **Testing**: Pytest, pytest-asyncio, pytest-cov
- **Documentation**: MkDocs with Material theme
- **Development Tools**: Black, Flake8, MyPy

## For Testing -
 checkout SETUP.txt to run it

## Environment Configuration
The application requires several API keys and configuration parameters set in the `.env` file:
- OpenAI API key for natural language processing
- Financial data API keys (CoinMarketCap, Alpha Vantage, Finnhub)
- Application settings (port, environment, logging level)
- Cache configuration parameters

## API Endpoints
- `/api/chat`: Main endpoint for processing user queries
- `/api/stocks`: Direct access to stock market data
- `/api/crypto`: Cryptocurrency information endpoint
- `/api/market`: General market insights and indices

## Development
- Follow the setup instructions in SETUP.txt
- Run tests with `pytest`
- Format code with `black .`
- Check for linting issues with `flake8`

## Limitations
- API rate limits may affect real-time data availability
- Financial advice is for informational purposes only
- Historical data may be limited for some financial instruments




