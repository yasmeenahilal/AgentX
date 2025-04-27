import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from langchain_community.embeddings import HuggingFaceEmbeddings

import database
import rag_app
from models import User
from models.vector_db import EmbeddingModel
from schemas.index_schemas import (
    PineconeDeleteIndex,
    PineconeSetup,
    VectorDB,
    get_pinecone_setup,
)
from user.auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

index_router = APIRouter()


@index_router.post("/insert_data_to_index")
async def insert_data_to_index(
    index_name: str = Form(...),
    embedding: str = Form(default="sentence-transformers/all-mpnet-base-v2"),
    file: UploadFile = File(...),
    vectordb: VectorDB = Form(...),
    pinecone_setup: Optional[PineconeSetup] = Depends(get_pinecone_setup),
    current_user: User = Depends(get_current_active_user),
):
    user_id = str(current_user.id)

    try:
        # Validate the file extension
        file_extension = file.filename.split(".")[-1].lower()
        allowed_extensions = ["pdf", "txt", "md"]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Please upload a file with one of these extensions: {', '.join(allowed_extensions)}",
            )

        # Generate a filename
        if vectordb == VectorDB.pinecone:
            filename = f"temp_data_A711A.{file_extension}"
        else:
            filename = f"temp_{file.filename}"

        file_path = f"media/{filename}"
        file_data = await file.read()

        # Check if media directory exists, create if not
        os.makedirs("media", exist_ok=True)

        # Validate embedding model
        valid_embeddings = [e.value for e in EmbeddingModel]
        if embedding not in valid_embeddings:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid embedding model: '{embedding}'. Please choose from: {', '.join(valid_embeddings)}",
            )

        # Attempt to insert data into the vector_db table (track db_type)
        try:
            database.insert_into_vector_db(user_id, index_name, vectordb.value)
        except ValueError as ve:
            # Catch the specific exception raised in insert_into_vector_db
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            # Catch any other exceptions and raise HTTPException with a general error
            if "already exists" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=f"A record with user_id: {user_id} and index_name: {index_name} already exists.",
                )
            else:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        if vectordb == VectorDB.pinecone:
            if not pinecone_setup:
                raise HTTPException(
                    status_code=400, detail="Pinecone setup details are required."
                )

            # Save file to media folder with the fixed name
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(file_data)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to save file: {str(e)}"
                )

            # Insert Pinecone configuration into the pinecone_db table
            try:
                database.insert_into_pinecone_db(
                    pinecone_setup, user_id, index_name, embedding
                )
            except Exception as e:
                # Clean up file if there's an error
                if os.path.exists(file_path):
                    os.remove(file_path)
                if "EmbeddingModel" in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid embedding model: '{embedding}'. Please choose from the supported models.",
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create Pinecone database configuration: {str(e)}",
                    )

            # Call function to create Pinecone index (external logic)
            try:
                response = rag_app.create_pinecone_index(
                    pinecone_setup=pinecone_setup,
                    index_name=index_name,
                )
                if response.get("status") != "success":
                    raise HTTPException(
                        status_code=400,
                        detail=response.get(
                            "message", "Error creating Pinecone index."
                        ),
                    )
            except HTTPException as he:
                # Clean up any existing entries if index creation fails
                try:
                    database.delete_from_vector_db(user_id, index_name)
                except:
                    pass
                raise he

            # Load and split document into chunks
            try:
                docs = rag_app.data_splitter(file_path)
                embeddings = HuggingFaceEmbeddings(model_name=embedding)

                # Insert data into Pinecone index (external logic)
                rag_app.insert_data_to_pinecone(
                    embeddings=embeddings,
                    docs=docs,
                    api_key=pinecone_setup.pinecone_api_key,
                    index_name=index_name,
                )
            except Exception as e:
                # Clean up any existing entries if data insertion fails
                try:
                    database.delete_from_vector_db(user_id, index_name)
                except:
                    pass

                # Provide user-friendly error messages for common issues
                if "EmbeddingModel" in str(e) or "is not a valid" in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid embedding model: '{embedding}'. Please choose from the supported models.",
                    )
                elif "dimension" in str(e).lower():
                    raise HTTPException(
                        status_code=400,
                        detail="Dimension mismatch error. The embedding model dimensions don't match the vector database configuration.",
                    )
                else:
                    raise HTTPException(
                        status_code=500, detail=f"Failed to process document: {str(e)}"
                    )

            # Remove the temporary file after processing
            if os.path.exists(file_path):
                os.remove(file_path)

        elif vectordb == VectorDB.faiss:
            # Save file to media folder
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(file_data)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to save file: {str(e)}"
                )

            # Insert Faiss-specific data into faiss_db table
            try:
                database.insert_into_faiss_db(
                    user_id, index_name, filename, file_path, embedding
                )
            except Exception as e:
                # Clean up file if there's an error
                if os.path.exists(file_path):
                    os.remove(file_path)

                if "EmbeddingModel" in str(e) or "is not a valid" in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to create FAISS database: '{embedding}' is not a valid embedding model",
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create FAISS database: {str(e)}",
                    )

        return {"message": "Data inserted into Index successfully"}

    except HTTPException as he:
        # Handle HTTPExceptions specifically - these already have user-friendly messages
        raise he
    except Exception as e:
        # Provide a generic but still informative error message
        error_message = str(e)
        if "EmbeddingModel" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid embedding model. Please choose a valid embedding model.",
            )
        elif "already exists" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"An index with this name already exists for your account. Please use a different name.",
            )
        else:
            # Catch any other unhandled exceptions with a generic message
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request. Please check your inputs and try again.",
            )


