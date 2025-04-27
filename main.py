"""
Main application entry point for the AgentX API.
Sets up the FastAPI application with all middleware, routers, and handlers.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi_utils.tasks import repeat_every

from exception_handlers import register_exception_handlers

# Import our modularized components
from middleware import setup_middleware
from models import create_db_and_tables
from router_setup import setup_routers
from static_files import setup_static_files

logger = logging.getLogger(__name__)

# Configure base logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Initialize the database on startup
    logger.info("Starting application...")
    create_db_and_tables()
    yield
    logger.info("Shutting down application...")


# Initialize the FastAPI app
app = FastAPI(
    title="Welcome to the Multi Model Agentic RAG System API!",
    description="An API for managing Agent, Pinecone and FAISS (VectorDB) integrations, Text and PDF processing, and more.",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up middleware, static files, routers, and exception handlers
setup_middleware(app)
templates = setup_static_files(app)
setup_routers(app)
register_exception_handlers(app)


# Root endpoint for HTML rendering
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Background tasks
@app.on_event("startup")
@repeat_every(seconds=60)
async def cleanup_old_sessions():
    # Implement session cleanup logic here
    pass


# Root API endpoint
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
