"""API router for deployment endpoints."""
import logging
import secrets
from fastapi import APIRouter, HTTPException, Body, Depends, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
import base64
import hashlib
import re

from models import User, Agent
from models.deployment import Deployment, DeploymentMethodEnum
from models.base import get_session
from user.auth import get_current_active_user, get_current_user
from database import get_agent_settings
from utils.security import encrypt_string, decrypt_string
from rag_app import query_agent_logic

# Setup logger
logger = logging.getLogger(__name__)

# Define separate routers for different functionality
deployment_router = APIRouter(tags=["Deployment"])  # Main deployment features
api_v1_router = APIRouter(tags=["API"])  # API v1 features
shortener_router = APIRouter(tags=["Shortener"])  # URL shortening

# URL shortening functions
def generate_short_id(original_url: str, length: int = 7) -> str:
    """Generate a short ID based on the original URL"""
    # Create a hash of the original URL
    hash_object = hashlib.md5(original_url.encode())
    # Get the first 'length' characters of the base64 representation
    short_id = base64.urlsafe_b64encode(hash_object.digest()).decode()[:length]
    # Make it URL friendly
    short_id = re.sub(r'[^a-zA-Z0-9]', '', short_id)
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
    db: Session = Depends(get_session)
):
    """
    Deploy an agent with the specified deployment method.
    """
    # Check if the agent exists and belongs to the user
    agent = db.query(Agent).filter(
        Agent.agent_name == request.agent_name,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with name '{request.agent_name}' not found or you don't have access to it"
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
        created_at=datetime.utcnow()
    )
    
    # Process deployment method
    api_key = None
    api_secret = None
    api_secret_encrypted = None
    api_endpoint = None
    embed_code = None
    embed_settings = None
    short_url = None
    
    if request.deployment_method in [DeploymentMethodEnum.api, DeploymentMethodEnum.both]:
        # Generate API key and secret
        api_key = f"agentx_{secrets.token_urlsafe(16)}"
        api_secret = secrets.token_urlsafe(32)
        
        # Encrypt the API secret
        api_secret_encrypted = encrypt_string(api_secret)
        
        # Set API details in response
        response.api_key = api_key
        api_endpoint = f"/api/v1/deployment/{deployment_id}/query"
        response.api_endpoint = api_endpoint
    
    if request.deployment_method in [DeploymentMethodEnum.embed, DeploymentMethodEnum.both]:
        # Generate embed code based on settings
        embed_settings = request.embed_settings or {}
        
        # Generate short URL for the embed script
        original_url = f"http://127.0.0.1:8000/static/embed.js?agent={request.agent_name}&id={deployment_id}&theme={embed_settings.get('theme', 'light')}&pos={embed_settings.get('position', 'bottom-right')}"
        short_id = generate_short_id(original_url)
        short_url = f"/s/{short_id}"
        
        # Store the mapping
        url_mappings[short_id] = original_url
        response.short_url = f"http://127.0.0.1:8000{short_url}"
        
        # Basic embed code template with short URL
        embed_code = f"""
        <script src="http://127.0.0.1:8000{short_url}"></script>
        """
        
        response.embed_code = embed_code.strip()
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
        agent_id=agent.id,
        user_id=current_user.id
    )
    
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    
    return response

@deployment_router.get("/list", response_model=List[DeploymentResponse])
async def list_deployments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    List all deployments for the authenticated user.
    """
    deployments = db.query(Deployment).filter(
        Deployment.user_id == current_user.id
    ).all()
    
    result = []
    for deployment in deployments:
        agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
        if not agent:
            continue
            
        result.append(DeploymentResponse(
            deployment_id=deployment.deployment_id,
            agent_name=agent.agent_name,
            deployment_method=deployment.deployment_method,
            deployment_name=deployment.deployment_name,
            deployment_description=deployment.deployment_description,
            created_at=deployment.created_at,
            api_key=deployment.api_key,
            api_endpoint=deployment.api_endpoint,
            embed_code=deployment.embed_code,
            embed_settings=deployment.embed_settings
        ))
    
    return result

@deployment_router.post("/generate-key", response_model=APIKeyResponse)
async def generate_api_key(
    agent_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Generate a new API key for an agent.
    """
    # Check if the agent exists and belongs to the user
    agent = db.query(Agent).filter(
        Agent.agent_name == agent_name,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with name '{agent_name}' not found or you don't have access to it"
        )
    
    # Generate API key and secret
    api_key = f"agentx_{secrets.token_urlsafe(16)}"
    api_secret = secrets.token_urlsafe(32)
    
    # Return the API key response (but don't save to database)
    return APIKeyResponse(
        api_key=api_key,
        api_secret=api_secret,
        created_at=datetime.utcnow()
    )

@deployment_router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get deployment details by ID.
    """
    deployment = db.query(Deployment).filter(
        Deployment.deployment_id == deployment_id,
        Deployment.user_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it"
        )
    
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent associated with this deployment not found"
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
        embed_settings=deployment.embed_settings
    )

@deployment_router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    request: DeploymentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Update deployment details.
    """
    deployment = db.query(Deployment).filter(
        Deployment.deployment_id == deployment_id,
        Deployment.user_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it"
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
            detail=f"Agent associated with this deployment not found"
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
        embed_settings=deployment.embed_settings
    )

@deployment_router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete a deployment.
    """
    deployment = db.query(Deployment).filter(
        Deployment.deployment_id == deployment_id,
        Deployment.user_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID '{deployment_id}' not found or you don't have access to it"
        )
    
    # Delete the deployment
    db.delete(deployment)
    db.commit()
    
    # No content response
    return None

# -------------- API V1 ROUTER ENDPOINTS --------------

@api_v1_router.post("/deployment/{deployment_id}/query", response_model=Dict[str, Any])
async def query_deployed_agent(
    deployment_id: str,
    query: AgentQueryRequest,
    request: Request,
    db: Session = Depends(get_session)
):
    """Query a deployed agent with a question."""
    # First, verify the deployment exists
    deployment = db.query(Deployment).filter(Deployment.deployment_id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    
    # Get the agent
    agent = db.query(Agent).filter(Agent.id == deployment.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent for this deployment not found")
    
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
                    detail=f"Origin {origin} not allowed for this deployment"
                )
    
    # For API deployments, verify the API key
    if deployment.deployment_method in ["api", "both"]:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != deployment.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
    
    # Process the query using the agent's capabilities
    try:
        # Call the actual agent query processing logic
        result = query_agent_logic(
            agent_name=agent.agent_name,
            question=query.question,
            current_user=user,
            agent_id=agent.id,
            session_id=query.session_id
        )
        
        # Return the properly formatted response
        return {
            "agent_name": agent.agent_name,
            "question": query.question,
            "response": result.get("answer", "Error processing your query"),
            "session_id": result.get("session_id"),
            "tokens_in": result.get("tokens_in", 0),
            "tokens_out": result.get("tokens_out", 0),
            "total_tokens": result.get("total_tokens", 0)
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your query: {str(e)}"
        )

# -------------- SHORTENER ROUTER ENDPOINTS --------------

@shortener_router.get("/{short_id}")
async def redirect_short_url(short_id: str):
    """
    Redirect a short URL to the original URL.
    """
    if short_id not in url_mappings:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    original_url = url_mappings[short_id]
    return RedirectResponse(url=original_url) 