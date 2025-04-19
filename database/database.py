"""Database initialization and management module."""
import os
import sqlite3
import logging
from sqlmodel import SQLModel
from models.base import engine, get_session, create_db_and_tables

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy SQLite database path - will be replaced by SQLModel
DATABASE = "agentX.db"

def init_db():
    """Initialize the database and create tables using SQLModel."""
    try:
        logger.info("Initializing database with SQLModel...")
        create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Keep this for backward compatibility during migration
def legacy_init_db():
    """Legacy function to initialize SQLite database directly."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS vector_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            index_name TEXT NOT NULL,
            db_type TEXT NOT NULL CHECK(db_type IN ('Pinecone', 'FAISS')),
            UNIQUE(user_id, index_name)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS pinecone_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pinecone_api_key TEXT,
            metric TEXT,
            cloud TEXT,
            region TEXT,
            dimension INTEGER,
            embedding TEXT NOT NULL,
            index_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS faiss_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT,
            embedding TEXT NOT NULL,
            index_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS multi_agent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            llm_provider TEXT NOT NULL,
            llm_model_name TEXT NOT NULL,
            llm_api_key TEXT NOT NULL,
            prompt_template TEXT,
            index_name TEXT,
            index_type TEXT,
            UNIQUE(user_id, agent_name)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS file_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            index_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            UNIQUE(user_id, index_name)
        )
        """
        )

        conn.commit()
        logger.info("SQLite database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
