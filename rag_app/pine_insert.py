import logging

import database
from fastapi import HTTPException
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, PineconeException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def insert_data_to_pinecone(embeddings, docs, api_key, index_name):
    """
    Inserts data into a Pinecone index.

    Parameters:
    - embeddings: HuggingFaceEmbeddings object for generating embeddings
    - docs: List of documents to be inserted
    - api_key: Pinecone API key
    - index_name: Name of the Pinecone index
    """
    logger.info("Starting data insertion into Pinecone index...")
    try:
        data_to_insert = []
        for doc_id, doc in enumerate(docs):
            logger.debug(f"Processing document ID {doc_id}: {doc}")

            # Convert document text to string (if not already)
            doc = [str(part) for part in doc]

            # Generate embeddings for the document
            embedding = embeddings.embed_documents(doc)
            logger.debug(
                f"Embedding shape for doc {doc_id}: {len(embedding[0])} dimensions"
            )

            # Validate embedding dimension
            if len(embedding[0]) != 768:
                raise ValueError(
                    f"Embedding for document {doc_id} has invalid dimension: {len(embedding[0])}"
                )

            # Add metadata for each vector
            metadata = {"source": f"doc_{doc_id}"}

            # Prepare data for insertion
            data_to_insert.append(
                {"id": str(doc_id), "values": embedding[0], "metadata": metadata}
            )

        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=api_key)
        index = pinecone_client.Index(index_name)

        # Insert data into the Pinecone index
        index.upsert(vectors=data_to_insert)
        logger.info("Data successfully inserted into Pinecone index.")

    except Exception as e:
        logger.error(f"An error occurred while inserting data into Pinecone: {e}")
        raise


def update_data_in_pinecone(
    embeddings: HuggingFaceEmbeddings, docs: list, api_key: str, index_name: str
):
    """
    Updates data in a Pinecone index by replacing existing vectors with new ones.

    Parameters:
    - embeddings: HuggingFaceEmbeddings object for generating embeddings
    - docs: List of documents to update
    - api_key: Pinecone API key
    - index_name: Name of the Pinecone index
    """
    logger.info("Starting data update in Pinecone index...")
    try:
        data_to_update = []
        for doc_id, doc in enumerate(docs):
            logger.debug(f"Processing document ID {doc_id}: {doc}")

            # Convert document text to string
            doc = [str(part) for part in doc]

            # Generate embeddings
            embedding = embeddings.embed_documents(doc)
            logger.debug(
                f"Embedding shape for doc {doc_id}: {len(embedding[0])} dimensions"
            )

            # Validate embedding dimension
            if len(embedding[0]) != 768:
                raise ValueError(
                    f"Embedding for document {doc_id} has invalid dimension: {len(embedding[0])}"
                )

            # Add metadata
            metadata = {"source": f"doc_{doc_id}"}

            # Prepare data for update
            data_to_update.append(
                {"id": str(doc_id), "values": embedding[0], "metadata": metadata}
            )

        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=api_key)
        index = pinecone_client.Index(index_name)

        # Update data in Pinecone index
        index.upsert(vectors=data_to_update)
        logger.info("Data successfully updated in Pinecone index.")

    except Exception as e:
        logger.error(f"An error occurred while updating data in Pinecone: {e}")
        raise


def delete_pinecone_index(user_id: str, index_name: str) -> bool:
    """
    Deletes a Pinecone index.

    Parameters:
    - user_id: User identifier to retrieve API key
    - index_name: Name of the Pinecone index to delete

    Returns:
    - bool: True if deletion is successful, otherwise raises an exception.
    """
    logger.info(f"Attempting to delete Pinecone index: {index_name}")
    try:
        # Retrieve Pinecone API key
        pinecone_api_key = database.get_pinecone_api_index_name_type_db(
            user_id, index_name
        )

        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=pinecone_api_key)

        # List all existing indexes
        all_indexes = pinecone_client.list_indexes()
        index_names = [index["name"] for index in all_indexes]

        # Check if the index exists
        if index_name not in index_names:
            raise HTTPException(
                status_code=404, detail=f"Index '{index_name}' not found."
            )

        # Delete the index
        pinecone_client.delete_index(index_name)
        logger.info(f"Index '{index_name}' deleted successfully.")
        return True

    except PineconeException as e:
        logger.error(f"Pinecone error occurred: {e}")
        raise HTTPException(status_code=400, detail=f"Pinecone error: {str(e)}")

    except Exception as e:
        logger.exception(
            f"An unexpected error occurred while deleting Pinecone index: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
