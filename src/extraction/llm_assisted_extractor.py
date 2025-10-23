"""
LLM-Assisted Interpretation Link Extractor

Uses GPT-4o-mini to find implicit interpretation relationships.
Expected: 800-1200 links with 75-80% precision, confidence 0.6-0.85
Cost: ~$20-30 for 5000 cases

Week 2: Extraction Pipeline - Part 3/5
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from src.extraction.models import (
    Authority,
    CaseMetadata,
    CaseParagraph,
    ExtractionMethod,
    ExtractionResult,
    InterpretationLink,
    InterpretationType,
)


# ============================================================================
# LLM EXTRACTION PROMPT
# ============================================================================

LLM_EXTRACTION_PROMPT = """Analyze this Singapore court case paragraph for statutory interpretation.

**Case:** {case_name}
**Citation:** {citation}
**Court:** {court}
**Paragraph {para_no}:**
{text}

**Task:** Determine if this paragraph INTERPRETS or APPLIES a statute.

**Rules:**
1. **Interpretation** = Court explains what statute MEANS (clarifies scope, purpose, or application criteria)
2. **Application** = Court applies statute to facts without explaining meaning
3. Mere mention ≠ interpretation (must affect understanding of statute)
4. Must actually change or clarify how statute is understood

**If interpretation found, extract:**
- `statute_name`: Full statute name (e.g., "Misrepresentation Act", "Companies Act")
- `section`: Section number (e.g., "2", "2(1)", "216")
- `interpretation_type`: Choose ONE of:
  - **NARROW**: Court restricts statute scope
  - **BROAD**: Court expands statute scope
  - **CLARIFY**: Court explains ambiguous term
  - **PURPOSIVE**: Court interprets based on legislative intent
  - **LITERAL**: Court applies plain text meaning
  - **APPLY**: Court simply applies statute without interpretation
- `holding`: 1-2 sentence summary of what court held about statute
- `is_binding`: Is this part of ratio decidendi (binding precedent)?

**Return JSON:**
{{
  "has_interpretation": true/false,
  "statute_name": "...",
  "section": "...",
  "interpretation_type": "NARROW|BROAD|CLARIFY|PURPOSIVE|LITERAL|APPLY",
  "holding": "...",
  "is_binding": true/false
}}

**If no interpretation, return:**
{{"has_interpretation": false}}

