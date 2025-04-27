# Import necessary modules
import logging
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from langchain import PromptTemplate
from langchain.document_loaders import TextLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFaceHub
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Pinecone as pns
from pinecone import Pinecone, PineconeException, ServerlessSpec

import schemas
import schemas.index_schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_pinecone_index(
    pinecone_setup: schemas.index_schemas.PineconeSetup, index_name
):
    try:
        api_key = pinecone_setup.pinecone_api_key
        index_name = index_name
        metric = pinecone_setup.metric
        cloud = pinecone_setup.cloud  # Use the string value of enum
        region = pinecone_setup.region
        dimension = pinecone_setup.dimension

        pinecone_client = Pinecone(api_key=api_key)
        logger.info("Connection to Pinecone established successfully.")

        if index_name not in pinecone_client.list_indexes().names():
            spec = ServerlessSpec(cloud=cloud, region=region)
            pinecone_client.create_index(
                name=index_name, dimension=dimension, metric=metric, spec=spec
            )
            logger.info(f"Index '{index_name}' created successfully.")
            return {
                "status": "success",
                "message": f"Index '{index_name}' created successfully.",
            }
        else:
            logger.warning(f"Index '{index_name}' already exists.")
            return {
                "status": "warning",
                "message": f"Index '{index_name}' already exists.",
            }

    except Exception as e:
        # Extract the real error message from the exception
        error_message = None
        if hasattr(e, "response") and hasattr(e.response, "json"):
            try:
                error_message = (
                    e.response.json().get("error", {}).get("message", str(e))
                )
            except Exception:
                error_message = str(e)  # Fallback to raw exception message
        else:
            error_message = str(e)  # Default fallback

        logger.error(f"An error occurred while creating the index: {error_message}")
        return {"status": "error", "message": error_message}


def check_pinecone_index(pinecone_api_key: str, index_name: str):
    try:
        # Initialize Pinecone client
        pinecone_client = Pinecone(api_key=pinecone_api_key)

        # List indexes
        data = pinecone_client.list_indexes()

        # Extract the list of index names from the 'data'
        existing_indexes = [index["name"] for index in data]

        # Check if the desired index exists
        if index_name in existing_indexes:
            logger.info(f"Index '{index_name}' exists in Pinecone.")
            return True
        else:
            logger.warning(f"Index '{index_name}' does not exist in Pinecone.")
            return False

    except PineconeException as e:
        # Handle any Pinecone-specific exception (e.g., API issues, bad key)
        logger.error(f"Pinecone error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Pinecone error: {str(e)}")

    except Exception as e:
        # Handle general exceptions (e.g., network issues, unexpected errors)
        logger.exception(
            "An unexpected error occurred while checking the Pinecone index."
        )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
