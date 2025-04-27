"""
Middleware components for the application.
Contains all the middleware configuration that was previously in main.py.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_utils.timing import add_timing_middleware
from config import get_settings

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI) -> None:
    """
    Sets up all middleware for the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
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

    # Add timing middleware
    add_timing_middleware(app, record=logger.info, prefix="app", exclude="untimed") 