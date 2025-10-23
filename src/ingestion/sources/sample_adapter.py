"""
Sample data adapter for testing ingestion pipeline.

Generates mock statute and case documents with realistic structure.
Use this when real legal sources aren't available.
"""

from typing import Iterator, Optional
from pathlib import Path
import json

from ..interfaces import SourceAdapter
from ..models import SourceDocument


# ============================================================================
# Sample Data
# ============================================================================

SAMPLE_STATUTES = {
    "misrepresentation_act": """MISREPRESENTATION ACT 1967
(CHAPTER 390)

An Act to amend the law relating to innocent misrepresentations and to amend sections 2(1) and 3 of the Misrepresentation Act 1967.

Section 1: Definitions

(1) In this Act, "misrepresentation" means a false statement of fact made by one party to another which, while not being a term of the contract, induces the other party to enter into the contract.

(2) For the purposes of this Act, a statement is a statement of fact if it is capable of being proved or disproved.

Section 2: Duty to disclose

(1) Where a person has entered into a contract after a misrepresentation has been made to him by another party and as a result thereof he has suffered loss, then if the person making the misrepresentation would be liable to damages in respect thereof had the misrepresentation been made fraudulently, that person shall be so liable notwithstanding that the misrepresentation was not made fraudulently, unless he proves that he had reasonable ground to believe and did believe up to the time the contract was made that the facts represented were true.

(2) This section does not apply in any case where the misrepresentation was made by the defendant through the fraud of a third party for whose conduct he is not vicariously liable.

Section 3: Remedies for misrepresentation

(1) Where a person has entered into a contract after a misrepresentation has been made to him, and the misrepresentation has become a term of the contract, then, without prejudice to the provisions of section 2(1), if otherwise he would be entitled to rescind the contract, he shall be entitled to rescind it.

(2) Damages may be awarded against a person where another has entered into a contract in consequence of a misrepresentation made by that person, whether fraudulently or otherwise.""",

    "contract_law_act": """CONTRACT LAW ACT 2022
(CHAPTER 12A)

An Act to consolidate and modernize the law of contract in Singapore.

Section 1: Formation of contracts

(1) A contract is formed when there is an offer, acceptance, consideration, and intention to create legal relations.

(2) The offer must be communicated to the offeree.

(3) Acceptance must be communicated to the offeror unless the offer waives this requirement.

Section 2: Consideration

(1) Consideration must be sufficient but need not be adequate.

(2) Past consideration is not valid consideration.

(3) A promise to perform an existing duty is not valid consideration unless it provides a practical benefit to the promisor."""
}


SAMPLE_CASES = {
    "wee_chiaw_sek_anna": """WEE CHIAW SEK ANNA v NG LI-ANN GENEVIEVE
[2013] SGCA 36

Court of Appeal - Civil Appeal No 169 of 2012

JUDGMENT

[1] This appeal concerns the scope of a solicitor's duty to disclose conflicts of interest when acting for multiple parties in a property transaction.

[2] The appellant, Anna Wee Chiaw Sek, was the purchaser of a property. The respondent, Genevieve Ng Li-Ann, was a solicitor who acted for both the purchaser and the seller in the transaction.

[3] The facts are as follows. In 2007, the appellant agreed to purchase a property from one Ms Tan. The respondent acted for both parties in the transaction. Unknown to the appellant, Ms Tan was in financial difficulties and the property was subject to a caveat lodged by creditors.

[4] The transaction eventually failed to complete, and the appellant lost her deposit. She sued the respondent for breach of duty, alleging that the respondent failed to disclose the conflict of interest.

[5] The High Court dismissed the claim. The appellant now appeals.

[6] The key issue is whether Section 2 of the Misrepresentation Act applies to a solicitor's failure to disclose conflicts of interest.

[7] We begin by examining the statutory language. Section 2(1) provides that where a person has entered into a contract after a misrepresentation has been made to him, the person making the misrepresentation shall be liable for damages unless he proves reasonable grounds for belief.

[8] The appellant argues that the respondent's failure to disclose the conflict amounted to a misrepresentation. We disagree.

[9] The Misrepresentation Act requires a positive false statement. A mere non-disclosure, even if it amounts to a breach of duty, does not constitute a misrepresentation for the purposes of the Act.

[10] This interpretation is supported by the legislative history. When the Act was enacted in 1967, the Law Reform Committee specifically noted that the Act would not extend to pure non-disclosure cases.

[11] However, this does not leave the appellant without a remedy. A solicitor who fails to disclose a conflict of interest may be liable in negligence or breach of fiduciary duty.

[12] We find that the respondent was indeed in breach of her fiduciary duty to the appellant. However, this breach does not fall within Section 2 of the Misrepresentation Act.

[13] Accordingly, while we find that the respondent breached her duties, we hold that Section 2 of the Misrepresentation Act does not apply to this case.

[14] For these reasons, the appeal is dismissed, but we make no order as to costs given the breach of duty found.""",

    "lim_koon_park": """LIM KOON PARK PETER v YONG TIAN CHOY & ANOTHER
[2020] SGHC 100

High Court - Suit No 452 of 2019

JUDGMENT

[1] This case concerns a dispute over a commercial lease. The plaintiff claims that the defendant made fraudulent misrepresentations which induced him to enter into the lease.

[2] The facts can be stated briefly. The plaintiff agreed to lease commercial premises from the defendant for use as a restaurant. During negotiations, the defendant stated that the premises had "good foot traffic" and "high visibility from the main road."

[3] After taking possession, the plaintiff discovered that a large construction project had commenced next door, significantly reducing foot traffic. The restaurant failed within six months.

[4] The plaintiff now seeks rescission of the lease and damages under Section 2 of the Misrepresentation Act.

[5] The threshold question is whether the defendant's statements were statements of fact or mere opinion. This is a question of mixed fact and law.

[6] Statements of opinion generally do not give rise to liability under the Misrepresentation Act. However, a statement of opinion may be treated as a statement of fact if the person making it knew or ought to have known that the facts did not support the opinion.

[7] Here, the defendant was aware of the planned construction project at the time he made the representations. He was therefore not expressing a genuine opinion about future foot traffic, but rather making a statement about existing circumstances which he knew to be false.

[8] We therefore find that the representations were statements of fact, not opinion.

[9] The next question is whether the defendant has established the defense under Section 2(1) - namely, that he had reasonable grounds to believe the representations were true.

[10] The defendant argues that the construction plans were not finalized at the time of the representations. This argument fails. The defendant was aware of the likelihood of construction and failed to disclose this material fact.

[11] Accordingly, we find that the defendant cannot establish the defense under Section 2(1).

[12] As to remedies, the plaintiff is entitled to rescission of the lease. We also award damages under Section 2(1) for the plaintiff's wasted expenditure in fitting out the premises.

[13] Judgment is therefore entered for the plaintiff."""
}


