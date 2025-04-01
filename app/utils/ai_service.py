"""
AI Service for external AI providers
"""
import os
import logging
import aiohttp
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """
    Service for interacting with OpenAI
    """
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.max_retries = 3
        self.base_delay = 1  # Base delay in seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI Service initialized with OpenAI")
        
    async def get_ai_response(self, prompt: str, context: str = None) -> str:
        """
        Get response from OpenAI with retry logic
        
        Args:
            prompt: The user's query
            context: Additional context to provide to the AI
            
        Returns:
            The AI's response as a string
        """
        try:
            if not self.openai_api_key:
                self.logger.warning("OpenAI API key not found. Using fallback response.")
                return "I don't have access to the AI service at the moment. Please check your API configuration."
            
            for attempt in range(self.max_retries):
                try:
                    return await self._get_openai_response(prompt, context)
                except Exception as e:
                    if "429" in str(e) and attempt < self.max_retries - 1:  # Rate limit error
                        delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                        self.logger.warning(f"Rate limit hit, retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    raise e
            
        except Exception as e:
            self.logger.error(f"Error getting AI response: {str(e)}")
            if "429" in str(e):
                return "I'm currently experiencing high traffic. Please try again in a few moments."
            return "I encountered an error while trying to get a response from the AI service."
    
    async def _get_openai_response(self, prompt: str, context: str = None) -> str:
        """
        Get response from OpenAI
        
        Args:
            prompt: The user's query
            context: Additional context to provide
            
        Returns:
            OpenAI's response as a string
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            messages = []
            
            # Add system message with context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"You are a helpful financial assistant. Use the following information to help answer the user's question: {context}"
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful financial assistant. Provide concise and accurate information about financial topics."
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        raise Exception(f"OpenAI API error: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Error with OpenAI request: {str(e)}")
            raise e 