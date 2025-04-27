"""
Router setup for the FastAPI application.
Contains logic for including all application routers.
"""
import logging
from fastapi import FastAPI
import router
from html_router.html_router import html_app
from router.deployment_api import deployment_router, api_v1_router, shortener_router

logger = logging.getLogger(__name__)

def setup_routers(app: FastAPI) -> None:
    """
    Register all routers for the application.
    
    Args:
        app: The FastAPI application instance
    """
    # Include main routers
    app.include_router(html_app, prefix="", tags=["HTML"])
    app.include_router(router.index_router, prefix="/index", tags=["Index"])
    app.include_router(router.agent_router, prefix="/agent", tags=["Agent"])
    app.include_router(router.user_router, prefix="/user", tags=["User"])
    app.include_router(router.chat_router, prefix="/chat", tags=["Chat"])
    
    # Include deployment-related routers
    app.include_router(deployment_router, prefix="/deployment", tags=["Deployment"])
    app.include_router(api_v1_router, prefix="/api/v1", tags=["API"])
    app.include_router(shortener_router, prefix="/s", tags=["Shortener"])
    
    logger.info("All routers have been set up successfully") 