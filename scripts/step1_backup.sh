#!/bin/bash
# STEP 1: Backup Current System
# Run this first before making any changes

set -e  # Exit on error

echo "========================================="
echo "STEP 1: Backing up current system"
echo "========================================="

# Navigate to project directory
cd /home/amee/legal-rag-poc

# Create backup directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/pre_fix_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

echo "Backup directory: $BACKUP_DIR"

# Backup critical files
echo "Backing up rag_generator.py..."
cp src/generation/rag_generator.py "$BACKUP_DIR/rag_generator.py.backup"

echo "Backing up hybrid_retriever.py..."
cp src/retrieval/hybrid_retriever.py "$BACKUP_DIR/hybrid_retriever.py.backup"

# Backup database (optional but recommended)
echo "Would you like to backup the database? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Backing up database..."
    pg_dump $DATABASE_URL > "$BACKUP_DIR/database_backup.sql"
    echo "Database backup complete"
fi

# Create restore script
cat > "$BACKUP_DIR/RESTORE.sh" << 'RESTORE_EOF'
#!/bin/bash
# Restore files from this backup
set -e
cd /home/amee/legal-rag-poc
cp backups/pre_fix_*/rag_generator.py.backup src/generation/rag_generator.py
cp backups/pre_fix_*/hybrid_retriever.py.backup src/retrieval/hybrid_retriever.py
echo "✅ Files restored from backup"
RESTORE_EOF

chmod +x "$BACKUP_DIR/RESTORE.sh"

echo ""
echo "✅ Backup complete!"
echo ""
echo "Files backed up to: $BACKUP_DIR"
echo ""
echo "To restore if needed, run:"
echo "  bash $BACKUP_DIR/RESTORE.sh"
echo ""
echo "========================================="
echo "Ready for STEP 2: Fix System Prompt"
echo "========================================="
