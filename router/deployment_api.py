"""API router for deployment endpoints."""

import base64
import hashlib
import json
import logging
import re
import secrets
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_agent_settings
from models import Agent, User
from models.base import get_session
from models.deployment import Deployment, DeploymentMethodEnum
from rag_app import query_agent_logic
from user.auth import get_current_active_user, get_current_user
from utils.security import decrypt_string, encrypt_string, generate_short_token

# Setup logger
logger = logging.getLogger(__name__)

# Define separate routers for different functionality
deployment_router = APIRouter(tags=["Deployment"])  # Main deployment features
api_v1_router = APIRouter(tags=["API"])  # API v1 features
shortener_router = APIRouter(tags=["Shortener"])  # URL shortening

# -------------- CORS CONFIGURATION --------------
# Note: This won't work here at router level - needs to be configured at the FastAPI app level
# We'll leave this as a reference to be moved to main.py


# URL shortening functions
def generate_short_id(original_url: str, length: int = 7) -> str:
    """Generate a short ID based on the original URL"""
    # Create a hash of the original URL
    hash_object = hashlib.md5(original_url.encode())
    # Get the first 'length' characters of the base64 representation
    short_id = base64.urlsafe_b64encode(hash_object.digest()).decode()[:length]
    # Make it URL friendly
    short_id = re.sub(r"[^a-zA-Z0-9]", "", short_id)
    return short_id


# Store URL mappings (in a real app, this would be in a database)
url_mappings = {}


# Models
class DeploymentRequest(BaseModel):
    agent_name: str
    deployment_method: DeploymentMethodEnum
    deployment_name: Optional[str] = None
    deployment_description: Optional[str] = None
    embed_settings: Optional[Dict[str, Any]] = None
    allowed_domains: Optional[str] = None


class DeploymentUpdateRequest(BaseModel):
    deployment_name: Optional[str] = None
    deployment_description: Optional[str] = None
    embed_settings: Optional[Dict[str, Any]] = None


class AgentQueryRequest(BaseModel):
    question: str
    agent_name: Optional[str] = None
    session_id: Optional[str] = None


class APIKeyResponse(BaseModel):
    api_key: str
    api_secret: str
    created_at: datetime


class DeploymentResponse(BaseModel):
    deployment_id: str
    agent_name: str
    deployment_method: DeploymentMethodEnum
    deployment_name: Optional[str]
    deployment_description: Optional[str]
    created_at: datetime
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    embed_code: Optional[str] = None
    short_url: Optional[str] = None
    embed_settings: Optional[Dict[str, Any]] = None


# -------------- DEPLOYMENT ROUTER ENDPOINTS --------------


