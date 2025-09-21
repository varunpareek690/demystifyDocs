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

    async def chat_with_document(self, document_content: str, document_title: str, 
                               user_message: str, chat_history: List[Dict] = None) -> str:
        """Chat with AI about a specific document."""
        try:
            # Build context from document and chat history
            system_prompt = f"""You are an expert legal AI assistant helping users understand legal documents. 

DOCUMENT CONTEXT:
Title: {document_title}
Content: {document_content[:3000]}  # Limit to avoid token limits

Your role is to:
1. Answer questions about the document clearly and accurately
2. Explain legal terms in plain English
3. Highlight important obligations, rights, and deadlines
4. Provide practical advice when appropriate
5. Reference specific sections of the document when relevant

Be conversational, helpful, and always prioritize the user's understanding. If you're unsure about something, say so rather than guessing."""

            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent chat history if available
            if chat_history:
                for msg in chat_history[-6:]:  # Last 6 messages for context
                    if msg['role'] in ['user', 'ai']:
                        role = "user" if msg['role'] == 'user' else "assistant"
                        messages.append({"role": role, "content": msg['content']})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            raise ServiceUnavailableError(f"Chat AI service error: {str(e)}")

    async def generate_document_questions(self, document_content: str, document_title: str) -> List[str]:
        """Generate suggested questions about a document."""
        try:
            prompt = f"""Based on the following legal document, generate 5 helpful questions that a user might want to ask to better understand the document:

Document Title: {document_title}
Document Content: {document_content[:2000]}

Generate questions that would help someone understand:
- Key obligations and rights
- Important deadlines or dates
- Potential risks or concerns
- Practical implications
- Next steps they might need to take

Format as a simple JSON array of strings: ["question1", "question2", ...]
"""

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal expert who helps people understand documents by suggesting relevant questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )

            import json
            try:
                questions = json.loads(response.choices[0].message.content)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                return [
                    "What are my main obligations under this document?",
                    "What are my key rights?",
                    "Are there any important deadlines I need to know about?",
                    "What are the potential consequences if I don't comply?",
                    "What should I do next after reading this document?"
                ]

        except Exception as e:
            # Return default questions if AI service fails
            return [
                "What are the main points of this document?",
                "What obligations do I have?",
                "What are my rights under this agreement?",
                "Are there any important deadlines?",
                "What should I be most concerned about?"
            ]