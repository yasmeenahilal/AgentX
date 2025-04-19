"""Agent services module implementing business logic for RAG operations."""
import json
import logging
from fastapi import HTTPException
from langchain.embeddings import HuggingFaceEmbeddings
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import IntegrityError

from database import get_index_name_type_db
from database.rag_db import (
    create_agent as create_agent_db,
    delete_agent as delete_agent_db,
    get_user_agents,
    get_agent_settings,
    update_agent as update_agent_db,
)
from rag_app.rag_main import Agent
from schemas.agent_schemas import (
    AgentCreateRequest,
    AgentDeleteRequest,
    AgentQueryRequest,
    AgentUpdateRequest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # You can adjust the logging level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)  # Use a logger specific to this module


def get_agent_details(user_id: str, agent_name: str) -> Dict[str, Any]:
    """
    Get agent details for a user's agent.
    
    Args:
        user_id: User identifier
        agent_name: Name of the agent to retrieve
        
    Returns:
        Dictionary containing agent details or None if not found
    """
    try:
        # Validate parameters
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required"
            )
        
        if not agent_name:
            raise HTTPException(
                status_code=400,
                detail="Agent name is required"
            )
            
        # Get agent settings from database
        agent_settings = get_agent_settings(user_id, agent_name)
        
        if not agent_settings:
            return None  # Let the API endpoint handle the 404 response
            
        return agent_settings
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.exception("Unexpected error occurred in get_agent_details.")
        raise HTTPException(status_code=500, detail=str(e))


def get_all_user_agents(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all agents for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of dictionaries containing agent details
    """
    try:
        # Validate user_id
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required"
            )
            
        # Get all agents from database
        result = get_user_agents(user_id)
        return result
    except Exception as e:
        logger.exception("Unexpected error occurred in get_all_user_agents.")
        raise HTTPException(status_code=500, detail=str(e))


def create_agent(request: AgentCreateRequest) -> Dict[str, Any]:
    """
    Create a new agent for a user.
    
    Args:
        request: Agent creation request details
        
    Returns:
        Dictionary with creation result message
    """
    try:
        # Validate that user_id has been set by the API endpoint
        if not request.user_id:
            logger.error("User ID was not set in the API endpoint")
            raise HTTPException(
                status_code=400,
                detail="User ID is required but was not provided. This should be set by the API endpoint."
            )
        
        # Check for required fields
        if not request.agent_name:
            raise HTTPException(
                status_code=400,
                detail="Agent name is required"
            )
            
        if not request.llm_api_key:
            raise HTTPException(
                status_code=400,
                detail="LLM API key is required"
            )
            
        # Create the agent using the database function
        message = create_agent_db(request)
        return message
    except IntegrityError:
        logger.error(f"Agent settings for agent '{request.agent_name}' already exist.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for agent '{request.agent_name}' already exist."
        )
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.exception("Unexpected error occurred in create_agent.")
        raise HTTPException(status_code=500, detail=str(e))


def update_agent(request: AgentUpdateRequest) -> Dict[str, Any]:
    """
    Update an existing agent's settings.
    
    Args:
        request: Agent update request details
        
    Returns:
        Dictionary with update result message
    """
    try:
        message = update_agent_db(request)
        return message
    except Exception as e:
        logger.exception("Unexpected error occurred in update_agent.")
        raise HTTPException(status_code=500, detail=str(e))


def delete_agent(request: AgentDeleteRequest) -> tuple[Dict[str, Any], int]:
    """
    Delete an existing agent.
    
    Args:
        request: Agent deletion request details
        
    Returns:
        Tuple containing dictionary with deletion result message and HTTP status code
    """
    try:
        message, status_code = delete_agent_db(request)
        print(message)
        return message, status_code  # Return message and status code
    except Exception as e:
        logger.exception("Unexpected error occurred in delete_agent.")
        raise HTTPException(status_code=500, detail=str(e))


def setup_rag(result, question: str, user_id: str, index_type: str) -> Agent:
    """
    Set up the RAG pipeline for an agent.
    
    Args:
        result: Agent settings data
        question: User's question
        user_id: ID of the user
        index_type: Type of vector index
        
    Returns:
        Agent instance configured for RAG querying
    """
    try:
        (
            agent_name,
            index_name,
            llm_provider,
            llm_model_name,
            llm_api_key,
            prompt_template,
            embeddings_model,
        ) = result
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
        
        response = Agent(
            index_name=index_name,
            embeddings=embeddings,
            model_name=llm_model_name,
            api_key=llm_api_key,
            prompt_template=prompt_template,
            use_llm=llm_provider,
            question=question,
            user_id=user_id,
            index_type=index_type,
        )

        return response
    except Exception as e:
        logger.exception("Error creating Agent pipeline.")
        raise e


def query_agent(request: AgentQueryRequest) -> Any:
    """
    Query an agent with a question.
    
    Args:
        request: Agent query request containing the question
        
    Returns:
        Agent response object
    """
    try:
        # Validate user_id and agent_name
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required but was not provided"
            )
        
        if not request.agent_name:
            raise HTTPException(
                status_code=400,
                detail="Agent name is required"
            )
            
        logger.info(f"Querying agent: user_id={request.user_id}, agent_name={request.agent_name}")
        
        # Get agent settings
        agent_settings = get_agent_settings(request.user_id, request.agent_name)
        
        if not agent_settings:
            logger.warning(f"No agent settings found for user_id '{request.user_id}' and agent_name '{request.agent_name}'")
            raise HTTPException(
                status_code=404,
                detail=f"No agent settings found for user_id '{request.user_id}' and agent_name '{request.agent_name}'"
            )
            
        # Extract necessary info for RAG setup
        index_name = agent_settings.get('index_name')
        index_type = agent_settings.get('index_type')
        embedding = agent_settings.get('embedding')
        
        # Setup RAG pipeline
        if index_name and index_type:
            # Create Agent instance
            agent = Agent(
                index_name=index_name,
                embeddings=HuggingFaceEmbeddings(model_name=embedding or "sentence-transformers/all-mpnet-base-v2"),
                model_name=agent_settings['llm_model_name'],
                api_key=agent_settings['llm_api_key'],
                prompt_template=agent_settings['prompt_template'],
                use_llm=agent_settings['llm_provider'],
                question=request.question,
                user_id=request.user_id,
                index_type=index_type,
            )
            
            return agent
        else:
            # Agent exists but has no associated vector DB
            logger.warning(f"Agent has no associated vector database: user_id={request.user_id}, agent_name={request.agent_name}")
            raise HTTPException(
                status_code=400,
                detail="This agent has no associated vector database. Please update the agent with an index."
            )

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred in query_agent.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
