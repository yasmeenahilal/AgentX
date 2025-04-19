"""Database package initialization file."""
# Import the database initialization
from .database import init_db, DATABASE

# Import functions from vector_db.py
from .vector_db import (
    insert_into_vector_db,
    insert_into_pinecone_db,
    get_data_from_pinecone_db,
    insert_into_faiss_db,
    insert_into_file_uploads,
    update_file_upload,
    get_file_from_faiss_db,
    get_pinecone_api_index_name_type_db,
    delete_pinecone_index_from_db,
    delete_faiss_index_from_db,
    set_agent_index_to_none,
    delete_from_vector_db,
)

# Import functions from rag_db.py with new snake_case names
from .rag_db import (
    create_agent,
    update_agent,
    delete_agent,
    get_agent_settings,
    get_user_agents,
    get_index_type,
)

# Convenience function for getting index type
def get_index_name_type_db(user_id: str, index_name: str):
    """Get the database type (Pinecone or FAISS) for a given index."""
    return get_index_type(user_id, index_name)
