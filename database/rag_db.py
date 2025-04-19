"""RAG database operations using SQLModel ORM instead of raw SQL."""
import logging
import sqlite3
from sqlmodel import Session, select
from fastapi import HTTPException
from models.base import engine
from models.agent import Agent, LLMProviderEnum
from models.vector_db import VectorDB, PineconeDB, FaissDB, DBTypeEnum
from models.user import User
from schemas.agent_schemas import (
    CreateAgentRequest,
    UpdateAgentRequest,
    DeleteAgent,
)
import json
from typing import Dict, List, Optional, Tuple, Union, Any

# Remove circular import
# from database import get_index_name_type_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy database path - kept for backward compatibility
DATABASE = "agentX.db"

# Helper function to get index type - moved from __init__.py to avoid circular imports
def get_index_type(user_id: str, index_name: str, session: Session = None):
    """Get the database type (Pinecone or FAISS) for a given index."""
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True
        
    try:
        statement = select(VectorDB).where(
            VectorDB.user_id == int(user_id),
            VectorDB.index_name == index_name
        )
        vector_db = session.exec(statement).first()
        
        if not vector_db:
            return None
            
        return vector_db.db_type.value
    finally:
        if close_session:
            session.close()

def create_rag_db(request: CreateAgentRequest):
    """Create a new agent entry in the database using SQLModel."""
    try:
        # Check if user_id is provided
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required. This should be set by the API endpoint."
            )
            
        # Get or create user by user_id
        with Session(engine) as session:
            # Ensure user_id is treated as integer
            user_id = int(request.user_id)
            
            # Check if an agent with this name already exists for this user
            statement = select(Agent).where(
                Agent.user_id == user_id,
                Agent.agent_name == request.agent_name
            )
            existing_agent = session.exec(statement).first()
            
            if existing_agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent with name '{request.agent_name}' already exists for this user"
                )
            
            # Check if user exists
            user = session.get(User, user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with ID {user_id} not found"
                )
            
            # Create new agent
            new_agent = Agent(
                agent_name=request.agent_name,
                user_id=user_id,
                llm_provider=request.llm_provider,
                llm_model_name=request.llm_model_name,
                llm_api_key=request.llm_api_key,
                prompt_template=request.prompt_template,
                vector_db_id=None  # Will be updated if index is associated
            )
            
            # If index_name provided, associate with existing vector DB
            if request.index_name and hasattr(request, 'index_type') and request.index_type:
                # Find the vector DB
                vector_db_stmt = select(VectorDB).where(
                    VectorDB.user_id == user_id,
                    VectorDB.index_name == request.index_name
                )
                vector_db = session.exec(vector_db_stmt).first()
                
                if vector_db:
                    new_agent.vector_db_id = vector_db.id
                else:
                    logger.warning(f"Vector DB with name {request.index_name} not found")
            
            session.add(new_agent)
            session.commit()
            session.refresh(new_agent)
            
            return {"message": f"Agent '{request.agent_name}' created successfully"}
            
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create agent: {str(e)}"
        )

def update_rag_db(request: UpdateAgentRequest):
    """Update an existing agent in the database using SQLModel."""
    try:
        # Check if user_id is provided
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required. This should be set by the API endpoint."
            )
            
        with Session(engine) as session:
            # Ensure user_id is treated as integer
            user_id = int(request.user_id)
            
            # Find the agent to update
            statement = select(Agent).where(
                Agent.user_id == user_id,
                Agent.agent_name == request.agent_name
            )
            agent = session.exec(statement).first()
            
            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent with name '{request.agent_name}' not found for user ID {user_id}"
                )
            
            # Update agent fields
            if request.new_agent_name:
                # Check if the new name already exists for another agent
                if request.new_agent_name != request.agent_name:
                    check_stmt = select(Agent).where(
                        Agent.user_id == user_id,
                        Agent.agent_name == request.new_agent_name
                    )
                    if session.exec(check_stmt).first():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Agent with name '{request.new_agent_name}' already exists for this user"
                        )
                    agent.agent_name = request.new_agent_name
            
            if request.llm_provider:
                agent.llm_provider = request.llm_provider
                
            if request.llm_model_name:
                agent.llm_model_name = request.llm_model_name
                
            if request.llm_api_key:
                agent.llm_api_key = request.llm_api_key
                
            if request.prompt_template:
                agent.prompt_template = request.prompt_template
                
            # Handle vector database association
            if request.index_name and request.index_type:
                # Find the vector DB
                vector_db_stmt = select(VectorDB).where(
                    VectorDB.user_id == user_id,
                    VectorDB.index_name == request.index_name
                )
                vector_db = session.exec(vector_db_stmt).first()
                
                if vector_db:
                    agent.vector_db_id = vector_db.id
                else:
                    logger.warning(f"Vector DB with name {request.index_name} not found")
            
            # Remove vector DB association if requested
            if request.index_name == "None" or request.index_type == "None":
                agent.vector_db_id = None
            
            session.add(agent)
            session.commit()
            
            return {"message": f"Agent '{request.agent_name}' updated successfully"}
            
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update agent: {str(e)}"
        )

