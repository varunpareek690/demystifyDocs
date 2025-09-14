import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in environment")

def summarize_text(text: str):
    url = f"{BASE_URL}?key={API_KEY}"   # <-- key goes here
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": text}]}
        ]
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        return f"Error: {response.text}"

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
