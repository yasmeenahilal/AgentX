# rag_app/rag_models.py
from langchain.llms import HuggingFaceHub, OpenAI
from langchain_openai import ChatOpenAI


# Placeholder for Gemini integration
class GeminiLLM:
    def __init__(self, model_name, api_key):
        self.model_name = model_name
        self.api_key = api_key

    def __call__(self, inputs: dict) -> str:
        prompt = inputs.get("prompt", "")
        return f"Response from Gemini model {self.model_name}: {prompt}"


def initialize_huggingface_llm(repo_id, temperature=0.8, top_k=50):
    return HuggingFaceHub(
        repo_id=repo_id, model_kwargs={"temperature": temperature, "top_k": top_k}
    )


def initialize_openai_llm(model_name, api_key, temperature=0.7, max_tokens=256):
    return OpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=api_key,
    )


def initialize_gemini_llm(model_name, api_key):
    return GeminiLLM(model_name=model_name, api_key=api_key)
