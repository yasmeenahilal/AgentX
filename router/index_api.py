import os
from typing import Optional

import database
import rag_app
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from langchain_community.embeddings import HuggingFaceEmbeddings
from schemas.index_schemas import (
    PineconeDeleteIndex,
    PineconeSetup,
    VectorDB,
    get_pinecone_setup,
)
from models import User
from user.auth import get_current_active_user

index_router = APIRouter()


@index_router.post("/insert_data_to_index")
async def insert_data_to_index(
    index_name: str = Form(...),
    embedding: str = Form(default="sentence-transformers/all-mpnet-base-v2"),
    file: UploadFile = File(...),
    vectordb: VectorDB = Form(...),
    pinecone_setup: Optional[PineconeSetup] = Depends(get_pinecone_setup),
    current_user: User = Depends(get_current_active_user)
):
    user_id = str(current_user.id)
    
    try:
        file_extesion = file.filename.split(".")[-1]

        if vectordb == VectorDB.pinecone:
            filename = f"temp_data_A711A.{file_extesion}"
        else:
            filename = f"temp_{file.filename}"

        file_path = f"media/{filename}"
        file_data = await file.read()

        # Attempt to insert data into the vector_db table (track db_type)
        try:
            database.insert_into_vector_db(user_id, index_name, vectordb.value)
        except ValueError as ve:
            # Catch the specific exception raised in insert_into_vector_db
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            # Catch any other exceptions and raise HTTPException with a general error
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        if vectordb == VectorDB.pinecone:
            if not pinecone_setup:
                raise HTTPException(
                    status_code=400, detail="Pinecone setup details are required."
                )

            # Save file to media folder with the fixed name
            with open(file_path, "wb") as buffer:
                buffer.write(file_data)

            # Insert Pinecone configuration into the pinecone_db table
            database.insert_into_pinecone_db(
                pinecone_setup, user_id, index_name, embedding
            )

            # Call function to create Pinecone index (external logic)
            response = rag_app.create_pinecone_index(
                pinecone_setup=pinecone_setup,
                index_name=index_name,
            )
            if response.get("status") != "success":
                raise HTTPException(
                    status_code=400,
                    detail=response.get("message", "Error creating Pinecone index."),
                )

            # Load and split document into chunks
            docs = rag_app.data_splitter(file_path)
            embeddings = HuggingFaceEmbeddings(model_name=embedding)

            # Insert data into Pinecone index (external logic)
            rag_app.insert_data_to_pinecone(
                embeddings=embeddings,
                docs=docs,
                api_key=pinecone_setup.pinecone_api_key,
                index_name=index_name,
            )

            # Remove the temporary file after processing
            os.remove(file_path)

        elif vectordb == VectorDB.faiss:
            # Save file to media folder
            with open(file_path, "wb") as buffer:
                buffer.write(file_data)

            # Insert Faiss-specific data into faiss_db table
            database.insert_into_faiss_db(
                user_id, index_name, filename, file_path, embedding
            )

            # Insert the PDF file info into the file_uploads table
            database.insert_into_file_uploads(user_id, index_name, filename, file_path)

        return {"message": "Data inserted into Index successfully"}

    except HTTPException as he:
        # Handle HTTPExceptions specifically
        raise he
    except Exception as e:
        # Catch any other unhandled exceptions
        raise HTTPException(
            status_code=500, detail=f"Error inserting data into Index: {str(e)}"
        )


@index_router.post("/update_data_in_index")
async def update_data_in_index(
    index_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
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
            response = rag_app.check_pinecone_index(
                pinecone_api_key=pinecone_setup[1],
                index_name=index_name,
            )
            if not response:
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
            rag_app.update_data_in_pinecone(
                embeddings=embeddings,
                docs=docs,
                api_key=pinecone_setup[1],
                index_name=index_name,
            )

        elif index_type == "FAISS":
            # Replace the existing file and update the database
            database.update_pdf_file(
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
    request: PineconeDeleteIndex,
    current_user: User = Depends(get_current_active_user)
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
            pinecone_api_key = database.get_pinecone_api_index_name_type_db(
                request.user_id, request.index_name
            )
            if not pinecone_api_key:
                raise HTTPException(
                    status_code=400, detail="Pinecone API key not found."
                )

            # Delete the Pinecone index
            response = rag_app.delete_pinecone_index(
                pinecone_api_key=pinecone_api_key,
                index_name=request.index_name,
            )
            if response != "Index deleted successfully":
                raise HTTPException(status_code=400, detail=response)

            # Delete the index entry from the database
            database.delete_pinecone_index_from_db(
                request.user_id, request.index_name
            )

        elif index_type == "FAISS":
            # Get the file associated with the index
            file_data = database.get_file_from_faiss_db(
                request.user_id, request.index_name
            )
            if not file_data:
                raise HTTPException(
                    status_code=400, detail="No file associated with this index."
                )

            # Remove the file if it exists
            file_path = file_data[1]
            if os.path.exists(file_path):
                os.remove(file_path)

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
        raise HTTPException(
            status_code=500, detail=f"Error deleting index: {str(e)}"
        )
