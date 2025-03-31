from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from typing import List, Dict, Any, Optional
import json

# Templates directory
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
os.makedirs(templates_dir, exist_ok=True)

# Create templates object
templates = Jinja2Templates(directory=templates_dir)

class ChatInterface:
    """Simple chat interface for the finance chatbot"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        
        # Set up routes
        self.setup_routes()
        
        # Create chat history storage (in-memory for demo)
        self.chat_history = {}
    
    def setup_routes(self):
        """Set up the routes for the chat interface"""
        
        # HTML routes
        @self.app.get("/", response_class=HTMLResponse)
        async def home_page(request: Request):
            return templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/chat", response_class=HTMLResponse)
        async def chat_page(request: Request):
            return templates.TemplateResponse("chat.html", {"request": request})
        
        # API routes (simplified - relying on the main API routes)
        @self.app.get("/api/chat/history")
        async def get_chat_history(request: Request, user_id: str = "anonymous"):
            """Get the chat history for a user"""
            return {"history": self.chat_history.get(user_id, [])}
        
        @self.app.post("/api/chat/clear")
        async def clear_chat_history(request: Request, user_id: str = Form(default="anonymous")):
            """Clear the chat history for a user"""
            self.chat_history[user_id] = []
            return {"status": "success", "message": "Chat history cleared"} 