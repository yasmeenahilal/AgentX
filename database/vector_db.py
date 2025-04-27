"""Vector database operations using SQLModel ORM instead of raw SQL."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException
from sqlmodel import Session, select

from models.base import engine
from models.user import User
from models.vector_db import (
    DBTypeEnum,
    EmbeddingModel,
    FaissDB,
    FileUpload,
    PineconeDB,
    VectorDB,
)
from schemas.index_schemas import PineconeSetup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy database path - kept for backward compatibility
DATABASE = "agentX.db"


def ensure_tables_exist():
    """Ensure that all required tables exist in the database"""
    try:
        # This function now just logs a message since SQLModel creates tables
        logger.info("Tables are managed by SQLModel automatically")
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {str(e)}")
        raise


def insert_into_vector_db(user_id: str, index_name: str, db_type: str):
    """Insert a new vector database entry using SQLModel."""
    try:
        with Session(engine) as session:
            # Check if a record with the same user_id and index_name already exists
            statement = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            existing_db = session.exec(statement).first()

            if existing_db:
                raise HTTPException(
                    status_code=400,
                    detail=f"A record with user_id: {user_id} and index_name: {index_name} already exists.",
                )

            # Create new vector DB entry
            new_vector_db = VectorDB(
                user_id=int(user_id), index_name=index_name, db_type=DBTypeEnum(db_type)
            )

            session.add(new_vector_db)
            session.commit()
            session.refresh(new_vector_db)

            logger.info(
                f"Inserted into vector_db: user_id={user_id}, index_name={index_name}, db_type={db_type}"
            )
            return new_vector_db.id

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error inserting into vector_db: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create vector database: {str(e)}"
        )


def insert_into_pinecone_db(
    pinecone_setup: PineconeSetup, user_id: str, index_name: str, embedding: str
):
    """Insert a new Pinecone database entry using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            statement = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(statement).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Create new Pinecone DB entry
            new_pinecone_db = PineconeDB(
                pinecone_api_key=pinecone_setup.pinecone_api_key,
                metric=pinecone_setup.metric,
                cloud=pinecone_setup.cloud,
                region=pinecone_setup.region,
                dimension=pinecone_setup.dimension,
                embedding=EmbeddingModel(embedding),
                vector_db_id=vector_db.id,
            )

            session.add(new_pinecone_db)
            session.commit()

            logger.info(
                f"Inserted into pinecone_db: user_id={user_id}, index_name={index_name}"
            )

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error inserting into pinecone_db: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create Pinecone database: {str(e)}"
        )


def get_data_from_pinecone_db(user_id: str, index_name: str) -> Dict[str, Any]:
    """Get Pinecone database data using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Find the Pinecone DB
            pinecone_stmt = select(PineconeDB).where(
                PineconeDB.vector_db_id == vector_db.id
            )
            pinecone_db = session.exec(pinecone_stmt).first()

            if not pinecone_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"No Pinecone DB found for Vector DB with ID {vector_db.id}.",
                )

            return {
                "pinecone_api_key": pinecone_db.pinecone_api_key,
                "metric": pinecone_db.metric,
                "cloud": pinecone_db.cloud,
                "region": pinecone_db.region,
                "dimension": pinecone_db.dimension,
                "embedding": pinecone_db.embedding.value,
                "index_name": index_name,
                "user_id": user_id,
            }

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error getting data from pinecone_db: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Pinecone database data: {str(e)}"
        )


def insert_into_faiss_db(
    user_id: str, index_name: str, file_name: str, file_path: str, embedding: str
):
    """Insert a new FAISS database entry using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            statement = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(statement).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Check if a FAISS DB already exists
            faiss_stmt = select(FaissDB).where(FaissDB.vector_db_id == vector_db.id)
            existing_faiss = session.exec(faiss_stmt).first()

            if not existing_faiss:
                # Create new FAISS DB entry
                new_faiss_db = FaissDB(
                    embedding=EmbeddingModel(embedding), vector_db_id=vector_db.id
                )
                session.add(new_faiss_db)
                session.commit()
                session.refresh(new_faiss_db)
                faiss_db_id = new_faiss_db.id
            else:
                faiss_db_id = existing_faiss.id

            # Create file upload entry
            file_upload = FileUpload(
                file_name=file_name,
                file_path=file_path,
                user_id=int(user_id),
                faiss_db_id=faiss_db_id,
            )
            session.add(file_upload)
            session.commit()

            logger.info(
                f"Inserted into faiss_db: user_id={user_id}, index_name={index_name}"
            )

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error inserting into faiss_db: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create FAISS database: {str(e)}"
        )


def insert_into_file_uploads(
    user_id: str, index_name: str, file_name: str, file_path: str
):
    """Insert file upload record using SQLModel."""
    # This functionality is now handled in insert_into_faiss_db
    # This function is kept for backward compatibility
    try:
        logger.info(f"File upload is now handled by insert_into_faiss_db")
        insert_into_faiss_db(
            user_id,
            index_name,
            file_name,
            file_path,
            "sentence-transformers/all-mpnet-base-v2",
        )
    except Exception as e:
        logger.error(f"Error inserting into file_uploads: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create file upload: {str(e)}"
        )


