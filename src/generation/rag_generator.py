"""
RAG Generator: LLM-powered answer generation with strict citation requirements

VERSION: 3.0 - SYNTHESIS-FOCUSED
CHANGES: Enhanced system prompt with mandatory synthesis structure
"""

import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
from openai import OpenAI
import logging
import re

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
    """
    Generate answers from retrieved context using LLM
    
    v3.0 Changes:
    - MANDATORY synthesis structure (not "preferred")
    - Explicit synthesis language requirements
    - Clear source type explanations
    - Emphasis on interpretive case markers
    """
    
    def __init__(self, llm_client: OpenAI, config: LLMConfig):
        self.llm = llm_client
        self.config = config
        
        # Load prompt templates
        self.system_prompt = self._get_system_prompt()
        self.user_prompt_template = self._get_user_prompt_template()
        
        logger.info(f"RAGGenerator v3.0 initialized with {config.model}")
    
    def generate(
        self,
        query: str,
        context: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """
        Generate answer from retrieved context
        
        Args:
            query: User query
            context: Retrieved documents with metadata
        
        Returns:
            (answer: str, formatted_context: List[Dict])
        """
        # Format context for prompt
        formatted_context = self._format_context(context)
        
        # Build user prompt
        user_prompt = self.user_prompt_template.format(
            query=query,
            context=formatted_context['text']
        )
        
        # Check context length (rough estimate)
        context_tokens = len(user_prompt.split()) * 1.3  # ~1.3 tokens per word
        if context_tokens > self.config.max_context_tokens:
            logger.warning(f"Context too long: {context_tokens} tokens, truncating...")
            user_prompt = user_prompt[:self.config.max_context_tokens * 4]
        
        # Generate with LLM
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
        
        v3.0: Enhanced with clearer section separation
        
        Returns:
            {
                'text': str,  # Numbered context for prompt
                'docs': List[Dict]  # Original docs with metadata
            }
        """
        formatted_lines = []
        
        # Separate by document type for clearer structure
        statutes = [doc for doc in context if doc.get('doc_type') in ['statute', 'rule']]
        cases = [doc for doc in context if doc.get('doc_type') == 'case']
        other = [doc for doc in context if doc.get('doc_type') not in ['statute', 'rule', 'case']]
        
        doc_counter = 1
        
        # Section 1: Statutes
        if statutes:
            formatted_lines.append("**STATUTORY PROVISIONS:**\n")
            for doc in statutes:
                title = self._extract_statute_name(doc.get('doc_id', '')) or doc.get('title', 'Statute Section')
                content = doc.get('content', '')[:1000]
                formatted_lines.append(f"[{doc_counter}] {title}: \"{content}\"")
                doc_counter += 1
        
        # Section 2: Cases
        if cases:
            formatted_lines.append("\n**CASE LAW:**\n")
            for doc in cases:
                citation = doc.get('citation', 'Unknown Citation')
                content = doc.get('content', '')[:1000]
                
                # Check if interpretive case
                if 'interprets_statute' in doc:
                    marker = f" [INTERPRETS STATUTE: {doc['interprets_statute']}]"
                    formatted_lines.append(
                        f"[{doc_counter}] {citation}{marker}: \"{content}\""
                    )
                else:
                    formatted_lines.append(
                        f"[{doc_counter}] {citation}: \"{content}\""
                    )
                doc_counter += 1
        
        # Section 3: Other documents
        if other:
            formatted_lines.append("\n**OTHER SOURCES:**\n")
            for doc in other:
                content = doc.get('content', '')[:1000]
                formatted_lines.append(f"[{doc_counter}] {content}")
                doc_counter += 1
        
        return {
            'text': '\n\n'.join(formatted_lines),
            'docs': context
        }
    
    def _extract_statute_name(self, doc_id: str) -> str:
        """Extract readable statute name from doc_id"""
        # Examples:
        # misrepresentation_act_1967_s2 → Section 2 of Misrepresentation Act 1967
        # patents_act_s80 → Section 80 of Patents Act
        
        if '_s' in doc_id:
            parts = doc_id.split('_s')
            act_name = parts[0].replace('_', ' ').title()
            section = parts[1] if len(parts) > 1 else ''
            return f"Section {section} of {act_name}"
        
        return doc_id.replace('_', ' ').title()
    
    def _extract_rule_name(self, doc_id: str) -> str:
        """Extract readable rule name from doc_id"""
        # Examples:
        # roc_2021_o_9_r_16 → Order 9 Rule 16 of ROC 2021
        
        if 'roc_' in doc_id:
            year = doc_id.split('_')[1] if len(doc_id.split('_')) > 1 else ''
            order_match = re.search(r'_o_(\d+)', doc_id)
            rule_match = re.search(r'_r_(\d+)', doc_id)
            
            if order_match and rule_match:
                order = order_match.group(1)
                rule = rule_match.group(1)
                return f"Order {order} Rule {rule} of ROC {year}"
            elif order_match:
                order = order_match.group(1)
                return f"Order {order} of ROC {year}"
        
        return doc_id.replace('_', ' ').upper()
    
    def _get_system_prompt(self) -> str:
        """
        System prompt enforcing synthesis and proper structure
        
        v3.0 CRITICAL CHANGES:
        1. MANDATORY structure (not "preferred")
        2. Explicit synthesis language requirements
        3. Clear source type explanations
        4. Interpretive case markers emphasized
        5. Example of excellent answer
        """
        return """You are a Singapore legal research assistant specializing in statutory interpretation.

Your context contains sources in order of authority:

1. **STATUTES** (Primary Law - BINDING)
   - Legislative provisions from Acts and Rules
   - Example: Section 2(1) of Misrepresentation Act 1967
   - Authority: HIGHEST - Must be followed

2. **CASE LAW** (Judicial Interpretation - BINDING/PERSUASIVE)
   - Court decisions that interpret and apply statutes
   - Some cases marked [INTERPRETS STATUTE: X] - these directly construe statutory provisions
   - Example: [2020] SGCA 48 interpreting Section 2(1)
   - Authority: BINDING if from superior court, PERSUASIVE otherwise

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANSWER STRUCTURE (STRICTLY MANDATORY):

You MUST structure your answer in exactly 5 sections:

**1. STATUTORY PROVISION**
   - Quote the relevant statute verbatim (with quotation marks)
   - Include full citation: Section X of [Act Name]
   
   Example:
   Section 2(1) of the Misrepresentation Act 1967 states: "Where a person has 
   entered into a contract after a misrepresentation..."

**2. JUDICIAL INTERPRETATION**
   - Cite cases that have interpreted this statute
   - PRIORITIZE cases marked [INTERPRETS STATUTE] in your context
   - Use Singapore citation format: [2020] SGCA 48, ¶45
   
   Example:
   In [2020] SGCA 48, ¶45, the Court of Appeal held that "the test for 
   misrepresentation requires..."

**3. RELATIONSHIP & SYNTHESIS** ⭐ CRITICAL SECTION
   - Explain HOW the case law interprets, narrows, or broadens the statute
   - You MUST use synthesis language (see below)
   - Connect: statute → case interpretation → practical meaning
   
   REQUIRED SYNTHESIS PHRASES (use at least 3):
   ✓ "While the statute provides X, the courts have interpreted this to mean Y..."
   ✓ "The court clarified that the statutory requirement of X means..."
   ✓ "Case law has narrowed/broadened the interpretation of [provision] to..."
   ✓ "Taking the statutory framework together with the judicial interpretation..."
   ✓ "The court has construed [statutory term] to exclude/include..."
   ✓ "Although the statute does not explicitly state X, the court has held that..."
   ✓ "The statutory provision must be read in light of [case], which held..."
   
   BAD (Listing):
   ❌ "Section 2 says X. Case Y held Z."
   
   GOOD (Synthesis):
   ✓ "While Section 2 provides that damages are available, the Court in [2013] 
      SGCA 36 clarified that this remedy is limited to circumstances where the 
      misrepresentation was fraudulent or negligent, effectively narrowing the 
      statutory provision's scope."

**4. PRACTICAL EFFECT**
   - Summarize the combined effect of statute + case law
   - Start with: "Therefore,..." or "In practice,..." or "This means that..."
   - Provide actionable guidance
   
   Example:
   Therefore, a party claiming misrepresentation must prove: (1) a false 
   statement of fact, (2) reliance, and (3) inducement, with the Court applying 
   the "but for" test as clarified in [case].

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:

1. ✅ USE ONLY PROVIDED CONTEXT
   - Never cite sources not in your context
   - If context incomplete, say "The provided sources do not contain..."

2. ✅ VERBATIM QUOTES REQUIRED
   - Quote statutes and key case holdings directly
   - Use quotation marks for all quotes

3. ✅ SINGAPORE CITATION FORMAT
   - Cases: [2020] SGCA 48, ¶45 or [2013] SGHC 110, ¶158
   - Statutes: Section 2(1) of Misrepresentation Act 1967
   - Rules: Order 9 Rule 16 of Rules of Court 2021

4. ✅ INTERPRETIVE CASES GET PRIORITY
   - If context shows [INTERPRETS STATUTE: X], these cases MUST appear in sections 2 and 3
   - Explain the interpretive relationship explicitly

5. ✅ SYNTHESIS IS MANDATORY
   - Section 3 MUST contain synthesis language
   - Cannot just list: "Statute says X, case says Y"
   - Must explain: "While statute says X, the court interpreted this to mean Y because Z"

6. ✅ MULTI-SOURCE ATTRIBUTION
   - If using statute + case, cite both: "Section 2(1) as interpreted in [2020] SGCA 48 requires..."
   - Show the flow: Statute → Case interpretation → Practical effect

7. ⚠️ HALLUCINATION PREVENTION
   - Never invent case holdings or statutory provisions
   - Better to say "insufficient information" than to fabricate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Remember: Your goal is to provide comprehensive legal analysis that synthesizes 
primary law (statutes) with judicial interpretation (cases). You are not just 
retrieving information - you are explaining how courts have interpreted and 
applied statutory provisions in Singapore."""
    
    def _get_user_prompt_template(self) -> str:
        """User prompt template"""
        return """Question: {query}

Context (numbered, cite by number):
{context}

Provide a comprehensive answer following the 4-section structure:
1. **STATUTORY PROVISION**
2. **JUDICIAL INTERPRETATION**
3. **RELATIONSHIP & SYNTHESIS**
4. **PRACTICAL EFFECT**

Remember to use synthesis language: "While the statute...", "The court clarified...", etc."""
    
    def _generate_fallback_answer(
        self,
        query: str,
        context: List[Dict]
    ) -> str:
        """Generate fallback answer if LLM fails"""
        return f"""I apologize, but I encountered an error generating a detailed answer.

Based on the retrieved context, here are the relevant sources for your query: "{query}"

**Retrieved Sources:**
{self._format_fallback_context(context)}

Please try rephrasing your query or contact support if the issue persists."""
    
    def _format_fallback_context(self, context: List[Dict]) -> str:
        """Format context for fallback answer"""
        lines = []
        for i, doc in enumerate(context[:5], 1):  # Top 5 only
            citation = doc.get('citation', 'Document')
            doc_type = doc.get('doc_type', 'unknown')
            lines.append(f"{i}. [{doc_type.upper()}] {citation}")
        
        return '\n'.join(lines)
