from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader


def text_loader(filename):
    """Loads and returns documents from a text file."""
    try:
        loader = TextLoader(filename)
        documents = loader.load()
        return documents
    except Exception as e:
        raise RuntimeError(f"Error loading text file '{filename}': {e}")


def pdf_loader(filename):
    """Loads and returns documents from a PDF file."""
    try:
        pdfloader = PyPDFLoader(filename)
        documents = pdfloader.load()
        return documents
    except Exception as e:
        raise RuntimeError(f"Error loading PDF file '{filename}': {e}")


def csv_loader(filename):
    """Loads and returns data from a CSV file."""
    try:
        loader = CSVLoader(filename)
        data = loader.load()
        return data
    except Exception as e:
        raise RuntimeError(f"Error loading CSV file '{filename}': {e}")


def read_data(filename):
    """
    Determines file type by its extension and loads the corresponding documents or data.
    Returns a list of documents.
    """
    file_extension = filename.split(".")[-1].lower()
    try:
        if file_extension == "txt":
            return text_loader(filename)
        elif file_extension == "pdf":
            return pdf_loader(filename)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        raise RuntimeError(f"Error processing file '{filename}': {e}")


def data_splitter(filename):
    """
    Splits documents into smaller chunks for processing using RecursiveCharacterTextSplitter.
    Returns the split documents.
    """
    documents = read_data(filename)
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
        return text_splitter.split_documents(documents)
    except Exception as e:
        raise RuntimeError(f"Error splitting documents: {e}")
