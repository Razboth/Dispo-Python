#!/usr/bin/env python3
"""
Test document number validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.validators import DocumentValidator

# Test various document number formats
test_numbers = [
    "001/SK/2024",           # Standard format
    "INV-2024-001",          # Invoice format
    "2024/01/001",           # Year first
    "SM/001/XII/2024",       # Complex format
    "001-DISP-2024",         # With text
    "A123",                  # Simple alphanumeric
    "2024.01.001",           # With dots
    "DOC 2024 001",          # With spaces
    "123",                   # Simple number
    "AB-123-CD",             # Mixed format
    "",                      # Empty (should fail)
    "A",                     # Too short (should fail)
    "@#$%",                  # Special chars only (should fail)
]

print("Testing Document Number Validation")
print("=" * 50)

for num in test_numbers:
    result = DocumentValidator.validate_document_number(num)
    status = "✅ VALID" if result else "❌ INVALID"
    print(f"{status:12} | '{num}'")

print("\n" + "=" * 50)
print("Validation is now more flexible!")
print("\nAccepted formats include:")
print("  - 001/SK/2024")
print("  - INV-2024-001")
print("  - 2024/01/001")
print("  - SM/001/XII/2024")
print("  - Any alphanumeric with /, -, ., or spaces")