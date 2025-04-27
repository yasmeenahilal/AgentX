# rag_app/rag_models.py
import logging
from typing import Any, Dict, Optional, Union

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from langchain.llms import HuggingFaceHub, OpenAI
from langchain_core.language_models.base import LanguageModelInput
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


# Real Gemini integration using Google's Generative AI library
class GeminiLLM:
    def __init__(self, model_name: str, api_key: str):
        # Configure the Gemini API with proper settings
        genai.configure(
            api_key=api_key,
            transport="rest",  # Use REST transport for better compatibility
        )

        # Configure model defaults
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        # Safety settings as a dictionary
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Wrapper to use with LangChain
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
            safety_settings=safety_settings,
            convert_system_message_to_human=True,  # Better compatibility with system prompts
        )

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
            logger.error(f"Error calling Gemini model: {str(e)}")
            return f"Error calling Gemini model: {str(e)}"


def initialize_huggingface_llm(repo_id, temperature=0.8, top_k=50):
    # Validate model name
    valid_models = [
        # Qwen Models
        "Qwen/Qwen2-1.5B-Instruct",
        "Qwen/Qwen-7B-Chat",
        
        # Mistral Models
        "mistralai/Mistral-7B-Instruct-v0.1",
        
        # Llama Models
        "meta-llama/Llama-2-13b-chat-hf",
        
        # Flan-T5 Models
        "google/flan-t5-xxl",
        
        # BART Models
        "facebook/bart-large",
        
        # BLOOM Models
        "bigscience/bloom-7b1",
        
        # StableLM Models
        "stabilityai/stablelm-tuned-alpha-7b",
        
        # TinyLlama Models
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    ]
    
    if repo_id not in valid_models:
        raise ValueError(f"Invalid Hugging Face model name. Must be one of: {', '.join(valid_models)}")
    
    try:
        return HuggingFaceHub(
            repo_id=repo_id,
            model_kwargs={"temperature": temperature, "top_k": top_k}
        )
    except Exception as e:
        logger.error(f"Error initializing Hugging Face model: {str(e)}")
        raise


def initialize_openai_llm(model_name, api_key, temperature=0.8, max_tokens=256):
    return OpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=api_key,
    )


def initialize_gemini_llm(model_name, api_key):
    # Validate model name
    valid_models = [
        "gemini-2.0-flash",
        "gemini-2.5-flash-preview-04-17",
        "gemini-2.5-pro-preview-03-25",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.5-pro-vision",
        # "gemini-embedding-exp",
        # "imagen-3.0-generate-002",
        # "veo-2.0-generate-001",
        # "gemini-2.0-flash-live-001",
    ]
    if model_name not in valid_models:
        raise ValueError(f"Invalid Gemini model name. Must be one of: {', '.join(valid_models)}")
        
    try:
        return GeminiLLM(model_name=model_name, api_key=api_key)
    except Exception as e:
        logger.error(f"Error initializing Gemini model: {str(e)}")
        raise
