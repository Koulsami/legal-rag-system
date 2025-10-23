# Legal RAG - Week 1 Models

## Created Files

This installer created the following structure:

```
src/database/models/
├── __init__.py          # Package initialization
├── base.py              # Database manager and base classes
├── document.py          # Document model (TO BE ADDED)
├── interpretation_link.py  # Interpretation link model (TO BE ADDED)
└── tree_utils.py        # Tree traversal utilities (TO BE ADDED)
```

## Next Steps

### Step 1: Complete Model Files

The base.py file has been created. You now need to add the remaining model files.

**IMPORTANT**: Due to file size, you need to manually copy these files from the artifacts:

1. **document.py** - Document model with tree structure
2. **interpretation_link.py** - Interpretation links model
3. **tree_utils.py** - Tree traversal utilities

Copy the content from the artifacts I provided and create these files in:
`src/database/models/`

### Step 2: Update Requirements

Add these to your `requirements.txt` if not already present:

```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

Then install:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Test the Setup

Run the integration test:
```bash
python test_integration.py
```

## Database Connection

Your database connection string should be in your `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/legal_rag
```

## Getting Help

If you encounter issues:
1. Check that PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify your virtual environment is activated: `which python`
3. Check installed packages: `pip list | grep -i sqlalchemy`

For more help, refer to the Week 1 Implementation README.
