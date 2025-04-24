import os

import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from html_router.html_router import html_app
from models import create_db_and_tables
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Initialize the database on startup
    create_db_and_tables()
    if not os.path.exists("media"):
        os.makedirs("media")
    yield
    # Cleanup on shutdown

# Initialize the FastAPI app
app = FastAPI(
    title="Welcome to the Multi Model Agentic RAG System API!",
    description="An API for managing Agent, Pinecone and FAISS (VectorDB) integrations, Text and PDF processing, and more.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(html_app, prefix="", tags=["HTML API"])
app.include_router(router.index_router, prefix="/index", tags=["Index API"])
app.include_router(router.agent_router, prefix="/agent", tags=["Agent API"])
app.include_router(router.user_router, prefix="/user", tags=["User API"])
app.include_router(router.chat_router, prefix="/chat", tags=["Chat History"])
# Add the same router with /api prefix to handle RESTful endpoints
app.include_router(router.agent_router, prefix="/api", tags=["REST API"])


# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint providing basic information about the API.
    """
    return {
        "message": "Welcome to the Multi Model Agentic RAG System API!",
        "documentation_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0",
    }
