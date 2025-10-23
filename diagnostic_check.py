"""
Diagnostic Script - Review Current Project State

Run this to show Claude what's actually been built and the current environment.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess

def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def check_directory_structure():
    """Check project directory structure"""
    print_section("1. PROJECT DIRECTORY STRUCTURE")
    
    # Get current directory
    cwd = Path.cwd()
    print(f"Current directory: {cwd}\n")
    
    # Find Python files
    py_files = list(cwd.rglob("*.py"))
    sql_files = list(cwd.rglob("*.sql"))
    md_files = list(cwd.rglob("*.md"))
    
    print(f"Python files found: {len(py_files)}")
    print(f"SQL files found: {len(sql_files)}")
    print(f"Markdown files found: {len(md_files)}")
    
    print("\nPython modules:")
    for f in sorted(py_files)[:20]:  # Show first 20
        rel_path = f.relative_to(cwd) if f.is_relative_to(cwd) else f
        size = f.stat().st_size
        print(f"  {rel_path} ({size:,} bytes)")
    
    if len(py_files) > 20:
        print(f"  ... and {len(py_files) - 20} more")
    
    print("\nSQL files:")
    for f in sorted(sql_files):
        rel_path = f.relative_to(cwd) if f.is_relative_to(cwd) else f
        print(f"  {rel_path}")


def check_database_connection():
    """Check database connection and schema"""
    print_section("2. DATABASE CONNECTION & SCHEMA")
    
    try:
        import psycopg2
        from psycopg2 import sql
        
        # Try to connect (adjust connection params as needed)
        conn_params = {
            "dbname": os.getenv("DB_NAME", "legal_rag"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
        }
        
        print("Attempting database connection...")
        print(f"Host: {conn_params['host']}:{conn_params['port']}")
        print(f"Database: {conn_params['dbname']}")
        print(f"User: {conn_params['user']}\n")
        
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        print("✓ Database connection successful!\n")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        print(f"Tables in database ({len(tables)}):")
        for (table,) in tables:
            print(f"  - {table}")
        
        print("\n" + "-" * 80)
        
        # Show schema for key tables
        key_tables = ["documents", "interpretation_links", "cases", "statutes"]
        
        for table in key_tables:
            print(f"\nTable: {table}")
            try:
                cur.execute("""
                    SELECT column_name, data_type, character_maximum_length, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cur.fetchall()
                if columns:
                    print(f"  Columns ({len(columns)}):")
                    for col_name, data_type, max_len, nullable in columns:
                        len_str = f"({max_len})" if max_len else ""
                        null_str = "NULL" if nullable == "YES" else "NOT NULL"
                        print(f"    {col_name:30} {data_type}{len_str:15} {null_str}")
                    
                    # Get row count
                    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table)
                    ))
                    count = cur.fetchone()[0]
                    print(f"  Row count: {count:,}")
                else:
                    print("  (Table not found)")
            except Exception as e:
                print(f"  (Error: {e})")
        
        cur.close()
        conn.close()
        
    except ImportError:
        print("⚠ psycopg2 not installed. Install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists: CREATE DATABASE legal_rag;")
        print("  3. Connection parameters in environment variables")


def check_sqlalchemy_models():
    """Check if SQLAlchemy models exist"""
    print_section("3. SQLALCHEMY MODELS")
    
    try:
        # Try to import models
        sys.path.insert(0, str(Path.cwd()))
        
        try:
            import models
            print("✓ models.py found")
            
            # List classes
            model_classes = [
                name for name in dir(models) 
                if not name.startswith('_') and name[0].isupper()
            ]
            print(f"\nModel classes ({len(model_classes)}):")
            for name in model_classes:
                print(f"  - {name}")
                
        except ImportError:
            print("✗ models.py not found")
        
        try:
            import database
            print("\n✓ database.py found")
        except ImportError:
            print("\n✗ database.py not found")
            
        try:
            from interpretation_link_models import InterpretationLink
            print("✓ interpretation_link_models.py found")
            print("  - InterpretationLink class available")
        except ImportError:
            print("✗ interpretation_link_models.py not found")
            
    except Exception as e:
        print(f"Error checking models: {e}")


