#!/bin/bash
# SIMPLE DEPLOYMENT - Just backup and remind you what to do

set -e

PROJECT="/home/amee/legal-rag-poc"

echo "════════════════════════════════════════════════════════════"
echo "LEGAL RAG v3.0 - SYNTHESIS FIX DEPLOYMENT"
echo "════════════════════════════════════════════════════════════"
echo ""

cd "$PROJECT"

# Step 1: Backup
echo "Step 1: Creating backup..."
BACKUP_DIR="backups/pre_v3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp src/generation/rag_generator.py "$BACKUP_DIR/"
echo "✅ Backup saved to: $BACKUP_DIR"
echo ""

# Step 2: Instructions
echo "Step 2: Now you need to replace the file"
echo ""
echo "ACTION REQUIRED:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. In Claude chat, find the artifact called:"
echo "   'STEP 2: Complete Fixed rag_generator.py'"
echo ""
echo "2. Click the artifact to open it"
echo ""
echo "3. Copy ALL the content (it's ~300 lines)"
echo ""
echo "4. Open your file for editing:"
echo "   nano src/generation/rag_generator.py"
echo "   (or use your preferred editor)"
echo ""
echo "5. Delete everything and paste the new content"
echo ""
echo "6. Save the file"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter when you've done this..."

# Step 3: Verify
echo ""
echo "Step 3: Verifying deployment..."
echo ""

if grep -q "VERSION: 3.0" src/generation/rag_generator.py; then
    echo "✅ Version 3.0 detected"
else
    echo "❌ Version 3.0 NOT found - file may not have been updated"
    exit 1
fi

if grep -q "STRICTLY MANDATORY" src/generation/rag_generator.py; then
    echo "✅ New prompt structure detected"
else
    echo "❌ New prompt NOT found - file may not have been updated"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next: Test the fix"
echo ""
echo "python3 -c '"
echo "import sys"
echo "sys.path.insert(0, \"/home/amee/legal-rag-poc\")"
echo "from src.generation.rag_generator import RAGGenerator"
echo "print(\"✅ Import successful - ready to test\")"
echo "'"
echo ""
echo "To rollback if needed:"
echo "cp $BACKUP_DIR/rag_generator.py src/generation/"
echo ""
