from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agentX.db")

# Create SQLModel engine
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
        
def create_db_and_tables():
    """Initialize the database and create tables."""
    try:
        logger.info("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise 