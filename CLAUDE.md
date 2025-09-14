# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based document disposition (Disposisi) application with two main variants:
- **Dispo-TI.py**: IT department-specific disposition system
- **Dispo-Umum.py**: General-purpose disposition system

The application features:
- MongoDB database integration for document storage
- GridFS for file/scan storage
- PDF generation using ReportLab
- GUI interface using Tkinter with ttkbootstrap styling
- Document backup and restore functionality

## Architecture

### Core Components

1. **ConfigManager** (lines 37-69): Manages database configuration stored in `config.ini`
   - Default MongoDB connection: localhost:27017
   - Database name: disposisi

2. **DatabaseManager** (lines 512-657): Handles all MongoDB operations
   - CRUD operations for documents
   - GridFS file management
   - Backup/restore functionality
   - Auto-increment ID generation

3. **PDFRenderer** (lines 71-511): Generates disposition PDF documents
   - Supports A4 and F4 paper sizes
   - Creates structured disposition forms with tables
   - Handles QR code generation for document tracking

4. **FileHandler** (lines 658-687): Manages file operations
   - Opens files from GridFS storage
   - Handles temporary file creation for viewing

5. **AplikasiDisposisiDokumen** (lines 731-1695): Main GUI application class
   - Tkinter-based interface with ttkbootstrap theming
   - Document search, filtering, and fuzzy matching
   - CSV import/export functionality
   - CRUD operations UI

## Development Commands

### Running the Application
```bash
# For IT department version
python3 Dispo-TI.py

# For general version
python3 Dispo-Umum.py
```

### Building Executables
```bash
# Build IT department executable
pyinstaller Dispo-TI.spec

# Build general executable
pyinstaller Dispo-Umum.spec
```

### Virtual Environment
```bash
# The project uses a Windows-style venv structure
# Scripts are in venv/Scripts/ rather than venv/bin/
```

## Required Dependencies

The application requires these Python packages:
- pymongo (MongoDB driver)
- gridfs (MongoDB file storage)
- reportlab (PDF generation)
- PIL/Pillow (Image processing)
- ttkbootstrap (Modern Tkinter themes)
- fuzzywuzzy (Fuzzy string matching)
- tkinter (GUI framework - usually included with Python)

## Database Configuration

The application connects to MongoDB using settings in `config.ini`:
- Host: Can be localhost or remote IP
- Port: Default 27017
- Database: disposisi

The database contains:
- Main collection for document records
- GridFS collections (fs.files, fs.chunks) for file storage
- Counters collection for auto-increment IDs

## Key Features Implementation

- **Document Search**: Uses fuzzy matching with fuzzywuzzy for flexible searching
- **PDF Generation**: Creates structured disposition forms with proper Indonesian formatting
- **File Attachments**: Stores scanned documents in GridFS, viewable through the GUI
- **Data Import/Export**: CSV format support for bulk operations
- **Backup System**: JSON-based backup with metadata tracking