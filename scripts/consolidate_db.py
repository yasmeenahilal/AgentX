#!/usr/bin/env python
"""
Database migration script to consolidate duplicate tables.

This script migrates data from legacy tables (vector_db, pinecone_db, faiss_db, file_uploads)
to their new SQLModel-based tables (vectordb, pineconedb, faissdb, fileupload).
"""
import logging
import os
import sqlite3
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing project modules
sys.path.append(str(Path(__file__).parent.parent))

# Import SQLModel models
from sqlmodel import Session

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

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "agentX.db"


def get_sqlite_connection():
    """Create a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to SQLite: {e}")
        raise


def check_duplicate_tables():
    """Check if legacy tables exist and have data."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]

    # Define pairs of old and new tables
    table_pairs = [
        ("vector_db", "vectordb"),
        ("pinecone_db", "pineconedb"),
        ("faiss_db", "faissdb"),
        ("file_uploads", "fileupload"),
    ]

    legacy_tables_exist = False
    for old_table, new_table in table_pairs:
        if old_table in tables:
            # Check if the old table has data
            cursor.execute(f"SELECT COUNT(*) as count FROM {old_table}")
            count = cursor.fetchone()["count"]
            if count > 0:
                legacy_tables_exist = True
                logger.info(f"Legacy table {old_table} exists with {count} rows")

    conn.close()
    return legacy_tables_exist


