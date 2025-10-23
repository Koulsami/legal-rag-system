# Week 2: Extraction Pipeline

## Structure

```
src/extraction/
├── __init__.py                   # Package exports
├── models.py                     # Data models ✅ INSTALLED
├── rule_based_extractor.py       # Regex extraction (copy from artifacts)
├── llm_assisted_extractor.py     # LLM extraction (copy from artifacts)
├── link_quality_validator.py     # Quality checks (copy from artifacts)
└── pipeline_orchestrator.py      # Main pipeline (copy from artifacts)
```

## Next Steps

1. **Copy remaining modules** from artifacts:
   - rule_based_extractor.py (rule_extractor artifact)
   - llm_assisted_extractor.py (llm_extractor artifact)
   - link_quality_validator.py (quality_validator artifact)
   - pipeline_orchestrator.py (extraction_pipeline artifact)
   - test_extraction_pipeline.py (test_extraction artifact)

2. **Test the pipeline**:
   ```bash
   python -m pytest tests/extraction/test_extraction_pipeline.py -v
   ```

3. **Run extraction** (after ingesting case documents):
   ```python
   from src.extraction import ExtractionPipeline, PipelineConfig
   
   config = PipelineConfig(
       use_rule_based=True,
       openai_api_key="your-key",
       output_dir="./data/extraction_output"
   )
   
   pipeline = ExtractionPipeline(config)
   # Load case paragraphs from database
   # results = await pipeline.run(paragraphs)
   ```

## Integration with Database

The extraction pipeline creates `ExtractedLink` objects that can be saved to your
`interpretation_links` table using the `.to_db_dict()` method.

See `pipeline_orchestrator.py` for the complete workflow.
