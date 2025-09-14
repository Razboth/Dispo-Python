#!/usr/bin/env python3
"""
Test saving a document to the database
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import DatabaseManager
from src.utils.config import ConfigManager
from datetime import datetime

# Initialize database
config = ConfigManager()
db = DatabaseManager(config)

# Test document data
test_document = {
    'jenis_dokumen': 'Surat Masuk',
    'nomor_surat': '001/SM/2024',
    'tanggal_surat': datetime.now().strftime('%Y-%m-%d'),
    'perihal': 'Test Document',
    'asal_surat': 'Divisi IT',
    'tujuan': 'Divisi HRD',
    'sifat_surat': 'Biasa',
    'klasifikasi': 'Umum',
    'catatan': 'This is a test document',
    'status': 'Active'
}

print("Testing Document Save")
print("=" * 50)
print("Document data:")
for key, value in test_document.items():
    print(f"  {key}: {value}")

print("\nValidating document...")
from src.utils.validators import DocumentValidator

valid, errors = DocumentValidator.validate_disposition_data(test_document)
if valid:
    print("✅ Document validation passed")
else:
    print("❌ Validation errors:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print("\nSaving document to database...")
try:
    doc_id = db.insert_document(test_document, user_id='test_user')
    print(f"✅ Document saved successfully with ID: {doc_id}")

    # Verify by retrieving
    saved_doc = db.documents.find_one({'_id': doc_id})
    if saved_doc:
        print("\n✅ Document verified in database:")
        print(f"  Document Number: {saved_doc.get('document_number')}")
        print(f"  Nomor Surat: {saved_doc.get('nomor_surat')}")
        print(f"  Perihal: {saved_doc.get('perihal')}")

    # Show total documents
    total = db.documents.count_documents({})
    print(f"\nTotal documents in database: {total}")

except Exception as e:
    print(f"❌ Error saving document: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()