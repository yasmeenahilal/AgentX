# Database Migration Guide

This document outlines the database changes and migration process that was completed for the AgentX platform.

## Table Structure Changes

The codebase has been refactored from using raw SQL queries to using SQLModel ORM. The following table structure changes were made:

### Old Tables (Legacy SQLite) - Now Removed
- `vector_db` 
- `pinecone_db`
- `faiss_db`
- `file_uploads`
- `multi_agent`

### New Tables (SQLModel ORM)
- `vectordb`
- `pineconedb`
- `faissdb`
- `fileupload`
- `agent`

## API Changes

The following function names were originally aliased for backward compatibility but have now been fully replaced:
- `create_rag_db` → `create_agent`
- `update_rag_db` → `update_agent`
- `delete_rag_db` → `delete_agent`
- `get_rag_settings` → `get_agent_settings`
- `get_all_agents_for_user` → `get_user_agents`

Legacy API endpoints that were previously marked as deprecated have been removed:
```python
@agent_router.get("/legacy/{user_id}/{agent_name}", deprecated=True)
@agent_router.get("/legacy/{user_id}", deprecated=True)
```

## Migration Process

1. The `scripts/consolidate_db.py` script migrated data from old tables to new tables
2. It handled the following:
   - Mapping user IDs from string format to integer format
   - Creating placeholder users for orphaned records
   - Migrating vector database configurations
   - Migrating Pinecone and FAISS specific configurations
   - Migrating file upload records
   - Dropping legacy tables after confirmation

## Migration Status

**COMPLETED**: The migration has been fully completed and all backward compatibility code has been removed.

If you're using an outdated version of the codebase that still has the legacy tables, you should run the migration script first before updating to the latest codebase:

```bash
# Make sure you have the latest dependencies
pip install -r requirements.txt

# Run the migration script
python scripts/consolidate_db.py

# When prompted "Migration completed. Drop legacy tables? (yes/no):"
# Type "yes" to remove the old tables
```

## Verifying the Migration

You can verify that only the new tables exist:

```bash
# Check the tables in the database
sqlite3 agentX.db ".tables"

# You should see: agent, faissdb, fileupload, pineconedb, user, vectordb
# But NOT: vector_db, pinecone_db, faiss_db, file_uploads, multi_agent
``` 