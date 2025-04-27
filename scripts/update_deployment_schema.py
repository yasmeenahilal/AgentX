#!/usr/bin/env python
"""
Manual migration script to update the Deployment table with new security fields.
Use this instead of Alembic for SQLite database updates.
"""
import logging
import os
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database file path (adjust as needed)
DB_PATH = "agentX.db"


def backup_database(db_path):
    """Create a backup of the database before modifying it"""
    backup_path = f"{db_path}.backup"
    try:
        if os.path.exists(db_path):
            import shutil

            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created at {backup_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
    return False


def add_deployment_security_fields():
    """Add the new security fields to the Deployment table"""
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return False

    # Create backup first
    if not backup_database(DB_PATH):
        logger.warning("Proceeding without backup")

    # Connect to the database
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the deployment table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='deployment'"
        )
        if not cursor.fetchone():
            logger.error("Deployment table does not exist")
            return False

        # Method 1: Try to add columns without constraints first (simplest approach)
        try:
            # Get existing columns
            cursor.execute("PRAGMA table_info(deployment)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add new columns if they don't exist
            new_columns = {
                "short_token": "TEXT",  # No UNIQUE constraint in ALTER TABLE
                "allowed_domains": "TEXT DEFAULT '*'",
                "is_active": "BOOLEAN DEFAULT 1",
                "rate_limit": "INTEGER DEFAULT 100",
            }

            for column, definition in new_columns.items():
                if column not in columns:
                    logger.info(f"Adding column '{column}' to deployment table")
                    cursor.execute(
                        f"ALTER TABLE deployment ADD COLUMN {column} {definition}"
                    )
                    logger.info(f"Column '{column}' added successfully")

            # Create index for short_token (instead of UNIQUE constraint)
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_deployment_short_token ON deployment (short_token)"
            )
            logger.info("Created unique index for short_token")

            # Commit changes
            conn.commit()
            logger.info("Database updated using simple ALTER TABLE approach")
            return True

        except sqlite3.OperationalError as e:
            logger.warning(f"Simple ALTER TABLE approach failed: {e}")
            logger.info("Trying full table recreation approach...")
            conn.rollback()

            # Method 2: Create new table, copy data, drop old, rename new
            # Get table structure
            cursor.execute("PRAGMA table_info(deployment)")
            table_info = cursor.fetchall()

            # Get foreign keys
            cursor.execute("PRAGMA foreign_key_list(deployment)")
            foreign_keys = cursor.fetchall()

            # Build column definitions for the new table
            column_defs = []
            for col in table_info:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                col_def = f"{col_name} {col_type}"

                if is_pk:
                    col_def += " PRIMARY KEY"
                if not_null:
                    col_def += " NOT NULL"
                if default_val is not None:
                    col_def += f" DEFAULT {default_val}"

                column_defs.append(col_def)

            # Add new columns
            column_defs.append("short_token TEXT UNIQUE")
            column_defs.append("allowed_domains TEXT DEFAULT '*'")
            column_defs.append("is_active BOOLEAN DEFAULT 1")
            column_defs.append("rate_limit INTEGER DEFAULT 100")

            # Build foreign key constraints
            fk_constraints = []
            for fk in foreign_keys:
                id, seq, table, from_col, to_col, on_update, on_delete, match = fk
                fk_constraints.append(
                    f"FOREIGN KEY ({from_col}) REFERENCES {table}({to_col})"
                )

            # Create new table
            cursor.execute(
                f"""
            CREATE TABLE deployment_new (
                {', '.join(column_defs)},
                {', '.join(fk_constraints) if fk_constraints else ''}
            )
            """
            )

            # Get list of existing columns for data copying
            cursor.execute("PRAGMA table_info(deployment)")
            existing_cols = [row[1] for row in cursor.fetchall()]

            # Copy data
            cursor.execute(
                f"""
            INSERT INTO deployment_new ({', '.join(existing_cols)})
            SELECT {', '.join(existing_cols)} FROM deployment
            """
            )

            # Drop old table
            cursor.execute("DROP TABLE deployment")

            # Rename new table
            cursor.execute("ALTER TABLE deployment_new RENAME TO deployment")

            # Create index for short_token
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS ix_deployment_short_token ON deployment (short_token)"
            )

            # Commit changes
            conn.commit()
            logger.info("Database updated using table recreation approach")
            return True

    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    logger.info("Starting manual database migration")
    if add_deployment_security_fields():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
