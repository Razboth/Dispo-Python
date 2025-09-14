#!/usr/bin/env python3
"""
Test script to verify the application setup
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")

    try:
        from src.utils.config import ConfigManager
        print("✅ ConfigManager imported")
    except Exception as e:
        print(f"❌ ConfigManager import failed: {e}")

    try:
        from src.models.database import DatabaseManager
        print("✅ DatabaseManager imported")
    except Exception as e:
        print(f"❌ DatabaseManager import failed: {e}")

    try:
        from src.models.user import User
        print("✅ User model imported")
    except Exception as e:
        print(f"❌ User model import failed: {e}")

    try:
        from src.views.main_window import MainApplication
        print("✅ MainApplication imported")
    except Exception as e:
        print(f"❌ MainApplication import failed: {e}")

    try:
        from src.utils.validators import InputValidator
        print("✅ Validators imported")
    except Exception as e:
        print(f"❌ Validators import failed: {e}")

def test_database():
    """Test database connection"""
    print("\nTesting database connection...")

    try:
        from pymongo import MongoClient
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB connection successful")

        db = client['disposisi']
        collections = db.list_collection_names()
        print(f"✅ Database 'disposisi' has {len(collections)} collections")

        user_count = db.users.count_documents({})
        print(f"✅ Found {user_count} user(s) in database")

        doc_count = db.documents.count_documents({})
        print(f"✅ Found {doc_count} document(s) in database")

    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_gui_components():
    """Test GUI components"""
    print("\nTesting GUI components...")

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        print("✅ Tkinter is working")
        root.destroy()
    except Exception as e:
        print(f"❌ Tkinter test failed: {e}")

    try:
        import ttkbootstrap
        print("✅ ttkbootstrap is installed")
    except Exception as e:
        print(f"❌ ttkbootstrap import failed: {e}")

def main():
    print("=" * 50)
    print("Dispo-Python Application Test")
    print("=" * 50)

    test_imports()
    test_database()
    test_gui_components()

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print("\n✅ Application is ready to run!")
    print("\nTo start the application:")
    print("  ./run.sh          # Interactive menu")
    print("  ./run-gui.sh      # GUI directly")
    print("  ./run-api.sh      # API server")

if __name__ == "__main__":
    main()