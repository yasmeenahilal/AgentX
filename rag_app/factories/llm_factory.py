# rag_app/factories/llm_factory.py
from abc import ABC, abstractmethod


class LLMFactory(ABC):
    @abstractmethod
    def create_llm(self, model_name: str, api_key: str = None) -> object:
        pass
