"""Database initialization and management module."""
import os
import logging
from sqlmodel import SQLModel
from models.base import engine, get_session, create_db_and_tables

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path for SQLModel
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
