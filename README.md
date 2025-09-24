# 📚 Demystify Legal Documents with Generative AI

## Empowering Users to Navigate the Legal Landscape

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Angular Version](https://img.shields.io/badge/Angular-16%2B-red)](https://angular.io/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Enabled-lightgrey)](https://cloud.google.com/)

---

## ✨ Project Overview

Legal documents are often a labyrinth of complex jargon, creating a significant information asymmetry that can lead to unforeseen financial and legal risks for individuals and small businesses. Our solution, **Demystify Legal Documents with Generative AI**, directly addresses this critical challenge.

We've developed an **AI-powered platform** that acts as a reliable first point of contact, simplifying complex legal documents into clear, accessible guidance. Our goal is to empower users to make informed decisions and protect themselves, providing a private, safe, and supportive environment.

### 🎯 Why This Project Matters (The MVP)

* **Bridging the Information Gap:** Transforms opaque legal language into understandable insights.
* **Risk Mitigation:** Helps users avoid unknowingly agreeing to unfavorable terms.
* **Accessibility:** Makes essential legal information available to everyone, from everyday citizens to small business owners.
* **Empowerment:** Provides the knowledge needed for informed decision-making.

Our Minimum Viable Product (MVP) focuses on two core functionalities:
1.  **Instant Summarization:** Get a quick, clear overview of any uploaded legal document.
2.  **AI-Powered Q&A:** Ask specific questions and receive grounded answers, leveraging both your document's content and relevant constitutional laws.

---

## 🚀 Features

* **Intelligent Document Ingestion:** Seamlessly upload various legal document formats (PDF, DOCX, TXT) with intelligent text and structure extraction via Vertex AI Document AI.
* **Contextual Summarization:** Obtain immediate, concise, and easy-to-understand summaries of complex legal texts powered by Gemini 1.5 Pro.
* **AI-Powered Q&A (RAG):** Engage in a natural language chat to ask specific questions, receiving accurate answers grounded in your uploaded document and relevant constitutional laws, utilizing a robust Retrieval-Augmented Generation (RAG) pipeline.
* **Persistent Chat History:** Securely save and review all past conversations within the app, ensuring continuity and easy access to previous insights (powered by Firestore).
* **Secure Authentication:** User authentication powered by Google OAuth for secure and seamless access.
* **End-to-End Google Cloud Platform (GCP) Integration:** Leveraging a suite of GCP services for scalability, reliability, and security from frontend to AI processing.
* **Multilingual Support (Future):** Planned integration with Google Cloud Translation API to offer communication in multiple languages.

---

## 🛠️ Technology Stack

Our solution is built on a modern, scalable, and robust technology stack:

### Frontend
* **Angular:** A powerful framework for building dynamic and responsive user interfaces.

### Backend (API Gateway)
* **FastAPI:** A high-performance, easy-to-use Python web framework for building our robust API backend.
* **Postman:** Used for efficient API testing and development during the entire lifecycle.

### Google Cloud Platform (GCP) Services
* **Vertex AI Document AI:** For intelligent document parsing, OCR, and information extraction.
* **Gemini 1.5 Pro (LLM):** The core Large Language Model for advanced text summarization and generating responses within the RAG pipeline.
* **Vertex AI Vector Search (formerly Matching Engine):** A highly scalable vector database for efficient storage and semantic retrieval of document embeddings.
* **Google Cloud Storage:** Secure and scalable object storage for housing original user-uploaded legal documents.
* **Firestore:** A flexible, scalable NoSQL document database used for managing user profiles and persisting chat history.
* **Cloud Identity & Access Management (IAM) / OAuth:** For secure user authentication and granular access control across GCP services.
* **Cloud Translation API:** (Planned for future) For enabling multilingual capabilities.

### AI/ML Frameworks & Tools
* **LangChain:** An indispensable framework for orchestrating the Retrieval-Augmented Generation (RAG) pipeline, including text chunking and managing interactions with LLMs and vector databases.
* **`text-embedding-004`:** The specific embedding model used to convert text chunks and user queries into numerical vectors for semantic search.

---

## 🚀 How to Run the Repository

This project consists of two main parts: the `frontend` (Angular) and the `server` (FastAPI).

### Prerequisites
* Node.js (LTS version) & npm
* Python 3.11+ & pip
* Docker (if deploying locally or using Cloud Run)
* Google Cloud SDK (`gcloud` CLI) configured with your project.
* A Google Cloud Project with billing enabled and necessary APIs enabled (Vertex AI, Document AI, Cloud Storage, Firestore, Cloud Run, Artifact Registry, etc.).
* Service accounts with appropriate roles for your GCP services.

### 1. Backend Setup (`server/`)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/varunpareek690/demystifyDocs.git] (https://github.com/varunpareek690/demystifyDocs.git)
    cd demystifyDocs/server
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  **Configure environment variables:**
    Create a `.env` file in the `server/` directory based on `.env.example`.
    ```
    # Example .env content:
    GOOGLE_PROJECT_ID="your-gcp-project-id"
    # ... other API keys/configurations for Document AI, Gemini, etc.
    # Ensure your gcloud authentication is set up for your local environment
    ```
4.  **Run the FastAPI server locally:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API should be accessible at `http://localhost:8000`.

### 2. Frontend Setup (`frontend/`)

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend # Assuming frontend is a sibling directory
    ```
2.  **Install npm dependencies:**
    ```bash
    npm install
    ```
3. **Run the Angular development server:**
    ```bash
    ng serve --open
    ```
    The Angular app should open in your browser, typically at `http://localhost:4200`.

    * See `frontend/README.md` to setup Angular

### 3. Google Cloud Run Deployment (for Backend)

To deploy your FastAPI backend to Google Cloud Run, follow these steps from your `RAG_Service/` directory:

This project uses two main scripts—`ingest.py` and `query.py`—to interact with Google Cloud services. Follow these steps to set up your environment and run the scripts.

#### Prerequisites

* **Python 3.11+** installed.
* **Google Cloud SDK** (`gcloud` CLI) installed and configured with your GCP project. You must authenticate your local environment by running `gcloud auth login` and `gcloud config set project <YOUR_PROJECT_ID>`.
* Ensure **billing** is enabled on your GCP project and that all necessary APIs are enabled.

---

### Step 1: Set Up the Environment

First, you need to set up your Python environment and install the required dependencies. Navigate to your project's `root` directory.

1.  **Create a Python virtual environment** to isolate your project's dependencies:
    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment:**
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **On Windows:**
        ```bash
        venv\Scripts\activate
        ```

3.  **Install the required libraries** from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

---

### Step 2: Run the Scripts

Now that your environment is set up, you can execute the scripts.

1.  **Run `ingest.py`**: This script is responsible for the document ingestion and embedding process. It will connect to the Document AI and Vector Search services to prepare your data.

    ```bash
    python ingest.py
    ```
    This script will perform tasks like extracting text, creating embeddings, and storing them in your vector search database.

2.  **Run `query.py`**: After the data is ingested, you can run this script to interact with your RAG model. It will take a user query, find relevant information, and generate a response using the Gemini API.

    ```bash
    python query.py
    ```
    This script handles the conversational aspect, demonstrating the core Q&A functionality of your application.

Each of these files is designed to connect directly to the respective **GCP services** you've enabled in your project, allowing you to run the full workflow locally.

---
