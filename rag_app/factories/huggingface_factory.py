# rag_app/factories/huggingface_factory.py
from rag_app.rag_models import initialize_huggingface_llm

from .llm_factory import LLMFactory


class HuggingFaceFactory(LLMFactory):
    def create_llm(self, model_name: str, api_key: str = None) -> object:
        return initialize_huggingface_llm(model_name)
