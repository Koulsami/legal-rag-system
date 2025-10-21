"""LLM generation service"""
import logging
from typing import List, Tuple
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class GenerationService:
    """Handles LLM-based answer generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_statutory_interpretation(
        self,
        query: str,
        context: str,
        enable_synthesis: bool = True
    ) -> Tuple[str, List[str]]:
        """Generate answer using GPT-4"""
        
        prompt = f"""You are a Singapore legal expert. Answer the following question using ONLY the provided context.

Context:
{context}

Question: {query}

Provide a clear, accurate answer with citations in square brackets like [Citation Name]."""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a Singapore legal expert specializing in statutory interpretation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            
            import re
            citations = re.findall(r'\[([^\]]+)\]', answer)
            
            return answer, citations
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")

generation_service = GenerationService()
