import sqlite3

DATABASE = "agentX"


def init_db():
    """Initialize the SQLite database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Create the table for vector DB configurations
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS vector_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            index_name TEXT NOT NULL,
            db_type TEXT NOT NULL CHECK(db_type IN ('Pinecone', 'FAISS')), -- Specify DB type
            UNIQUE(user_id, index_name) -- Composite unique constraint
        )"""
        )

        # Table for Pinecone-specific configuration details
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
            index_name TEXT NOT NULL,  -- Foreign key for Pinecone index configuration
            user_id TEXT NOT NULL,  -- Foreign key for user to associate with vector DB
            FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
        )"""
        )

        # Table for Faiss-specific configuration details
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS faiss_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT,
            embedding TEXT NOT NULL,
            index_name TEXT NOT NULL,  -- Foreign key for Faiss index configuration
            user_id TEXT NOT NULL,  -- Foreign key for user to associate with vector DB
            FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE
        )"""
        )

        # Table for the multi-agent configurations
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS multi_agent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            index_name TEXT, -- Allowing NULL values here
            llm_provider TEXT NOT NULL,
            llm_model_name TEXT NOT NULL,
            llm_api_key TEXT NOT NULL,
            prompt_template TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES vector_db(user_id) ON DELETE CASCADE -- Ensures cascade delete
        )"""
        )

        # Table to store file uploads
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS file_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            index_name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (index_name, user_id) REFERENCES vector_db(index_name, user_id) ON DELETE CASCADE, 
            UNIQUE(user_id, index_name) -- Composite unique constraint
        )
        """
        )

        conn.commit()
