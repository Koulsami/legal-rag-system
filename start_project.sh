#!/bin/bash
echo "🚀 Starting Legal RAG PoC Environment..."
echo ""

# Start PostgreSQL
echo "📊 Starting PostgreSQL..."
sudo service postgresql start

# Navigate to project
cd ~/legal-rag-poc

# Activate virtual environment
echo "🐍 Activating Python environment..."
source .venv/bin/activate

echo ""
echo "✅ Environment ready!"
echo "📍 Location: $(pwd)"
echo "🐍 Python: $(python --version)"
echo "💾 Database: $(sudo service postgresql status | grep online && echo '✅ Online' || echo '❌ Offline')"
echo ""
echo "Type 'python test_setup.py' to verify everything works"
echo "Type 'deactivate' when done to exit virtual environment"
