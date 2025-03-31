# Finance FAQ Chatbot: Architecture Overview

## System Architecture

The Finance FAQ Chatbot uses a hybrid architecture that combines a knowledge graph with a large language model (LLM) to provide accurate, contextual responses to financial questions.

```
┌─────────────────┐     ┌────────────────────┐     ┌───────────────────┐
│   User Query    │────▶│ Query Processing   │────▶│  Knowledge Graph  │
└─────────────────┘     └────────────────────┘     └───────────────────┘
                                  │                           │
                                  ▼                           ▼
                         ┌────────────────────┐     ┌───────────────────┐
                         │  Context Assembly  │◀────│ Relevant Concepts │
                         └────────────────────┘     └───────────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │     LLM Response   │
                         └────────────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │   User Response    │
                         └────────────────────┘
```

## Core Components

### 1. Knowledge Graph

The knowledge graph represents financial concepts, their relationships, and hierarchies.

- **Technology**: Implemented using NetworkX with MeTTa for reasoning
- **Structure**:
  - Nodes: Financial concepts with attributes (definitions, categories)
  - Edges: Relationships between concepts (e.g., "affects", "contains", "is_type_of")
- **Key Features**:
  - Semantic query processing
  - Hierarchy and relationship traversal
  - Contextual entity linking

### 2. MeTTa Integration

MeTTa provides logical reasoning capabilities on top of the knowledge graph.

- **Reasoning Rules**:
  - Transitivity of hierarchical relationships
  - Inference of affects relationships
  - Relationship deduction between financial concepts
- **Query Patterns**:
  - Direct concept relationships
  - Multi-step inference
  - Comparative analysis

### 3. LLM Integration

The LLM (Large Language Model) generates natural language responses using knowledge graph context.

- **Technology**: OpenAI GPT-4 (configurable)
- **Integration Points**:
  - Receives structured context from the knowledge graph
  - Formats responses with citations to knowledge sources
  - Maintains conversation history for contextual awareness

### 4. API Layer

FastAPI-based backend providing REST endpoints for chat and knowledge graph operations.

- **Endpoints**:
  - Chat messaging and history management
  - Knowledge graph querying
  - Concept exploration

### 5. Web Interface

Simple web interface for interacting with the chatbot.

- **Features**:
  - Real-time chat experience
  - Display of knowledge sources
  - Financial concept exploration sidebar

## Information Flow

1. **Query Processing**:
   - User submits a finance-related question
   - System analyzes the query to identify entities, intent, and relationships

2. **Knowledge Retrieval**:
   - Knowledge graph is queried for relevant concepts
   - MeTTa reasoning enhances retrieval with logical inference
   - Relevant context is assembled (definitions, relationships, hierarchies)

3. **Response Generation**:
   - LLM receives user query, conversation history, and knowledge graph context
   - Generates a coherent, factual response grounded in the retrieved knowledge
   - Citations to sources are included

4. **Response Delivery**:
   - Formatted response is returned to the user interface
   - Sources and related concepts are displayed

## Technical Choices

### NetworkX for Graph Representation

NetworkX provides flexible graph data structures with rich querying capabilities, making it suitable for representing the financial knowledge graph.

### MeTTa for Reasoning

MeTTa enables logical reasoning over the knowledge graph, allowing the system to make inferences beyond explicit relationships.

### FastAPI for Backend

FastAPI provides high-performance API endpoints with automatic documentation, making it ideal for building the chatbot backend.

### Modular Architecture

The system uses a modular architecture to separate concerns:
- Knowledge graph logic (`app/knowledge_graph/`)
- LLM integration (`app/models/`)
- API endpoints (`app/api/`)
- UI components (`app/components/`)

This modular approach allows for easier maintenance and future extension of the system.