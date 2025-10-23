#!/bin/bash

# Find Latest Ingestion Files
# Shows modification dates to identify most recent versions

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  FINDING LATEST INGESTION FILES (by modification date)"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /home/amee/legal-rag-poc

echo "1. INGESTION SCRIPTS (sorted by date):"
echo "────────────────────────────────────────────────────────────────"
find . -name "*ingest*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -exec ls -lh {} \; | \
    awk '{print $6, $7, $8, $9}' | sort -k1,1M -k2,2n -k3,3
echo ""

echo "2. PARSERS (sorted by date):"
echo "────────────────────────────────────────────────────────────────"
find . -name "*parser*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -exec ls -lh {} \; | \
    awk '{print $6, $7, $8, $9}' | sort -k1,1M -k2,2n -k3,3
echo ""

echo "3. DETAILED VIEW - Latest ingestion scripts:"
echo "────────────────────────────────────────────────────────────────"
find . -name "*ingest*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -printf '%T+ %p\n' | sort -r | while read date file; do
    size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
    echo "$date - $file ($size lines)"
done
echo ""

echo "4. DETAILED VIEW - Parsers:"
echo "────────────────────────────────────────────────────────────────"
find . -name "*parser*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -printf '%T+ %p\n' | sort -r | while read date file; do
    size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
    echo "$date - $file ($size lines)"
done
echo ""

echo "5. PIPELINE AND MODELS:"
echo "────────────────────────────────────────────────────────────────"
for file in src/ingestion/pipeline.py src/ingestion/models.py src/ingestion/interfaces.py; do
    if [ -f "$file" ]; then
        date=$(stat -c '%y' "$file" 2>/dev/null || stat -f '%Sm' "$file")
        size=$(wc -l "$file" | awk '{print $1}')
        echo "$date - $file ($size lines)"
    fi
done
echo ""

echo "6. LOADERS:"
echo "────────────────────────────────────────────────────────────────"
if [ -d "src/ingestion/loaders" ]; then
    find src/ingestion/loaders/ -name "*.py" -type f ! -name "__*" -printf '%T+ %p\n' | sort -r | while read date file; do
        size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
        echo "$date - $file ($size lines)"
    done
else
    echo "(loaders directory not found)"
fi
echo ""

echo "7. SOURCES/ADAPTERS:"
echo "────────────────────────────────────────────────────────────────"
if [ -d "src/ingestion/sources" ]; then
    find src/ingestion/sources/ -name "*.py" -type f ! -name "__*" -printf '%T+ %p\n' | sort -r | while read date file; do
        size=$(wc -l "$file" 2>/dev/null | awk '{print $1}')
        echo "$date - $file ($size lines)"
    done
else
    echo "(sources directory not found)"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  MOST RECENT FILES SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Most recent ingestion script:"
find . -name "*ingest*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -printf '%T+ %p\n' | sort -r | head -1

echo ""
echo "Most recent parsers:"
find . -name "*parser*.py" -type f ! -path "./.venv/*" ! -path "*__pycache__*" -printf '%T+ %p\n' | sort -r | head -3

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "TIP: Files modified on Oct 18 are likely the most recent and correct"
echo ""
