"""Agent services module implementing business logic for RAG operations."""
import json
import logging
from fastapi import HTTPException
from langchain.embeddings import HuggingFaceEmbeddings
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import IntegrityError
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import database # USE THIS INSTEAD
from models import MessageTypeEnum, Agent as AgentModel, User # Rename import to avoid conflict and add User


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


def query_agent(
    agent_name: str, 
    question: str, 
    session_id: Optional[int], 
    current_user: User # Accept the User object directly
) -> Dict[str, Any]:
    """
    Query an agent with a question, handling chat history.
    Relies on the authenticated user object passed in.
    
    Args:
        agent_name: Name of the agent to query.
        question: The user's question.
        session_id: The optional chat session ID.
        current_user: The authenticated user object.
        
    Returns:
        Dictionary containing the answer and session_id: {'answer': str, 'session_id': int}
    """
    # Get user_id from the authenticated user object
    user_id = current_user.id
    # session_id = request.session_id # Already passed directly
    # question = request.question # Already passed directly
    # agent_name = request.agent_name # Already passed directly

    try:
        # Get agent settings using user_id from current_user
        agent_settings = get_agent_settings(str(user_id), agent_name)
        if not agent_settings:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found for user.")

        agent_id = agent_settings.get('id')
        if not agent_id:
             logger.error(f"Agent ID missing in settings for agent_name: {agent_name}, user_id: {user_id}")
             raise HTTPException(status_code=500, detail="Internal configuration error: Agent ID not found.")

        # Load history or create new session
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        if session_id:
            logger.info(f"Loading history for session_id: {session_id}")
            # Access chat_db functions via database package
            db_messages = database.chat_db.get_chat_messages(session_id=session_id, user_id=user_id)
            # Convert DB messages to LangChain messages
            history_messages = []
            for msg in db_messages:
                if msg.message_type == MessageTypeEnum.HUMAN:
                    history_messages.append(HumanMessage(content=msg.content))
                elif msg.message_type == MessageTypeEnum.AI:
                    history_messages.append(AIMessage(content=msg.content))
            memory.chat_memory.messages = history_messages
            logger.info(f"Loaded {len(history_messages)} messages into memory.")
        else:
            logger.info(f"No session_id provided. Creating new session for user {user_id}, agent {agent_id}.")
            # Access chat_db functions via database package
            new_session = database.chat_db.create_chat_session(user_id=user_id, agent_id=agent_id, first_message=question)
            session_id = new_session.id
            database.chat_db.add_chat_message(session_id=session_id, message_type=MessageTypeEnum.HUMAN, content=question)
            logger.info(f"New session created with id: {session_id}. First message saved.")
        
        # Extract necessary info for RAG setup (as before)
        index_name = agent_settings.get('index_name')
        index_type = agent_settings.get('index_type')
        embedding = agent_settings.get('embedding')

        if not index_name or not index_type:
             # ... (handle agent exists but no vector DB) ...
              raise HTTPException(status_code=400, detail="Agent has no associated vector DB.")


        # Call the core Agent function (from rag_main), passing the memory object
        # Assuming Agent function is updated to accept memory
        final_answer = Agent( # Function from rag_main
            index_name=index_name,
            embeddings=HuggingFaceEmbeddings(model_name=embedding or "sentence-transformers/all-mpnet-base-v2"),
            model_name=agent_settings['llm_model_name'],
            api_key=agent_settings['llm_api_key'],
            prompt_template=agent_settings['prompt_template'],
            use_llm=agent_settings['llm_provider'],
            question=question,
            user_id=str(user_id), # Pass user_id as string to rag_main Agent
            index_type=index_type,
            memory=memory # Pass the prepared memory object
        )

        # Save the AI response to the history
        if final_answer and not final_answer.startswith("Error:"):
            # Access chat_db functions via database package
            database.chat_db.add_chat_message(session_id=session_id, message_type=MessageTypeEnum.AI, content=final_answer)
            logger.info(f"Saved AI answer to session {session_id}")
        else:
            logger.warning(f"Did not save AI answer to session {session_id} due to error or empty response.")

        # Return the answer and session_id
        return {"answer": final_answer, "session_id": session_id}

    except HTTPException as http_exc:
        logger.error(f"HTTPException in query_agent: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred in query_agent.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