class SampleAdapter(SourceAdapter):
    """Source adapter that provides sample legal documents"""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.include_statutes = config.get('include_statutes', True) if config else True
        self.include_cases = config.get('include_cases', True) if config else True
    
    def validate_source(self) -> bool:
        """Sample source is always available"""
        return True
    
    def fetch_documents(self) -> Iterator[SourceDocument]:
        """
        Generate sample documents.
        
        Yields:
            SourceDocument objects
        """
        # Yield statutes
        if self.include_statutes:
            for name, content in SAMPLE_STATUTES.items():
                yield SourceDocument(
                    filepath=f"<sample>/{name}.txt",
                    source_type='statute',
                    format='txt',
                    raw_content=content,
                    metadata={'source': 'sample_data'}
                )
        
        # Yield cases
        if self.include_cases:
            for name, content in SAMPLE_CASES.items():
                yield SourceDocument(
                    filepath=f"<sample>/{name}.txt",
                    source_type='case',
                    format='txt',
                    raw_content=content,
                    metadata={'source': 'sample_data'}
                )
    
    def get_source_name(self) -> str:
        """Return source name"""
        return "Sample Data Generator"


class FileAdapter(SourceAdapter):
    """Source adapter that reads documents from file system"""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.statute_dir = Path(config.get('statute_dir', 'data/statutes/raw')) if config else Path('data/statutes/raw')
        self.case_dir = Path(config.get('case_dir', 'data/cases/raw')) if config else Path('data/cases/raw')
    
    def validate_source(self) -> bool:
        """Check that source directories exist"""
        return self.statute_dir.exists() or self.case_dir.exists()
    
    def fetch_documents(self) -> Iterator[SourceDocument]:
        """
        Read documents from file system.
        
        Yields:
            SourceDocument objects
        """
        # Read statutes
        if self.statute_dir.exists():
            for filepath in self.statute_dir.glob('**/*'):
                if not filepath.is_file():
                    continue
                
                if filepath.suffix.lower() in ['.txt', '.html', '.pdf']:
                    yield self._read_file(filepath, 'statute')
        
        # Read cases
        if self.case_dir.exists():
            for filepath in self.case_dir.glob('**/*'):
                if not filepath.is_file():
                    continue
                
                if filepath.suffix.lower() in ['.txt', '.html', '.pdf']:
                    yield self._read_file(filepath, 'case')
    
    def _read_file(self, filepath: Path, doc_type: str) -> SourceDocument:
        """
        Read a single file.
        
        Args:
            filepath: Path to file
            doc_type: Document type
            
        Returns:
            SourceDocument
        """
        content = ""
        
        # Handle PDF files
        if filepath.suffix.lower() == '.pdf':
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            content += page_text + "\n"
                print(f"  ✓ Extracted {len(content)} chars from PDF: {filepath.name}")
            except Exception as e:
                print(f"  ⚠️  Failed to read PDF {filepath.name}: {e}")
                content = ""
        else:
            # Handle text/HTML files
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"  ⚠️  Failed to read {filepath.name}: {e}")
                content = ""
        
        return SourceDocument(
            filepath=str(filepath),
            source_type=doc_type,
            format=filepath.suffix[1:],
            raw_content=content,
            metadata={'source': 'filesystem'}
        )



def create_sample_files(output_dir: str = 'data/sample'):
    """
    Create sample statute and case files on disk.
    
    Args:
        output_dir: Directory to write files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write statutes
    statutes_dir = output_path / 'statutes'
    statutes_dir.mkdir(exist_ok=True)
    
    for name, content in SAMPLE_STATUTES.items():
        filepath = statutes_dir / f"{name}.txt"
        filepath.write_text(content, encoding='utf-8')
        print(f"Created: {filepath}")
    
    # Write cases
    cases_dir = output_path / 'cases'
    cases_dir.mkdir(exist_ok=True)
    
    for name, content in SAMPLE_CASES.items():
        filepath = cases_dir / f"{name}.txt"
        filepath.write_text(content, encoding='utf-8')
        print(f"Created: {filepath}")
    
    print(f"\nSample files created in {output_dir}/")
    print(f"- {len(SAMPLE_STATUTES)} statutes")
    print(f"- {len(SAMPLE_CASES)} cases")