@deployment_router.post("/deploy", response_model=DeploymentResponse)
async def deploy_agent(
    request: DeploymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Deploy an agent with the specified deployment method.
    """
    # Check if the agent exists and belongs to the user
    agent = (
        db.query(Agent)
        .filter(
            Agent.agent_name == request.agent_name, Agent.user_id == current_user.id
        )
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with name '{request.agent_name}' not found or you don't have access to it",
        )

    # Generate a deployment ID
    deployment_id = str(uuid.uuid4())
    deployment_name = request.deployment_name or f"{request.agent_name}-deployment"

    # Create response object
    response = DeploymentResponse(
        deployment_id=deployment_id,
        agent_name=request.agent_name,
        deployment_method=request.deployment_method,
        deployment_name=deployment_name,
        deployment_description=request.deployment_description,
        created_at=datetime.utcnow(),
    )

    # Process deployment method
    api_key = None
    api_secret = None
    api_secret_encrypted = None
    api_endpoint = None
    embed_code = None
    embed_settings = None
    short_url = None
    short_token = None
    allowed_domains = request.allowed_domains or "*"

    if request.deployment_method in [
        DeploymentMethodEnum.api,
        DeploymentMethodEnum.both,
    ]:
        # Generate API key and secret
        api_key = f"agentx_{secrets.token_urlsafe(16)}"
        api_secret = secrets.token_urlsafe(32)

        # Encrypt the API secret
        api_secret_encrypted = encrypt_string(api_secret)

        # Set API details in response
        response.api_key = api_key
        api_endpoint = f"/api/v1/deployment/{deployment_id}/query"
        response.api_endpoint = api_endpoint

    if request.deployment_method in [
        DeploymentMethodEnum.embed,
        DeploymentMethodEnum.both,
    ]:
        # Generate embed code based on settings
        embed_settings = request.embed_settings or {}

        # Create token data
        token_data = {
            "deployment_id": deployment_id,
            "agent_name": request.agent_name,
            "api_key": api_key,  # Include API key in token for secure authentication
            "theme": embed_settings.get("theme", "light"),
            "position": embed_settings.get("position", "bottom-right"),
        }

        # Generate a secure token
        short_token = generate_short_token(token_data)

        # Generate short URL with the token
        short_url = f"/s/{short_token}"

        # Update response with short URL
        response.short_url = f"http://127.0.0.1:8000{short_url}"

        # Create two versions of embed code: full and shorthand
        full_embed_code = f"""
        <script 
            src="http://127.0.0.1:8000/static/embed.js" 
            data-agent="{request.agent_name}" 
            data-deployment-id="{deployment_id}"
            data-theme="{embed_settings.get('theme', 'light')}"
            data-position="{embed_settings.get('position', 'bottom-right')}">
        </script>
        """

        short_embed_code = f"""
        <script src="http://127.0.0.1:8000{short_url}"></script>
        """

        # Use the short embed code for simplicity
        embed_code = short_embed_code.strip()
        response.embed_code = embed_code
        response.embed_settings = embed_settings

    # Save deployment information to the database
    new_deployment = Deployment(
        deployment_id=deployment_id,
        deployment_name=deployment_name,
        deployment_description=request.deployment_description,
        deployment_method=request.deployment_method,
        api_key=api_key,
        api_secret_encrypted=api_secret_encrypted,
        api_endpoint=api_endpoint,
        embed_code=embed_code,
        embed_settings=embed_settings,
        short_token=short_token,
        allowed_domains=allowed_domains,
        agent_id=agent.id,
        user_id=current_user.id,
    )

    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)

    return response


@deployment_router.get("/list", response_model=List[DeploymentResponse])
async def list_deployments(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_session)
):
    """
    List all deployments for the authenticated user.
    """
    deployments = (
        db.query(Deployment).filter(Deployment.user_id == current_user.id).all()
    )

    result = []
    for deployment in deployments:
        agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
        if not agent:
            continue

        result.append(
            DeploymentResponse(
                deployment_id=deployment.deployment_id,
                agent_name=agent.agent_name,
                deployment_method=deployment.deployment_method,
                deployment_name=deployment.deployment_name,
                deployment_description=deployment.deployment_description,
                created_at=deployment.created_at,
                api_key=deployment.api_key,
                api_endpoint=deployment.api_endpoint,
                embed_code=deployment.embed_code,
                embed_settings=deployment.embed_settings,
            )
        )

    return result


@deployment_router.post("/generate-key", response_model=APIKeyResponse)
async def generate_api_key(
    agent_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Generate a new API key for an agent.
    """
    # Check if the agent exists and belongs to the user
    agent = (
        db.query(Agent)
        .filter(Agent.agent_name == agent_name, Agent.user_id == current_user.id)
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with name '{agent_name}' not found or you don't have access to it",
        )

    # Generate API key and secret
    api_key = f"agentx_{secrets.token_urlsafe(16)}"
    api_secret = secrets.token_urlsafe(32)

    # Return the API key response (but don't save to database)
    return APIKeyResponse(
        api_key=api_key, api_secret=api_secret, created_at=datetime.utcnow()
    )


@deployment_router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Get deployment details by ID.
    """
    deployment = (
        db.query(Deployment)
        .filter(
            Deployment.deployment_id == deployment_id,
            Deployment.user_id == current_user.id,
        )
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it",
        )

    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent associated with this deployment not found",
        )

    return DeploymentResponse(
        deployment_id=deployment.deployment_id,
        agent_name=agent.agent_name,
        deployment_method=deployment.deployment_method,
        deployment_name=deployment.deployment_name,
        deployment_description=deployment.deployment_description,
        created_at=deployment.created_at,
        api_key=deployment.api_key,
        api_endpoint=deployment.api_endpoint,
        embed_code=deployment.embed_code,
        embed_settings=deployment.embed_settings,
    )


@deployment_router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    request: DeploymentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Update deployment details.
    """
    deployment = (
        db.query(Deployment)
        .filter(
            Deployment.deployment_id == deployment_id,
            Deployment.user_id == current_user.id,
        )
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it",
        )

    # Update fields if provided
    if request.deployment_name is not None:
        deployment.deployment_name = request.deployment_name

    if request.deployment_description is not None:
        deployment.deployment_description = request.deployment_description

    if request.embed_settings is not None and deployment.embed_settings is not None:
        # Merge existing settings with new settings
        embed_settings = deployment.embed_settings.copy()
        embed_settings.update(request.embed_settings)
        deployment.embed_settings = embed_settings

        # Update the embed code
        agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
        if agent:
            embed_code = f"""
            <script src="http://127.0.0.1:8000/static/embed.js" 
                    data-agent="{agent.agent_name}" 
                    data-deployment-id="{deployment.deployment_id}"
                    data-theme="{embed_settings.get('theme', 'light')}"
                    data-position="{embed_settings.get('position', 'bottom-right')}">
            </script>
            """
            deployment.embed_code = embed_code.strip()

    db.commit()
    db.refresh(deployment)

    # Prepare response
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent associated with this deployment not found",
        )

    return DeploymentResponse(
        deployment_id=deployment.deployment_id,
        agent_name=agent.agent_name,
        deployment_method=deployment.deployment_method,
        deployment_name=deployment.deployment_name,
        deployment_description=deployment.deployment_description,
        created_at=deployment.created_at,
        api_key=deployment.api_key,
        api_endpoint=deployment.api_endpoint,
        embed_code=deployment.embed_code,
        embed_settings=deployment.embed_settings,
    )


