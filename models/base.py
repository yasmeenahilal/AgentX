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
        
        # Initialize vector_db table - fallback for raw SQL version
        import sqlite3
        with sqlite3.connect("agentX.db") as conn:
            cursor = conn.cursor()
            
            # Create the vector_db table using raw SQL if it doesn't exist yet
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_db (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                index_name TEXT NOT NULL,
                db_type TEXT NOT NULL CHECK(db_type IN ('Pinecone', 'FAISS')),
                UNIQUE(user_id, index_name)
            )
            """)
            
            # Create related tables
            cursor.execute("""
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
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS faiss_db (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_path TEXT,
                embedding TEXT NOT NULL,
                index_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                chunk_size INTEGER,
                chunk_overlap INTEGER,
                index_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
            )
            """)
            
            conn.commit()
            logger.info("Raw SQL tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise 