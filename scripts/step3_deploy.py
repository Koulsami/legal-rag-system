#!/bin/bash
# STEP 3: Deploy Fixed RAG Generator
# This script safely replaces rag_generator.py with the v3.0 version

set -e

echo "========================================="
echo "STEP 3: Deploying Fixed RAG Generator"
echo "========================================="

cd /home/amee/legal-rag-poc

# Check if backup exists
if [ ! -d "backups" ]; then
    echo "❌ ERROR: No backup found. Run STEP 1 first!"
    exit 1
fi

echo ""
echo "This will replace src/generation/rag_generator.py with v3.0"
echo "The fixed version includes:"
echo "  - MANDATORY synthesis structure (not 'preferred')"
echo "  - Explicit synthesis language requirements"
echo "  - Clear source type explanations"
echo ""
echo "Your backup is safe in: backups/"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Create the new file
# Note: You'll paste the STEP 2 artifact content into this file
cat > src/generation/rag_generator_v3.py << 'EOF'
# Paste the complete content from STEP 2 artifact here
# Or download it and place it here
EOF

echo ""
echo "⚠️  ACTION REQUIRED:"
echo ""
echo "Please do ONE of the following:"
echo ""
echo "Option A: Copy the file manually"
echo "  1. Copy the content from the 'STEP 2: Complete Fixed rag_generator.py' artifact"
echo "  2. Save it as: src/generation/rag_generator.py"
echo ""
echo "Option B: Use this script template"
echo "  1. Edit this script"
echo "  2. Paste the content between the 'EOF' markers above"
echo "  3. Run this script again"
echo ""
echo "After copying, verify with:"
echo "  head -20 src/generation/rag_generator.py | grep 'VERSION: 3.0'"
echo ""
echo "Then run STEP 4 to test the fix."
echo ""