@index_router.post("/update_data_in_index")
async def update_data_in_index(
    index_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    API endpoint for updating data in an Index.

    Parameters:
    - index_name: Name of the Index
    - file: Uploaded file containing data to be updated
    """
    user_id = str(current_user.id)

    try:
        # Save the uploaded file
        filename = f"temp_{file.filename}"
        file_path = f"media/{filename}"
        file_data = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(file_data)

        # Determine the index type from the database (e.g., Pinecone or Faiss)
        index_type = database.get_index_name_type_db(
            user_id, index_name
        )  # Function to retrieve the index type from DB
        if index_type == "Pinecone":
            # Retrieve Pinecone setup details from the database
            pinecone_setup = database.get_data_from_pinecone_db(
                user_id, index_name
            )  # Fetch Pinecone setup
            if not pinecone_setup:
                raise HTTPException(
                    status_code=400, detail="Pinecone setup details are missing."
                )

            # Ensure the Pinecone index exists
            index_exists = rag_app.check_pinecone_index(
                pinecone_api_key=pinecone_setup["pinecone_api_key"],
                index_name=index_name,
            )
            if not index_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pinecone index '{index_name}' does not exist.",
                )

            # Load and split the document into chunks
            docs = rag_app.data_splitter(file_path)
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2"
            )

            # Update data in Pinecone
            try:
                rag_app.update_data_in_pinecone(
                    embeddings=embeddings,
                    docs=docs,
                    api_key=pinecone_setup["pinecone_api_key"],
                    index_name=index_name,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error updating data in Pinecone: {str(e)}"
                )

        elif index_type == "FAISS":
            # Replace the existing file and update the database
            database.update_file_upload(
                user_id=user_id,
                index_name=index_name,
                file_name=filename,
                file_path=file_path,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported index type.",
            )

        return {"message": "Data updated in Index successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating data in Index: {str(e)}"
        )


@index_router.delete("/delete_index")
async def delete_index_api(
    request: PineconeDeleteIndex, current_user: User = Depends(get_current_active_user)
):
    """
    API endpoint for deleting an Index.

    Parameters:
    - request: A PineconeDeleteIndex object containing:
      - user_id: User ID
      - index_name: Name of the Index to delete
    """
    # Override the user_id in the request with the current authenticated user
    request.user_id = str(current_user.id)

    try:
        # Get the index type from the database
        index_type = database.get_index_name_type_db(
            request.user_id, request.index_name
        )

        if index_type == "Pinecone":
            # Get Pinecone API key from the database
            pinecone_data = database.get_pinecone_api_index_name_type_db(
                request.user_id, request.index_name
            )
            if not pinecone_data:
                raise HTTPException(
                    status_code=400, detail="Pinecone API key not found."
                )

            # Delete the Pinecone index
            try:
                # Extract the Pinecone API key from the retrieved data
                pinecone_api_key = pinecone_data.get("pinecone_api_key")
                if not pinecone_api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid Pinecone API key configuration.",
                    )

                # Call the deletion function with the correct parameters
                success = rag_app.delete_pinecone_index(
                    user_id=request.user_id, index_name=request.index_name
                )
                if not success:
                    raise HTTPException(
                        status_code=400, detail="Failed to delete Pinecone index."
                    )
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error deleting Pinecone index: {str(e)}"
                )

            # Delete the index entry from the database
            database.delete_pinecone_index_from_db(request.user_id, request.index_name)

        elif index_type == "FAISS":
            # Get the file associated with the index
            try:
                file_path = database.get_file_from_faiss_db(
                    request.user_id, request.index_name
                )
                if not file_path:
                    raise HTTPException(
                        status_code=400, detail="No file associated with this index."
                    )

                # Remove the file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file at path: {file_path}")
                else:
                    logger.warning(f"File not found at path: {file_path}")
            except HTTPException as he:
                raise he
            except Exception as e:
                logger.warning(f"Error accessing or deleting file: {str(e)}")
                # Continue with database deletion even if file removal fails

            # Delete the index entry from the database
            database.delete_faiss_index_from_db(request.user_id, request.index_name)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported index type.",
            )

        # Set agent index to none if this index was being used by any agent
        database.set_agent_index_to_none(request.user_id, request.index_name)

        return {"message": "Index deleted successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")