@deployment_router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Delete a deployment.
    """
    deployment = (
        db.query(Deployment)
        .filter(
            Deployment.deployment_id == deployment_id,
            Deployment.user_id == current_user.id,
        )
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it",
        )

    # Delete the deployment
    db.delete(deployment)
    db.commit()

    # No content response
    return None


# -------------- API V1 ROUTER ENDPOINTS --------------


@api_v1_router.get("/widget-config", response_model=Dict[str, Any])
async def get_widget_config(
    id: str, request: Request, db: Session = Depends(get_session)
):
    """
    Secure endpoint to provide widget configuration without exposing sensitive details in HTML source.
    This is called by the embed.js script rather than having configuration directly in the HTML.
    """
    # Verify the deployment exists
    deployment = db.query(Deployment).filter(Deployment.deployment_id == id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment {id} not found")

    # Get the agent
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=404, detail="Agent for this deployment not found"
        )

    # Check if domain is allowed (CORS)
    origin = request.headers.get("Origin")
    if origin and deployment.allowed_domains != "*":
        allowed_domains = [
            domain.strip() for domain in deployment.allowed_domains.split(",")
        ]
        if not any(origin.endswith(domain) for domain in allowed_domains):
            raise HTTPException(
                status_code=403,
                detail=f"Domain {origin} is not allowed to embed this agent",
            )

    # Return minimal necessary configuration
    return {
        "agentName": agent.agent_name,
        "deploymentId": deployment.deployment_id,
        "theme": (deployment.embed_settings or {}).get("theme", "light"),
        "position": (deployment.embed_settings or {}).get("position", "bottom-right"),
        "apiKey": deployment.api_key,  # Only included here for secure server-to-server transfer
    }


@api_v1_router.post("/deployment/{deployment_id}/query", response_model=Dict[str, Any])
async def query_deployed_agent(
    deployment_id: str,
    query: AgentQueryRequest,
    request: Request,
    db: Session = Depends(get_session),
):
    """Query a deployed agent with a question."""
    # First, verify the deployment exists
    deployment = (
        db.query(Deployment).filter(Deployment.deployment_id == deployment_id).first()
    )
    if not deployment:
        raise HTTPException(
            status_code=404, detail=f"Deployment {deployment_id} not found"
        )

    # Get the agent
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=404, detail="Agent for this deployment not found"
        )

    # Get the agent owner (we need a User object for the query_agent_logic function)
    user = db.query(User).filter(User.id == deployment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Agent owner not found")

    # Verify deployment method and permissions
    if deployment.deployment_method == "embed":
        # Check if the request is coming from an allowed domain
        origin = request.headers.get("Origin")
        if deployment.allowed_domains and origin:
            # Check if the origin is in the allowed domains
            allowed = False
            for domain in deployment.allowed_domains.split(","):
                if domain.strip() in origin:
                    allowed = True
                    break

            if not allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Origin {origin} not allowed for this deployment",
                )

    # For API deployments, verify the API key
    if deployment.deployment_method in ["api", "both"]:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != deployment.api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Process the query using the agent's capabilities
    try:
        # Call the actual agent query processing logic
        result = query_agent_logic(
            agent_name=agent.agent_name,
            question=query.question,
            current_user=user,
            agent_id=agent.id,
            session_id=query.session_id,
        )

        # Return the properly formatted response
        return {
            "agent_name": agent.agent_name,
            "question": query.question,
            "response": result.get("answer", "Error processing your query"),
            "session_id": result.get("session_id"),
            "tokens_in": result.get("tokens_in", 0),
            "tokens_out": result.get("tokens_out", 0),
            "total_tokens": result.get("total_tokens", 0),
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing your query: {str(e)}"
        )


# -------------- SHORTENER ROUTER ENDPOINTS --------------


@shortener_router.get("/{short_token}")
async def redirect_short_url(
    short_token: str, request: Request, db: Session = Depends(get_session)
):
    """
    Redirect a short URL to a custom embed script with deployment information.
    """
    # Look up the token in the database
    deployment = (
        db.query(Deployment)
        .filter(Deployment.short_token == short_token, Deployment.is_active == True)
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=404, detail="Short URL not found or has been deactivated"
        )

    # Check if request origin is allowed (CORS check)
    origin = request.headers.get("Origin")
    if origin and deployment.allowed_domains != "*":
        allowed_domains = [
            domain.strip() for domain in deployment.allowed_domains.split(",")
        ]
        if not any(origin.endswith(domain) for domain in allowed_domains):
            raise HTTPException(
                status_code=403,
                detail=f"Domain {origin} is not allowed to embed this agent",
            )

    # Get the agent
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Generate dynamic embed script with deployment info
    embed_config = {
        "agentName": agent.agent_name,
        "deploymentId": deployment.deployment_id,
        "apiKey": deployment.api_key,  # Include API key for secure API calls
        "theme": (deployment.embed_settings or {}).get("theme", "light"),
        "position": (deployment.embed_settings or {}).get("position", "bottom-right"),
    }

    # Generate JavaScript that sets window.AgentXConfig and loads the widget
    js_content = f"""
    window.AgentXConfig = {json.dumps(embed_config)};
    (function() {{
        var script = document.createElement('script');
        script.src = '{request.base_url}static/chat-widget.js';
        document.head.appendChild(script);
    }})();
    """

    # Return JavaScript content with proper Content-Type
    return Response(content=js_content, media_type="application/javascript")
