import logging

import database
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
# from langchain.vectorstores import Pinecone as pns
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as pns


# New imports
# from langchain_community.vectorstores import Pinecone as pns
from langchain_community.embeddings import HuggingFaceEmbeddings
from rag_app.factories.gemini_factory import GeminiFactory
from rag_app.factories.huggingface_factory import HuggingFaceFactory
from rag_app.factories.openai_factory import OpenAIFactory

# Configure the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Function to set up Pinecone retriever
def initialize_docsearch(index_name, embeddings, api_key):
    """
    Initializes a Pinecone retriever.

    Parameters:
        index_name (str): Name of the Pinecone index.
        embeddings: Embedding model used for the retriever.
        api_key (str): API key for Pinecone access.

    Returns:
        docsearch: A Pinecone retriever instance.
    # """
    # new_pns = pns(api_key = api_key)
    # index = new_pns.Index(name=index_name)
    docsearch = PineconeVectorStore(pinecone_api_key = api_key, index_name=index_name, embedding=embeddings)
    return docsearch
    # print("\n\n\n\nIndex Name:",index_name, "\n\n\nAPI Key:",api_key)
    # return pns.from_existing_index(index_name, embeddings)


# Step 1: Load and clean PDF files
def load_pdf(pdf_path):
    """Load PDF using PyPDFLoader and clean the text."""
    if pdf_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
    elif pdf_path.lower().endswith(".txt"):
        loader = TextLoader(pdf_path)
        pages = loader.load()

    new_pages = [remove_ws(page) for page in pages]

    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=150, length_function=len
    )
    docs = text_splitter.split_documents(new_pages)
    return docs


def remove_ws(page):
    """Remove any newlines, extra spaces, etc., from page content."""
    page_content = page.page_content.replace("\n", " ").strip()
    page.page_content = page_content
    return page


# Step 2: Create a FAISS VectorStore
def create_vector_store(pages):
    """Create a FAISS VectorStore from the loaded and processed PDF pages."""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
    vector_store = FAISS.from_documents(pages, embeddings)
    return vector_store


def create_faiss_retriever(vector_store):
    """Create a FAISS retriever for document search."""
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return retriever


def create_prompt_template(template):
    """
    Creates a prompt template for the Agent chain.

    Parameters:
        template (str): Customizable prompt template.

    Returns:
        PromptTemplate: A prompt template instance.
    """
    propmt_template = """
    if you didn't find answer then simply return false
    Use only the context for your answers, do not make up information
    Context: {context}
    Question: {question}
    Answer: 
    """
    final_template = template + propmt_template

    return PromptTemplate(
        template=final_template, input_variables=["context", "question"]
    )


