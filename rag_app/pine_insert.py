import logging

from fastapi import HTTPException
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, PineconeException

import database

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
            # Get content and existing metadata from the Document object
            doc_content = doc.page_content
            doc_metadata = doc.metadata
            logger.debug(
                f"Processing document ID {doc_id}, source: {doc_metadata.get('source', 'N/A')}"
            )

            # Generate embeddings for the document content
            # embed_documents expects a list of strings
            embedding = embeddings.embed_documents([doc_content])
            logger.debug(
                f"Embedding shape for doc {doc_id}: {len(embedding[0])} dimensions"
            )

            # Optionally: Validate embedding dimension (Ensure 768 matches your index setting)
            # This value might need to come from index config instead of being hardcoded
            expected_dimension = (
                768  # Example: Get this from config or index description if possible
            )
            if len(embedding[0]) != expected_dimension:
                raise ValueError(
                    f"Embedding for document {doc_id} has dimension {len(embedding[0])}, but index expects {expected_dimension}"
                )

            # Prepare metadata: MUST include 'text' key for LangChain retrieval
            metadata = {
                "text": doc_content,  # Store the original text chunk
                **doc_metadata,  # Include original metadata (like source file)
            }

            # Prepare data for insertion
            # Ensure ID is unique and suitable for Pinecone (string)
            # Using doc_id (index) might cause collisions if run multiple times without clearing
            # Consider using a hash of content or a UUID if doc_id isn't stable/unique
            vector_id = f"{index_name}_{doc_metadata.get('source', 'unknown')}_{doc_id}"  # Example of a potentially more unique ID

            data_to_insert.append(
                {"id": vector_id, "values": embedding[0], "metadata": metadata}
            )

        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=api_key)
        index = pinecone_client.Index(index_name)

        # Insert data into the Pinecone index
        logger.info(
            f"Upserting {len(data_to_insert)} vectors into index '{index_name}'"
        )
        index.upsert(vectors=data_to_insert)
        logger.info("Data successfully inserted into Pinecone index.")

    except Exception as e:
        logger.error(f"An error occurred while inserting data into Pinecone: {e}")
        # Consider re-raising a more specific exception if needed
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
        pinecone_data = database.get_pinecone_api_index_name_type_db(
            user_id, index_name
        )

        if not pinecone_data or "pinecone_api_key" not in pinecone_data:
            raise HTTPException(status_code=400, detail="Pinecone API key not found.")

        pinecone_api_key = pinecone_data["pinecone_api_key"]

        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=pinecone_api_key)

        # List all existing indexes
        all_indexes = pinecone_client.list_indexes()
        index_names = [index["name"] for index in all_indexes]

        # Check if the index exists
        if index_name not in index_names:
            logger.warning(
                f"Index '{index_name}' not found in Pinecone, but proceeding with local deletion."
            )
            return True

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
