# Testing Scripts

Test suites for the application.

## Scripts

- `test_parsers.py` - Parser unit tests
- `test_ingestion.py` - Integration tests
- `test_database.py` - Database tests

## Usage

```bash
# Run all tests
pytest scripts/testing/ -v

# Run specific test
pytest scripts/testing/test_parsers.py -v

# With coverage
pytest scripts/testing/ -v --cov=src --cov-report=html
```
