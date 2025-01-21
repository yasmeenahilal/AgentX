import logging
import sqlite3

from database import get_index_name_type_db
from database.rag_db import (
    create_rag_db,
    delete_rag_db,
    get_rag_settings,
    update_rag_db,
)
from fastapi import HTTPException
from langchain_huggingface import HuggingFaceEmbeddings
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


async def get_agent_details(request):
    """
    Business logic to create Agent settings for a user.
    """
    try:
        data = get_rag_settings(request.user_id, request.agent_name)
        return data
    except sqlite3.IntegrityError:
        logger.error(f"Agent settings for index '{request.agent_name}' not found.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for index '{request.agent_name}' not found.",
        )
    except Exception as e:
        logger.exception("Unexpected error occurred in get_agent_details.")
        raise HTTPException(status_code=500, detail=str(e))


async def create_agent_logic(request: CreateAgentRequest):
    """
    Business logic to create Agent settings for a user.
    """
    try:
        message = create_rag_db(request)
        return message
    except sqlite3.IntegrityError:
        logger.error(f"Agent settings for index '{request.index_name}' already exist.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for index '{request.index_name}' already exist.",
        )
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
        message = delete_rag_db(request)
        return message
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

        embeddings = HuggingFaceEmbeddings(model_name=str(embeddings_model))
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
        result = get_rag_settings(request.user_id, request.agent_name)
        index_type = get_index_name_type_db(request.user_id, result[1])

        if not result:
            logger.warning(f"No Agent settings found for user_id '{request.user_id}'.")
            raise HTTPException(
                status_code=404,
                detail=f"No Agent settings found for user_id '{request.user_id}'.",
            )

        response = await setup_rag(
            result, request.question, request.user_id, index_type
        )

        return response

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred in query_agent_logic.")
        raise HTTPException(status_code=500, detail="Internal Server Error")