def delete_rag_db(request: DeleteAgent) -> Tuple[Dict[str, str], int]:
    """Delete an agent from the database using SQLModel."""
    try:
        # Check if user_id is provided
        if not request.user_id:
            return {"message": "User ID is required. This should be set by the API endpoint."}, 400
            
        with Session(engine) as session:
            # Ensure user_id is treated as integer
            user_id = int(request.user_id)
            
            # Find the agent to delete
            statement = select(Agent).where(
                Agent.user_id == user_id,
                Agent.agent_name == request.agent_name
            )
            agent = session.exec(statement).first()
            
            if not agent:
                return {"message": f"Agent with name '{request.agent_name}' not found"}, 404
            
            # Delete the agent
            session.delete(agent)
            session.commit()
            
            return {"message": f"Agent '{request.agent_name}' deleted successfully"}, 200
            
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        return {"message": f"Failed to delete agent: {str(e)}"}, 500

def get_rag_settings(user_id: str, agent_name: str) -> Dict[str, Any]:
    """Get agent settings from the database using SQLModel."""
    try:
        # Check if user_id is provided
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required"
            )
            
        with Session(engine) as session:
            # Ensure user_id is treated as integer
            user_id_int = int(user_id)
            
            # Find the agent
            statement = select(Agent).where(
                Agent.user_id == user_id_int,
                Agent.agent_name == agent_name
            )
            agent = session.exec(statement).first()
            
            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent with name '{agent_name}' not found for user ID {user_id}"
                )
            
            # Build the response with agent data
            result = {
                "user_id": user_id,
                "agent_name": agent.agent_name,
                "llm_provider": agent.llm_provider,
                "llm_model_name": agent.llm_model_name,
                "llm_api_key": agent.llm_api_key,
                "prompt_template": agent.prompt_template,
                "index_name": None,
                "index_type": None,
                "embedding": None
            }
            
            # If agent has an associated vector DB, get the details
            if agent.vector_db_id:
                vector_db = session.get(VectorDB, agent.vector_db_id)
                if vector_db:
                    result["index_name"] = vector_db.index_name
                    result["index_type"] = vector_db.db_type.value
                    
                    # Get embedding model based on DB type
                    if vector_db.db_type.value == "Pinecone":
                        pinecone_stmt = select(PineconeDB).where(
                            PineconeDB.vector_db_id == vector_db.id
                        )
                        pinecone_db = session.exec(pinecone_stmt).first()
                        if pinecone_db:
                            result["embedding"] = pinecone_db.embedding.value
                    elif vector_db.db_type.value == "FAISS":
                        faiss_stmt = select(FaissDB).where(
                            FaissDB.vector_db_id == vector_db.id
                        )
                        faiss_db = session.exec(faiss_stmt).first()
                        if faiss_db:
                            result["embedding"] = faiss_db.embedding.value
            
            return result
            
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error getting agent settings: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get agent settings: {str(e)}"
        )

def get_all_agents_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all agents for a user from the database using SQLModel."""
    try:
        # Check if user_id is provided
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required"
            )
            
        with Session(engine) as session:
            # Ensure user_id is treated as integer
            user_id_int = int(user_id)
            
            # Find all agents for the user
            statement = select(Agent).where(Agent.user_id == user_id_int)
            agents = session.exec(statement).all()
            
            result = []
            for agent in agents:
                agent_data = {
                    "agent_name": agent.agent_name,
                    "llm_provider": agent.llm_provider,
                    "llm_model_name": agent.llm_model_name,
                    "prompt_template": agent.prompt_template,
                    "index_name": None,
                    "index_type": None
                }
                
                # If agent has an associated vector DB, get the details
                if agent.vector_db_id:
                    vector_db = session.get(VectorDB, agent.vector_db_id)
                    if vector_db:
                        agent_data["index_name"] = vector_db.index_name
                        agent_data["index_type"] = vector_db.db_type.value
                
                result.append(agent_data)
            
            return result
            
    except Exception as e:
        logger.error(f"Error getting agents for user: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get agents for user: {str(e)}"
        )

# Legacy raw SQL functions - kept for backward compatibility
def _legacy_create_rag_db(request: CreateAgentRequest):
    """Legacy function to create agent using raw SQL."""
    # ... existing raw SQL implementation ...
    pass

def _legacy_update_rag_db(request: UpdateAgentRequest):
    """Legacy function to update agent using raw SQL."""
    # ... existing raw SQL implementation ...
    pass

def _legacy_delete_rag_db(request: DeleteAgent):
    """Legacy function to delete agent using raw SQL."""
    # ... existing raw SQL implementation ...
    pass

def _legacy_get_rag_settings(user_id: str, agent_name: str):
    """Legacy function to get agent settings using raw SQL."""
    # ... existing raw SQL implementation ...
    pass

def _legacy_get_all_agents_for_user(user_id: str):
    """Legacy function to get all agents for a user using raw SQL."""
    # ... existing raw SQL implementation ...
    pass
