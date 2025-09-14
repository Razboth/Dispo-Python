"""
Main application window for Dispo-Python
Enhanced version with modern features and security
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap import Style
from datetime import datetime
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.database import DatabaseManager
from src.models.user import User, UserRole
from src.utils.config import ConfigManager
from src.utils.validators import DocumentValidator, InputValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MainApplication:
    """Main GUI Application with enhanced features"""

    def __init__(self, config: ConfigManager = None, db: DatabaseManager = None):
        """Initialize the main application"""
        self.config = config or ConfigManager()
        self.db = db or DatabaseManager(self.config)
        self.current_user = None
        self.is_fullscreen = False

        # Create main window
        self.root = tk.Tk()
        self.root.title("Dispo-Python - Document Management System")
        self.root.geometry("1400x800")

        # Set theme
        self.style = Style(theme=self.config.get('APPLICATION', 'theme', 'darkly'))

        # Setup UI
        self.setup_menu()
        self.setup_ui()
        self.setup_keybindings()

        # Load initial data
        self.load_data()

        logger.info("Main application initialized")

    def setup_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Document", command=self.new_document, accelerator="Ctrl+N")
        file_menu.add_command(label="Import CSV", command=self.import_csv)
        file_menu.add_command(label="Export CSV", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Edit Document", command=self.edit_document, accelerator="Ctrl+E")
        edit_menu.add_command(label="Delete Document", command=self.delete_document, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Search", command=self.show_search, accelerator="Ctrl+F")

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.load_data, accelerator="F5")
        view_menu.add_command(label="Toggle Fullscreen", command=self.toggle_fullscreen, accelerator="F11")
        view_menu.add_separator()
        view_menu.add_command(label="Dashboard", command=self.show_dashboard)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Backup Database", command=self.backup_database)
        tools_menu.add_command(label="Restore Database", command=self.restore_database)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.show_settings)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)

    def setup_ui(self):
        """Setup the main UI components"""
        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=3)
        main_container.rowconfigure(1, weight=1)

        # Create left panel (form inputs)
        self.create_left_panel(main_container)

        # Create right panel (data display)
        self.create_right_panel(main_container)

        # Status bar
        self.create_status_bar()

    def create_left_panel(self, parent):
        """Create the left panel with form inputs"""
        left_frame = ttk.LabelFrame(parent, text="Document Input", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        # Document type selection
        ttk.Label(left_frame, text="Jenis Dokumen:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.doc_type_var = tk.StringVar()
        doc_types = ["Surat Masuk", "Surat Keluar", "Nota Dinas", "Memo", "Undangan"]
        self.doc_type_combo = ttk.Combobox(left_frame, textvariable=self.doc_type_var, values=doc_types, width=25)
        self.doc_type_combo.grid(row=0, column=1, pady=2, sticky=(tk.W, tk.E))
        self.doc_type_combo.current(0)

        # Document number
        ttk.Label(left_frame, text="Nomor Surat:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.doc_number_var = tk.StringVar()
        self.doc_number_entry = ttk.Entry(left_frame, textvariable=self.doc_number_var, width=25)
        self.doc_number_entry.grid(row=1, column=1, pady=2, sticky=(tk.W, tk.E))

        # Date
        ttk.Label(left_frame, text="Tanggal Surat:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.doc_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.doc_date_entry = ttk.Entry(left_frame, textvariable=self.doc_date_var, width=25)
        self.doc_date_entry.grid(row=2, column=1, pady=2, sticky=(tk.W, tk.E))

        # Subject
        ttk.Label(left_frame, text="Perihal:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.subject_var = tk.StringVar()
        self.subject_entry = ttk.Entry(left_frame, textvariable=self.subject_var, width=25)
        self.subject_entry.grid(row=3, column=1, pady=2, sticky=(tk.W, tk.E))

        # Origin
        ttk.Label(left_frame, text="Asal Surat:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.origin_var = tk.StringVar()
        self.origin_entry = ttk.Entry(left_frame, textvariable=self.origin_var, width=25)
        self.origin_entry.grid(row=4, column=1, pady=2, sticky=(tk.W, tk.E))

        # Destination
        ttk.Label(left_frame, text="Tujuan:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.dest_var = tk.StringVar()
        self.dest_entry = ttk.Entry(left_frame, textvariable=self.dest_var, width=25)
        self.dest_entry.grid(row=5, column=1, pady=2, sticky=(tk.W, tk.E))

        # Nature of letter
        ttk.Label(left_frame, text="Sifat Surat:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.nature_var = tk.StringVar()
        natures = ["Biasa", "Segera", "Sangat Segera", "Rahasia"]
        self.nature_combo = ttk.Combobox(left_frame, textvariable=self.nature_var, values=natures, width=25)
        self.nature_combo.grid(row=6, column=1, pady=2, sticky=(tk.W, tk.E))
        self.nature_combo.current(0)

        # Classification
        ttk.Label(left_frame, text="Klasifikasi:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.class_var = tk.StringVar()
        classifications = ["Umum", "Penting", "Rahasia", "Sangat Rahasia"]
        self.class_combo = ttk.Combobox(left_frame, textvariable=self.class_var, values=classifications, width=25)
        self.class_combo.grid(row=7, column=1, pady=2, sticky=(tk.W, tk.E))
        self.class_combo.current(0)

        # Notes
        ttk.Label(left_frame, text="Catatan:").grid(row=8, column=0, sticky=tk.NW, pady=2)
        self.notes_text = tk.Text(left_frame, height=4, width=25)
        self.notes_text.grid(row=8, column=1, pady=2, sticky=(tk.W, tk.E))

        # File attachment
        ttk.Label(left_frame, text="File Scan:").grid(row=9, column=0, sticky=tk.W, pady=2)
        file_frame = ttk.Frame(left_frame)
        file_frame.grid(row=9, column=1, pady=2, sticky=(tk.W, tk.E))
        self.file_path_var = tk.StringVar()
        self.file_label = ttk.Label(file_frame, textvariable=self.file_path_var, width=20)
        self.file_label.pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Browse", command=self.browse_file, width=8).pack(side=tk.LEFT, padx=(5, 0))

        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_document, style="success.TButton", width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Update", command=self.update_document, style="info.TButton", width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=self.clear_form, style="secondary.TButton", width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Print PDF", command=self.print_pdf, style="warning.TButton", width=10).pack(side=tk.LEFT, padx=2)

        # Configure column weight
        left_frame.columnconfigure(1, weight=1)

    def create_right_panel(self, parent):
        """Create the right panel with data display"""
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Search bar
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Filter by document type
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar()
        filter_types = ["All"] + ["Surat Masuk", "Surat Keluar", "Nota Dinas", "Memo", "Undangan"]
        self.filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, values=filter_types, width=15)
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.filter_combo.current(0)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter)

        # Refresh button
        ttk.Button(search_frame, text="Refresh", command=self.load_data, style="primary.TButton").pack(side=tk.RIGHT)

        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ("No", "Jenis", "Nomor", "Tanggal", "Perihal", "Asal", "Tujuan", "Sifat", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                 yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Configure scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)

        # Define column headings and widths
        column_configs = [
            ("No", 50, tk.CENTER),
            ("Jenis", 120, tk.W),
            ("Nomor", 150, tk.W),
            ("Tanggal", 100, tk.CENTER),
            ("Perihal", 250, tk.W),
            ("Asal", 150, tk.W),
            ("Tujuan", 150, tk.W),
            ("Sifat", 100, tk.CENTER),
            ("Status", 100, tk.CENTER)
        ]

        for col, width, anchor in column_configs:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor, minwidth=50)

        # Bind events
        self.tree.bind("<Double-Button-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Summary information
        summary_frame = ttk.Frame(right_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))

        self.total_label = ttk.Label(summary_frame, text="Total Documents: 0")
        self.total_label.pack(side=tk.LEFT, padx=10)

        self.filtered_label = ttk.Label(summary_frame, text="Filtered: 0")
        self.filtered_label.pack(side=tk.LEFT, padx=10)

    def create_status_bar(self):
        """Create status bar at the bottom"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Add connection status
        self.update_status("Connected to database" if self.db else "No database connection")

    def setup_keybindings(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Control-n>", lambda e: self.new_document())
        self.root.bind("<Control-s>", lambda e: self.save_document())
        self.root.bind("<Control-e>", lambda e: self.edit_document())
        self.root.bind("<Control-f>", lambda e: self.show_search())
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        self.root.bind("<F5>", lambda e: self.load_data())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Delete>", lambda e: self.delete_document())

    def load_data(self):
        """Load documents from database"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Fetch documents
            result = self.db.search_documents(limit=1000)
            documents = result.get('documents', [])

            # Populate tree
            for idx, doc in enumerate(documents, 1):
                values = (
                    idx,
                    doc.get('jenis_dokumen', ''),
                    doc.get('nomor_surat', ''),
                    doc.get('tanggal_surat', ''),
                    doc.get('perihal', ''),
                    doc.get('asal_surat', ''),
                    doc.get('tujuan', ''),
                    doc.get('sifat_surat', ''),
                    doc.get('status', 'Active')
                )

                # Add with tag for styling
                tag = self.get_tag_for_document(doc)
                self.tree.insert("", tk.END, values=values, tags=(tag,), iid=doc.get('_id'))

            # Configure tags for styling
            self.tree.tag_configure("urgent", background="#ffcccc")
            self.tree.tag_configure("secret", background="#ffe6cc")
            self.tree.tag_configure("normal", background="")

            # Update summary
            self.total_label.config(text=f"Total Documents: {len(documents)}")
            self.update_status(f"Loaded {len(documents)} documents")

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def get_tag_for_document(self, doc):
        """Get tag for document styling"""
        if doc.get('sifat_surat') in ['Sangat Segera', 'Segera']:
            return 'urgent'
        elif doc.get('klasifikasi') in ['Rahasia', 'Sangat Rahasia']:
            return 'secret'
        return 'normal'

    def save_document(self):
        """Save new document"""
        try:
            # Get form data
            data = self.get_form_data()

            # Validate
            valid, errors = DocumentValidator.validate_disposition_data(data)
            if not valid:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return

            # Save to database
            doc_id = self.db.insert_document(data)

            # Clear form and reload
            self.clear_form()
            self.load_data()

            self.update_status(f"Document saved with ID: {doc_id}")
            messagebox.showinfo("Success", "Document saved successfully!")

        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            messagebox.showerror("Error", f"Failed to save document: {str(e)}")

    def update_document(self):
        """Update selected document"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a document to update")
            return

        try:
            doc_id = selected[0]
            data = self.get_form_data()

            # Validate
            valid, errors = DocumentValidator.validate_disposition_data(data)
            if not valid:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return

            # Update in database
            if self.db.update_document(doc_id, data):
                self.clear_form()
                self.load_data()
                self.update_status(f"Document {doc_id} updated")
                messagebox.showinfo("Success", "Document updated successfully!")
            else:
                messagebox.showerror("Error", "Failed to update document")

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            messagebox.showerror("Error", f"Failed to update document: {str(e)}")

    def delete_document(self):
        """Delete selected document"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a document to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this document?"):
            try:
                doc_id = selected[0]
                if self.db.delete_document(doc_id):
                    self.load_data()
                    self.update_status(f"Document {doc_id} deleted")
                    messagebox.showinfo("Success", "Document deleted successfully!")
                else:
                    messagebox.showerror("Error", "Failed to delete document")

            except Exception as e:
                logger.error(f"Failed to delete document: {e}")
                messagebox.showerror("Error", f"Failed to delete document: {str(e)}")

    def get_form_data(self):
        """Get data from form fields"""
        return {
            'jenis_dokumen': self.doc_type_var.get(),
            'nomor_surat': self.doc_number_var.get(),
            'tanggal_surat': self.doc_date_var.get(),
            'perihal': self.subject_var.get(),
            'asal_surat': self.origin_var.get(),
            'tujuan': self.dest_var.get(),
            'sifat_surat': self.nature_var.get(),
            'klasifikasi': self.class_var.get(),
            'catatan': self.notes_text.get("1.0", tk.END).strip(),
            'file_path': self.file_path_var.get()
        }

    def clear_form(self):
        """Clear all form fields"""
        self.doc_type_combo.current(0)
        self.doc_number_var.set("")
        self.doc_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.subject_var.set("")
        self.origin_var.set("")
        self.dest_var.set("")
        self.nature_combo.current(0)
        self.class_combo.current(0)
        self.notes_text.delete("1.0", tk.END)
        self.file_path_var.set("")

    def browse_file(self):
        """Browse for file attachment"""
        filename = filedialog.askopenfilename(
            title="Select file",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(Path(filename).name)

    def on_search(self, event=None):
        """Handle search"""
        search_text = self.search_var.get()
        self.filter_documents(search_text)

    def on_filter(self, event=None):
        """Handle filter selection"""
        self.filter_documents(self.search_var.get())

    def filter_documents(self, search_text=""):
        """Filter documents based on search and filter criteria"""
        # Implementation for filtering
        # This would filter the treeview items based on criteria
        pass

    def on_item_double_click(self, event):
        """Handle double-click on tree item"""
        self.edit_document()

    def show_context_menu(self, event):
        """Show right-click context menu"""
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Edit", command=self.edit_document)
        context_menu.add_command(label="Delete", command=self.delete_document)
        context_menu.add_separator()
        context_menu.add_command(label="View Details", command=self.view_details)
        context_menu.add_command(label="Print PDF", command=self.print_pdf)

        # Display menu
        context_menu.tk_popup(event.x_root, event.y_root)

    def new_document(self):
        """Create new document"""
        self.clear_form()
        self.doc_number_entry.focus()

    def edit_document(self):
        """Edit selected document"""
        # Load selected document data into form
        pass

    def view_details(self):
        """View document details"""
        # Show detailed view of document
        pass

    def print_pdf(self):
        """Print document as PDF"""
        messagebox.showinfo("Print", "PDF generation feature coming soon!")

    def import_csv(self):
        """Import documents from CSV"""
        messagebox.showinfo("Import", "CSV import feature coming soon!")

    def export_csv(self):
        """Export documents to CSV"""
        messagebox.showinfo("Export", "CSV export feature coming soon!")

    def show_search(self):
        """Show advanced search dialog"""
        self.search_entry.focus()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def show_dashboard(self):
        """Show dashboard window"""
        messagebox.showinfo("Dashboard", "Dashboard feature coming soon!")

    def backup_database(self):
        """Backup database"""
        try:
            backup_path = self.db.backup_database()
            messagebox.showinfo("Success", f"Database backed up to:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")

    def restore_database(self):
        """Restore database from backup"""
        backup_dir = filedialog.askdirectory(title="Select backup directory")
        if backup_dir:
            if messagebox.askyesno("Confirm", "This will replace current data. Continue?"):
                try:
                    self.db.restore_database(backup_dir)
                    self.load_data()
                    messagebox.showinfo("Success", "Database restored successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {str(e)}")

    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog coming soon!")

    def show_about(self):
        """Show about dialog"""
        about_text = """Dispo-Python Document Management System

Version: 2.0
Author: Dispo-Python Team
License: MIT

A modern document management system with:
• Secure authentication
• Document workflow
• Advanced search
• PDF generation
• Multi-language support"""

        messagebox.showinfo("About", about_text)

    def show_docs(self):
        """Show documentation"""
        import webbrowser
        webbrowser.open("https://github.com/Razboth/Dispo-Python")

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=f"  {message}")

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            logger.info("Application closing")
            self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()