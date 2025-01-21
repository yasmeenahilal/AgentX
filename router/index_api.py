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

index_router = APIRouter()


@index_router.post("/insert_data_to_index")
async def insert_data_to_index(
    user_id: str = Form(...),
    index_name: str = Form(...),
    embedding: str = Form(default="sentence-transformers/all-mpnet-base-v2"),
    file: UploadFile = File(...),
    vectordb: VectorDB = Form(...),
    pinecone_setup: Optional[PineconeSetup] = Depends(get_pinecone_setup),
):
    # Print the data received
    print("\n\n\nNEWwwww")
    print(f"user_id: {user_id}")
    print(f"index_name: {index_name}")
    print(f"embedding: {embedding}")
    print(f"file filename: {file.filename}, content type: {file.content_type}")
    print(f"vectordb: {vectordb}")
    print(f"pinecone_setup: {pinecone_setup}")
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
    user_id: str = Form(...),
    index_name: str = Form(...),
    file: UploadFile = File(...),
):
    """
    API endpoint for updating data in an Index.

    Parameters:
    - user_id: User ID
    - index_name: Name of the Index
    - file: Uploaded file containing data to be updated
    """
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
            # pass
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
async def delete_index_api(request: PineconeDeleteIndex):
    try:
        index_name = request.index_name
        user_id = request.user_id
        # Determine the index type from the database (e.g., Pinecone or Faiss)
        index_type = database.get_index_name_type_db(
            user_id, index_name
        )  # Function to retrieve the index type from DB
        if index_type == "Pinecone":
            pinecone_deleted = rag_app.delete_pinecone_index(user_id, index_name)
            if pinecone_deleted:
                database.delete_pinecone_index_from_db(user_id, index_name)

        elif index_type == "FAISS":
            database.delete_pdf_file(user_id, index_name)
            database.delete_faiss_index_from_db(user_id, index_name)

        return {"message": f"Index '{index_name}' deleted successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting Index: {str(e)}")
