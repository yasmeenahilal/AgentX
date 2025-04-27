from typing import Any, Dict, Optional
from pydantic import BaseModel
from enum import Enum


class HuggingFaceModelEnum(str, Enum):
    # Qwen Models
    QWEN_1_5B = "Qwen/Qwen2-1.5B-Instruct"
    QWEN_7B = "Qwen/Qwen-7B-Chat"
    
    # Mistral Models
    MISTRAL_7B = "mistralai/Mistral-7B-Instruct-v0.1"
    
    # Llama Models
    LLAMA_2_13B = "meta-llama/Llama-2-13b-chat-hf"
    
    # Flan-T5 Models
    FLAN_T5_XXL = "google/flan-t5-xxl"
    
    # BART Models
    BART_LARGE = "facebook/bart-large"
    
    # BLOOM Models
    BLOOM_7B = "bigscience/bloom-7b1"
    
    # StableLM Models
    STABLELM_7B = "stabilityai/stablelm-tuned-alpha-7b"
    
    # TinyLlama Models
    TINYLLAMA_1_1B = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


class GeminiModelEnum(str, Enum):
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_5_FLASH_PREVIEW = "gemini-2.5-flash-preview-04-17"
    GEMINI_2_5_PRO_PREVIEW = "gemini-2.5-pro-preview-03-25"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_PRO_VISION = "gemini-1.5-pro-vision"


class AgentGetRequest(BaseModel):
    """Request to get an agent's details"""

    agent_name: str
    user_id: str


class AgentCreateRequest(BaseModel):
    """Request to create a new agent"""

    agent_name: str = "MyBot"
    user_id: Optional[str] = None  # Made optional as it will be set from authenticated user
    index_name: Optional[str] = None
    index_type: Optional[str] = None
    llm_provider: str = "huggingface"  # e.g., "huggingface", "openai", "gemini"
    llm_model_name: str = "mistralai/Mistral-7B-Instruct-v0.3"
    llm_api_key: str
    prompt_template: str = (
        "You are a knowledgeable assistant trained to provide answers based on accurate, reliable, and factual information. If you do not have enough data to answer a question, do not invent information or provide a speculative response. Instead, acknowledge the lack of sufficient data and refrain from answering. Only answer questions that you can confirm with the provided data. If the query is ambiguous or outside the scope of the data, state 'I do not have enough information to answer that."
    )


class AgentUpdateRequest(BaseModel):
    """Request to update an existing agent"""

    agent_name: str
    user_id: str
    index_name: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model_name: Optional[str] = None
    llm_api_key: Optional[str] = None
    prompt_template: Optional[str] = None
    embeddings_model: Optional[str] = None


class AgentQueryRequest(BaseModel):
    """Request to query an agent with a question"""

    agent_name: str = "MyBot"
    question: str
    session_id: Optional[int] = None


class AgentDeleteRequest(BaseModel):
    """Request to delete an agent"""

    agent_name: str
    user_id: str
    index_name: str


class DeploymentRequest(BaseModel):
    agent_name: str
    deployment_method: str  # Using string here instead of enum for flexibility
    deployment_name: Optional[str] = None
    deployment_description: Optional[str] = None
    embed_settings: Optional[Dict[str, Any]] = None
    allowed_domains: Optional[str] = None  # Comma-separated list of allowed domains
