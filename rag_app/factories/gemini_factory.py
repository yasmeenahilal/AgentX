# rag_app/factories/gemini_factory.py
from rag_app.rag_models import initialize_gemini_llm

from .llm_factory import LLMFactory


class GeminiFactory(LLMFactory):
    def create_llm(self, model_name: str, api_key: str = None) -> object:
        return initialize_gemini_llm(model_name, api_key)
