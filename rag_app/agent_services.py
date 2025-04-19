"""Agent services module implementing business logic for RAG operations."""
import json
import logging
import sqlite3
from fastapi import HTTPException
from langchain.embeddings import HuggingFaceEmbeddings
from typing import Dict, Any, List, Optional

from database import get_index_name_type_db
from database.rag_db import (
    create_rag_db,
    delete_rag_db,
    get_all_agents_for_user,
    get_rag_settings,
    update_rag_db,
)
from rag_app.rag_main import Agent
from schemas.agent_schemas import (
    CreateAgentRequest,
    DeleteAgent,
    QuerAgentRequest,
    UpdateAgentRequest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # You can adjust the logging level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)  # Use a logger specific to this module


async def get_agent_details(user_id, agent_name):
    """
    Get agent details including column names.
    """
    try:
        data = get_rag_settings(user_id, agent_name)
        
        # Extract the data and column names from the response
        raw_data = data["data"]
        
        # Create a dictionary with named fields
        result = {}
 
        # Ensure correct mapping based on database schema
        # The expected order is: agent_name, index_name, llm_provider, llm_model_name, llm_api_key, prompt_template, embedding
        result = {
            "agent_name": raw_data[0],
            "index_name": raw_data[1],
            "llm_provider": raw_data[2],
            "llm_model_name": raw_data[3],
            "llm_api_key": raw_data[4],
            "prompt_template": raw_data[5],
            "embedding": raw_data[6] if len(raw_data) > 6 else None
        }
        print("llm_api_key", result["llm_api_key"])
        
        # Add additional metadata
        result["user_id"] = user_id
        # result["database_columns"] = data.get("database_columns", [])
        result["index_type"] = data.get("index_type")
        
        return result
    except sqlite3.IntegrityError:
        logger.error(f"Agent settings for index '{agent_name}' not found.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for index '{agent_name}' not found.",
        )
    except Exception as e:
        logger.exception("Unexpected error occurred in get_agent_details.")
        raise HTTPException(status_code=500, detail=str(e))


async def get_all_user_agents(user_id):
    """
    Get all agents for a specific user.
    """
    try:
        result = get_all_agents_for_user(user_id)
        return result
    except Exception as e:
        logger.exception("Unexpected error occurred in get_all_user_agents.")
        raise HTTPException(status_code=500, detail=str(e))


async def create_agent_logic(request: CreateAgentRequest):
    """
    Business logic to create Agent settings for a user.
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
            
        # Create the agent
        message = create_rag_db(request)
        return message
    except sqlite3.IntegrityError:
        logger.error(f"Agent settings for agent '{request.agent_name}' already exist.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for agent '{request.agent_name}' already exist."
        )
    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.exception("Unexpected error occurred in create_agent_logic.")
        raise HTTPException(status_code=500, detail=str(e))


async def update_agent_logic(request: UpdateAgentRequest):
    """
    Business logic to update Agent settings.
    """
    try:
        message = update_rag_db(request)
        return message
    except Exception as e:
        logger.exception("Unexpected error occurred in update_agent_logic.")
        raise HTTPException(status_code=500, detail=str(e))


async def delete_agent_logic(request: DeleteAgent):
    """
    Business logic to delete an Agent index.
    """
    try:
        message, status_code = delete_rag_db(request)
        print(message)
        return message, status_code  # Return message and status code
    except Exception as e:
        logger.exception("Unexpected error occurred in delete_agent_logic.")
        raise HTTPException(status_code=500, detail=str(e))

async def setup_rag(result, question, user_id, index_type):
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
        embeddings= HuggingFaceEmbeddings(
                        model_name=embeddings_model
                    ) 
        # embeddings = HuggingFaceEmbeddings(model_name=str(embeddings_model))
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


async def query_agent_logic(request: QuerAgentRequest):
    """
    Business logic to handle querying of an Agent pipeline with proper debugging.
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
        agent_settings = get_rag_settings(request.user_id, request.agent_name)
        
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
        logger.exception("Unexpected error occurred in query_agent_logic.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
