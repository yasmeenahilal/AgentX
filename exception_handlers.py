"""
Exception handlers for the FastAPI application.
Contains all exception handler logic that was previously in main.py.
"""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """
    Register all exception handlers for the application.

    Args:
        app: The FastAPI application instance
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions gracefully"""
        logger.info(f"HTTP Exception: {exc.status_code} at path {request.url.path}")

        # For API endpoints, return JSON response
        if request.url.path.startswith(
            ("/agent/", "/index/", "/user/", "/chat/", "/api/", "/deployment/")
        ):
            return JSONResponse(
                status_code=exc.status_code, content={"detail": str(exc.detail)}
            )

        # For authentication errors on HTML pages, redirect to login page
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(
                url="/?error=login_required", status_code=status.HTTP_302_FOUND
            )

        # For 404 errors, provide a custom not found page or JSON response
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            if (
                "accept" in request.headers
                and "application/json" in request.headers["accept"]
            ):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "The requested resource was not found."},
                )
            # For HTML requests, you could return a custom 404 page
            # return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

        # For other errors, use default handling
        raise exc
