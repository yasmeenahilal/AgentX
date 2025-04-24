"""API router for agent-related endpoints following RESTful conventions."""
import rag_app
from fastapi import APIRouter, HTTPException, Body, Depends
from schemas.agent_schemas import (
    AgentCreateRequest,
    AgentDeleteRequest,
    AgentGetRequest,
    AgentQueryRequest,
    AgentUpdateRequest,
)
from database import get_agent_settings
from models import User
from user.auth import get_current_active_user
from typing import Optional, List, Dict, Any
import logging

# For query endpoint
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None

# Setup logger
logger = logging.getLogger(__name__)

agent_router = APIRouter(prefix="", tags=["agents"])


@agent_router.get("/list_agents")
async def list_agents(current_user: User = Depends(get_current_active_user)):
    """
    List all agents for the authenticated user.
    """
    try:
        user_id = str(current_user.id)
        agents = rag_app.get_all_user_agents(user_id)
        
        # Format response to match what frontend expects
        return {
            "agents": agents,
            "columns": ["agent_name", "index_name", "llm_provider", "llm_model_name", "prompt_template"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.get("/all")
async def list_all_agents(current_user: User = Depends(get_current_active_user)):
    """
    Alternative endpoint to list all agents for the authenticated user.
    """
    try:
        user_id = str(current_user.id)
        agents = rag_app.get_all_user_agents(user_id)
        
        # Format response to match what frontend expects
        return {
            "agents": agents,
            "columns": ["agent_name", "index_name", "llm_provider", "llm_model_name", "prompt_template"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.get("/list_agents/{user_id}")
async def list_agents_by_id(user_id: str, current_user: User = Depends(get_current_active_user)):
    """
    List all agents for a specific user ID.
    Only the authenticated user can access their own agents.
    """
    try:
        # Security check - only allow users to access their own data
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="You can only access your own agent list")
            
        agents = rag_app.get_all_user_agents(user_id)
        
        # Format response to match what frontend expects
        return {
            "agents": agents,
            "columns": ["agent_name", "index_name", "llm_provider", "llm_model_name", "prompt_template"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.get("/{agent_name}/")
async def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get agent details for the authenticated user.
    """
    try:
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
            
        agent = get_agent_settings(current_user.id, agent_name)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Security check: verify that the agent belongs to the current user
        if agent["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this agent")
            
        return agent
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@agent_router.post("")
async def create_agent(
    request: AgentCreateRequest, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new agent for the authenticated user.
    
    Args:
        request: Agent creation details
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        # Ensure the user_id is set to the current authenticated user
        request.user_id = str(current_user.id)
        response = rag_app.create_agent(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.put("")
async def update_agent(
    request: AgentUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing agent for the authenticated user.
    
    Args:
        request: Agent update details
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        # Ensure the user_id is set to the current authenticated user
        request.user_id = str(current_user.id)
        response = rag_app.update_agent(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.put("/{agent_name}")
async def update_agent_by_path(
    agent_name: str, 
    data: dict = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    RESTful endpoint to update an agent by name.
    Used by the frontend update form.
    
    Args:
        agent_name: Name of the agent to update
        data: Updated agent details
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        # Ensure user_id and agent_name are set correctly in the request data
        data["user_id"] = str(current_user.id)
        data["agent_name"] = agent_name
        
        # Convert the dictionary to an AgentUpdateRequest
        request = AgentUpdateRequest(**data)
        
        # Use the existing update logic
        response = rag_app.update_agent(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.delete("")
async def delete_agent(
    agent_name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an agent for the authenticated user.
    
    Args:
        agent_name: Name of the agent to delete
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        # Create DeleteAgent object with current user's ID
        request = AgentDeleteRequest(
            agent_name=agent_name,
            user_id=str(current_user.id)
        )
        response, status_code = rag_app.delete_agent(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@agent_router.post("/{agent_name}/query", response_model=QueryResponse)
async def query_agent(
    agent_name: str, 
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Query an agent with a question"""
    try:
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
            
        # Verify agent exists and belongs to the current user
        agent = get_agent_settings(current_user.id, agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
        # Security check: verify that the agent belongs to the current user
        if agent["user_id"] !=current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this agent")
            
        # Create the agent query request
        query_request = AgentQueryRequest(
            agent_name=agent_name,
            user_id=str(current_user.id),
            question=request.question
        )
        
        # Process the query using the Agent function from rag_main
        # This now returns the extracted answer string (or an error string)
        answer_string = rag_app.query_agent(query_request)
        
        # Construct the QueryResponse object
        # For now, we don't have sources information easily available from the Agent function
        # So, we'll return sources as None.
        response_object = QueryResponse(answer=answer_string, sources=None)
        
        return response_object # Return the structured QueryResponse
        
    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.error(f"Error querying agent '{agent_name}': {str(e)}")
        # Catch other exceptions and return a 500 error
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@agent_router.get("/debug/{user_id}")
async def debug_agent_data(user_id: str, current_user: User = Depends(get_current_active_user)):
    """
    Debug endpoint to check agent data and database connectivity.
    
    Args:
        user_id: User ID to check
        current_user: Authenticated user
        
    Returns:
        Debug information
    """
    try:
        # Security check - only allow users to access their own data or admins to access any data
        if str(current_user.id) != user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="You can only access your own debug data")
            
        from sqlmodel import Session, select
        from models.base import engine
        from models.agent import Agent
        from models.vector_db import VectorDB
        
        debug_info = {
            "user_id": user_id,
            "database_connected": True,
            "agents": [],
            "vector_dbs": []
        }
        
        with Session(engine) as session:
            # Get all agents for user
            agent_stmt = select(Agent).where(Agent.user_id == int(user_id))
            agents = session.exec(agent_stmt).all()
            
            # Get all vector DBs for user
            vector_db_stmt = select(VectorDB).where(VectorDB.user_id == int(user_id))
            vector_dbs = session.exec(vector_db_stmt).all()
            
            # Collect agent info
            for agent in agents:
                agent_info = {
                    "agent_name": agent.agent_name,
                    "vector_db_id": agent.vector_db_id
                }
                debug_info["agents"].append(agent_info)
                
            # Collect vector DB info
            for vector_db in vector_dbs:
                vector_db_info = {
                    "id": vector_db.id,
                    "index_name": vector_db.index_name,
                    "db_type": vector_db.db_type.value
                }
                debug_info["vector_dbs"].append(vector_db_info)
            
        return debug_info
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }


@agent_router.get("/get_agent/{user_id}/{agent_name}")
async def get_agent_by_id(
    user_id: str,
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get agent details by user ID and agent name.
    """
    try:
        # Security check - only allow users to access their own data
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="You can only access your own agent details")
            
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
            
        agent = get_agent_settings(user_id, agent_name)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Security check: verify that the agent belongs to the user
        if agent["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this agent")
            
        return agent
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


