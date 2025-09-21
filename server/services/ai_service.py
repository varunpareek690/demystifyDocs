import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import json
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, ChatSession as VertexChatSession
import vertexai
from core.config import settings
from utils.exceptions import ServiceUnavailableError
from utils.chunking import TextChunker

class VertexAIService:
    """Vertex AI service for document summarization and chat."""
    
    def __init__(self):
        """Initialize Vertex AI client."""
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_vertex()
        
    def _initialize_vertex(self):
        """Initialize Vertex AI with credentials."""
        try:
            if settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
                # Initialize from JSON string
                import json
                from google.oauth2 import service_account
                credentials_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                
                vertexai.init(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID,
                    location=settings.VERTEX_AI_LOCATION,
                    credentials=credentials
                )
            else:
                vertexai.init(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID,
                    location=settings.VERTEX_AI_LOCATION
                )
                
            self.model = GenerativeModel(settings.VERTEX_AI_MODEL_NAME)
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to initialize AI service: {str(e)}")

    async def summarize_legal_document(self, content: str, title: str = "") -> Dict:
        """
        Summarize legal document using Vertex AI.
        
        Args:
            content: Document content
            title: Document title
            
        Returns:
            Dict containing summary, key_points, etc.
        """
        try:
            chunks = TextChunker.chunk_text(content, max_tokens=8000)
            
            if len(chunks) == 1:
                return await self._summarize_single_chunk(chunks[0], title)
            else:
                return await self._summarize_multiple_chunks(chunks, title)
                
        except Exception as e:
            raise ServiceUnavailableError(f"AI summarization service error: {str(e)}")

    async def _summarize_single_chunk(self, content: str, title: str) -> Dict:
        """Summarize a single chunk of content."""
        prompt = f"""
        As a legal expert, analyze this legal document and provide a structured response.
        
        Document Title: {title}
        Document Content: {content}
        
        Provide your analysis in the following JSON format:
        {{
            "summary": "A concise 2-3 paragraph summary of the document",
            "key_points": ["5-7 most important points as bullet items"],
            "complexity_score": 5,
            "important_dates": ["Any deadlines, expiration dates, or time-sensitive items"],
            "obligations": ["Key obligations or responsibilities"],
            "rights": ["Important rights or entitlements"],
            "highlights": [
                {{"text": "Important text snippet", "reason": "Why this is important", "section": "Document section"}}
            ]
        }}
        
        Focus on making complex legal language accessible to non-lawyers while maintaining accuracy.
        """
        
        def _generate_summary():
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "max_output_tokens": 2048
                    }
                )
                return response.text
            except Exception as e:
                raise ServiceUnavailableError(f"AI generation failed: {str(e)}")
        
        response_text = await asyncio.get_event_loop().run_in_executor(
            self.executor, _generate_summary
        )
        
        try:
            result = json.loads(response_text.strip())
            
            required_fields = ['summary', 'key_points', 'complexity_score']
            for field in required_fields:
                if field not in result:
                    result[field] = self._get_fallback_value(field)
                    
            if 'highlights' not in result:
                result['highlights'] = []
                
            return result
            
        except json.JSONDecodeError:
            return self._create_fallback_summary(content, title)

    async def _summarize_multiple_chunks(self, chunks: List[str], title: str) -> Dict:
        """Summarize multiple chunks and combine results."""
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"""
            Analyze this section of a legal document titled "{title}" (Part {i+1} of {len(chunks)}).
            
            Content: {chunk}
            
            Provide a brief summary and key points in JSON format:
            {{
                "summary": "Summary of this section",
                "key_points": ["3-5 key points from this section"],
                "important_dates": ["Any dates in this section"],
                "obligations": ["Obligations mentioned"],
                "rights": ["Rights mentioned"]
            }}
            """
            
            def _generate_chunk_summary():
                response = self.model.generate_content(
                    chunk_prompt,
                    generation_config={"temperature": 0.2, "max_output_tokens": 800}
                )
                return response.text
            
            chunk_response = await asyncio.get_event_loop().run_in_executor(
                self.executor, _generate_chunk_summary
            )
            
            try:
                chunk_summary = json.loads(chunk_response.strip())
                chunk_summaries.append(chunk_summary)
            except json.JSONDecodeError:
                continue
        
        # Combine chunk summaries
        return self._combine_chunk_summaries(chunk_summaries, title)

    def _combine_chunk_summaries(self, chunk_summaries: List[Dict], title: str) -> Dict:
        """Combine multiple chunk summaries into a single comprehensive summary."""
        if not chunk_summaries:
            return self._create_fallback_summary("", title)
        
        # Combine summaries
        combined_summary = " ".join([cs.get('summary', '') for cs in chunk_summaries])
        
        # Combine and deduplicate lists
        combined_key_points = []
        combined_dates = []
        combined_obligations = []
        combined_rights = []
        
        for cs in chunk_summaries:
            combined_key_points.extend(cs.get('key_points', []))
            combined_dates.extend(cs.get('important_dates', []))
            combined_obligations.extend(cs.get('obligations', []))
            combined_rights.extend(cs.get('rights', []))
        
        # Remove duplicates while preserving order
        combined_key_points = list(dict.fromkeys(combined_key_points))[:7]
        combined_dates = list(dict.fromkeys(combined_dates))
        combined_obligations = list(dict.fromkeys(combined_obligations))
        combined_rights = list(dict.fromkeys(combined_rights))
        
        # Estimate complexity based on number of chunks and content
        complexity_score = min(10, 4 + len(chunk_summaries))
        
        return {
            "summary": combined_summary,
            "key_points": combined_key_points,
            "complexity_score": complexity_score,
            "important_dates": combined_dates,
            "obligations": combined_obligations,
            "rights": combined_rights,
            "highlights": []  # Would need more sophisticated processing
        }

    async def chat_with_document(self, document_content: str, document_title: str, 
                               user_message: str, chat_history: List[Dict] = None) -> str:
        """
        Chat with AI about a specific document.
        
        Args:
            document_content: Full document text
            document_title: Document title
            user_message: User's question
            chat_history: Previous messages for context
            
        Returns:
            AI response string
        """
        try:
            # Prepare document context (chunk if necessary)
            doc_chunks = TextChunker.chunk_text(document_content, max_tokens=6000)
            doc_context = doc_chunks[0] if doc_chunks else document_content[:6000]
            
            # Build conversation context
            system_context = f"""You are an expert legal AI assistant helping users understand legal documents.

DOCUMENT CONTEXT:
Title: {document_title}
Content: {doc_context}

Your role is to:
1. Answer questions about this specific document accurately
2. Explain legal terms in plain English
3. Highlight important obligations, rights, and deadlines
4. Provide practical guidance when appropriate
5. Reference specific parts of the document when relevant

Be conversational, helpful, and always prioritize the user's understanding. If you're unsure about something specific to this document, say so rather than making assumptions."""

            # Build chat prompt with history
            conversation_prompt = system_context + "\n\n"
            
            if chat_history:
                conversation_prompt += "Previous conversation:\n"
                for msg in chat_history[-6:]:  # Include last 6 messages
                    role = "Human" if msg['role'] == 'user' else "Assistant"
                    conversation_prompt += f"{role}: {msg['content']}\n"
            
            conversation_prompt += f"\nHuman: {user_message}\nAssistant: "
            
            def _generate_chat_response():
                response = self.model.generate_content(
                    conversation_prompt,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_output_tokens": 1024
                    }
                )
                return response.text
            
            # Generate response
            response_text = await asyncio.get_event_loop().run_in_executor(
                self.executor, _generate_chat_response
            )
            
            return response_text.strip()
            
        except Exception as e:
            raise ServiceUnavailableError(f"Chat AI service error: {str(e)}")

    async def generate_document_questions(self, document_content: str, document_title: str) -> List[str]:
        """Generate suggested questions about a document."""
        try:
            # Use first chunk for question generation
            chunks = TextChunker.chunk_text(document_content, max_tokens=4000)
            content = chunks[0] if chunks else document_content
            
            prompt = f"""Based on this legal document, generate 5 helpful questions that would help someone understand it better:

Title: {document_title}
Content: {content}

Focus on questions about:
- Key obligations and rights
- Important deadlines
- Potential risks or concerns
- Practical implications
- Next steps

Return as JSON array: ["question1", "question2", "question3", "question4", "question5"]"""

            def _generate_questions():
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.8, "max_output_tokens": 400}
                )
                return response.text
            
            response_text = await asyncio.get_event_loop().run_in_executor(
                self.executor, _generate_questions
            )
            
            try:
                questions = json.loads(response_text.strip())
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                pass
                
        except Exception:
            pass        
        # Fallback questions
        return [
            "What are my main obligations under this document?",
            "What are my key rights and entitlements?",
            "Are there any important deadlines I need to know about?",
            "What are the potential consequences if I don't comply?",
            "What should I do next after reading this document?"
        ]

    def _create_fallback_summary(self, content: str, title: str) -> Dict:
        """Create a basic fallback summary when AI processing fails."""
        word_count = len(content.split())
        complexity = min(10, max(1, word_count // 500))
        
        return {
            "summary": f"This document titled '{title}' contains {word_count} words. A detailed analysis could not be generated at this time. Please review the full document carefully.",
            "key_points": [
                "Document requires careful review",
                "May contain legal obligations",
                "May contain important rights",
                "Review for deadlines and dates",
                "Consider consulting legal counsel if needed"
            ],
            "complexity_score": complexity,
            "important_dates": [],
            "obligations": [],
            "rights": [],
            "highlights": []
        }

    def _get_fallback_value(self, field: str):
        """Get fallback values for required fields."""
        fallbacks = {
            'summary': 'Document analysis unavailable',
            'key_points': ['Document requires manual review'],
            'complexity_score': 5,
            'important_dates': [],
            'obligations': [],
            'rights': [],
            'highlights': []
        }
        return fallbacks.get(field)

# Alias for backward compatibility
AIService = VertexAIService