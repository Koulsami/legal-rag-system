#!/usr/bin/env python3
"""Create database tables"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
from dotenv import load_dotenv
from src.database.models import init_db, Base

load_dotenv()

print("=" * 70)
print("CREATING DATABASE SCHEMA")
print("=" * 70)

# Initialize database connection
db = init_db(os.getenv('DATABASE_URL', 'postgresql://localhost/legal_rag_dev'))

print("\nCreating all tables...")

# Create all tables
with db.engine.begin() as conn:
    Base.metadata.create_all(conn)

print("✓ Tables created successfully!")

# Verify tables exist
print("\nVerifying tables...")
with db.engine.connect() as conn:
    result = conn.execute(db.text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """))
    
    tables = [row[0] for row in result]
    
    if tables:
        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
    else:
        print("✗ No tables found!")

print("\n" + "=" * 70)
print("SCHEMA CREATION COMPLETE")
print("=" * 70 + "\n")
