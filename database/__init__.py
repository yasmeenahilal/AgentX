"""Database package initialization file."""
# Import the database initialization
# from .database import init_db, DATABASE # Assuming this was old or incorrect

# Import base engine/session getter using relative path from correct file
from .database import engine, get_session

# Import functions using relative paths
from .vector_db import (
    insert_into_vector_db,
    insert_into_pinecone_db,
    get_data_from_pinecone_db,
    insert_into_faiss_db,
    # insert_into_file_uploads, # Marked as legacy/handled by faiss
    update_file_upload,
    get_file_from_faiss_db,
    get_pinecone_api_index_name_type_db,
    delete_pinecone_index_from_db,
    delete_faiss_index_from_db,
    set_agent_index_to_none,
    # delete_from_vector_db, # Marked as legacy
)

# Import functions from rag_db.py (Agent settings etc.)
from .rag_db import (
    create_agent,
    update_agent,
    delete_agent,
    get_agent_settings,
    get_user_agents,
    get_index_type,
)

# Import functions from chat_db.py
from .chat_db import (
    get_chat_sessions,
    get_chat_messages,
    create_chat_session,
    add_chat_message,
    delete_chat_session,
) 

# Convenience function for getting index type (if still needed)
# def get_index_name_type_db(user_id: str, index_name: str):
#     """Get the database type (Pinecone or FAISS) for a given index."""
#     return get_index_type(user_id, index_name)

# Optional: Define __all__ if you want to control `from database import *`
__all__ = [
    # Base
    "engine", "get_session",
    # Vector DB
    "insert_into_vector_db", "insert_into_pinecone_db", "get_data_from_pinecone_db",
    "insert_into_faiss_db", "update_file_upload", "get_file_from_faiss_db",
    "get_pinecone_api_index_name_type_db", "delete_pinecone_index_from_db",
    "delete_faiss_index_from_db", "set_agent_index_to_none",
    # Agent DB
    "create_agent", "update_agent", "delete_agent", "get_agent_settings",
    "get_user_agents", "get_index_type",
    # Chat DB
    "get_chat_sessions", "get_chat_messages", "create_chat_session",
    "add_chat_message", "delete_chat_session",
]
