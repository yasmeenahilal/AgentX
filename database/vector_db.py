import sqlite3

from fastapi import HTTPException
from schemas.index_schemas import PineconeSetup

from .database import DATABASE


# Custom exception class for database operations
class DatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def insert_into_vector_db(user_id: str, index_name: str, db_type: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Check if a record with the same user_id and index_name already exists
            cursor.execute(
                """
            SELECT 1 FROM vector_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )

            if cursor.fetchone():  # If a record is found, raise an error
                raise DatabaseError(
                    f"A record with user_id: {user_id} and index_name: {index_name} already exists."
                )

            # If no conflict, insert the new record
            cursor.execute(
                """
            INSERT INTO vector_db (user_id, index_name, db_type) 
            VALUES (?, ?, ?);
            """,
                (user_id, index_name, db_type),
            )

            conn.commit()

    except sqlite3.DatabaseError as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


def insert_into_pinecone_db(
    pinecone_setup: PineconeSetup, user_id: str, index_name: str, embedding: str
):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT INTO pinecone_db (pinecone_api_key, metric, cloud, region, dimension, index_name, user_id, embedding) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pinecone_setup.pinecone_api_key,
                    pinecone_setup.metric,
                    pinecone_setup.cloud,
                    pinecone_setup.region,
                    pinecone_setup.dimension,
                    index_name,
                    user_id,
                    embedding,
                ),
            )
            conn.commit()
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while inserting into Pinecone DB: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while inserting into Pinecone DB: {str(e)}",
        )


def get_data_from_pinecone_db(user_id: str, index_name: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            SELECT * FROM pinecone_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            result = cursor.fetchone()

            if result is None:
                raise DatabaseError(
                    f"No data found for user_id: {user_id} and index_name: {index_name} in Pinecone DB."
                )
            return result
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching from Pinecone DB: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching from Pinecone DB: {str(e)}",
        )


def insert_into_faiss_db(
    user_id: str, index_name: str, file_name: str, file_path: str, embedding: str
):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT INTO faiss_db (index_name, user_id, file_name, file_path, embedding)
            VALUES (?, ?, ?, ?, ?)
            """,
                (index_name, user_id, file_name, file_path, embedding),
            )
            conn.commit()
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while inserting into Faiss DB: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while inserting into Faiss DB: {str(e)}",
        )


def insert_into_file_uploads(
    user_id: str, index_name: str, file_name: str, file_path: str
):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT INTO file_uploads (user_id, index_name, file_name, file_path) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, index_name) DO NOTHING;
            """,
                (user_id, index_name, file_name, file_path),
            )
            conn.commit()
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while inserting into file uploads: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while inserting into file uploads: {str(e)}",
        )


def update_file_upload(user_id: str, index_name: str, file_name: str, file_path: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            UPDATE file_uploads
            SET file_name = ?, file_path = ?
            WHERE user_id = ? AND index_name = ?;
            """,
                (file_name, file_path, user_id, index_name),
            )
            conn.commit()
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while updating file upload: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while updating file upload: {str(e)}",
        )


def get_file_from_faiss_db(user_id: str, index_name: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            SELECT file_path FROM faiss_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            result = cursor.fetchone()

            if result is None:
                raise DatabaseError(
                    f"No file found for user_id: {user_id} and index_name: {index_name} in Faiss DB."
                )
            return result[0]
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching file from Faiss DB: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching file from Faiss DB: {str(e)}",
        )


def get_index_name_type_db(user_id: str, index_name: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT db_type FROM vector_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            result = cursor.fetchone()

            if result is None:
                raise DatabaseError(
                    f"No db_type found for user_id: {user_id} and index_name: {index_name}."
                )
            return result[0]
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching db_type: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching db_type: {str(e)}",
        )


def get_pinecone_api_index_name_type_db(user_id: str, index_name: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT pinecone_api_key FROM pinecone_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            result = cursor.fetchone()

            if result is None:
                raise DatabaseError(
                    f"No Pinecone API key found for user_id: {user_id} and index_name: {index_name}."
                )
            return result[0]
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching Pinecone API key: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching Pinecone API key: {str(e)}",
        )


def delete_pinecone_index_from_db(user_id: str, index_name: str):
    try:
        # delete_from_vector_db(user_id, index_name)
        set_agent_index_to_none(user_id, index_name)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

        # Check if the record exists for the given user_id and index_name
        cursor.execute(
            """
        SELECT 1 FROM pinecone_db WHERE user_id = ? AND index_name = ?;
        """,
            (user_id, index_name),
        )
        if cursor.fetchone() is None:
            raise DatabaseError(
                f"No Pinecone index found for user_id: {user_id} and index_name: {index_name}."
            )

        # Delete the record
        cursor.execute(
            """
        DELETE FROM pinecone_db WHERE user_id = ? AND index_name = ?;
        """,
            (user_id, index_name),
        )
        conn.commit()

        return True
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting Pinecone index: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while deleting Pinecone index: {str(e)}",
        )


def delete_faiss_index_from_db(user_id: str, index_name: str):
    try:
        # delete_from_vector_db(user_id, index_name)
        set_agent_index_to_none(user_id, index_name)
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Check if the record exists for the given user_id and index_name
            cursor.execute(
                """
            SELECT 1 FROM faiss_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            if cursor.fetchone() is None:
                raise DatabaseError(
                    f"No Faiss index found for user_id: {user_id} and index_name: {index_name}."
                )

            # Delete the record
            cursor.execute(
                """
            DELETE FROM faiss_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            conn.commit()

            return True
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting Faiss index: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while deleting Faiss index: {str(e)}",
        )


def set_agent_index_to_none(user_id: str, index_name: str):
    try:
        delete_from_vector_db(user_id, index_name)
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

        # Update the agent record for the given user_id to set index_name to None
        cursor.execute(
            """
        UPDATE multi_agent
        SET index_name = NULL
        WHERE user_id = ? AND index_name = ?;
        """,
            (user_id, index_name),
        )
        conn.commit()
        return True
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while updating agent index: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while updating agent index: {str(e)}",
        )


def delete_from_vector_db(user_id: str, index_name: str):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Check if the record exists for the given user_id and index_name
            cursor.execute(
                """
            SELECT 1 FROM vector_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            if cursor.fetchone() is None:
                raise DatabaseError(
                    f"No record found for user_id: {user_id} and index_name: {index_name} in vector_db."
                )

            # Delete the record
            cursor.execute(
                """
            DELETE FROM vector_db WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            conn.commit()

            return True
    except sqlite3.DatabaseError as db_error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting record from vector_db: {str(db_error)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while deleting record from vector_db: {str(e)}",
        )
