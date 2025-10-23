#!/bin/bash

# Rebuild Database Script - Week 3 Complete Ingestion
# Version: 2.0
# Date: 2025-10-18
# Description: Clean rebuild of database with all Week 3 data sources

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/amee/legal-rag-poc"
DB_NAME="legal_rag_dev"
DB_USER="legal_rag"
DB_PASSWORD="legal_rag_2025"
DB_HOST="localhost"
DB_PORT="5432"

# Data sources
STATUTES_DIR="/home/amee/LegalDB/Statue"
CASES_DIR="/home/amee/LegalDB/Case"
RULES_PDF="/home/amee/LegalDB/Rules_of_Court_2021.pdf"  # Update if different

# Expected results
EXPECTED_TOTAL=1630
EXPECTED_STATUTES=14
EXPECTED_RULES=650
EXPECTED_CASES=816

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Database Rebuild - Week 3 Complete Ingestion              ║"
echo "╔════════════════════════════════════════════════════════════════╝"
echo ""

# Check if in correct directory
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}Error: Project directory not found: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo -e "${BLUE}Working directory: $(pwd)${NC}"
echo ""

# Step 0: Check data sources
echo "════════════════════════════════════════════════════════════════"
echo "STEP 0: Check data sources"
echo "════════════════════════════════════════════════════════════════"
echo ""

check_data_source() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        if [ -d "$path" ]; then
            count=$(find "$path" -type f -name "*.pdf" 2>/dev/null | wc -l)
            echo -e "${GREEN}✓${NC} $description: $path ($count PDFs)"
        else
            echo -e "${GREEN}✓${NC} $description: $path"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} $description: $path (NOT FOUND)"
        return 1
    fi
}

ALL_SOURCES_OK=true

check_data_source "$STATUTES_DIR" "Statutes directory" || ALL_SOURCES_OK=false
check_data_source "$CASES_DIR" "Cases directory" || ALL_SOURCES_OK=false

# Check for Rules PDF - try common locations
RULES_FOUND=false
RULES_LOCATIONS=(
    "/home/amee/LegalDB/Rules_of_Court_2021.pdf"
    "/home/amee/LegalDB/Rules/Rules_of_Court_2021.pdf"
    "/home/amee/legal-rag-poc/data/rules/Rules_of_Court_2021.pdf"
)

for rules_path in "${RULES_LOCATIONS[@]}"; do
    if [ -f "$rules_path" ]; then
        RULES_PDF="$rules_path"
        check_data_source "$RULES_PDF" "Rules of Court PDF"
        RULES_FOUND=true
        break
    fi
done

if [ "$RULES_FOUND" = false ]; then
    echo -e "${YELLOW}⚠${NC} Rules of Court PDF not found in common locations"
    echo "  Tried:"
    for rules_path in "${RULES_LOCATIONS[@]}"; do
        echo "    - $rules_path"
    done
    echo ""
    echo "  Enter path to Rules of Court PDF (or press Enter to skip):"
    read -r rules_input
    if [ -n "$rules_input" ] && [ -f "$rules_input" ]; then
        RULES_PDF="$rules_input"
        echo -e "${GREEN}✓${NC} Using: $RULES_PDF"
    else
        echo -e "${YELLOW}⚠${NC} Will skip Rules of Court ingestion"
        RULES_PDF=""
    fi
fi

echo ""

if [ "$ALL_SOURCES_OK" = false ] && [ -z "$RULES_PDF" ]; then
    echo -e "${RED}Error: Required data sources not found${NC}"
    echo "Please check the paths above and update the script if needed"
    exit 1
fi

# Step 1: Check prerequisites
echo "════════════════════════════════════════════════════════════════"
echo "STEP 1: Check prerequisites"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check Python environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Please create with: python3 -m venv .venv"
    exit 1
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Check database connection
if ! psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "SELECT 1" >/dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    echo "Please check database connection settings"
    exit 1
else
    echo -e "${GREEN}✓${NC} Database connection OK"
fi

# Check ingestion scripts
if [ ! -f "scripts/ingestion/run_ingestion.py" ]; then
    echo -e "${YELLOW}⚠${NC} scripts/ingestion/run_ingestion.py not found"
    # Try old location
    if [ -f "run_ingestion.py" ]; then
        echo -e "${BLUE}  Using: run_ingestion.py${NC}"
        INGESTION_SCRIPT="run_ingestion.py"
    else
        echo -e "${RED}✗ Ingestion script not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Ingestion scripts found"
    INGESTION_SCRIPT="scripts/ingestion/run_ingestion.py"
fi

# Check Rules ingestion script
if [ -n "$RULES_PDF" ]; then
    if [ ! -f "scripts/ingestion/ingest_rules.py" ]; then
        if [ -f "ingest_rules.py" ]; then
            echo -e "${BLUE}  Using: ingest_rules.py${NC}"
            RULES_SCRIPT="ingest_rules.py"
        else
            echo -e "${YELLOW}⚠${NC} Rules ingestion script not found"
            RULES_PDF=""  # Skip rules if script not found
        fi
    else
        echo -e "${GREEN}✓${NC} Rules ingestion script found"
        RULES_SCRIPT="scripts/ingestion/ingest_rules.py"
    fi
