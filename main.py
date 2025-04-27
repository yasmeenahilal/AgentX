import os

import router
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from html_router.html_router import html_app
from models import create_db_and_tables
from contextlib import asynccontextmanager
from config import get_settings

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

# Add Session Middleware FIRST (order can matter)
app.add_middleware(
    SessionMiddleware, 
    secret_key=get_settings().SECRET_KEY
)

# Add CORS Middleware AFTER SessionMiddleware
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
app.include_router(router.agent_router, prefix="/api", tags=["REST API"])

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions gracefully"""
    # For API endpoints, return JSON response
    if request.url.path.startswith(("/agent/", "/index/", "/user/", "/chat/", "/api/")):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail)}
        )
    
    # For authentication errors on HTML pages, redirect to login page
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/?error=login_required", status_code=status.HTTP_302_FOUND)
    
    # For other errors, use default handling
    raise exc

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
