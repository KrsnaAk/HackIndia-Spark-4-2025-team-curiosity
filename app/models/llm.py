import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    openai.api_key = api_key
else:
    print("Warning: OPENAI_API_KEY not found in environment variables. LLM functionality will be limited.")

def format_chat_history(chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Format chat history for OpenAI API"""
    formatted_history = []
    for msg in chat_history:
        if "role" in msg and "content" in msg:
            formatted_history.append({"role": msg["role"], "content": msg["content"]})
        elif "user" in msg:
            formatted_history.append({"role": "user", "content": msg["user"]})
        elif "assistant" in msg:
            formatted_history.append({"role": "assistant", "content": msg["assistant"]})
    return formatted_history

def format_kg_context(kg_context: Dict[str, Any]) -> str:
    """Format knowledge graph context for LLM consumption"""
    context_parts = []
    
    # Add definitions
    if kg_context.get("definitions"):
        context_parts.append("## Financial Definitions")
        for definition in kg_context["definitions"]:
            context_parts.append(f"- {definition['concept']}: {definition['definition']}")
    
    # Add relationships
    if kg_context.get("relationships"):
        context_parts.append("## Relationships Between Financial Concepts")
        for rel in kg_context["relationships"]:
            if "target_name" in rel:
                context_parts.append(f"- {rel['source_name']} {rel['type']} {rel['target_name']}")
            elif "source_name" in rel and rel["source_name"] != rel.get("source_name"):
                context_parts.append(f"- {rel['source_name']} {rel['type']} {rel['source_name']}")
    
    # Add query info if present
    if kg_context.get("query_info") and kg_context["query_info"].get("intent"):
        intent = kg_context["query_info"]["intent"]
        context_parts.append(f"## Query Intent\nThe user is asking for {intent} about financial concepts.")
    
    return "\n\n".join(context_parts)

def get_llm_response(query: str, chat_history: List[Dict[str, str]] = None, kg_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get a response from the LLM using the query, chat history, and knowledge graph context
    
    Args:
        query: User query
        chat_history: Optional chat history
        kg_context: Optional knowledge graph context
        
    Returns:
        Dict containing the LLM response
    """
    try:
        # Initialize messages with system prompt
        messages = [{
            "role": "system",
            "content": "You are a knowledgeable financial advisor chatbot. You provide accurate, contextual "
                      "information about financial concepts and answer user questions with precision. "
                      "When providing information, cite your sources when applicable."
        }]
        
        # Add chat history if available
        if chat_history:
            formatted_history = format_chat_history(chat_history)
            messages.extend(formatted_history)
        
        # Add knowledge graph context if available
        if kg_context:
            kg_formatted = format_kg_context(kg_context)
            if kg_formatted:
                messages.append({
                    "role": "system",
                    "content": f"Here is relevant financial knowledge to help answer the question:\n\n{kg_formatted}"
                })
        
        # Add user query
        messages.append({"role": "user", "content": query})
        
        # If OpenAI API key is available, use OpenAI
        if api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or "gpt-3.5-turbo" for a more cost-effective option
                messages=messages,
                temperature=0.4,
                max_tokens=800
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": response.model,
                "context": {
                    "used_kg": bool(kg_context),
                    "tokens": {
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            }
        else:
            # Fallback to a simple response if no API key
            return {
                "text": "I don't have access to my knowledge base right now. Please try again later or ask a different question.",
                "model": "fallback",
                "context": {
                    "used_kg": bool(kg_context),
                    "error": "No OpenAI API key provided"
                }
            }
    
    except Exception as e:
        print(f"Error getting LLM response: {str(e)}")
        return {
            "text": f"I'm having trouble processing your request right now. Please try again later.",
            "error": str(e),
            "context": {
                "used_kg": bool(kg_context)
            }
        } 