fi

echo ""

# Step 2: Backup current database
echo "════════════════════════════════════════════════════════════════"
echo "STEP 2: Backup current database"
echo "════════════════════════════════════════════════════════════════"
echo ""

BACKUP_FILE="backup_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${BLUE}Creating backup: $BACKUP_FILE${NC}"

if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
    pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || true
    
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✓ Backup created: $BACKUP_FILE ($backup_size)${NC}"
    else
        echo -e "${YELLOW}⚠ Backup failed or database is empty${NC}"
        rm -f "$BACKUP_FILE"
        BACKUP_FILE=""
    fi
else
    echo -e "${YELLOW}⚠ Database doesn't exist yet (first time setup)${NC}"
    BACKUP_FILE=""
fi

echo ""

# Step 3: Confirmation
echo "════════════════════════════════════════════════════════════════"
echo "STEP 3: Confirm database rebuild"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}⚠ WARNING: This will:${NC}"
echo "  1. Drop the existing database: $DB_NAME"
echo "  2. Create a fresh database"
echo "  3. Re-ingest all data:"
echo "     - Misrepresentation Act (from $STATUTES_DIR)"
echo "     - Cases (from $CASES_DIR)"
if [ -n "$RULES_PDF" ]; then
    echo "     - Rules of Court 2021 (from $RULES_PDF)"
fi
echo ""

if [ -n "$BACKUP_FILE" ]; then
    echo -e "${BLUE}Backup saved at: $BACKUP_FILE${NC}"
    echo "You can restore with: psql $DB_NAME < $BACKUP_FILE"
else
    echo -e "${YELLOW}No backup created (database was empty or doesn't exist)${NC}"
fi

echo ""
echo "Expected results:"
echo "  - Total documents: ~$EXPECTED_TOTAL"
echo "  - Statutes: $EXPECTED_STATUTES (Misrepresentation Act)"
if [ -n "$RULES_PDF" ]; then
    echo "  - Rules: $EXPECTED_RULES (Rules of Court 2021)"
fi
echo "  - Cases: $EXPECTED_CASES (judgments + paragraphs)"
echo ""

read -p "Continue with database rebuild? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}✗ Database rebuild cancelled${NC}"
    echo ""
    exit 0
fi

# Step 4: Drop and recreate database
echo "════════════════════════════════════════════════════════════════"
echo "STEP 4: Drop and recreate database"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Dropping database $DB_NAME..."
dropdb -h "$DB_HOST" -U "$DB_USER" --if-exists "$DB_NAME" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Database dropped"

echo "Creating database $DB_NAME..."
createdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME"
echo -e "${GREEN}✓${NC} Database created"

# Run migrations (if schema file exists)
if [ -f "schema.sql" ]; then
    echo "Applying schema..."
    psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" < schema.sql >/dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Schema applied"
fi

echo ""

# Step 5: Ingest statutes and cases
echo "════════════════════════════════════════════════════════════════"
echo "STEP 5: Ingest statutes and cases"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${CYAN}Running main ingestion pipeline...${NC}"
echo ""

python "$INGESTION_SCRIPT" --filesystem \
    --statutes "$STATUTES_DIR" \
    --cases "$CASES_DIR" 2>&1 | tee ingestion_log.txt

INGESTION_SUCCESS=$?

echo ""

if [ $INGESTION_SUCCESS -eq 0 ]; then
    echo -e "${GREEN}✓ Statutes and cases ingestion completed${NC}"
else
    echo -e "${RED}✗ Statutes and cases ingestion failed${NC}"
    echo "Check ingestion_log.txt for details"
fi

echo ""

# Step 6: Ingest Rules of Court (if available)
if [ -n "$RULES_PDF" ] && [ -n "$RULES_SCRIPT" ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo "STEP 6: Ingest Rules of Court 2021"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    echo -e "${CYAN}Running Rules of Court ingestion...${NC}"
    echo ""
    
    python "$RULES_SCRIPT" --pdf "$RULES_PDF" 2>&1 | tee rules_log.txt
    
    RULES_SUCCESS=$?
    
    echo ""
    
    if [ $RULES_SUCCESS -eq 0 ]; then
        echo -e "${GREEN}✓ Rules of Court ingestion completed${NC}"
    else
        echo -e "${RED}✗ Rules of Court ingestion failed${NC}"
        echo "Check rules_log.txt for details"
    fi
    
    echo ""
fi

# Step 7: Verify results
echo "════════════════════════════════════════════════════════════════"
echo "STEP 7: Verify database contents"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Querying database..."
echo ""

# Total documents
TOTAL=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | xargs)

# By type
STATUTES=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE doc_type='statute';" 2>/dev/null | xargs)
RULES=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE doc_type='rule';" 2>/dev/null | xargs)
CASES=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE doc_type='case';" 2>/dev/null | xargs)

# By level
LEVEL0=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE level=0;" 2>/dev/null | xargs)
LEVEL1=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE level=1;" 2>/dev/null | xargs)
LEVEL2=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE level=2;" 2>/dev/null | xargs)
LEVEL3=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE level=3;" 2>/dev/null | xargs)

