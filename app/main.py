import os
import uvicorn
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import routers
from app.api.chat import router as chat_router
from app.api.knowledge_graph import router as kg_router

# Import chat interface
from app.components.chat import ChatInterface

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join("logs", "app.log"), encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Finance FAQ Chatbot",
    description="A domain-specific chatbot for finance that combines LLMs with a knowledge graph",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(kg_router, prefix="/api/knowledge_graph", tags=["Knowledge Graph"])

# Initialize chat interface
chat_interface = ChatInterface(app)

# Create directories if they don't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Homepage route
@app.get("/")
async def root(request: Request):
    return {"message": "Finance FAQ Chatbot API is running"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}