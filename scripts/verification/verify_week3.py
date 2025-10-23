#!/usr/bin/env python3
"""
Verify database setup and show table information
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

def main():
    print("\n" + "=" * 80)
    print(" DATABASE VERIFICATION")
    print("=" * 80 + "\n")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return
    
    # Hide password in display
    display_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"Connecting to: {display_url}\n")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()")).fetchone()
            print(f"✓ PostgreSQL connected!")
            print(f"  Version: {result[0][:50]}...\n")
            
            # Check current database and user
            result = conn.execute(text("SELECT current_database(), current_user")).fetchone()
            print(f"✓ Database: {result[0]}")
            print(f"✓ User: {result[1]}\n")
            
            # List all tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print(f"Tables in database: {len(tables)}")
            
            if tables:
                print("\n" + "-" * 80)
                for table_name in sorted(tables):
                    print(f"\n📊 Table: {table_name}")
                    
                    # Get columns
                    columns = inspector.get_columns(table_name)
                    print(f"   Columns: {len(columns)}")
                    
                    # Show first 5 columns
                    for col in columns[:5]:
                        nullable = "NULL" if col['nullable'] else "NOT NULL"
                        print(f"     - {col['name']:30} {str(col['type']):20} {nullable}")
                    
                    if len(columns) > 5:
                        print(f"     ... and {len(columns) - 5} more columns")
                    
                    # Get row count
                    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                    count = conn.execute(count_query).scalar()
                    print(f"   Rows: {count:,}")
                    
                    # Get indexes
                    indexes = inspector.get_indexes(table_name)
                    if indexes:
                        print(f"   Indexes: {len(indexes)}")
                        for idx in indexes[:3]:
                            print(f"     - {idx['name']}")
                
                print("\n" + "-" * 80)
                print("\n✅ DATABASE SETUP COMPLETE!")
                print("\nYour database is ready for:")
                print("  1. Document ingestion")
                print("  2. Interpretation link extraction")
                print("  3. Retrieval operations")
                
            else:
                print("\n⚠️  No tables found!")
                print("\nRun this to create tables:")
                print("  python setup_database.py")
        
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check PostgreSQL is running:")
        print("     sudo systemctl status postgresql")
        print("  2. Verify credentials in .env file")
        print("  3. Test manual connection:")
        print("     psql -U legal_rag -d legal_rag_dev -h localhost")
        print("\n")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