# Orphans
ORPHANS=$(psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents WHERE parent_id IS NOT NULL AND parent_id NOT IN (SELECT id FROM documents);" 2>/dev/null | xargs)

# Display results
echo "────────────────────────────────────────────────────────────────"
echo "DATABASE CONTENTS"
echo "────────────────────────────────────────────────────────────────"
echo ""

# Function to check if value matches expected
check_value() {
    local actual="$1"
    local expected="$2"
    local label="$3"
    
    if [ "$actual" -ge "$expected" ]; then
        echo -e "${GREEN}✓${NC} $label: $actual (expected: ~$expected)"
    else
        echo -e "${YELLOW}⚠${NC} $label: $actual (expected: ~$expected)"
    fi
}

echo "Total Documents:"
check_value "$TOTAL" "$EXPECTED_TOTAL" "  Total"
echo ""

echo "By Document Type:"
check_value "$STATUTES" "$EXPECTED_STATUTES" "  Statutes"
if [ -n "$RULES_PDF" ]; then
    check_value "$RULES" "$EXPECTED_RULES" "  Rules"
fi
check_value "$CASES" "$EXPECTED_CASES" "  Cases"
echo ""

echo "By Hierarchy Level:"
echo "  Level 0 (roots): $LEVEL0"
echo "  Level 1 (sections/paras/orders/rules): $LEVEL1"
echo "  Level 2 (subsections/rules/sub-rules): $LEVEL2"
echo "  Level 3 (sub-rules): $LEVEL3"
echo ""

echo "Data Quality:"
if [ "$ORPHANS" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Orphaned documents: 0"
else
    echo -e "${RED}✗${NC} Orphaned documents: $ORPHANS (should be 0!)"
fi

echo ""

# Detailed breakdown
echo "────────────────────────────────────────────────────────────────"
echo "DETAILED BREAKDOWN"
echo "────────────────────────────────────────────────────────────────"
echo ""

echo "📖 STATUTES:"
psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -c "
    SELECT 
        level,
        CASE 
            WHEN level = 0 THEN 'Acts'
            WHEN level = 1 THEN 'Sections'
            WHEN level = 2 THEN 'Subsections'
        END as description,
        COUNT(*) as count
    FROM documents 
    WHERE doc_type = 'statute'
    GROUP BY level
    ORDER BY level;
" 2>/dev/null

echo ""

if [ -n "$RULES_PDF" ]; then
    echo "📜 RULES OF COURT:"
    psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -c "
        SELECT 
            level,
            CASE 
                WHEN level = 0 THEN 'Root'
                WHEN level = 1 THEN 'Orders'
                WHEN level = 2 THEN 'Rules'
                WHEN level = 3 THEN 'Sub-rules'
            END as description,
            COUNT(*) as count
        FROM documents 
        WHERE doc_type = 'rule'
        GROUP BY level
        ORDER BY level;
    " 2>/dev/null
    
    echo ""
fi

echo "⚖️  CASES:"
psql -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" -c "
    SELECT 
        level,
        CASE 
            WHEN level = 0 THEN 'Judgments'
            WHEN level = 1 THEN 'Paragraphs'
        END as description,
        COUNT(*) as count
    FROM documents 
    WHERE doc_type = 'case'
    GROUP BY level
    ORDER BY level;
" 2>/dev/null

echo ""

# Step 8: Final summary
echo "════════════════════════════════════════════════════════════════"
echo "DATABASE REBUILD COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Determine overall success
SUCCESS=true

if [ "$TOTAL" -lt $(($EXPECTED_TOTAL - 100)) ]; then
    SUCCESS=false
fi

if [ "$ORPHANS" -gt 0 ]; then
    SUCCESS=false
fi

if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}✓ Week 3 database rebuild successful!${NC}"
    echo ""
    echo "Results:"
    echo "  - Total documents: $TOTAL"
    echo "  - Statutes: $STATUTES (Misrepresentation Act)"
    if [ -n "$RULES_PDF" ]; then
        echo "  - Rules: $RULES (Rules of Court 2021)"
    fi
    echo "  - Cases: $CASES"
    echo "  - Orphans: 0"
else
    echo -e "${YELLOW}⚠ Database rebuild completed with warnings${NC}"
    echo ""
    echo "Please review the results above and check logs:"
    echo "  - ingestion_log.txt"
    if [ -n "$RULES_PDF" ]; then
        echo "  - rules_log.txt"
    fi
fi

echo ""

if [ -n "$BACKUP_FILE" ]; then
    echo "Backup location: $BACKUP_FILE"
    echo "To restore: psql $DB_NAME < $BACKUP_FILE"
    echo ""
fi

echo "Next steps:"
echo "  1. Run verification: python scripts/verification/verify_week3.py"
echo "  2. Check hierarchy: python scripts/verification/verify_hierarchy.py"
echo "  3. View diagnostics: python scripts/verification/diagnostic_db.py"
echo ""
echo "You are now ready for Week 4: Interpretation Link Extraction!"
echo ""
