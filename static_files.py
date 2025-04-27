"""
Static files setup for the FastAPI application.
Contains logic for mounting static files and templates.
"""
import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

def setup_static_files(app: FastAPI) -> tuple:
    """
    Set up static files and templates for the application.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        tuple: A tuple containing (templates)
    """
    # Create directories if they don't exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("media", exist_ok=True)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Initialize templates
    templates = Jinja2Templates(directory="templates")
    
    logger.info("Static files and templates initialized")
    
    return templates 