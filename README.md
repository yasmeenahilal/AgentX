# AgentX - Multi-Agent RAG Platform

A versatile platform for creating and managing multiple RAG agents with customizable LLMs and vector databases.

## Database Structure

The project uses SQLModel ORM for database operations. The database schema includes these main tables:

- `agent`: Stores agent configurations and settings
- `vectordb`: Manages vector database metadata
- `pineconedb`: Contains Pinecone-specific configuration
- `faissdb`: Contains FAISS-specific configuration
- `fileupload`: Tracks uploaded files for vector databases

The codebase previously used raw SQLite operations with tables like `vector_db`, `pinecone_db`, etc., but has been fully migrated to the SQLModel structure.

## Migration History

The migration from raw SQLite to SQLModel has been completed. Legacy tables and backward compatibility code have been removed. If you're working with an older version of the codebase, make sure to run the migration script before updating:

```bash
python scripts/consolidate_db.py
```

For more details on the migration process, see [MIGRATION.md](MIGRATION.md)
