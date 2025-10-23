# Ingestion Scripts

Scripts for loading data into the database.

## Scripts

- `run_ingestion.py` - Main ingestion pipeline (statutes + cases)
- `ingest_rules.py` - Rules of Court 2021 ingestion
- `batch_ingest.py` - Batch processing for large datasets

## Usage

```bash
# Full ingestion
python scripts/ingestion/run_ingestion.py --filesystem \
  --statutes /path/to/statutes \
  --cases /path/to/cases

# Rules only
python scripts/ingestion/ingest_rules.py --pdf /path/to/rules.pdf
```
