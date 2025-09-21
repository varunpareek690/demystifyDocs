# ingest.py - Handles document processing and vector database indexing

# Imports
import os
import logging
from google.cloud import aiplatform, documentai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from google.api_core.client_options import ClientOptions
from vertexai.language_models import TextEmbeddingModel
from langchain_google_vertexai.vectorstores import VectorSearchVectorStore
from langchain_core.documents import Document
# Corrected import for the embeddings wrapper
from langchain_google_vertexai import VertexAIEmbeddings

# Load variables from the .env file
load_dotenv()
# Configuration and Initialization
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
PROCESSOR_ID = os.getenv("DOCUMENT-PROCESSOR-ID")
PROCESSOR_REGION = os.getenv("DOCUMENT-PROCESSOR-REGION")
VECTOR_SEARCH_INDEX_ID = os.getenv("VECTOR_SEARCH_INDEX_ID")
VECTOR_SEARCH_ENDPOINT_ID = os.getenv("VECTOR_SEARCH_ENDPOINT_ID")

# Set up logging for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Starting ingest.py script.")
logging.info(f"Project ID: {PROJECT_ID}")
logging.info(f"Region: {REGION}")
logging.info(f"Bucket Name: {BUCKET_NAME}")

aiplatform.init(project=PROJECT_ID, location=REGION)
logging.info("Vertex AI Platform initialized.")

def process_document(file_path):
    """Orchestrates the document ingestion workflow."""
    
    try:
        logging.info(f"Attempting to process document at path: {file_path}")

        # Step 1: Extract Text
        logging.info("Step 1: Starting document text extraction with Document AI...")
        client_options = ClientOptions(api_endpoint=f"{PROCESSOR_REGION}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=client_options)
        processor_name = client.processor_path(PROJECT_ID, PROCESSOR_REGION, PROCESSOR_ID)
        
        with open(file_path, "rb") as image:
            image_content = image.read()
        
        raw_document = documentai.RawDocument(content=image_content, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
        result = client.process_document(request=request)
        document_text = result.document.text
        logging.info("PDF text extraction successful.")

        # Step 2: Split into Chunks
        logging.info("Step 2: Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.create_documents([document_text])
        logging.info(f"Text split into {len(chunks)} chunks.")
        
        # Step 3 & 4: Generate Embeddings and Index into Vector Database
        logging.info("Step 3 & 4: Generating embeddings and indexing into Vector Search...")
        
        # Initialize a LangChain-compatible embeddings object
        embedding_model = VertexAIEmbeddings(model_name="text-embedding-004")
        logging.info("LangChain embeddings model loaded.")
        
        logging.info(f"Initializing VectorStore client using from_components...")
        vector_store = VectorSearchVectorStore.from_components(
            project_id=PROJECT_ID,
            region=REGION,
            gcs_bucket_name=BUCKET_NAME,
            index_id=VECTOR_SEARCH_INDEX_ID,
            endpoint_id=VECTOR_SEARCH_ENDPOINT_ID,
            embedding=embedding_model,
            stream_update=True
        )
        
        logging.info(f"Adding {len(chunks)} documents to the Vector Search index...")
        chunk_texts = [chunk.page_content for chunk in chunks]
        vector_store.add_texts(texts=chunk_texts)

        logging.info(f"Successfully saved {len(chunks)} embeddings to Vector Search.")
        return "Document ingestion successful."

    except FileNotFoundError:
        logging.error(f"Error: File not found at {file_path}")
        return "Document ingestion failed."
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return "Document ingestion failed."


if __name__ == "__main__":
    sample_doc_path = "sample.pdf"
    
    if not all([VECTOR_SEARCH_INDEX_ID, VECTOR_SEARCH_ENDPOINT_ID]):
        logging.error("Please add your VECTOR_SEARCH_INDEX_ID and VECTOR_SEARCH_ENDPOINT_ID to your .env file.")
    else:
        logging.info("Vector Search environment variables found. Starting document processing.")
        process_document(sample_doc_path)