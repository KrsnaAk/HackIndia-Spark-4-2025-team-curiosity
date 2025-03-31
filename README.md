# Finance and Cryptocurrency Chatbot with Graph RAG and Knowledge Graph Integration

A domain-specific chatbot for the finance and cryptocurrency industries that leverages a knowledge graph and Graph RAG for providing accurate, contextual, and enriched responses to financial and crypto-related queries.

![Finance Chatbot Demo](https://placehold.co/800x400/e9f2ff/0a2647?text=Finance+Chatbot+Demo)

## Key Features
- **Knowledge Graph Integration**: Enhanced context and relationship-aware responses
- **Graph RAG (Retrieval Augmented Generation)**: Combines vector search with graph-based knowledge
- **Real-Time Crypto Data**: Fetches the latest cryptocurrency information from multiple sources
- **Relationship Queries**: Specialized handling of queries about relationships between entities
- **Fallback Mechanisms**: Ensures reliable responses even when APIs are unavailable
- **Comprehensive Coverage**: Financial topics including investments, crypto trading, blockchain technologies

## Knowledge Domains
- **Cryptocurrency**: Digital assets, blockchain projects, trading methods, market data
- **Investment**: Stocks, bonds, mutual funds, ETFs, real estate
- **Personal Finance**: Budgeting, savings, credit, debt, retirement
- **Banking**: Accounts, loans, interest rates, fees, services
- **Market Analysis**: Indicators, trends, analysis, sectors, indices
- **Risk Management**: Types, assessment, management, mitigation, insurance

## Project Structure

- `app/`: Main application directory
  - `api/`: API endpoints
  - `knowledge_graph/`: Knowledge graph implementation
  - `utils/`: Utility functions and integrations
  - `main.py`: Application entry point
- `logs/`: Application logs
- `static/`: Static files
- `templates/`: HTML templates

## Tech Stack
### Backend
- **Python**: Core programming language
- **FastAPI**: Modern web framework for building APIs
- **Google Generative AI (Gemini)**: Large Language Model integration for response generation
- **MeTTa**: Symbolic AI framework for knowledge representation and reasoning
- **Graph RAG**: Custom implementation for enhanced context retrieval
- **Knowledge Graph**: Custom implementation for structured data relationships
- **Sentence Transformers**: For vector embeddings and semantic search
- **CoinGecko/Binance/CoinMarketCap APIs**: Cryptocurrency data sources
- **Logging System**: Comprehensive logging for monitoring and debugging

### Infrastructure
- **Uvicorn**: ASGI server for running the FastAPI application
- **Python-dotenv**: Environment variable management

## Dependencies
```
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
pydantic==2.4.2
python-multipart==0.0.6
python-dotenv==1.0.0
requests==2.31.0
google-generativeai  # For Gemini AI integration
sentence-transformers  # For vector embeddings
```

## Deployment Options

### Local Development

1. Clone the repository
2. Create a `.env` file with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m app.main`
5. Access the API at `http://localhost:8000`

### API Endpoints

The primary API endpoint is:
- `/api/chat/`: POST endpoint for sending messages to the chatbot

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
