from fastapi import FastAPI, UploadFile, File
import os
from parser import extract_text_from_pdf, extract_text_from_docx
from gemini_client import summarize_text

app = FastAPI(title="DemystificalDoc API")

@app.post("/summarize")
async def summarize_document(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename)[1]

    # save temporarily
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
    return {"summary": summary}


@app.post("/summarize_text")
def summarize_text_api(payload: dict):
    text = payload.get("text")
    summary = summarize_text(text)
    return {"summary": summary}
