"""
RAG Generator: LLM-powered answer generation with strict citation requirements
"""

import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 2000
    max_context_tokens: int = 8000


class RAGGenerator:
    """Generate answers from retrieved context using LLM"""
    
    def __init__(self, llm_client: OpenAI, config: LLMConfig):
        self.llm = llm_client
        self.config = config
        self.system_prompt = self._get_system_prompt()
        self.user_prompt_template = self._get_user_prompt_template()
        logger.info(f"RAGGenerator initialized with {config.model}")
    
    def generate(self, query: str, context: List[Dict]) -> Tuple[str, List[Dict]]:
        """Generate answer from retrieved context"""
        formatted_context = self._format_context(context)
        user_prompt = self.user_prompt_template.format(
            query=query,
            context=formatted_context['text']
        )
        
        try:
            response = self.llm.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated answer: {len(answer)} chars")
            return answer, context
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_answer(query, context), context
    
    def _format_context(self, context: List[Dict]) -> Dict:
        """
        Format retrieved documents for prompt
        
        CRITICAL: Must include citations for every document so LLM can cite them!
        
        Returns:
            {'text': formatted string, 'docs': original docs}
        """
        formatted_lines = []
        
        for i, doc in enumerate(context, 1):
            doc_type = doc.get('doc_type', 'unknown')
            doc_id = doc.get('doc_id', 'unknown')
            content = doc.get('content', '')[:2000]  # Increased from 1000 to 2000
            
            # Format based on document type with CITATIONS
            if doc_type == 'case':
                citation = doc.get('citation')
                if citation:
                    # Case with citation
                    formatted_lines.append(
                        f"[{i}] {citation}: \"{content}\""
                    )
                else:
                    # Case without citation - use doc_id
                    formatted_lines.append(
                        f"[{i}] Case {doc_id}: \"{content}\""
                    )
            
            elif doc_type == 'statute':
                # Statute - extract section from doc_id or use title
                section_name = self._extract_statute_section(doc_id)
                formatted_lines.append(
                    f"[{i}] {section_name}: \"{content}\""
                )
            
            elif doc_type == 'rule':
                # Rules of Court - extract order/rule from doc_id
                rule_name = self._extract_rule_name(doc_id)
                formatted_lines.append(
                    f"[{i}] {rule_name}: \"{content}\""
                )
            
            else:
                # Generic document
                formatted_lines.append(
                    f"[{i}] Document {doc_id}: \"{content}\""
                )
        
        return {
            'text': '\n\n'.join(formatted_lines),
            'docs': context
        }
    
    def _extract_statute_section(self, doc_id: str) -> str:
        """Extract readable section name from statute doc_id"""
        # Examples:
        # misrepresentation_act_1967_s2 → Section 2 of Misrepresentation Act 1967
        # patents_act_1994_s80 → Section 80 of Patents Act 1994
        
        if '_s' in doc_id:
            parts = doc_id.split('_s')
            act_name = parts[0].replace('_', ' ').title()
            section = parts[1].replace('_', '(')  # s2_1 → s2(1)
            if '(' not in section:
                return f"Section {section} of {act_name}"
            else:
                return f"Section {section}) of {act_name}"
        
        # Fallback
        return doc_id.replace('_', ' ').title()
    
    def _extract_rule_name(self, doc_id: str) -> str:
        """Extract readable rule name from doc_id"""
        # Examples:
        # roc_2021_o_9_r_16 → Order 9 Rule 16 of ROC 2021
        # roc_2021_o_22_r_6 → Order 22 Rule 6 of ROC 2021
        
        if 'roc_' in doc_id:
            # Extract year
            year = doc_id.split('_')[1] if len(doc_id.split('_')) > 1 else ''
            
            # Extract order and rule
            import re
            order_match = re.search(r'_o_(\d+)', doc_id)
            rule_match = re.search(r'_r_(\d+)', doc_id)
            
            if order_match and rule_match:
                order = order_match.group(1)
                rule = rule_match.group(1)
                return f"Order {order} Rule {rule} of ROC {year}"
            elif order_match:
                order = order_match.group(1)
                return f"Order {order} of ROC {year}"
        
        # Fallback
        return doc_id.replace('_', ' ').upper()
    
    def _get_system_prompt(self) -> str:
        """System prompt enforcing structure and citations"""
        return """You are a Singapore legal research assistant specializing in statutory interpretation.

Your task is to answer the user's legal question using the provided context. Even if the context is not perfect, do your best to provide a helpful answer based on what is available.

INSTRUCTIONS:
1. Use the provided context as your primary source
2. Always include citations when referencing sources:
   - Cases: [2013] SGHC 110, [2020] SGCA 50
   - Statutes: Section 2 of Misrepresentation Act 1967
   - Rules: Order 9 Rule 16 of ROC 2021
3. Quote key passages when relevant (use quotation marks)
4. If you can provide partial information, do so and explain what is covered
5. Only say you cannot answer if the context is completely unrelated to the query

PREFERRED ANSWER STRUCTURE:
1. **Rule/Statute:** State the relevant provision (if available in context)
2. **Interpretation:** Explain how it has been interpreted (if case law is available)
3. **Application:** Describe how this applies to the query
4. **Conclusion:** Provide a clear answer

IMPORTANT: Be helpful! If the context has relevant information, use it. Don't refuse to answer unless the context is truly unrelated to the question."""
    
    def _get_user_prompt_template(self) -> str:
        """User prompt template"""
        return """Question: {query}

Context (with citations):
{context}

Please answer the question based on the context provided. Include proper citations for any sources you reference."""
    
    def _generate_fallback_answer(self, query: str, context: List[Dict]) -> str:
        """Generate fallback if LLM fails"""
        return f"Error generating answer for: {query}\n\nRelevant sources found: {len(context)}"
