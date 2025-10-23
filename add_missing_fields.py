#!/usr/bin/env python3
"""Add missing fields to documents table"""

from sqlalchemy import text
from src.database.models import init_db
import os
from dotenv import load_dotenv

load_dotenv()

db = init_db(os.getenv('DATABASE_URL'))

print("Adding missing columns to documents table...")
print()

with db.engine.connect() as conn:
    # Add missing columns
    columns = [
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS act_name VARCHAR(500)",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS subsection VARCHAR(50)",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS parties VARCHAR(500)",
    ]
    
    for sql in columns:
        try:
            conn.execute(text(sql))
            col_name = sql.split("ADD COLUMN IF NOT EXISTS ")[1].split()[0]
            print(f"✅ Added column: {col_name}")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    conn.commit()

print()
print("✅ Database schema updated!")
