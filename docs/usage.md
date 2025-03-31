# Finance FAQ Chatbot Usage Guide

## Getting Started

### Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example` and add your OpenAI API key
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m app.main`
5. Access the web interface at `http://localhost:8000/chat`

### API Endpoints

#### Chat API

- `POST /api/chat/message`: Send a message to the chatbot
  - Parameters:
    - `query` (string): The user's question
    - `user_id` (string, optional): User identifier for session tracking
  - Returns:
    - `response` (string): The chatbot's response
    - `sources` (array): Knowledge graph sources used for the response
    - `context` (object): Additional context about the response

- `GET /api/chat/history`: Get chat history for a user
  - Parameters:
    - `user_id` (string): User identifier
  - Returns:
    - `history` (array): Array of chat messages

- `POST /api/chat/clear`: Clear chat history for a user
  - Parameters:
    - `user_id` (string): User identifier
  - Returns:
    - `status` (string): Operation status
    - `message` (string): Status message

#### Knowledge Graph API

- `GET /api/knowledge/concepts`: Get financial concepts from the knowledge graph
  - Parameters:
    - `category` (string, optional): Filter by concept category
    - `limit` (integer, optional): Maximum number of concepts to return
  - Returns:
    - `concepts` (array): Array of financial concepts

- `GET /api/knowledge/entity/{entity_id}`: Get detailed information about a specific financial entity
  - Parameters:
    - `entity_id` (string): ID of the entity to retrieve
  - Returns:
    - Entity information with properties and relationships

- `POST /api/knowledge/query`: Query the financial knowledge graph
  - Parameters:
    - `query` (string): Natural language query
    - `filters` (object, optional): Filters to apply to the results
    - `limit` (integer, optional): Maximum number of results to return
  - Returns:
    - `results` (array): Query results
    - `count` (integer): Number of results
    - `query_info` (object): Information about the query

## Examples

### Asking a Simple Question

```
POST /api/chat/message
{
  "query": "What is a stock?",
  "user_id": "example_user"
}
```

Response:
```json
{
  "response": "A stock is a type of security that represents ownership in a corporation and a claim on a portion of the corporation's assets and earnings. When you purchase a stock, you're essentially buying a small piece of the company. Stocks are bought and sold primarily on stock exchanges and are the foundation of many individual investors' portfolios.",
  "sources": [
    {
      "type": "knowledge_graph",
      "content": "Financial concept: Stock (investment)",
      "relevance": 0.9
    }
  ],
  "context": {
    "used_kg": true,
    "concepts": ["Stock"],
    "model": "gpt-4"
  }
}
```

### Exploring Relationships

```
POST /api/chat/message
{
  "query": "How are bonds affected by interest rates?",
  "user_id": "example_user"
}
```

Response:
```json
{
  "response": "Bonds are inversely affected by interest rates, which is one of the fundamental relationships in finance. When interest rates rise, bond prices typically fall, and when interest rates fall, bond prices typically rise.\n\nThis happens because bonds pay a fixed amount of interest, known as the coupon rate. When market interest rates increase, newly issued bonds come with higher coupon rates, making existing bonds with lower coupon rates less attractive to investors. This lower demand causes the prices of existing bonds to drop.\n\nConversely, when market interest rates decrease, the fixed coupon payments of existing bonds become more attractive compared to newly issued bonds with lower coupon rates, increasing demand and driving up prices for existing bonds.",
  "sources": [
    {
      "type": "knowledge_graph",
      "content": "Financial concept: Bond (investment)",
      "relevance": 0.9
    },
    {
      "type": "knowledge_graph",
      "content": "Financial concept: Interest Rate (economics)",
      "relevance": 0.9
    }
  ],
  "context": {
    "used_kg": true,
    "concepts": ["Bond", "Interest Rate"],
    "model": "gpt-4"
  }
}
```

## Tips for Effective Use

1. **Be Specific**: Ask clear, focused questions about financial concepts for the best results.

2. **Explore Relationships**: The chatbot excels at explaining relationships between financial concepts (e.g., "How do interest rates affect inflation?").

3. **Request Definitions**: Get clear definitions for financial terms (e.g., "What is market capitalization?").

4. **Compare Concepts**: Ask the chatbot to compare related financial concepts (e.g., "What's the difference between stocks and bonds?").

5. **Check Sources**: Review the sources provided with responses to understand where the information comes from.

6. **Follow-up Questions**: The chatbot maintains context, so you can ask follow-up questions to dive deeper into a topic. 