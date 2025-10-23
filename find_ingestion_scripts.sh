#!/bin/bash

# Find Ingestion Scripts
# Locates all ingestion-related scripts in the project

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Finding Ingestion Scripts"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /home/amee/legal-rag-poc

echo "Searching for ingestion scripts..."
echo ""

# Search for main ingestion script
echo "1. Main ingestion script (run_ingestion.py):"
find . -name "run_ingestion.py" -type f 2>/dev/null | while read file; do
    echo "   FOUND: $file"
done

# Search for rules ingestion script  
echo ""
echo "2. Rules ingestion script (ingest_rules.py):"
find . -name "ingest_rules.py" -type f 2>/dev/null | while read file; do
    echo "   FOUND: $file"
done

# Search for any Python scripts with "ingest" in the name
echo ""
echo "3. All scripts with 'ingest' in name:"
find . -name "*ingest*.py" -type f ! -path "./.venv/*" ! -path "./__pycache__/*" 2>/dev/null | while read file; do
    echo "   $file"
done

# Check if scripts directory exists
echo ""
echo "4. Directory structure:"
if [ -d "scripts" ]; then
    echo "   ✓ scripts/ exists"
    if [ -d "scripts/ingestion" ]; then
        echo "   ✓ scripts/ingestion/ exists"
        ls -la scripts/ingestion/ 2>/dev/null
    else
        echo "   ✗ scripts/ingestion/ does NOT exist"
    fi
else
    echo "   ✗ scripts/ does NOT exist"
fi

# Check src/ingestion
echo ""
echo "5. Checking src/ingestion/:"
if [ -d "src/ingestion" ]; then
    echo "   ✓ src/ingestion/ exists"
    ls -la src/ingestion/*.py 2>/dev/null | grep -v __pycache__
else
    echo "   ✗ src/ingestion/ does NOT exist"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
