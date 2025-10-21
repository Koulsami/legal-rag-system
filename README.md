# Legal RAG System - Complete File Documentation

**Generated:** 2025-10-17 15:22:10
**Project:** Legal Diagnostic RAG for Statutory Interpretation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Quick Start](#2-quick-start)
3. [File Documentation](#3-file-documentation)
   - [Database Models](#database-models)
   - [Extraction Pipeline](#extraction-pipeline)
   - [Tests](#tests)
   - [Setup & Installation](#setup--installation)
   - [Diagnostic & Status](#diagnostic--status)
   - [Utilities](#utilities)
4. [Development Workflow](#4-development-workflow)
5. [Architecture](#5-architecture)

---

## 1. Project Overview

This is a **Legal RAG (Retrieval-Augmented Generation) system** specialized for
Singapore statutory interpretation. The system:

- Links statutes to interpretive case law
- Enables fact-pattern-based matching
- Provides synthesis-aware generation
- Maintains high citation accuracy

**Core Innovation:** Interpretation Links Database - pairs statute sections
with case paragraphs that interpret them.

## 2. Quick Start

### Initial Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_database.py

# Verify installation
python verify_database.py
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/extraction/ -v
```

### Generate Status
```bash
# Create installation status document
python generate_installation_status.py

# View status
cat INSTALLATION_STATUS.md
```

## 3. File Documentation

### Database Models

*5 file(s)*

### `src/database/models/__init__.py`

**Size:** 1.0 KB | **Lines:** 62

**Purpose:**
```
Legal Diagnostic RAG - Database Models Package
```

---

### `src/database/models/base.py`

**Size:** 4.3 KB | **Lines:** 138

**Purpose:**
```
Database configuration and base models for Legal Diagnostic RAG.
```

**Classes:**
- `Base`
  - Base class for all SQLAlchemy models.
  - Methods: to_dict, __repr__
- `TimestampMixin`
  - Mixin for created_at and updated_at timestamps.
  - Methods: created_at, updated_at
- `DatabaseManager`
  - Manages database connections and sessions.
  - Methods: __init__, _setup_extensions, create_all, drop_all, get_session

**Key Functions:**
- `init_db(database_url)`
  - Initialize global database manager.
- `get_session()`
  - Get a database session from global manager.
- `to_dict(self)`
  - Convert model instance to dictionary.
- `created_at(cls)`
  - Timestamp when record was created.
- `updated_at(cls)`
  - Timestamp when record was last updated.
- ... and 3 more functions

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### `src/database/models/document.py`

**Size:** 8.2 KB | **Lines:** 228

**Purpose:**
```
Document model with hierarchical tree structure support.
```

**Classes:**
- `DocType`
  - Document type enumeration.
- `Outcome`
  - Case outcome enumeration.
- `Document`
  - Document model supporting both statutes and cases with tree structure.
  - Methods: is_statute, is_case, is_root, is_leaf, get_ancestors

**Key Functions:**
- `is_statute(self)`
  - Check if document is a statute.
- `is_case(self)`
  - Check if document is a case.
- `is_root(self)`
  - Check if document is a root node.
- `is_leaf(self)`
  - Check if document is a leaf node.
- `get_ancestors(self, session)`
  - Get all ancestor documents.
- ... and 4 more functions

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### `src/database/models/interpretation_link.py`

**Size:** 12.3 KB | **Lines:** 296

**Purpose:**
```
Interpretation link model with fact-pattern awareness.
This is the PRIMARY INNOVATION of the Legal Diagnostic RAG system.
```

**Classes:**
- `InterpretationType`
  - How the case interprets the statute.
- `Authority`
  - Legal authority level of the interpretation.
- `InterpretationLink`
  - Links statute sections to interpretive case paragraphs.
  - Methods: is_binding, is_verified, is_high_confidence, effective_boost, matches_fact_pattern
- `InterpretationLinkBuilder`
  - Builder pattern for creating interpretation links.
  - Methods: __init__, with_statute, with_case, with_interpretation, with_fact_pattern

**Key Functions:**
- `is_binding(self)`
  - Check if interpretation has binding authority.
- `is_verified(self)`
  - Check if link has been manually verified.
- `is_high_confidence(self)`
  - Check if extraction confidence is high.
- `effective_boost(self)`
  - Calculate effective boost considering applicability score.
- `matches_fact_pattern(self, user_tags)`
  - Check if interpretation matches user's fact pattern.
- ... and 10 more functions

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### `src/database/models/tree_utils.py`

**Size:** 12.4 KB | **Lines:** 391

**Purpose:**
```
Tree traversal utilities for hierarchical document structure.
```

**Classes:**
- `TreeNode`
  - Represents a node in the document tree.
  - Methods: __post_init__, add_child, is_root, is_leaf, get_path
- `TreeTraversal`
  - Utilities for traversing document tree structures.
  - Methods: __init__, get_parent, get_siblings, get_children, build_complete_provision

**Key Functions:**
- `get_complete_provision_for_retrieval(session, doc_id)`
  - Get complete provision with all context for retrieval results.
- `visualize_document_tree(session, root_id, max_depth)`
  - Visualize document tree structure.
- `add_child(self, child)`
  - Add a child node.
- `is_root(self)`
  - Check if this is a root node.
- `is_leaf(self)`
  - Check if this is a leaf node.
- ... and 17 more functions

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### Extraction Pipeline

*8 file(s)*

### `install_extraction_pipeline.py`

**Size:** 10.4 KB | **Lines:** 368

**Purpose:**
```
Install Week 2 Extraction Pipeline

This script creates the extraction pipeline files and integrates them
with your existing database models.

Directory structure created:
src/extraction/
  ├── __init__.py
  ├── models.py                    # Data models for extraction
  ├── rule_based_extractor.py      # Regex-based extraction
  ├── llm_assisted_extractor.py    # LLM-based extraction
  ├── link_quality_validator.py    # Quality validation
  ├── pipeline_orchestrator.py     # Main pipeline
  └── README.md

tests/extraction/
  ├── __init__.py
  └── test_extraction_pipeline.py
```

**Classes:**
- `Colors`

**Key Functions:**
- `print_header()`
- `print_success(msg)`
- `print_info(msg)`
- `print_warning(msg)`
- `create_directories()`
  - Create extraction directories
- ... and 2 more functions

**Usage:**
```bash
python install_extraction_pipeline.py
```

---

### `src/extraction/__init__.py`

**Size:** 0.7 KB | **Lines:** 32

**Purpose:**
```
Extraction pipeline for interpretation links.
Week 2: Core extraction functionality
```

---

### `src/extraction/extraction_pipeline_orchestrator.py`

**Size:** 14.5 KB | **Lines:** 424

**Purpose:**
```
Interpretation Links Extraction Pipeline Orchestrator

Coordinates rule-based, LLM-assisted, and quality validation.
Week 2: Extraction Pipeline - Part 5/5
```

**Classes:**
- `PipelineConfig`
  - Configuration for extraction pipeline
  - Methods: __init__
- `ExtractionPipeline`
  - Orchestrates complete interpretation links extraction
  - Methods: __init__, _merge_links, _export_results, _save_links_json, _save_statistics

**Usage:**
```bash
# Import in your code:
from src.extraction import ExtractionPipeline
```

---

### `src/extraction/link_quality_validator.py`

**Size:** 14.8 KB | **Lines:** 430

**Purpose:**
```
Interpretation Link Quality Validator

Validates extracted links to ensure high quality before database insertion.
Targets: 80%+ links pass quality threshold

Week 2: Extraction Pipeline - Part 4/5
```

**Classes:**
- `QualityValidator`
  - Validates interpretation link quality
  - Methods: __init__, validate, validate_batch, filter_passing, _check_statute_mentioned
- `BatchValidator`
  - Validate and filter large batches of links
  - Methods: __init__, validate_and_report, _print_report, export_failed_for_review

**Key Functions:**
- `validate(self, link)`
  - Validate a single interpretation link
- `validate_batch(self, links)`
  - Validate multiple links
- `filter_passing(self, links)`
  - Return only links that pass quality validation
- `validate_and_report(self, links, verbose)`
  - Validate links and generate report
- `export_failed_for_review(self, scores, output_path)`
  - Export failed links for manual review

**Usage:**
```bash
# Import in your code:
from src.extraction import ExtractionPipeline
```

---

### `src/extraction/llm_assisted_extractor.py`

**Size:** 14.0 KB | **Lines:** 423

**Purpose:**
```
LLM-Assisted Interpretation Link Extractor

Uses GPT-4o-mini to find implicit interpretation relationships.
Expected: 800-1200 links with 75-80% precision, confidence 0.6-0.85
Cost: ~$20-30 for 5000 cases

Week 2: Extraction Pipeline - Part 3/5
```

**Classes:**
- `StatuteIDMapper`
  - Map statute name+section to standardized ID
  - Methods: map_to_id
- `LLMClient`
  - Wrapper for OpenAI-compatible LLM API
  - Methods: __init__, get_cost_summary
- `LLMAssistedExtractor`
  - Extract interpretation links using LLM
  - Methods: __init__, _create_link

**Key Functions:**
- `contains_statute_keywords(text)`
  - Check if text likely contains statute discussion
- `map_to_id(self, statute_name, section)`
  - Generate standardized statute ID
- `get_cost_summary(self)`
  - Get cost summary

**Usage:**
```bash
# Import in your code:
from src.extraction import ExtractionPipeline
```

---

### `src/extraction/models.py`

**Size:** 3.5 KB | **Lines:** 140

**Purpose:**
```
Data models for extraction pipeline.

These are INPUT/OUTPUT models for the extraction process.
The actual database models are in src/database/models/.
```

**Classes:**
- `InterpretationType`
  - Types of statutory interpretation
- `Authority`
  - Authority level
- `ExtractionMethod`
  - Extraction method
- `CaseParagraphInput`
  - Input: Case paragraph for extraction
  - Methods: paragraph_id
- `ExtractedLink`
  - Output: Extracted interpretation link (before DB save)
  - Methods: to_db_dict
- ... and 3 more classes

**Key Functions:**
- `paragraph_id(self)`
- `to_db_dict(self)`
  - Convert to dictionary for database insertion
- `summary(self)`

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### `src/extraction/models_adapter.py`

**Size:** 0.2 KB | **Lines:** 9

**Purpose:**
```
Adapter to use existing database models with extraction pipeline
```

**Usage:**
```bash
# Import in your code:
from src.database.models import Document, InterpretationLink
```

---

### `src/extraction/rule_based_extractor.py`

**Size:** 15.9 KB | **Lines:** 485

**Purpose:**
```
Rule-Based Interpretation Link Extractor

Uses regex patterns to find explicit interpretation relationships.
Expected: 300-500 links with 90%+ precision, confidence 0.8-0.9

Week 2: Extraction Pipeline - Part 2/5
```

**Classes:**
- `StatuteCitationExtractor`
  - Extract statute citations from text
  - Methods: __init__, extract
- `InterpretationTypeClassifier`
  - Classify interpretation type from paragraph text
  - Methods: __init__, _compile_patterns, _map_pattern_type, classify
- `AuthorityDeterminer`
  - Determine authority level of interpretation
  - Methods: determine, _is_obiter, _is_dissent
- `HoldingExtractor`
  - Extract holding statement from paragraph
  - Methods: extract, _split_sentences
- `RuleBasedExtractor`
  - Extract interpretation links using regex patterns
  - Methods: __init__, extract, _has_interpretation_pattern, _create_link, _generate_statute_id

**Key Functions:**
- `extract(self, text)`
  - Find all statute citations in text
- `classify(self, text)`
  - Classify interpretation type
- `determine(self, case_metadata, paragraph_text)`
  - Determine authority level
- `extract(self, text, statute_cite)`
  - Extract 1-2 sentence holding about statute
- `extract(self, case_paragraphs, verbose)`
  - Extract interpretation links from case paragraphs

**Usage:**
```bash
# Import in your code:
from src.extraction import ExtractionPipeline
```

---

### Tests

*5 file(s)*

### `test_connection.py`

**Size:** 0.8 KB | **Lines:** 24

**Usage:**
```bash
python test_connection.py
# or
pytest test_connection.py -v
```

---

### `test_setup.py`

**Size:** 3.6 KB | **Lines:** 102

**Purpose:**
```
Simple test to verify the development environment is working.
```

**Key Functions:**
- `test_database_connection()`
  - Test PostgreSQL connection
- `test_table_operations()`
  - Test creating table, inserting, and querying data
- `test_imports()`
  - Test that all critical packages can be imported
- `main()`
  - Run all tests

**Usage:**
```bash
python test_setup.py
# or
pytest test_setup.py -v
```

---

### `test_simple.py`

**Size:** 3.9 KB | **Lines:** 129

**Purpose:**
```
Simple test to verify everything works.
```

**Key Functions:**
- `test_basic_operations()`

**Usage:**
```bash
python test_simple.py
# or
pytest test_simple.py -v
```

---

### `tests/extraction/__init__.py`

**Size:** 0.0 KB | **Lines:** 1

**Purpose:**
```
Tests for extraction pipeline
```

---

### `tests/extraction/test_extraction_pipeline.py`

**Size:** 15.0 KB | **Lines:** 442

**Purpose:**
```
Test Suite for Interpretation Links Extraction Pipeline

Covers: Models, Rule-based, LLM, Validation, Pipeline Orchestration
Target: 90%+ test coverage

Week 2: Extraction Pipeline - Tests
```

**Classes:**
- `TestInterpretationLink`
  - Test InterpretationLink data model
  - Methods: test_valid_link_creation, test_invalid_confidence_rejected, test_invalid_boost_factor_rejected, test_to_dict_serialization
- `TestStatuteCitationExtractor`
  - Test statute citation extraction
  - Methods: test_extract_basic_citation, test_extract_with_chapter, test_extract_multiple_citations, test_no_citation_returns_empty
- `TestInterpretationTypeClassifier`
  - Test interpretation type classification
  - Methods: test_classify_narrow_interpretation, test_classify_broad_interpretation, test_classify_purposive_interpretation, test_classify_ambiguous_defaults_to_clarify
- `TestAuthorityDeterminer`
  - Test authority level determination
  - Methods: test_sgca_binding_authority, test_sghc_persuasive_authority, test_obiter_dicta_detection, test_dissent_detection
- `TestRuleBasedExtractor`
  - Test rule-based extraction
  - Methods: test_extract_from_valid_paragraph, test_no_extraction_without_statute, test_extraction_confidence_range
- ... and 2 more classes

**Key Functions:**
- `sample_case_metadata()`
  - Sample case metadata
- `sample_paragraph(sample_case_metadata)`
  - Sample case paragraph with interpretation
- `sample_statute_citation()`
  - Sample statute citation
- `sample_interpretation_link(sample_case_metadata)`
  - Sample interpretation link
- `test_valid_link_creation(self, sample_interpretation_link)`
  - Test creating valid interpretation link
- ... and 22 more functions

**Usage:**
```bash
python test_extraction_pipeline.py
# or
pytest test_extraction_pipeline.py -v
```

---

### Setup & Installation

*4 file(s)*

### `generate_installation_status.py`

**Size:** 16.3 KB | **Lines:** 473

**Purpose:**
```
Generate INSTALLATION_STATUS.md

This script inspects your current installation and creates a comprehensive
status document for continuity across conversations.
```

**Key Functions:**
- `get_file_tree(directory, prefix, max_depth, ...)`
  - Generate file tree structure
- `check_database_status()`
  - Check database connection and tables
- `check_python_files(base_path)`
  - Count and categorize Python files
- `generate_status_md()`
  - Generate the complete status markdown
- `main()`

**Usage:**
```bash
python generate_installation_status.py
```

---

### `install_models.py`

**Size:** 1.1 KB | **Lines:** 45

**Purpose:**
```
Installer script for Legal RAG Week 1 models.
This creates all necessary model files.
```

**Key Functions:**
- `create_file(path, content)`
  - Create a file with given content.
- `main()`

**Usage:**
```bash
python install_models.py
```

---

### `install_week1_models.py`

**Size:** 12.8 KB | **Lines:** 445

**Purpose:**
```
Legal RAG Week 1 - Automated Model Installer

This script automatically creates all Week 1 model files in your project.
Just run: python3 install_week1_models.py

Created files:
- src/database/models/base.py
- src/database/models/document.py
- src/database/models/interpretation_link.py
- src/database/models/tree_utils.py
- src/database/models/__init__.py
```

**Classes:**
- `Colors`

**Key Functions:**
- `print_header()`
  - Print script header.
- `print_success(msg)`
- `print_info(msg)`
- `print_warning(msg)`
- `print_error(msg)`
- ... and 4 more functions

**Usage:**
```bash
python install_week1_models.py
```

---

### `setup_database.py`

**Size:** 2.2 KB | **Lines:** 73

**Purpose:**
```
Setup script to create database tables.
```

**Key Functions:**
- `main()`

**Usage:**
```bash
python setup_database.py
```

---

### Diagnostic & Status

*4 file(s)*

### `deep_diagnostic.py`

**Size:** 14.6 KB | **Lines:** 480

**Purpose:**
```
Deep Diagnostic - Find Everything

Searches entire project for any relevant files, databases, configs, etc.
```

**Key Functions:**
- `print_section(title)`
  - Print section header
- `run_command(cmd, cwd)`
  - Run shell command and return output
- `search_for_files(root, patterns, exclude_dirs)`
  - Search for files matching patterns
- `check_git_info()`
  - Check git repository information
- `find_project_files()`
  - Find all relevant project files
- ... and 9 more functions

**Usage:**
```bash
python deep_diagnostic.py
```

---

### `diagnostic_check.py`

**Size:** 11.2 KB | **Lines:** 369

**Purpose:**
```
Diagnostic Script - Review Current Project State

Run this to show Claude what's actually been built and the current environment.
```

**Key Functions:**
- `print_section(title)`
  - Print section header
- `check_directory_structure()`
  - Check project directory structure
- `check_database_connection()`
  - Check database connection and schema
- `check_sqlalchemy_models()`
  - Check if SQLAlchemy models exist
- `check_extraction_pipeline()`
  - Check extraction pipeline modules
- ... and 6 more functions

**Usage:**
```bash
python diagnostic_check.py
```

---

### `show_existing_code.py`

**Size:** 2.0 KB | **Lines:** 79

**Purpose:**
```
Show Existing Code - Display key files for Claude to review
```

**Key Functions:**
- `show_file(filepath, max_lines)`
  - Display file contents
- `main()`
  - Show all key existing files

---

### `verify_database.py`

**Size:** 3.8 KB | **Lines:** 108

**Purpose:**
```
Verify database setup and show table information
```

**Key Functions:**
- `main()`

**Usage:**
```bash
python verify_database.py
```

---

### Utilities

*1 file(s)*

### `generate_comprehensive_readme.py`

**Size:** 17.0 KB | **Lines:** 452

**Purpose:**
```
Generate Comprehensive README.md

Analyzes all Python files and creates detailed documentation
explaining what each file does, how to use it, and its purpose.
```

**Key Functions:**
- `extract_file_info(filepath)`
  - Extract docstring, functions, and classes from a Python file
- `categorize_files(base_path)`
  - Categorize Python files by purpose
- `generate_file_documentation(filepath, base_path, info)`
  - Generate markdown documentation for a single file
- `get_usage_hint(filepath)`
  - Generate usage hint based on filename
- `generate_readme()`
  - Generate comprehensive README.md
- ... and 1 more functions

**Usage:**
```bash
python generate_comprehensive_readme.py
```

---

## 4. Development Workflow

### Week 1: Database Foundation (COMPLETE)
- [x] Database models created
- [x] Tables created in PostgreSQL
- [x] Tree structure implemented

### Week 2: Extraction Pipeline (COMPLETE)
- [x] Rule-based extractor
- [x] LLM-assisted extractor
- [x] Quality validator
- [x] Pipeline orchestrator
- [x] Test suite

### Week 3: Document Ingestion (IN PROGRESS)
- [ ] Ingest Singapore statutes
- [ ] Ingest case law
- [ ] Populate documents table

### Week 4: Extraction Execution
- [ ] Run extraction pipeline
- [ ] Generate interpretation links
- [ ] Manual verification

### Week 5-6: Retrieval & Synthesis
- [ ] Build retrieval engine
- [ ] Implement synthesis prompts
- [ ] End-to-end testing

## 5. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Hybrid Retrieval Engine                    │
│  (BM25 + Dense Embeddings + Classification)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Interpretation Links Database                   │
│  (Statute ID → Case IDs with boost factors)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Enhanced Context Assembly                     │
│  (Statute + Interpretive Cases + Markers)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Synthesis-Aware Generation                      │
│  (4-step: Quote → Interpret → Synthesize → Summary)     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Validated Response                         │
└─────────────────────────────────────────────────────────┘
```

---

## Regenerating This File

```bash
python generate_comprehensive_readme.py
```

*Last updated: 2025-10-17 15:22:10*
