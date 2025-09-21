# from fastapi import FastAPI, UploadFile, File
# import os
# from parser import extract_text_from_pdf, extract_text_from_docx
# from gemini_client import summarize_text

# app = FastAPI(title="DemystificalDoc API")

# @app.post("/summarize")
# async def summarize_document(file: UploadFile = File(...)):
#     file_ext = os.path.splitext(file.filename)[1]

#     # save temporarily
#     tmp_path = f"temp{file_ext}"
#     with open(tmp_path, "wb") as f:
#         f.write(await file.read())

#     if file_ext == ".pdf":
#         text = extract_text_from_pdf(tmp_path)
#     elif file_ext == ".docx":
#         text = extract_text_from_docx(tmp_path)
#     else:
#         return {"error": "Unsupported file type"}

#     summary = summarize_text(text)
#     return {"summary": summary}


# @app.post("/summarize_text")
# def summarize_text_api(payload: dict):
#     text = payload.get("text")
#     summary = summarize_text(text)
#     return {"summary": summary}



# backend/main.py
from fastapi import FastAPI, UploadFile, File
import os
from parser import extract_text_from_pdf, extract_text_from_docx
from gemini_client import summarize_text
from database import SessionLocal, Document

app = FastAPI(title="DemystificalDoc API")

@app.post("/summarize")
async def summarize_document(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename)[1]

    tmp_path = f"temp{file_ext}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    if file_ext == ".pdf":
        text = extract_text_from_pdf(tmp_path)
    elif file_ext == ".docx":
        text = extract_text_from_docx(tmp_path)
    else:
        return {"error": "Unsupported file type"}

    summary = summarize_text(text)

    # Save to DB
    db = SessionLocal()
    new_doc = Document(
        filename=file.filename,
        raw_text=text,
        summary=summary
    ) 
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    db.close()

    return {"summary": summary, "document_id": new_doc.id}


@app.post("/summarize_text")
def summarize_text_api(payload: dict):
    text = payload.get("text")
    summary = summarize_text(text)

    # Save to DB (filename = None for raw text)
    db = SessionLocal()
    new_doc = Document(
        filename="raw_text_input",
        raw_text=text,
        summary=summary
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    db.close()

    return {"summary": summary, "document_id": new_doc.id}


@app.get("/documents")
def list_documents():
    db = SessionLocal()
    docs = db.query(Document).all()
    db.close()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at,
            "summary": doc.summary[:200] + "..."  # preview only
        }
        for doc in docs
    ]
