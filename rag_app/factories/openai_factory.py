# rag_app/factories/openai_factory.py
from rag_app.rag_models import initialize_openai_llm

from .llm_factory import LLMFactory


class OpenAIFactory(LLMFactory):
    def create_llm(self, model_name: str, api_key: str = None) -> object:
        return initialize_openai_llm(model_name, api_key)
