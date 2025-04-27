from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class DBTypeEnum(str, Enum):
    pinecone = "Pinecone"
    faiss = "FAISS"


class VectorDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    index_name: str = Field(index=True)
    db_type: DBTypeEnum
    created_at: datetime = Field(default_factory=datetime.now)

    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")

    # Relationships - use string references to avoid circular imports
    user: "User" = Relationship(back_populates="vector_dbs")
    pinecone_config: Optional["PineconeDB"] = Relationship(back_populates="vector_db")
    faiss_config: Optional["FaissDB"] = Relationship(back_populates="vector_db")

    # Define a unique constraint at the SQLAlchemy level
    class Config:
        table_name = "vectordb"


class EmbeddingModel(str, Enum):
    openai = "openai"
    huggingface = "huggingface"
    cohere = "cohere"
    sentence_transformers = "sentence-transformers/all-mpnet-base-v2"
    all_mpnet = "sentence-transformers/all-mpnet-base-v2"


class PineconeDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pinecone_api_key: str
    metric: str
    cloud: str
    region: str
    dimension: int
    embedding: EmbeddingModel

    # Foreign Keys
    vector_db_id: int = Field(foreign_key="vectordb.id")

    # Relationships
    vector_db: VectorDB = Relationship(back_populates="pinecone_config")

    class Config:
        table_name = "pineconedb"


class FaissDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    embedding: EmbeddingModel

    # Foreign Keys
    vector_db_id: int = Field(foreign_key="vectordb.id")

    # Relationships
    vector_db: VectorDB = Relationship(back_populates="faiss_config")
    files: List["FileUpload"] = Relationship(back_populates="faiss_db")

    class Config:
        table_name = "faissdb"


class FileUpload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.now)

    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    faiss_db_id: int = Field(foreign_key="faissdb.id")

    # Relationships
    faiss_db: FaissDB = Relationship(back_populates="files")

    class Config:
        table_name = "file_uploads"
