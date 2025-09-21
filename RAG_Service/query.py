# query_gemini.py - Retrieves chunks and sends them to Gemini for generation

import os
import logging
from dotenv import load_dotenv
from langchain_google_vertexai import VectorSearchVectorStore, VertexAIEmbeddings, ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from google.cloud import aiplatform

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION")
VECTOR_SEARCH_INDEX_ID = os.getenv("VECTOR_SEARCH_INDEX_ID")
VECTOR_SEARCH_ENDPOINT_ID = os.getenv("VECTOR_SEARCH_ENDPOINT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Vertex AI SDK
aiplatform.init(project=PROJECT_ID, location=REGION)
logging.info("Vertex AI Platform initialized.")

# Initialize the embedding model
embedding_model = VertexAIEmbeddings(model_name="text-embedding-004", project=PROJECT_ID)
logging.info("LangChain embeddings model loaded.")

# Initialize the VectorStore client
logging.info("Initializing VectorStore client...")
vector_store = VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=GCS_BUCKET_NAME,
    index_id=VECTOR_SEARCH_INDEX_ID,
    endpoint_id=VECTOR_SEARCH_ENDPOINT_ID,
    embedding=embedding_model,
    stream_update=True
)
logging.info("VectorStore client initialized.")

# Define the LLM (Gemini) and the RAG chain
logging.info("Setting up Gemini and the RAG chain.")

# Initialize the Gemini model
llm = ChatVertexAI(
    model_name="gemini-1.5-pro",
    project=PROJECT_ID,
    location=REGION
)

# Create a prompt template for RAG
template = """
You are an expert assistant for legal documents. Use the following context to answer the user's question. 
If you don't know the answer, just say that you don't have enough information. Provide the answer the language that is easily understandable by a 12-year-old. 

Context: {context}

Question: {question}

Answer:
"""
prompt = PromptTemplate.from_template(template)

# Define a simple retrieval function
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Create the RAG chain using LangChain's Runnable API
rag_chain = (
    {
        "context": (lambda x: x["question"]) | vector_store.as_retriever() | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Your query
query = "What are the parties involved in the document?"

# Run the RAG chain
logging.info(f"Running RAG chain for query: '{query}'")
result = rag_chain.invoke({"question": query})

# Print the final output from Gemini
print("\n--- Final Answer from Gemini ---")
print(result)