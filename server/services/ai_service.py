import openai
from typing import List, Dict
from core.config import settings
from utils.exceptions import ServiceUnavailableError

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    async def summarize_legal_document(self, content: str, title: str = "") -> Dict:
        """Summarize legal document using OpenAI."""
        try:
            prompt = f"""
            As a legal expert, please analyze the following legal document and provide:
            1. A concise summary (2-3 paragraphs)
            2. Key points (5-7 bullet points)
            3. A complexity score from 1-10 (1 being simple, 10 being highly complex)
            4. Any important deadlines, obligations, or rights mentioned

            Document Title: {title}
            Document Content: {content[:4000]}  # Limit content to avoid token limits

            Please format your response as JSON with the following structure:
            {{
                "summary": "...",
                "key_points": ["...", "..."],
                "complexity_score": 5,
                "important_dates": ["..."],
                "obligations": ["..."],
                "rights": ["..."]
            }}
            """

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert legal document analyzer. Provide clear, accessible explanations of complex legal terms and concepts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            # Parse the response (in a real application, you'd want more robust parsing)
            import json
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": response.choices[0].message.content[:500],
                    "key_points": ["Analysis provided above"],
                    "complexity_score": 5,
                    "important_dates": [],
                    "obligations": [],
                    "rights": []
                }

        except Exception as e:
            raise ServiceUnavailableError(f"AI service error: {str(e)}")
