from typing import Optional

from pydantic import BaseModel


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
    llm_model_name: str = (
        "mistralai/Mistral-7B-Instruct-v0.3"  # "mistralai/Mixtral-8x7B-Instruct-v0.1"
    )
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
    user_id: str = "user1"
    question: str = "What is the name of the candidate"


class AgentDeleteRequest(BaseModel):
    """Request to delete an agent"""
    agent_name: str
    user_id: str
    index_name: str
