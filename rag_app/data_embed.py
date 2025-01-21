from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mistralai import MistralAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings


def initialize_embeddings(model_type, model_name):
    """
    Initialize embeddings based on the selected model type and name.

    Args:
        model_type (str): Type of model ('huggingface', 'openai', 'ollama', 'mistral').
        model_name (str): Model name to be used for initialization.

    Returns:
        Embeddings instance based on the provided type and name.

    Raises:
        ValueError: If the model type is unsupported.
    """
    if model_type == "huggingface":
        return HuggingFaceEmbeddings(model_name=model_name)
    elif model_type == "openai":
        return OpenAIEmbeddings(model=model_name)
    elif model_type == "ollama":
        return OllamaEmbeddings(model=model_name)
    elif model_type == "mistral":
        return MistralAIEmbeddings(model=model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
