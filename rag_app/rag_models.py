# rag_app/rag_models.py
from langchain.llms import HuggingFaceHub, OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import LanguageModelInput
from typing import Any, Dict, Optional, Union
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

# Real Gemini integration using Google's Generative AI library
class GeminiLLM:
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        # Wrapper to use with LangChain
        self.llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        
    def __call__(self, inputs: Union[str, Dict[str, Any]]) -> str:
        if isinstance(inputs, dict):
            prompt = inputs.get("prompt", "")
        else:
            prompt = inputs
            
        try:
            # Use LangChain wrapper for compatibility with other models
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error calling Gemini model: {str(e)}"


def initialize_huggingface_llm(repo_id, temperature=0.8, top_k=50):
    return HuggingFaceHub(
        repo_id=repo_id, model_kwargs={"temperature": temperature, "top_k": top_k}
    )


def initialize_openai_llm(model_name, api_key, temperature=0.8, max_tokens=256):
    return OpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=api_key,
    )


def initialize_gemini_llm(model_name, api_key):
    return GeminiLLM(model_name=model_name, api_key=api_key)
