import os
import sqlite3

from fastapi import HTTPException

from .database import DATABASE

MEDIA_FOLDER = "./media"


def insert_pdf_file(user_id: str, index_name: str, file_name: str, file_path: str):
    """
    Inserts a new PDF record (file name and file path) into the database.
    """
    try:
        # Validate input parameters
        if not all([user_id, index_name, file_name, file_path]):
            raise HTTPException(
                status_code=400, detail="Invalid input. All parameters are required."
            )

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO file_uploads (user_id, index_name, file_name, file_path)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, index_name, file_name, file_path),
            )
            conn.commit()

        return True

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="File already exists or index/user combination is not unique.",
        )

    except sqlite3.OperationalError as e:
        raise HTTPException(
            status_code=400, detail=f"Database operation failed: {str(e)}"
        )

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected database error: {str(e)}"
        )


def update_pdf_file(user_id: str, index_name: str, file_name: str, file_path: str):
    """
    Updates an existing PDF record (file name and file path) in the database.
    1. Removes the old file from the media directory.
    2. Updates the database with the new file path.
    """
    try:
        # Validate input parameters
        if not all([user_id, index_name, file_name, file_path]):
            raise HTTPException(
                status_code=400, detail="Invalid input. All parameters are required."
            )

        # Get the old file path from the database
        old_file_path = get_file_path_and_name(user_id, index_name)

        # Check if the old file exists in the media folder
        if os.path.exists(old_file_path):
            pass
            # Remove the old file from the media folder
            # os.remove(old_file_path)
        else:
            raise HTTPException(
                status_code=404, detail="Old file not found in the media folder."
            )

        # Now move the new file to the media folder
        new_file_name = os.path.basename(
            file_path
        )  # Get the file name from the new file path
        new_file_dest = os.path.join(MEDIA_FOLDER, new_file_name)

        # Update the database with the new file path
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Check if the file exists in the database before updating
            cursor.execute(
                """
                SELECT * FROM faiss_db WHERE user_id = ? AND index_name = ?
            """,
                (user_id, index_name),
            )

            file_record = cursor.fetchone()

            if not file_record:
                raise HTTPException(
                    status_code=404,
                    detail="File not found for the given user, index, and file name.",
                )

            # Update the file record with the new file path
            # cursor.execute("""
            #     UPDATE file_uploads
            #     SET file_path = ?
            #     WHERE user_id = ? AND index_name = ? AND file_name = ?
            # """, (new_file_dest, user_id, index_name, file_name))
            # conn.commit()
            # #  with sqlite3.connect(DATABASE) as conn:
            # cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE faiss_db
                SET file_path = ?, file_name = ?
                WHERE user_id = ? AND index_name = ?
            """,
                (new_file_dest, file_name, user_id, index_name),
            )
            conn.commit()

        return True

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File operation failed: {str(e)}")
    except sqlite3.OperationalError as e:
        raise HTTPException(
            status_code=400, detail=f"Database operation failed: {str(e)}"
        )
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def get_file_path_and_name(user_id: str, index_name: str):
    """
    Retrieves the file path for all files uploaded by a specific user and index name.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT file_path
                FROM faiss_db
                WHERE user_id = ? AND index_name = ?
            """,
                (user_id, index_name),
            )
            results = cursor.fetchone()

            if not results:
                raise HTTPException(
                    status_code=404,
                    detail="No files found for the given user and index.",
                )

            # Return only the file paths
            # return [result[0] for result in results]
            return results[0]  # Return only the file path

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected database error: {str(e)}"
        )


def delete_pdf_file(user_id: str, index_name: str):
    """
    Deletes a PDF record from the database and removes the associated file from the media folder.

    Args:
        user_id (str): The user ID associated with the file.
        index_name (str): The index name associated with the file.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    try:
        # Validate input parameters
        if not all([user_id, index_name]):
            raise HTTPException(
                status_code=400,
                detail="Invalid input. Both user_id and index_name are required.",
            )

        # Get the file path from the database
        file_path = get_file_path_and_name(user_id, index_name)

        # Check if the file exists in the media folder
        if os.path.exists(file_path):
            # Remove the file from the media folder
            os.remove(file_path)
        else:
            raise HTTPException(
                status_code=404, detail="File not found in the media folder."
            )

        # Delete the record from the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM file_uploads WHERE user_id = ? AND index_name = ?;
            """,
                (user_id, index_name),
            )
            conn.commit()

            # Check if any record was deleted
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No file found for the given user and index.",
                )

        return True

    except sqlite3.OperationalError as e:
        raise HTTPException(
            status_code=400, detail=f"Database operation failed: {str(e)}"
        )
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
