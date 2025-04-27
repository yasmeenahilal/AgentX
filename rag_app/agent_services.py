"""Agent services module implementing business logic for RAG operations."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage
from sqlalchemy.exc import IntegrityError

import database  # USE THIS INSTEAD
from models import Agent as AgentModel  # Rename import to avoid conflict and add User
from models import User
from models.chat import MessageTypeEnum  # Add this import


# Token counting utility
def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    This is a simple approximation. For more precise counting, use a proper tokenizer.

    Args:
        text: The text to estimate token count for

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Simple estimation: ~4 chars per token for English text
    # This is an approximation that works reasonably well for most LLMs
    return max(1, int(len(text) / 4))


from database.chat_db import add_chat_message, create_chat_session, get_chat_messages
from database.rag_db import create_agent as create_agent_db
from database.rag_db import delete_agent as delete_agent_db
from database.rag_db import get_agent_settings, get_user_agents
from database.rag_db import update_agent as update_agent_db
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
            raise HTTPException(status_code=400, detail="User ID is required")

        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")

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
            raise HTTPException(status_code=400, detail="User ID is required")

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
                detail="User ID is required but was not provided. This should be set by the API endpoint.",
            )

        # Check for required fields
        if not request.agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")

        if not request.llm_api_key:
            raise HTTPException(status_code=400, detail="LLM API key is required")

        # Create the agent using the database function
        message = create_agent_db(request)
        return message
    except IntegrityError:
        logger.error(f"Agent settings for agent '{request.agent_name}' already exist.")
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for agent '{request.agent_name}' already exist.",
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

        # Initialize embeddings based on the LLM provider
        if llm_provider == "gemini":
            # For Gemini, we still use HuggingFace embeddings for the vector store
            # but we need to ensure we're using a valid HuggingFace model
            if not embeddings_model or embeddings_model.startswith("gemini"):
                # Default to a standard embedding model if not specified or if Gemini model is used
                embeddings_model = "sentence-transformers/all-mpnet-base-v2"

        # Initialize HuggingFace embeddings with proper parameters
        embeddings = HuggingFaceEmbeddings(
            model_name=embeddings_model,
            model_kwargs={"device": "cpu"},  # Force CPU usage to avoid GPU issues
            encode_kwargs={
                "normalize_embeddings": True
            },  # Normalize embeddings for better results
        )

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


def query_agent(
    agent_name: str,
    question: str,
    current_user: User,
    agent_id: int,
    session_id: Optional[int] = None,  # Add session_id parameter
) -> Dict[str, Any]:  # Return type changed to dict
    """
    Query an agent with a question, handling chat history via database.

    Args:
        agent_name: Name of the agent to query.
        question: The user's question.
        current_user: The authenticated user object.
        agent_id: The database ID of the agent being queried.
        session_id: Optional ID of the existing chat session.

    Returns:
        dict: Dictionary containing the agent's 'answer' and the 'session_id'.
    """
    user_id = current_user.id
    # session_key = f"chat_history_{agent_id}" # Removed session key

    # Calculate input tokens
    input_tokens = estimate_tokens(question)
    logger.info(
        f"Input question length: {len(question)} chars, estimated {input_tokens} tokens"
    )

    try:
        # Agent settings needed for RAG setup (API keys, models, etc.)
        agent_settings = get_agent_settings(str(user_id), agent_name)
        if not agent_settings:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_name}' not found for user."
            )

        # --- Database History ---
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        history_messages = []

        if session_id:
            # Load history from DB if session_id is provided
            logger.info(f"Loading history for session_id: {session_id}")
            db_messages = get_chat_messages(
                session_id=session_id, user_id=user_id
            )  # Fetch from DB
            for msg in db_messages:
                if msg.message_type == MessageTypeEnum.HUMAN:
                    history_messages.append(HumanMessage(content=msg.content))
                elif msg.message_type == MessageTypeEnum.AI:
                    history_messages.append(AIMessage(content=msg.content))
            memory.chat_memory.messages = history_messages
        else:
            # If no session_id, this is the start of a new chat.
            # DB session will be created *after* the first AI response.
            logger.info(
                f"No session_id provided. Starting new chat for agent_id: {agent_id}"
            )

        # Add current human question to memory for the call
        memory.chat_memory.add_user_message(question)

        # ... (Extract RAG setup info: index_name, index_type, embedding from agent_settings) ...
        index_name = agent_settings.get("index_name")
        index_type = agent_settings.get("index_type")
        embedding = agent_settings.get("embedding")
        if not index_name or not index_type:
            raise HTTPException(
                status_code=400, detail="Agent has no associated vector DB."
            )

        # Call the core Agent function (from rag_main), passing the memory object
        final_answer = Agent(  # Function from rag_main
            index_name=index_name,
            embeddings=HuggingFaceEmbeddings(
                model_name=embedding or "sentence-transformers/all-mpnet-base-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            ),
            model_name=agent_settings["llm_model_name"],
            api_key=agent_settings["llm_api_key"],
            prompt_template=agent_settings["prompt_template"],
            use_llm=agent_settings["llm_provider"],
            question=question,
            user_id=str(user_id),
            index_type=index_type,
            memory=memory,  # Pass the memory object populated from DB
        )

        # Calculate output tokens
        output_tokens = estimate_tokens(final_answer)
        logger.info(
            f"Output answer length: {len(final_answer)} chars, estimated {output_tokens} tokens"
        )

        # --- Save conversation to Database ---
        if final_answer and not final_answer.startswith("Error:"):
            if session_id is None:
                # Create a new session if it's the first message pair
                logger.info(
                    f"Creating new chat session for user {user_id}, agent {agent_id}"
                )
                new_session = create_chat_session(
                    user_id=user_id,
                    agent_id=agent_id,
                    first_message=question,  # Use the first question to potentially generate a title later
                )
                session_id = new_session.id  # Get the new session ID
                logger.info(f"Created new session with ID: {session_id}")
                # Add the first user message to the newly created session
                add_chat_message(
                    session_id=session_id,
                    message_type=MessageTypeEnum.HUMAN,
                    content=question,
                    token_count=input_tokens,
                )
                logger.info(f"Added first user message to session {session_id}")
            else:
                # Add user message to existing session (if not the very first interaction)
                # Check needed because in a new session, user message is added above
                if (
                    len(history_messages) > 0 or len(memory.chat_memory.messages) > 1
                ):  # check memory just in case
                    add_chat_message(
                        session_id=session_id,
                        message_type=MessageTypeEnum.HUMAN,
                        content=question,
                        token_count=input_tokens,
                    )
                    logger.info(
                        f"Added subsequent user message to session {session_id}"
                    )

            # Add the AI response message
            add_chat_message(
                session_id=session_id,
                message_type=MessageTypeEnum.AI,
                content=final_answer,
                token_count=output_tokens,
            )
            logger.info(f"Added AI message to session {session_id}")
        else:
            logger.warning(
                f"Did not save conversation to session {session_id} due to error or empty response."
            )
        # --- End Database Save ---

        # Prepare the response with token counts
        return {
            "answer": final_answer,
            "session_id": session_id,
            "tokens_in": input_tokens,
            "tokens_out": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    except HTTPException as http_exc:
        logger.error(f"HTTPException in query_agent: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred in query_agent.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
