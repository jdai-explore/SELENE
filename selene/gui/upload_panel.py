"""
File upload interface for schematics and datasheets
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
from PIL import Image, ImageTk
import shutil
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class UploadPanel(ttk.Frame):
    """Panel for uploading schematic images and datasheet PDFs"""
    
    def __init__(self, parent, upload_callback):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.upload_callback = upload_callback
        
        # State variables
        self.schematic_path = None
        self.datasheet_path = None
        self.schematic_thumbnail = None
        self.datasheet_thumbnail = None
        
        # Create UI
        self.create_ui()
        
        # Setup drag and drop
        self.setup_drag_drop()
        
        self.logger.info("Upload panel initialized")
    
    def create_ui(self):
        """Create the upload interface"""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Upload Files",
            font=(config.FONT_FAMILY, 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Schematic tab
        self.schematic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.schematic_tab, text="Schematic")
        self.create_schematic_area(self.schematic_tab)
        
        # Datasheet tab
        self.datasheet_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.datasheet_tab, text="Datasheet (Optional)")
        self.create_datasheet_area(self.datasheet_tab)
        
        # Clear button at bottom
        clear_button = ttk.Button(
            main_frame,
            text="Clear All Uploads",
            command=self.clear_uploads
        )
        clear_button.pack(pady=(10, 0))
    
    def create_schematic_area(self, parent):
        """Create the schematic upload area"""
        # Container frame
        container = ttk.Frame(parent, padding="10")
        container.pack(fill="both", expand=True)
        
        # Drop zone frame
        self.schematic_drop_frame = tk.Frame(
            container,
            bg="white",
            relief="solid",
            borderwidth=2,
            highlightthickness=2,
            highlightbackground=config.COLORS['accent'],
            highlightcolor=config.COLORS['accent']
        )
        self.schematic_drop_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Drop zone content
        drop_container = ttk.Frame(self.schematic_drop_frame)
        drop_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Icon or thumbnail
        self.schematic_display = ttk.Label(
            drop_container,
            text="📋",
            font=(config.FONT_FAMILY, 48)
        )
        self.schematic_display.pack()
        
        # Instructions
        self.schematic_label = ttk.Label(
            drop_container,
            text="Drag & Drop Schematic Image\nor Click to Browse",
            font=(config.FONT_FAMILY, 12),
            foreground=config.COLORS['text_secondary']
        )
        self.schematic_label.pack(pady=(10, 0))
        
        # Supported formats
        formats_label = ttk.Label(
            drop_container,
            text=f"Supported: {', '.join(config.SUPPORTED_IMAGE_FORMATS)}",
            font=(config.FONT_FAMILY, 10),
            foreground=config.COLORS['text_secondary']
        )
        formats_label.pack()
        
        # File info (initially hidden)
        self.schematic_info_frame = ttk.Frame(container)
        self.schematic_info_var = tk.StringVar()
        self.schematic_info_label = ttk.Label(
            self.schematic_info_frame,
            textvariable=self.schematic_info_var,
            font=(config.FONT_FAMILY, 10)
        )
        self.schematic_info_label.pack()
        
        # Browse button
        browse_button = ttk.Button(
            container,
            text="Browse for Schematic",
            command=self.browse_schematic
        )
        browse_button.pack(pady=(10, 0))
        
        # Bind click event to drop zone
        self.schematic_drop_frame.bind("<Button-1>", lambda e: self.browse_schematic())
        for child in drop_container.winfo_children():
            child.bind("<Button-1>", lambda e: self.browse_schematic())
    
    def create_datasheet_area(self, parent):
        """Create the datasheet upload area"""
        # Container frame
        container = ttk.Frame(parent, padding="10")
        container.pack(fill="both", expand=True)
        
        # Drop zone frame
        self.datasheet_drop_frame = tk.Frame(
            container,
            bg="white",
            relief="solid",
            borderwidth=2,
            highlightthickness=2,
            highlightbackground=config.COLORS['accent'],
            highlightcolor=config.COLORS['accent']
        )
        self.datasheet_drop_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Drop zone content
        drop_container = ttk.Frame(self.datasheet_drop_frame)
        drop_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Icon or thumbnail
        self.datasheet_display = ttk.Label(
            drop_container,
            text="📄",
            font=(config.FONT_FAMILY, 48)
        )
        self.datasheet_display.pack()
        
        # Instructions
        self.datasheet_label = ttk.Label(
            drop_container,
            text="Drag & Drop Datasheet PDF\nor Click to Browse",
            font=(config.FONT_FAMILY, 12),
            foreground=config.COLORS['text_secondary']
        )
        self.datasheet_label.pack(pady=(10, 0))
        
        # Supported formats
        formats_label = ttk.Label(
            drop_container,
            text=f"Supported: {', '.join(config.SUPPORTED_PDF_FORMATS)}",
            font=(config.FONT_FAMILY, 10),
            foreground=config.COLORS['text_secondary']
        )
        formats_label.pack()
        
        # File info (initially hidden)
        self.datasheet_info_frame = ttk.Frame(container)
        self.datasheet_info_var = tk.StringVar()
        self.datasheet_info_label = ttk.Label(
            self.datasheet_info_frame,
            textvariable=self.datasheet_info_var,
            font=(config.FONT_FAMILY, 10)
        )
        self.datasheet_info_label.pack()
        
        # Browse button
        browse_button = ttk.Button(
            container,
            text="Browse for Datasheet",
            command=self.browse_datasheet
        )
        browse_button.pack(pady=(10, 0))
        
        # Bind click event to drop zone
        self.datasheet_drop_frame.bind("<Button-1>", lambda e: self.browse_datasheet())
        for child in drop_container.winfo_children():
            child.bind("<Button-1>", lambda e: self.browse_datasheet())
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        # Note: Full drag-drop requires additional libraries like tkinterdnd2
        # For MVP, we'll use file browser dialogs
        # This is a placeholder for future enhancement
        
        # Add hover effects
        self.schematic_drop_frame.bind("<Enter>", lambda e: self.on_hover(self.schematic_drop_frame, True))
        self.schematic_drop_frame.bind("<Leave>", lambda e: self.on_hover(self.schematic_drop_frame, False))
        
        self.datasheet_drop_frame.bind("<Enter>", lambda e: self.on_hover(self.datasheet_drop_frame, True))
        self.datasheet_drop_frame.bind("<Leave>", lambda e: self.on_hover(self.datasheet_drop_frame, False))
    
    def on_hover(self, frame, entering):
        """Handle hover effects for drop zones"""
        if entering:
            frame.configure(bg="#f0f8ff")
        else:
            frame.configure(bg="white")
    
    def browse_schematic(self):
        """Browse for schematic image file"""
        file_types = [
            ("Image files", " ".join(f"*{ext}" for ext in config.SUPPORTED_IMAGE_FORMATS)),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Schematic Image",
            filetypes=file_types
        )
        
        if filename:
            self.handle_schematic_upload(filename)
    
    def browse_datasheet(self):
        """Browse for datasheet PDF file"""
        file_types = [
            ("PDF files", " ".join(f"*{ext}" for ext in config.SUPPORTED_PDF_FORMATS)),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Datasheet PDF",
            filetypes=file_types
        )
        
        if filename:
            self.handle_datasheet_upload(filename)
    
    def handle_schematic_upload(self, filepath):
        """Process schematic file upload"""
        try:
            # Validate file
            if not self.validate_file(filepath, "schematic"):
                return
            
            # Copy to temp directory
            temp_path = self.copy_to_temp(filepath, "schematic")
            self.schematic_path = temp_path
            
            # Create and display thumbnail
            self.display_schematic_thumbnail(filepath)
            
            # Update file info
            file_info = self.get_file_info(filepath)
            self.schematic_info_var.set(file_info)
            self.schematic_info_frame.pack(pady=(5, 0))
            
            # Notify callback
            self.upload_callback("schematic", temp_path)
            
            self.logger.info(f"Schematic uploaded: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error uploading schematic: {e}")
            messagebox.showerror("Upload Error", f"Failed to upload schematic:\n{str(e)}")
    
    def handle_datasheet_upload(self, filepath):
        """Process datasheet file upload"""
        try:
            # Validate file
            if not self.validate_file(filepath, "datasheet"):
                return
            
            # Copy to temp directory
            temp_path = self.copy_to_temp(filepath, "datasheet")
            self.datasheet_path = temp_path
            
            # Display PDF icon with info
            self.display_datasheet_info(filepath)
            
            # Update file info
            file_info = self.get_file_info(filepath)
            self.datasheet_info_var.set(file_info)
            self.datasheet_info_frame.pack(pady=(5, 0))
            
            # Notify callback
            self.upload_callback("datasheet", temp_path)
            
            self.logger.info(f"Datasheet uploaded: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error uploading datasheet: {e}")
            messagebox.showerror("Upload Error", f"Failed to upload datasheet:\n{str(e)}")
    
    def validate_file(self, filepath, file_type):
        """Validate uploaded file"""
        path = Path(filepath)
        
        # Check if file exists
        if not path.exists():
            messagebox.showerror("File Error", "File does not exist")
            return False
        
        # Check file extension
        if file_type == "schematic":
            if path.suffix.lower() not in config.SUPPORTED_IMAGE_FORMATS:
                messagebox.showerror(
                    "Invalid Format",
                    f"Unsupported image format: {path.suffix}\n"
                    f"Supported formats: {', '.join(config.SUPPORTED_IMAGE_FORMATS)}"
                )
                return False
        elif file_type == "datasheet":
            if path.suffix.lower() not in config.SUPPORTED_PDF_FORMATS:
                messagebox.showerror(
                    "Invalid Format",
                    f"Unsupported PDF format: {path.suffix}\n"
                    f"Supported formats: {', '.join(config.SUPPORTED_PDF_FORMATS)}"
                )
                return False
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > config.MAX_FILE_SIZE_MB:
            messagebox.showerror(
                "File Too Large",
                f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed size "
                f"({config.MAX_FILE_SIZE_MB} MB)"
            )
            return False
        
        return True
    
    def copy_to_temp(self, source_path, file_type):
        """Copy file to temp directory"""
        source = Path(source_path)
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Create unique filename
        dest_name = f"{file_type}_{source.stem}{source.suffix}"
        dest_path = temp_dir / dest_name
        
        # Copy file
        shutil.copy2(source, dest_path)
        
        return str(dest_path)
    
    def display_schematic_thumbnail(self, filepath):
        """Create and display thumbnail of schematic"""
        try:
            # Open image
            image = Image.open(filepath)
            
            # Create thumbnail
            thumbnail_size = (200, 150)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.schematic_thumbnail = ImageTk.PhotoImage(image)
            
            # Update display
            self.schematic_display.configure(
                image=self.schematic_thumbnail,
                text=""
            )
            
            # Update label
            self.schematic_label.configure(
                text=Path(filepath).name,
                foreground=config.COLORS['success']
            )
            
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            # Fall back to text display
            self.schematic_display.configure(
                text="✓",
                font=(config.FONT_FAMILY, 48),
                image=""
            )
    
    def display_datasheet_info(self, filepath):
        """Display datasheet upload confirmation"""
        # Update icon
        self.datasheet_display.configure(
            text="✓",
            font=(config.FONT_FAMILY, 48),
            foreground=config.COLORS['success']
        )
        
        # Update label
        self.datasheet_label.configure(
            text=Path(filepath).name,
            foreground=config.COLORS['success']
        )
    
    def get_file_info(self, filepath):
        """Get file information string"""
        path = Path(filepath)
        size_mb = path.stat().st_size / (1024 * 1024)
        
        if size_mb < 1:
            size_str = f"{path.stat().st_size / 1024:.1f} KB"
        else:
            size_str = f"{size_mb:.1f} MB"
        
        return f"Size: {size_str}"
    
    def clear_uploads(self):
        """Clear all uploaded files"""
        # Clear schematic
        self.schematic_path = None
        self.schematic_thumbnail = None
        self.schematic_display.configure(
            text="📋",
            font=(config.FONT_FAMILY, 48),
            image=""
        )
        self.schematic_label.configure(
            text="Drag & Drop Schematic Image\nor Click to Browse",
            foreground=config.COLORS['text_secondary']
        )
        self.schematic_info_frame.pack_forget()
        
        # Clear datasheet
        self.datasheet_path = None
        self.datasheet_display.configure(
            text="📄",
            font=(config.FONT_FAMILY, 48),
            foreground=config.COLORS['text_primary']
        )
        self.datasheet_label.configure(
            text="Drag & Drop Datasheet PDF\nor Click to Browse",
            foreground=config.COLORS['text_secondary']
        )
        self.datasheet_info_frame.pack_forget()
        
        # Clean up temp files
        self.cleanup_temp_files()
        
        self.logger.info("Cleared all uploads")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.schematic_path and Path(self.schematic_path).exists():
                Path(self.schematic_path).unlink()
            
            if self.datasheet_path and Path(self.datasheet_path).exists():
                Path(self.datasheet_path).unlink()
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp files: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_temp_files()