def check_extraction_pipeline():
    """Check extraction pipeline modules"""
    print_section("4. EXTRACTION PIPELINE MODULES")
    
    modules = [
        "interpretation_link_models.py",
        "rule_based_extractor.py",
        "llm_assisted_extractor.py",
        "link_quality_validator.py",
        "extraction_pipeline_orchestrator.py",
        "test_extraction_pipeline.py",
    ]
    
    cwd = Path.cwd()
    
    for module in modules:
        path = cwd / module
        if path.exists():
            size = path.stat().st_size
            lines = len(path.read_text().split('\n'))
            print(f"✓ {module:45} ({size:6,} bytes, {lines:4} lines)")
        else:
            print(f"✗ {module:45} NOT FOUND")


def check_dependencies():
    """Check installed dependencies"""
    print_section("5. PYTHON DEPENDENCIES")
    
    required = [
        "sqlalchemy",
        "psycopg2",
        "alembic",
        "openai",
        "pytest",
        "pydantic",
    ]
    
    for package in required:
        try:
            __import__(package)
            # Get version if possible
            try:
                mod = __import__(package)
                version = getattr(mod, "__version__", "unknown")
                print(f"✓ {package:20} (version: {version})")
            except:
                print(f"✓ {package:20} (installed)")
        except ImportError:
            print(f"✗ {package:20} NOT INSTALLED")


def check_environment_variables():
    """Check environment variables"""
    print_section("6. ENVIRONMENT VARIABLES")
    
    env_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "OPENAI_API_KEY",
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "PASSWORD" in var or "KEY" in var:
                display = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            else:
                display = value
            print(f"✓ {var:20} = {display}")
        else:
            print(f"✗ {var:20} NOT SET")


def check_data_files():
    """Check for data files"""
    print_section("7. DATA FILES")
    
    data_dirs = ["data", "extraction_output", "output"]
    cwd = Path.cwd()
    
    for dir_name in data_dirs:
        dir_path = cwd / dir_name
        if dir_path.exists():
            print(f"\n✓ {dir_name}/ exists")
            
            # List JSON files
            json_files = list(dir_path.glob("*.json"))
            if json_files:
                print(f"  JSON files ({len(json_files)}):")
                for f in sorted(json_files)[:10]:
                    size = f.stat().st_size
                    print(f"    {f.name} ({size:,} bytes)")
                if len(json_files) > 10:
                    print(f"    ... and {len(json_files) - 10} more")
            else:
                print("  (No JSON files)")
        else:
            print(f"✗ {dir_name}/ not found")


def check_alembic_migrations():
    """Check Alembic migrations"""
    print_section("8. ALEMBIC MIGRATIONS")
    
    cwd = Path.cwd()
    alembic_dir = cwd / "alembic"
    
    if alembic_dir.exists():
        print("✓ alembic/ directory exists")
        
        versions_dir = alembic_dir / "versions"
        if versions_dir.exists():
            migrations = list(versions_dir.glob("*.py"))
            print(f"  Migration files: {len(migrations)}")
            for mig in sorted(migrations)[:5]:
                print(f"    {mig.name}")
            if len(migrations) > 5:
                print(f"    ... and {len(migrations) - 5} more")
        else:
            print("  ✗ alembic/versions/ not found")
    else:
        print("✗ alembic/ directory not found")
    
    # Check if alembic is initialized
    alembic_ini = cwd / "alembic.ini"
    if alembic_ini.exists():
        print("✓ alembic.ini exists")
    else:
        print("✗ alembic.ini not found")


def generate_summary():
    """Generate summary report"""
    print_section("9. SUMMARY")
    
    cwd = Path.cwd()
    
    # Count files
    py_files = len(list(cwd.rglob("*.py")))
    sql_files = len(list(cwd.rglob("*.sql")))
    
    print(f"Project: {cwd.name}")
    print(f"Location: {cwd}")
    print(f"Python files: {py_files}")
    print(f"SQL files: {sql_files}")
    
    print("\nNext Steps:")
    print("  1. Review the output above")
    print("  2. Confirm database schema matches expectations")
    print("  3. Verify extraction pipeline modules are present")
    print("  4. Check if test data is available")
    print("  5. Ready to run extraction pipeline")


def main():
    """Run all diagnostic checks"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "LEGAL RAG DIAGNOSTIC CHECK" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        check_directory_structure()
        check_database_connection()
        check_sqlalchemy_models()
        check_extraction_pipeline()
        check_dependencies()
        check_environment_variables()
        check_data_files()
        check_alembic_migrations()
        generate_summary()
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC CHECK COMPLETE")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during diagnostic check: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