def create_rag_pipeline(docsearch, llm, prompt_template):
    """
    Creates the Agent pipeline.
    """
    logger.info("Creating Agent pipeline...")

    retriever_output = docsearch
    logger.info("Retriever Output: %s", retriever_output)

    try:
        rag_chain = (
            {"context": retriever_output, "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
        )
        logger.info("Created Agent pipeline successfully")
        return rag_chain
    except Exception as e:
        logger.error("Error creating Agent pipeline: %s", e)
        raise e


def extract_question_answer(response):
    """
    Extracts and formats the Question and Answer from the Agent response.
    """
    try:
        if isinstance(response, str):
            question_start = response.find("Question:")
            answer_start = response.find("Answer:")

            if question_start != -1 and answer_start != -1:
                question = response[question_start:answer_start].strip()
                answer = response[answer_start:].strip()
                return f"{question}\n{answer}"
            if response == "I do not have enough information to answer that.":
                return response
            else:
                return "Error: Could not find 'Question' or 'Answer' in the response."
        else:
            return "Error: The response is not a string."
    except Exception as e:
        logger.error("Error extracting question and answer: %s", e)
        return f"Error extracting question and answer: {str(e)}"


# def Agent(
#     index_name,
#     embeddings,
#     model_name,
#     api_key,
#     prompt_template,
#     use_llm,
#     question,
#     user_id,
#     index_type,
# ):
#     docsearch = None
#     if index_type == "Pinecone":
#         # pinecone_api_key = "pcsk_3VXw3K_7D1ayFVyK7ESzG15w9pXkUKejght3pzrDQpZAv2FjKphKQidWotKmn2dbjnSXFB"
#         pinecone_api_key = database.get_pinecone_api_index_name_type_db(
#             user_id, index_name
#         )
#         docsearch = initialize_docsearch(index_name, embeddings, pinecone_api_key)
#         if docsearch is not None:
#             docsearch = docsearch.as_retriever()

    # elif index_type == "FAISS":
    #     file_addr = database.get_file_from_faiss_db(user_id, index_name)
    #     if not file_addr:
    #         logger.warning("Data Not Found. Kindly upload files to the database.")
    #         return "Data Not Found kindly upload files to db"
    #     pages = load_pdf(file_addr)
    #     vector_store = create_vector_store(pages)
    #     docsearch = create_faiss_retriever(vector_store)

    # match use_llm:
    #     case "huggingface":
    #         factory = HuggingFaceFactory()
    #     case "openai":
    #         factory = OpenAIFactory()
    #     case "gemini":
    #         factory = GeminiFactory()
    #     case _:
    #         logger.error("The LLM type '%s' is not implemented.", use_llm)
    #         raise NotImplementedError(f"The LLM type '{use_llm}' is not implemented.")

#     llm = factory.create_llm(model_name, api_key)
#     prompt = create_prompt_template(prompt_template)
#     rag_chain = create_rag_pipeline(docsearch, llm, prompt)
#     print("\n\n\nQuestion:",question)
#     response = rag_chain.invoke(question)
#     print(f"  Raw LLM Response: {response}")

#     if use_llm == "openai":
#         response = f"Question: {question} Answer:{response}"
#     response = extract_question_answer(response)
#     return response

def Agent(
    index_name,
    embeddings,
    model_name,
    api_key,
    prompt_template,
    use_llm,
    question,
    user_id,
    index_type,
):
    docsearch = None
    print(f"\n--- Agent Function Called ---")
    print(f"  Index Name: {index_name}")
    print(f"  Index Type: {index_type}")
    print(f"  Question: {question}")
    print(f"  User ID: {user_id}")

    if index_type == "Pinecone":
        pinecone_api_key = database.get_pinecone_api_index_name_type_db(
            user_id, index_name
        )
        print(f"  Retrieved Pinecone API Key: {'*' * (len(pinecone_api_key) - 4) + pinecone_api_key[-4:] if pinecone_api_key else 'Not Found'}")
        print(f"  Initializing Pinecone docsearch...")
        docsearch = initialize_docsearch(index_name, embeddings, pinecone_api_key)
        if docsearch is not None:
            print(f"  Pinecone docsearch initialized successfully.")
            print(f"  Creating Pinecone retriever...")
            docsearch_retriever = docsearch.as_retriever()
            print(f"  Invoking Pinecone retriever with question: '{question}'")
            relevant_documents = docsearch_retriever.get_relevant_documents(question)
            print(f"  Retrieved {len(relevant_documents)} relevant documents from Pinecone:")
            if relevant_documents:
                for i, doc in enumerate(relevant_documents):
                    print(f"    Document {i+1}: {doc.metadata.get('source') if doc.metadata.get('source') else doc.page_content[:100]}...")
            else:
                print("    No relevant documents found by the Pinecone retriever.")
            docsearch = docsearch_retriever
        else:
            print(f"  Pinecone docsearch initialization failed.")

    elif index_type == "FAISS":
        file_addr = database.get_file_from_faiss_db(user_id, index_name)
        if not file_addr:
            logger.warning("Data Not Found. Kindly upload files to the database.")
            return "Data Not Found kindly upload files to db"
        pages = load_pdf(file_addr)
        vector_store = create_vector_store(pages)
        docsearch = create_faiss_retriever(vector_store)


    match use_llm:
        case "huggingface":
            factory = HuggingFaceFactory()
        case "openai":
            factory = OpenAIFactory()
        case "gemini":
            factory = GeminiFactory()
        case _:
            logger.error("The LLM type '%s' is not implemented.", use_llm)
            raise NotImplementedError(f"The LLM type '{use_llm}' is not implemented.")

    llm = factory.create_llm(model_name, api_key)
    prompt = create_prompt_template(prompt_template)
    rag_chain = create_rag_pipeline(docsearch, llm, prompt)
    print("\n\n\nQuestion:",question)
    print(f"  Invoking RAG chain with question...")
    response = rag_chain.invoke(question)
    print(f"  Raw LLM Response: {response}")
    response = extract_question_answer(response)
    print(f"  Final Response: {response}")
    return response


"""
import pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings

# Initialize Pinecone
pinecone.init(api_key="pcsk_4oYKGP_9tEKEWX8CXuS4DK8UrxfVGJu7gJ88THD4J7M4SSyqbmSjgGMzQom3oMgioJ53fZ", environment="us-east-1")
index = pinecone.Index(index_name="yasmeena1")

# Initialize the same embeddings model
embeddings_model = "your-huggingface-embedding-model" # Replace with your model
embeddings = HuggingFaceEmbeddings(model_name=sentence-transformers/all-mpnet-base-v2)

# Embed your question
question = "How betty determined to wear bangles and play the violin"
question_embedding = embeddings.embed_query(question)

# Query Pinecone
results = index.query(
    vector=question_embedding,
    top_k=5, # Or a suitable number
    include_values=False,
    include_metadata=True # Important to see the source/content
)

print(results)
"""