**Important:** Only mark as interpretation if the court is actually explaining what the statute means, not just mentioning it.
"""


# ============================================================================
# STATUTE KEYWORD DETECTOR
# ============================================================================

def contains_statute_keywords(text: str) -> bool:
    """Check if text likely contains statute discussion"""
    keywords = [
        "section", "s.", "act", "statute", "provision",
        "subsection", "paragraph", "rule", "order",
        "held that", "interpreted", "construed",
        "means", "requires", "applies"
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


# ============================================================================
# STATUTE ID MAPPER
# ============================================================================

class StatuteIDMapper:
    """Map statute name+section to standardized ID"""
    
    # Common statute name mappings
    NAME_MAPPINGS = {
        "misrepresentation act": "misrepresentation_act",
        "contract law act": "contract_law_act",
        "companies act": "companies_act",
        "evidence act": "evidence_act",
        "rules of court": "roc",
        "roc": "roc",
    }
    
    def map_to_id(self, statute_name: str, section: str) -> str:
        """
        Generate standardized statute ID
        
        Args:
            statute_name: Full statute name
            section: Section number
            
        Returns:
            Standardized ID like "sg_statute_misrepresentation_act_s2"
        """
        # Normalize name
        name_lower = statute_name.lower().strip()
        name_normalized = self.NAME_MAPPINGS.get(name_lower, name_lower)
        name_normalized = name_normalized.replace(" ", "_").replace("(", "").replace(")", "")
        
        # Normalize section
        section_normalized = section.replace("(", "").replace(")", "").replace(" ", "")
        
        statute_id = f"sg_statute_{name_normalized}"
        if section_normalized:
            statute_id += f"_s{section_normalized}"
        
        return statute_id


# ============================================================================
# LLM CLIENT WRAPPER (OpenAI-compatible)
# ============================================================================

class LLMClient:
    """Wrapper for OpenAI-compatible LLM API"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize LLM client
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o-mini recommended for cost)
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # GPT-4o-mini pricing (as of 2025)
        self.cost_per_1m_input = 0.15
        self.cost_per_1m_output = 0.60
    
    async def extract_interpretation(
        self,
        case_para: CaseParagraph
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to extract interpretation from paragraph
        
        Returns:
            Parsed JSON response or None if no interpretation
        """
        prompt = LLM_EXTRACTION_PROMPT.format(
            case_name=case_para.case_metadata.case_name,
            citation=case_para.case_metadata.citation,
            court=case_para.case_metadata.court,
            para_no=case_para.para_no,
            text=case_para.text
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal research assistant specializing in Singapore statutory interpretation."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Deterministic
            )
            
            # Track usage
            usage = response.usage
            self.total_tokens += usage.total_tokens
            self.total_cost += (
                (usage.prompt_tokens / 1_000_000) * self.cost_per_1m_input +
                (usage.completion_tokens / 1_000_000) * self.cost_per_1m_output
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            if not result.get("has_interpretation"):
                return None
            
            return result
            
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return None
    
    def get_cost_summary(self) -> str:
        """Get cost summary"""
        return f"Total tokens: {self.total_tokens:,} | Total cost: ${self.total_cost:.2f}"


# ============================================================================
# LLM-ASSISTED EXTRACTOR (MAIN CLASS)
# ============================================================================

class LLMAssistedExtractor:
    """
    Extract interpretation links using LLM
    
    Expected Performance:
    - Precision: 75-80%
    - Recall: 85-90%
    - Output: 800-1200 links from 5000 cases
    - Cost: ~$20-30 for full corpus
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize extractor
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.llm_client = LLMClient(api_key, model)
        self.statute_mapper = StatuteIDMapper()
    
    async def extract(
        self,
        case_paragraphs: List[CaseParagraph],
        batch_size: int = 10,
        max_paragraphs: Optional[int] = None,
        verbose: bool = False
    ) -> ExtractionResult:
        """
        Extract interpretation links using LLM
        
        Args:
            case_paragraphs: List of case paragraphs to process
            batch_size: Number of parallel LLM calls
            max_paragraphs: Limit for testing (None = all)
            verbose: Print progress
            
        Returns:
            ExtractionResult with extracted links and metrics
        """
        start_time = time.time()
        
        # Filter to likely candidates (reduces cost)
        candidates = [
            p for p in case_paragraphs
            if contains_statute_keywords(p.text) and len(p.text) > 100
        ]
        
        if max_paragraphs:
            candidates = candidates[:max_paragraphs]
        
        if verbose:
            print(f"Filtered to {len(candidates)} candidate paragraphs")
        
        # Process in batches
        links: List[InterpretationLink] = []
        cases_processed = set()
        
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            
            # Parallel LLM calls
            tasks = [
                self.llm_client.extract_interpretation(para)
                for para in batch
            ]
            results = await asyncio.gather(*tasks)
            
            # Create links
            for para, result in zip(batch, results):
                cases_processed.add(para.case_metadata.doc_id)
                
                if result:
                    link = self._create_link(para, result)
                    if link:
                        links.append(link)
            
            if verbose and (i + batch_size) % 100 == 0:
                print(f"Processed {i + batch_size}/{len(candidates)} paragraphs... "
                      f"({len(links)} links, {self.llm_client.get_cost_summary()})")
        
        duration = time.time() - start_time
        
        if verbose:
            print(f"\nFinal: {self.llm_client.get_cost_summary()}")
        
        return ExtractionResult(
            links=links,
            total_cases_processed=len(cases_processed),
            total_paragraphs_scanned=len(candidates),
            extraction_method=ExtractionMethod.LLM_ASSISTED,
            duration_seconds=duration
        )
    
    def _create_link(
        self,
        para: CaseParagraph,
        llm_result: Dict[str, Any]
    ) -> Optional[InterpretationLink]:
        """Create interpretation link from LLM result"""
        
        try:
            # Parse interpretation type
            interp_type = InterpretationType[llm_result["interpretation_type"]]
        except (KeyError, ValueError):
            interp_type = InterpretationType.CLARIFY
        
        # Determine authority
        is_binding = llm_result.get("is_binding", False)
        if para.case_metadata.court.upper() in {"SGCA", "CA"}:
            authority = Authority.BINDING if is_binding else Authority.PERSUASIVE
            boost_factor = 2.5 if is_binding else 1.8
        else:
            authority = Authority.PERSUASIVE
            boost_factor = 1.8
        
        # Generate statute ID
        statute_id = self.statute_mapper.map_to_id(
            llm_result.get("statute_name", ""),
            llm_result.get("section", "")
        )
        
        # Create link
        link = InterpretationLink(
            statute_id=statute_id,
            case_id=para.paragraph_id,
            statute_name=llm_result.get("statute_name", ""),
            statute_section=llm_result.get("section", ""),
            statute_text="",  # Populated later
            case_name=para.case_metadata.case_name,
            case_citation=para.case_metadata.citation,
            case_para_no=para.para_no,
            case_text=para.text,
            court=para.case_metadata.court,
            year=para.case_metadata.year,
            interpretation_type=interp_type,
            authority=authority,
            holding=llm_result.get("holding", "")[:300],  # Truncate
            extraction_method=ExtractionMethod.LLM_ASSISTED,
            confidence=0.7,  # Medium confidence, needs verification
            boost_factor=boost_factor,
        )
        
        return link


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def main():
    """Example usage"""
    import os
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable")
        return
    
    # Create sample case paragraph
    sample_para = CaseParagraph(
        para_no=45,
        text="""
        In determining whether a duty to disclose arises, we must consider the 
        legislative intent behind Section 2 of the Misrepresentation Act. The 
        provision was enacted to protect vulnerable parties in relationships of 
        trust and confidence. Accordingly, we adopt a purposive interpretation 
        and hold that the duty extends to situations where one party possesses 
        material information that the other party could not reasonably obtain.
        """,
        case_metadata=CaseMetadata(
            doc_id="sg_case_2015_sgca_12",
            case_name="Example Case v Test Case",
            citation="[2015] SGCA 12",
            court="SGCA",
            year=2015
        )
    )
    
    # Extract links
    extractor = LLMAssistedExtractor(api_key)
    result = await extractor.extract([sample_para], verbose=True)
    
    print(result.summary())
    
    if result.links:
        print("\nFirst Link:")
        link = result.links[0]
        print(f"Statute: {link.statute_id}")
        print(f"Case: {link.case_id}")
        print(f"Type: {link.interpretation_type.value}")
        print(f"Authority: {link.authority.value}")
        print(f"Confidence: {link.confidence:.2f}")
        print(f"Holding: {link.holding}")


if __name__ == "__main__":
    asyncio.run(main())
