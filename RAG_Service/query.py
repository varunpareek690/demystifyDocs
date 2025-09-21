# Handles user prompt, extracts top 3 chunks from the document and then give response

import os
import logging
from dotenv import load_dotenv
from langchain_google_vertexai import VectorSearchVectorStore, VertexAIEmbeddings, ChatVertexAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from google.cloud import aiplatform
from langchain_core.documents import Document

# New imports for multiple retrievers
from langchain.retrievers import MergerRetriever
from typing import List

# Import your custom constitutional retriever function
from constitutional_retriever import get_relevant_constitutional_articles

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

# Initialize the VectorStore client for user documents
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

# Define the LLM (Gemini)
llm = ChatVertexAI(
    model_name="gemini-1.5-pro",
    project=PROJECT_ID,
    location=REGION
)

# --- Define the new Retrieval Logic ---

# Step 1: Get top 3 chunks from the user's document
vector_retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# Step 2: Create a custom retriever for the constitutional database
def constitutional_retriever(query: str) -> List[Document]:
    # This function will be a simple wrapper for our custom logic
    return get_relevant_constitutional_articles(query)

# Now, we need to create a custom runnable to handle the two-step retrieval.
def retrieve_combined_docs(query: str) -> str:
    # First, retrieve from the vector store
    user_docs = vector_retriever.invoke(query)
    
    # Format the user document chunks to create a richer query for the constitutional database
    combined_context = query + "\n\n" + "\n\n".join([doc.page_content for doc in user_docs])

    # Second, retrieve from the constitutional database using the combined context
    constitutional_docs = constitutional_retriever(combined_context)

    # Combine and format both sets of documents
    all_docs = user_docs + constitutional_docs
    
    # Format all documents for the final prompt
    formatted_docs = []
    formatted_docs.append("--- User Document Context ---")
    formatted_docs.append("\n\n".join(doc.page_content for doc in user_docs))
    formatted_docs.append("\n\n--- Constitutional Articles ---")
    formatted_docs.append("\n\n".join(doc.page_content for doc in constitutional_docs))
    
    print("---------------", formatted_docs)
    return "\n\n".join(formatted_docs)

# --- Update the RAG chain ---

# Create a prompt template for RAG
template = """
You are an expert assistant for legal documents. Use the following context to answer the user's question. 
If you don't know the answer, just say that you don't have enough information. Provide the answer in a language that is easily understandable by a 12-year-old. 

Context:
{context}

Question: {question}

Answer:
"""
prompt = PromptTemplate.from_template(template)

# Create the RAG chain using LangChain's Runnable API
# The 'retrieve_combined_docs' function is now the core of the context retrieval
rag_chain = (
    {"context": RunnablePassthrough() | retrieve_combined_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Your query
query = "What is the jurisdiction of the court to hear a civil suit, and what is the rule of res judicata?"

# Run the RAG chain
logging.info(f"Running RAG chain for query: '{query}'")
result = rag_chain.invoke(query)

# Print the final output from Gemini
print("\n--- Final Answer from Gemini ---")
print(result)
