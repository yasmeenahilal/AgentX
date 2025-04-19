from enum import Enum as PyEnum
from typing import Literal, Optional

from fastapi import File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError


# List of valid roles
# OPENAI_MODELS_CHOICE = ["o1-mini", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo-0125", "gpt-4o-mini", "o1-mini"]
# HUGGINGFACE_MODELS_CHOICE = ["Qwen/Qwen2.5-1.5B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
# LLM_MODEL_CHOICE = ["huggingface", "openai", "gemini"]
# EMBEDDING_MODEL = "huggingface"
class VectorDB(str, PyEnum):
    pinecone = "Pinecone"
    faiss = "FAISS"


class ModelVendorEnum(PyEnum):
    openai = "openai"
    huggingface = "huggingface"
    gemini = "gemini"


class EmbeddingModelEnum(PyEnum):
    huggingface = "huggingface"
    openai = "openai"
    cohere = "cohere"
    sentence_transformers = "sentence-transformers/all-mpnet-base-v2"
    all_mpnet = "sentence-transformers/all-mpnet-base-v2"


class PineconeMetricEnum(PyEnum):
    cosine = "cosine"
    euclidean = "euclidean"
    dotproduct = "dotproduct"


class PineconeCloudEnum(PyEnum):
    aws = "aws"
    azure = "azure"
    gcp = "gcp"


class RegionAWSEnum(PyEnum):
    us_east_1 = "us-east-1"
    us_west_2 = "us-west-2"
    eu_west_1 = "eu-west-1"


class RegionGoogleCloudEnum(PyEnum):
    europe_west4 = "europe-west4"
    us_central_1 = "us-central-1"


class RegionAzureEnum(PyEnum):
    eastus2 = "eastus2"


class LLMModelChoiceEnum(PyEnum):
    openai = "openai"
    huggingface = "huggingface"
    gemini = "gemini"


class RAGToolSettings(BaseModel):
    filename: str
    model_name: Literal[
        "o1-mini",
        "gpt-3.5-turbo-instruct",
        "gpt-3.5-turbo-0125",
        "gpt-4o-mini",
        "o1-mini",
    ]
    embed_model_name: Literal[
        "Qwen/Qwen2.5-1.5B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"
    ]
    use_llm: bool
    prompt_template: Optional[str] = None


class PineconeSetup(BaseModel):
    pinecone_api_key: str = (
        "pcsk_4p4BJG_5SCHxrXCTfuF7URdywSLfiS7Yq51KQS4WXgNsp5Bqbq4mhE4CG6SaqaTTkWGESD"
    )
    metric: str  # PineconeMetricEnum = PineconeMetricEnum.cosine
    cloud: str  # PineconeCloudEnum = PineconeCloudEnum.aws
    region: str = "us-east-1"
    dimension: int = 768


# Dependency to validate Pinecone setup
def get_pinecone_setup(
    vectordb: VectorDB = Form(...),
    pinecone_api_key: Optional[str] = Form(
        default="pcsk_4p4BJG_5SCHxrXCTfuF7URdywSLfiS7Yq51KQS4WXgNsp5Bqbq4mhE4CG6SaqaTTkWGESD"
    ),
    # pinecone_api_key: Optional[str] = Form(default="your api key",None),
    metric: Optional[str] = Form(default="cosine"),
    cloud: Optional[str] = Form(default="aws"),
    region: Optional[str] = Form(default="us-east-1"),
    dimension: Optional[int] = Form(default=768),
) -> Optional[PineconeSetup]:
    if vectordb == VectorDB.pinecone:
        # Ensure all Pinecone fields are provided
        if not all([pinecone_api_key, metric, cloud, region, dimension]):
            raise HTTPException(
                status_code=400,
                detail=(
                    "When 'vectordb' is set to Pinecone, the following fields are required: "
                    "'pinecone_api_key', 'metric', 'cloud', 'region', and 'dimension'."
                ),
            )
        try:
            return PineconeSetup(
                pinecone_api_key=pinecone_api_key,
                metric=metric,
                cloud=cloud,
                region=region,
                dimension=dimension,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid Pinecone setup: {str(e)}"
            )
    return None


class PineconeDeleteIndex(BaseModel):
    user_id: str
    index_name: str