def update_file_upload(user_id: str, index_name: str, file_name: str, file_path: str):
    """Update file upload record using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Find the FAISS DB
            faiss_stmt = select(FaissDB).where(FaissDB.vector_db_id == vector_db.id)
            faiss_db = session.exec(faiss_stmt).first()

            if not faiss_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"No FAISS DB found for Vector DB with ID {vector_db.id}.",
                )

            # Find existing file upload
            file_stmt = select(FileUpload).where(
                FileUpload.faiss_db_id == faiss_db.id,
                FileUpload.user_id == int(user_id),
            )
            file_upload = session.exec(file_stmt).first()

            if file_upload:
                # Update existing file upload
                file_upload.file_name = file_name
                file_upload.file_path = file_path
                session.add(file_upload)
                session.commit()
            else:
                # Create new file upload
                new_file_upload = FileUpload(
                    file_name=file_name,
                    file_path=file_path,
                    user_id=int(user_id),
                    faiss_db_id=faiss_db.id,
                )
                session.add(new_file_upload)
                session.commit()

            logger.info(
                f"Updated file_upload: user_id={user_id}, index_name={index_name}"
            )

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error updating file_upload: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update file upload: {str(e)}"
        )


def get_file_from_faiss_db(user_id: str, index_name: str) -> str:
    """Get file path from FAISS database using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Find the FAISS DB
            faiss_stmt = select(FaissDB).where(FaissDB.vector_db_id == vector_db.id)
            faiss_db = session.exec(faiss_stmt).first()

            if not faiss_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"No FAISS DB found for Vector DB with ID {vector_db.id}.",
                )

            # Find file upload
            file_stmt = select(FileUpload).where(
                FileUpload.faiss_db_id == faiss_db.id,
                FileUpload.user_id == int(user_id),
            )
            file_upload = session.exec(file_stmt).first()

            if not file_upload:
                raise HTTPException(
                    status_code=404,
                    detail=f"No file found for FAISS DB with ID {faiss_db.id}.",
                )

            return file_upload.file_path

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error getting file from faiss_db: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file path from FAISS database: {str(e)}",
        )


# Add more refactored functions here, following the same pattern
# For example:
# - get_pinecone_api_index_name_type_db
# - delete_pinecone_index_from_db
# - delete_faiss_index_from_db
# - etc.


def get_pinecone_api_index_name_type_db(
    user_id: str, index_name: str
) -> Dict[str, Any]:
    """Get Pinecone API key and other details using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Find the Pinecone DB
            pinecone_stmt = select(PineconeDB).where(
                PineconeDB.vector_db_id == vector_db.id
            )
            pinecone_db = session.exec(pinecone_stmt).first()

            if not pinecone_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"No Pinecone DB found for Vector DB with ID {vector_db.id}.",
                )

            return {
                "pinecone_api_key": pinecone_db.pinecone_api_key,
                "index_name": index_name,
                "db_type": vector_db.db_type.value,
                "embedding": pinecone_db.embedding.value,
            }

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error getting Pinecone API key: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Pinecone API key: {str(e)}"
        )


def delete_pinecone_index_from_db(user_id: str, index_name: str):
    """Delete Pinecone index from database using SQLModel."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vector DB with user_id: {user_id} and index_name: {index_name} not found.",
                )

            # Cascade delete will handle related tables when vector_db is deleted
            session.delete(vector_db)
            session.commit()

            logger.info(
                f"Deleted index from DB: user_id={user_id}, index_name={index_name}"
            )
            return {"message": f"Index '{index_name}' deleted successfully"}

    except HTTPException as http_err:
        # Re-raise HTTP exceptions
        raise http_err
    except Exception as e:
        logger.error(f"Error deleting Pinecone index: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete Pinecone index: {str(e)}"
        )


def delete_faiss_index_from_db(user_id: str, index_name: str):
    """Delete FAISS index from database using SQLModel."""
    # This is the same as delete_pinecone_index_from_db
    # since we're deleting the vector_db entry which cascades
    return delete_pinecone_index_from_db(user_id, index_name)


def set_agent_index_to_none(user_id: str, index_name: str):
    """Set agent index to None when index is deleted."""
    try:
        with Session(engine) as session:
            # Find the associated vector DB
            vector_db_stmt = select(VectorDB).where(
                VectorDB.user_id == int(user_id), VectorDB.index_name == index_name
            )
            vector_db = session.exec(vector_db_stmt).first()

            if not vector_db:
                logger.warning(
                    f"Vector DB with user_id: {user_id} and index_name: {index_name} not found."
                )
                return

            # Find all agents associated with this vector DB
            agent_stmt = select(Agent).where(Agent.vector_db_id == vector_db.id)
            agents = session.exec(agent_stmt).all()

            # Set vector_db_id to None for each agent
            for agent in agents:
                agent.vector_db_id = None
                session.add(agent)

            session.commit()
            logger.info(
                f"Set agent index to None: user_id={user_id}, index_name={index_name}"
            )

    except Exception as e:
        logger.error(f"Error setting agent index to None: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to set agent index to None: {str(e)}"
        )


def delete_from_vector_db(user_id: str, index_name: str):
    """Delete entry from vector_db table using SQLModel."""
    # This is a legacy function now, as this is handled by delete_pinecone_index_from_db
    # and delete_faiss_index_from_db.
    return delete_pinecone_index_from_db(user_id, index_name)