def get_or_create_user(session, user_id_str):
    """Get or create a user record for the given user ID."""
    # Try to convert string user_id to int if possible
    try:
        user_id = int(user_id_str)
        user = session.get(User, user_id)
        if user:
            return user.id
    except (ValueError, TypeError):
        pass

    # If conversion or lookup fails, create a placeholder user
    username = f"migrated_user_{user_id_str}"
    email = f"{username}@example.com"

    # Check if this username already exists
    from sqlmodel import select

    statement = select(User).where(User.username == username)
    existing_user = session.exec(statement).first()

    if existing_user:
        return existing_user.id

    # Create a new user
    new_user = User(
        username=username,
        email=email,
        hashed_password="migrated_placeholder_hash",  # This user won't be able to log in
        is_active=False,  # Mark as inactive to prevent login attempts
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user.id


def migrate_vector_db():
    """Migrate data from vector_db to vectordb."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Check if vector_db has data
    cursor.execute("SELECT COUNT(*) as count FROM vector_db")
    count = cursor.fetchone()["count"]

    if count == 0:
        logger.info("No data in vector_db to migrate")
        conn.close()
        return

    logger.info(f"Migrating {count} records from vector_db to vectordb")

    # Get all records from vector_db
    cursor.execute("SELECT * FROM vector_db")
    vector_dbs = cursor.fetchall()

    with Session(engine) as session:
        for vdb in vector_dbs:
            # Check if this record already exists in vectordb
            from sqlmodel import select

            user_id = get_or_create_user(session, vdb["user_id"])

            statement = select(VectorDB).where(
                VectorDB.user_id == user_id, VectorDB.index_name == vdb["index_name"]
            )
            existing = session.exec(statement).first()

            if existing:
                logger.info(
                    f"Vector DB {vdb['index_name']} for user {vdb['user_id']} already exists in new table"
                )
                continue

            # Create new vectordb record
            new_vdb = VectorDB(
                index_name=vdb["index_name"],
                db_type=DBTypeEnum(vdb["db_type"]),
                user_id=user_id,
            )
            session.add(new_vdb)
            session.commit()
            session.refresh(new_vdb)

            logger.info(
                f"Migrated vector_db record: {vdb['index_name']} for user {vdb['user_id']}"
            )

    conn.close()


def migrate_pinecone_db():
    """Migrate data from pinecone_db to pineconedb."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Check if pinecone_db has data
    cursor.execute("SELECT COUNT(*) as count FROM pinecone_db")
    count = cursor.fetchone()["count"]

    if count == 0:
        logger.info("No data in pinecone_db to migrate")
        conn.close()
        return

    logger.info(f"Migrating {count} records from pinecone_db to pineconedb")

    # Get all records from pinecone_db
    cursor.execute("SELECT * FROM pinecone_db")
    pinecone_dbs = cursor.fetchall()

    with Session(engine) as session:
        for pdb in pinecone_dbs:
            # Find the corresponding vectordb record
            from sqlmodel import select

            user_id = get_or_create_user(session, pdb["user_id"])

            statement = select(VectorDB).where(
                VectorDB.user_id == user_id,
                VectorDB.index_name == pdb["index_name"],
                VectorDB.db_type == DBTypeEnum.pinecone,
            )
            vector_db = session.exec(statement).first()

            if not vector_db:
                logger.warning(
                    f"No matching vectordb found for pinecone_db {pdb['index_name']}"
                )
                continue

            # Check if this record already exists in pineconedb
            statement = select(PineconeDB).where(
                PineconeDB.vector_db_id == vector_db.id
            )
            existing = session.exec(statement).first()

            if existing:
                logger.info(
                    f"Pinecone DB for index {pdb['index_name']} already exists in new table"
                )
                continue

            # Create new pineconedb record
            embedding_model = EmbeddingModel.sentence_transformers
            if pdb["embedding"] in [e.value for e in EmbeddingModel]:
                embedding_model = EmbeddingModel(pdb["embedding"])

            new_pdb = PineconeDB(
                pinecone_api_key=pdb["pinecone_api_key"],
                metric=pdb["metric"] or "cosine",
                cloud=pdb["cloud"] or "aws",
                region=pdb["region"] or "us-west-2",
                dimension=pdb["dimension"] or 768,
                embedding=embedding_model,
                vector_db_id=vector_db.id,
            )
            session.add(new_pdb)
            session.commit()

            logger.info(f"Migrated pinecone_db record for index {pdb['index_name']}")

    conn.close()


def migrate_faiss_db():
    """Migrate data from faiss_db to faissdb."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Check if faiss_db has data
    cursor.execute("SELECT COUNT(*) as count FROM faiss_db")
    count = cursor.fetchone()["count"]

    if count == 0:
        logger.info("No data in faiss_db to migrate")
        conn.close()
        return

    logger.info(f"Migrating {count} records from faiss_db to faissdb")

    # Get all records from faiss_db
    cursor.execute("SELECT * FROM faiss_db")
    faiss_dbs = cursor.fetchall()

    with Session(engine) as session:
        for fdb in faiss_dbs:
            # Find the corresponding vectordb record
            from sqlmodel import select

            user_id = get_or_create_user(session, fdb["user_id"])

            statement = select(VectorDB).where(
                VectorDB.user_id == user_id,
                VectorDB.index_name == fdb["index_name"],
                VectorDB.db_type == DBTypeEnum.faiss,
            )
            vector_db = session.exec(statement).first()

            if not vector_db:
                logger.warning(
                    f"No matching vectordb found for faiss_db {fdb['index_name']}"
                )
                continue

            # Check if this record already exists in faissdb
            statement = select(FaissDB).where(FaissDB.vector_db_id == vector_db.id)
            existing = session.exec(statement).first()

            if existing:
                logger.info(
                    f"FAISS DB for index {fdb['index_name']} already exists in new table"
                )
                continue

            # Create new faissdb record
            embedding_model = EmbeddingModel.sentence_transformers
            if fdb["embedding"] in [e.value for e in EmbeddingModel]:
                embedding_model = EmbeddingModel(fdb["embedding"])

            new_fdb = FaissDB(embedding=embedding_model, vector_db_id=vector_db.id)
            session.add(new_fdb)
            session.commit()

            logger.info(f"Migrated faiss_db record for index {fdb['index_name']}")

    conn.close()


def migrate_file_uploads():
    """Migrate data from file_uploads to fileupload."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Check if file_uploads has data
    cursor.execute("SELECT COUNT(*) as count FROM file_uploads")
    count = cursor.fetchone()["count"]

    if count == 0:
        logger.info("No data in file_uploads to migrate")
        conn.close()
        return

    logger.info(f"Migrating {count} records from file_uploads to fileupload")

    # Get all records from file_uploads
    cursor.execute("SELECT * FROM file_uploads")
    file_uploads = cursor.fetchall()

    with Session(engine) as session:
        for fu in file_uploads:
            # Find the corresponding faissdb record
            from sqlmodel import select

            user_id = get_or_create_user(session, fu["user_id"])

            # Find the vector_db entry
            statement = select(VectorDB).where(
                VectorDB.user_id == user_id,
                VectorDB.index_name == fu["index_name"],
                VectorDB.db_type == DBTypeEnum.faiss,
            )
            vector_db = session.exec(statement).first()

            if not vector_db:
                logger.warning(
                    f"No matching vectordb found for file_upload {fu['file_name']}"
                )
                continue

            # Find the faissdb entry
            statement = select(FaissDB).where(FaissDB.vector_db_id == vector_db.id)
            faiss_db = session.exec(statement).first()

            if not faiss_db:
                logger.warning(
                    f"No matching faissdb found for file_upload {fu['file_name']}"
                )
                continue

            # Check if this record already exists in fileupload
            statement = select(FileUpload).where(
                FileUpload.user_id == user_id,
                FileUpload.file_path == fu["file_path"],
                FileUpload.faiss_db_id == faiss_db.id,
            )
            existing = session.exec(statement).first()

            if existing:
                logger.info(
                    f"File upload {fu['file_name']} already exists in new table"
                )
                continue

            # Create new fileupload record
            new_fu = FileUpload(
                file_name=fu["file_name"],
                file_path=fu["file_path"],
                user_id=user_id,
                faiss_db_id=faiss_db.id,
            )
            session.add(new_fu)
            session.commit()

            logger.info(f"Migrated file_uploads record for file {fu['file_name']}")

    conn.close()


def drop_legacy_tables():
    """Drop the legacy tables after successful migration."""
    logger.info("Dropping legacy tables...")

    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Legacy tables to drop
    legacy_tables = ["vector_db", "pinecone_db", "faiss_db", "file_uploads"]

    for table in legacy_tables:
        try:
            cursor.execute(f"DROP TABLE {table}")
            logger.info(f"Dropped legacy table {table}")
        except sqlite3.Error as e:
            logger.error(f"Error dropping table {table}: {e}")

    conn.commit()
    conn.close()


def main():
    """Main migration function."""
    logger.info("Starting database table consolidation...")

    # Check if legacy tables exist and have data
    if not check_duplicate_tables():
        logger.info("No legacy tables with data found. No migration needed.")
        return

    try:
        # Perform migration
        migrate_vector_db()
        migrate_pinecone_db()
        migrate_faiss_db()
        migrate_file_uploads()

        # Ask for confirmation before dropping legacy tables
        response = input("Migration completed. Drop legacy tables? (yes/no): ")
        if response.lower() == "yes":
            drop_legacy_tables()
            logger.info("Table consolidation completed successfully!")
        else:
            logger.info("Legacy tables preserved. Migration completed!")

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        logger.info("Migration failed. Legacy tables preserved.")


if __name__ == "__main__":
    main()
