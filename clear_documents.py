# clear_documents.py
from src.database.models import init_db, Document
import os
from dotenv import load_dotenv

load_dotenv()
db = init_db(os.getenv('DATABASE_URL'))

print("Clearing documents table...")
with db.get_session() as session:
    count = session.query(Document).delete()
    session.commit()
    print(f"✅ Deleted {count} documents")

print("\nNow re-run: python scripts/step1_verify_week3.py")
