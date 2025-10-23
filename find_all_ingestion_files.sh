#!/bin/bash

# Find ALL ingestion-related files
# More comprehensive search

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  COMPREHENSIVE SEARCH FOR INGESTION FILES"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /home/amee/legal-rag-poc

echo "1. All Python files in scripts/ directory:"
echo "────────────────────────────────────────────────────────────────"
find scripts/ -name "*.py" -type f ! -path "*__pycache__*" 2>/dev/null | while read file; do
    echo "   $file"
done
echo ""

echo "2. All Python files in root directory:"
echo "────────────────────────────────────────────────────────────────"
ls -1 *.py 2>/dev/null | while read file; do
    echo "   $file"
done
echo ""

echo "3. Scripts with 'statute' in name:"
echo "────────────────────────────────────────────────────────────────"
find . -name "*statute*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" 2>/dev/null | while read file; do
    echo "   $file"
done
echo ""

echo "4. Scripts with 'case' in name:"
echo "────────────────────────────────────────────────────────────────"
find . -name "*case*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" 2>/dev/null | while read file; do
    echo "   $file"
done
echo ""

echo "5. Scripts with 'rule' in name:"
echo "────────────────────────────────────────────────────────────────"
find . -name "*rule*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" 2>/dev/null | while read file; do
    echo "   $file"
done
echo ""

echo "6. All files in src/ingestion/:"
echo "────────────────────────────────────────────────────────────────"
find src/ingestion/ -type f -name "*.py" 2>/dev/null | while read file; do
    size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
    echo "   $file ($size lines)"
done
echo ""

echo "7. Checking parsers directory:"
echo "────────────────────────────────────────────────────────────────"
if [ -d "src/ingestion/parsers" ]; then
    find src/ingestion/parsers/ -name "*.py" -type f 2>/dev/null | while read file; do
        size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
        echo "   $file ($size lines)"
    done
else
    echo "   (parsers directory not found)"
fi
echo ""

echo "8. Checking loaders directory:"
echo "────────────────────────────────────────────────────────────────"
if [ -d "src/ingestion/loaders" ]; then
    find src/ingestion/loaders/ -name "*.py" -type f 2>/dev/null | while read file; do
        size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
        echo "   $file ($size lines)"
    done
else
    echo "   (loaders directory not found)"
fi
echo ""

echo "9. Checking sources directory:"
echo "────────────────────────────────────────────────────────────────"
if [ -d "src/ingestion/sources" ]; then
    find src/ingestion/sources/ -name "*.py" -type f 2>/dev/null | while read file; do
        size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
        echo "   $file ($size lines)"
    done
else
    echo "   (sources directory not found)"
fi
echo ""

echo "10. Let's check what run_ingestion.py actually does:"
echo "────────────────────────────────────────────────────────────────"
if [ -f "scripts/run_ingestion.py" ]; then
    echo "File: scripts/run_ingestion.py"
    echo ""
    echo "First 30 lines:"
    head -n 30 scripts/run_ingestion.py
    echo ""
    echo "Looking for main() or if __name__:"
    grep -A 10 "if __name__" scripts/run_ingestion.py 2>/dev/null || echo "(not found)"
else
    echo "   scripts/run_ingestion.py not found"
fi
echo ""

echo "11. Check ingest_rules.py:"
echo "────────────────────────────────────────────────────────────────"
if [ -f "scripts/ingest_rules.py" ]; then
    echo "File: scripts/ingest_rules.py"
    echo ""
    echo "First 30 lines:"
    head -n 30 scripts/ingest_rules.py
else
    echo "   scripts/ingest_rules.py not found"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  SEARCH COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
