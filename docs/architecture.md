# DemystificalDoc Architecture

## Layers
1. Data Ingestion Layer
   - Upload PDF/DOCX
   - Store in Cloud Storage
   - Extract text
2. Preprocessing Layer
   - Clean text
   - Chunk into clauses
   - Embed for retrieval
3. AI Processing Layer
   - Gemini API + RAG
   - Generate summaries, explanations
4. Application Layer
   - FastAPI backend
   - Role-based access (User/Admin)
5. Frontend Layer
   - Upload doc, view summaries
   - Dashboard for Admin notes
