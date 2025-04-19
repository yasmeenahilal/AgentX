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

# Import functions from rag_db.py
from .rag_db import (
    create_rag_db,
    update_rag_db,
    delete_rag_db,
    get_rag_settings,
    get_all_agents_for_user,
    get_index_type,
)

# Convenience function for getting index type
def get_index_name_type_db(user_id: str, index_name: str):
    """Get the database type (Pinecone or FAISS) for a given index."""
    from sqlmodel import Session, select
    from models.base import engine
    from models.vector_db import VectorDB
    
    with Session(engine) as session:
        statement = select(VectorDB).where(
            VectorDB.user_id == int(user_id),
            VectorDB.index_name == index_name
        )
        vector_db = session.exec(statement).first()
        
        if not vector_db:
            return None
            
        return vector_db.db_type.value

# For backward compatibility
get_index_name_type_db = get_index_type
