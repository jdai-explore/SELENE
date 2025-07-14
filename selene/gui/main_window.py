"""
Main application window and layout management for SELENE
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.upload_panel import UploadPanel
from gui.analysis_panel import AnalysisPanel
from gui.results_panel import ResultsPanel
from core.ollama_client import OllamaClient
from core.pdf_processor import PDFProcessor
from core.image_handler import ImageHandler
from analysis.analyzer import SchematicAnalyzer
import config


class MainWindow(tk.Tk):
    """Main application window for SELENE"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing main window")
        
        # Initialize core components
        self.ollama_client = None
        self.pdf_processor = PDFProcessor()
        self.image_handler = ImageHandler()
        self.analyzer = None
        
        # State variables
        self.current_schematic = None
        self.current_datasheet = None
        self.datasheet_data = {}  # Initialize as empty dict
        
        # Setup window
        self.setup_window()
        self.create_layout()
        self.create_menu_bar()
        
        # Initialize Ollama connection
        self.initialize_ollama()
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
        
        self.logger.info("Main window initialization complete")
    
    def setup_window(self):
        """Configure window properties"""
        self.title(config.WINDOW_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Set minimum window size
        self.minsize(800, 600)
        
        # Configure window icon if available
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception as e:
                self.logger.warning(f"Could not set window icon: {e}")
        
        # Configure window style
        self.configure(bg=config.COLORS['bg_primary'])
        
        # Center window on screen
        self.center_window()
        
        # Configure grid weights for responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - config.WINDOW_WIDTH) // 2
        y = (screen_height - config.WINDOW_HEIGHT) // 2
        
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x}+{y}")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Create main container with padding
        main_container = ttk.Frame(self, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create header
        self.create_header(main_container)
        
        # Create main content area with paned window
        self.create_main_content(main_container)
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self, parent):
        """Create application header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="SELENE - Schematic Review Tool",
            font=(config.FONT_FAMILY, 16, "bold")
        )
        title_label.pack(side="left")
        
        # Connection status indicator
        self.connection_frame = ttk.Frame(header_frame)
        self.connection_frame.pack(side="right")
        
        self.connection_label = ttk.Label(
            self.connection_frame,
            text="⚪ Ollama Status",
            font=(config.FONT_FAMILY, 10)
        )
        self.connection_label.pack(side="right")
        
        # Update connection status
        self.update_connection_status()
    
    def create_main_content(self, parent):
        """Create the main content area with three panels"""
        # Create horizontal paned window
        main_paned = ttk.PanedWindow(parent, orient="horizontal")
        main_paned.grid(row=1, column=0, sticky="nsew")
        
        # Left side - Upload Panel
        left_frame = ttk.Frame(main_paned, relief="solid", borderwidth=1)
        main_paned.add(left_frame, weight=1)
        
        self.upload_panel = UploadPanel(
            left_frame,
            self.on_file_uploaded
        )
        self.upload_panel.pack(fill="both", expand=True)
        
        # Right side - Vertical paned window for analysis and results
        right_paned = ttk.PanedWindow(main_paned, orient="vertical")
        main_paned.add(right_paned, weight=2)
        
        # Analysis controls (top)
        analysis_frame = ttk.Frame(right_paned, relief="solid", borderwidth=1)
        right_paned.add(analysis_frame, weight=1)
        
        self.analysis_panel = AnalysisPanel(
            analysis_frame,
            self.on_analysis_requested
        )
        self.analysis_panel.pack(fill="both", expand=True)
        
        # Results display (bottom)
        results_frame = ttk.Frame(right_paned, relief="solid", borderwidth=1)
        right_paned.add(results_frame, weight=2)
        
        self.results_panel = ResultsPanel(results_frame)
        self.results_panel.pack(fill="both", expand=True)
        
        # Set initial sash positions
        self.after(100, lambda: self.set_sash_positions(main_paned, right_paned))
    
    def set_sash_positions(self, h_paned, v_paned):
        """Set initial positions for paned windows"""
        try:
            # Set horizontal split (40% upload, 60% analysis/results)
            h_paned.sashpos(0, int(config.WINDOW_WIDTH * 0.4))
            
            # Set vertical split (30% analysis, 70% results)
            v_paned.sashpos(0, int(config.WINDOW_HEIGHT * 0.3))
        except Exception as e:
            self.logger.warning(f"Could not set sash positions: {e}")
    
    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ttk.Frame(self, relief="sunken")
        self.status_bar.grid(row=1, column=0, sticky="ew")
        
        # Status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_bar,
            textvariable=self.status_var,
            font=(config.FONT_FAMILY, 9)
        )
        self.status_label.pack(side="left", padx=5)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            self.status_bar,
            variable=self.progress_var,
            mode='indeterminate',
            length=200
        )
    
    def create_menu_bar(self):
        """Setup menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Open Schematic...",
            command=lambda: self.upload_panel.browse_schematic(),
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Open Datasheet...",
            command=lambda: self.upload_panel.browse_datasheet(),
            accelerator="Ctrl+D"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Export Results...",
            command=self.export_results,
            accelerator="Ctrl+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.on_closing,
            accelerator="Alt+F4"
        )
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Clear All",
            command=self.clear_all,
            accelerator="Ctrl+L"
        )
        edit_menu.add_command(
            label="Copy Results",
            command=self.results_panel.copy_results,
            accelerator="Ctrl+C"
        )
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Refresh Connection",
            command=self.initialize_ollama
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Toggle Full Screen",
            command=self.toggle_fullscreen,
            accelerator="F11"
        )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="User Guide",
            command=self.show_user_guide
        )
        help_menu.add_command(
            label="About SELENE",
            command=self.show_about
        )
    
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.bind("<Control-o>", lambda e: self.upload_panel.browse_schematic())
        self.bind("<Control-d>", lambda e: self.upload_panel.browse_datasheet())
        self.bind("<Control-s>", lambda e: self.export_results())
        self.bind("<Control-l>", lambda e: self.clear_all())
        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.bind("<Escape>", lambda e: self.exit_fullscreen())
    
    def initialize_ollama(self):
        """Initialize connection to Ollama"""
        self.update_status("Connecting to Ollama...")
        
        try:
            self.ollama_client = OllamaClient()
            if self.ollama_client.check_connection():
                self.analyzer = SchematicAnalyzer(self.ollama_client)
                self.update_connection_status(True)
                self.update_status("Connected to Ollama")
                self.logger.info("Ollama connection established")
            else:
                self.update_connection_status(False)
                self.update_status("Ollama not available - running in offline mode")
                self.logger.warning("Could not connect to Ollama")
        except Exception as e:
            self.logger.error(f"Error initializing Ollama: {e}")
            self.update_connection_status(False)
            self.update_status("Error connecting to Ollama")
    
    def update_connection_status(self, connected=None):
        """Update Ollama connection status indicator"""
        if connected is None:
            # Check current status
            connected = self.ollama_client and self.ollama_client.check_connection()
        
        if connected:
            self.connection_label.config(text="🟢 Ollama Connected")
        else:
            self.connection_label.config(text="🔴 Ollama Offline")
    
    def on_file_uploaded(self, file_type, file_path):
        """Handle file upload events"""
        self.logger.info(f"File uploaded: {file_type} - {file_path}")
        
        if file_type == "schematic":
            self.current_schematic = file_path
            self.update_status(f"Loaded schematic: {Path(file_path).name}")
        elif file_type == "datasheet":
            self.current_datasheet = file_path
            self.update_status("Processing datasheet...")
            self.process_datasheet(file_path)
        
        # Update analysis panel state
        self.analysis_panel.update_button_states(
            self.current_schematic is not None,
            self.current_datasheet is not None
        )
    
    def process_datasheet(self, pdf_path):
        """Process uploaded datasheet"""
        try:
            self.show_progress(True)
            
            # Extract text from PDF
            text = self.pdf_processor.extract_text(pdf_path)
            
            # Parse datasheet - ensure we always return a dict
            try:
                from analysis.datasheet_parser import DatasheetParser
                parser = DatasheetParser()
                self.datasheet_data = parser.parse(text)
                
                # Ensure datasheet_data is always a dict
                if not isinstance(self.datasheet_data, dict):
                    self.logger.warning("Parser returned non-dict, creating fallback dict")
                    self.datasheet_data = {
                        'component_name': 'Unknown',
                        'error': 'Parser returned invalid data type',
                        'full_text': str(text) if text else '',
                        'pin_config': {},
                        'electrical_specs': {},
                        'recommended_circuits': [],
                        'key_parameters': {},
                        'features': [],
                        'operating_conditions': {},
                        'package_info': 'Unknown',
                        'application_notes': []
                    }
                
            except Exception as parse_error:
                self.logger.error(f"Datasheet parsing failed: {parse_error}")
                # Create fallback datasheet data structure
                self.datasheet_data = {
                    'component_name': 'Unknown Component',
                    'error': f'Parsing failed: {str(parse_error)}',
                    'full_text': str(text) if text else '',
                    'pin_config': {},
                    'electrical_specs': {},
                    'recommended_circuits': [],
                    'key_parameters': {},
                    'features': [],
                    'operating_conditions': {},
                    'package_info': 'Unknown',
                    'application_notes': []
                }
            
            component_name = self.datasheet_data.get('component_name', 'Unknown Component')
            self.update_status(f"Processed datasheet: {component_name}")
            self.logger.info(f"Datasheet processed successfully for: {component_name}")
            
        except Exception as e:
            self.logger.error(f"Error processing datasheet: {e}")
            self.update_status("Error processing datasheet")
            
            # Create minimal fallback datasheet data
            self.datasheet_data = {
                'component_name': 'Unknown',
                'error': str(e),
                'full_text': '',
                'pin_config': {},
                'electrical_specs': {},
                'recommended_circuits': [],
                'key_parameters': {},
                'features': [],
                'operating_conditions': {},
                'package_info': 'Unknown',
                'application_notes': []
            }
            
            messagebox.showerror("Datasheet Error", f"Could not process datasheet:\n{str(e)}")
        finally:
            self.show_progress(False)
    
    def on_analysis_requested(self, analysis_type, custom_query=None):
        """Handle analysis request from analysis panel"""
        if not self.current_schematic:
            messagebox.showwarning("No Schematic", "Please upload a schematic first")
            return
        
        if not self.analyzer:
            messagebox.showwarning("Offline Mode", "Ollama is not available. Please check connection.")
            return
        
        self.logger.info(f"Analysis requested: {analysis_type}")
        self.update_status(f"Running {analysis_type}...")
        self.show_progress(True)
        
        # Clear previous results
        self.results_panel.clear_results()
        
        # Run analysis in separate thread to keep UI responsive
        self.after(100, lambda: self.run_analysis(analysis_type, custom_query))
    
    def run_analysis(self, analysis_type, custom_query):
        """Run the actual analysis"""
        try:
            # Ensure datasheet_data is always a dict
            if not isinstance(self.datasheet_data, dict):
                self.datasheet_data = {}
            
            # Perform analysis
            results = self.analyzer.analyze(
                self.current_schematic,
                self.datasheet_data,
                analysis_type,
                custom_query
            )
            
            # Display results
            self.results_panel.display_results(results)
            self.update_status(f"Analysis complete: {analysis_type}")
            
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            self.update_status("Analysis failed")
            messagebox.showerror("Analysis Error", f"Analysis failed:\n{str(e)}")
        finally:
            self.show_progress(False)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.update_idletasks()
    
    def show_progress(self, show):
        """Show or hide progress bar"""
        if show:
            self.progress_bar.pack(side="right", padx=5)
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def clear_all(self):
        """Clear all uploaded files and results"""
        self.current_schematic = None
        self.current_datasheet = None
        self.datasheet_data = {}  # Reset to empty dict
        
        self.upload_panel.clear_uploads()
        self.results_panel.clear_results()
        self.analysis_panel.update_button_states(False, False)
        
        self.update_status("Cleared all data")
    
    def export_results(self):
        """Export analysis results"""
        if not self.results_panel.has_results():
            messagebox.showinfo("No Results", "No analysis results to export")
            return
        
        self.results_panel.export_results()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current_state)
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        self.attributes("-fullscreen", False)
    
    def show_user_guide(self):
        """Show user guide"""
        guide_text = """SELENE User Guide

1. Upload Files:
   - Drag and drop or browse to upload schematic image (PNG/JPG)
   - Optionally upload component datasheet (PDF)

2. Run Analysis:
   - Choose from 5 preset analysis types
   - Or enter a custom query
   - Analysis uses AI to review your schematic

3. Review Results:
   - Results show potential issues and recommendations
   - Datasheet references are highlighted when available

4. Export Results:
   - Save analysis results for documentation

Keyboard Shortcuts:
   Ctrl+O: Open schematic
   Ctrl+D: Open datasheet
   Ctrl+S: Export results
   Ctrl+L: Clear all
   F11: Toggle fullscreen"""
        
        messagebox.showinfo("User Guide", guide_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """SELENE
Schematic Review Tool with Datasheet Integration

Version: 1.0.0
Author: AI-Assisted Development
License: MIT

SELENE uses AI to analyze electronic schematics
and provide intelligent design verification with
integrated datasheet support."""
        
        messagebox.showinfo("About SELENE", about_text)
    
    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to quit SELENE?"):
            self.logger.info("Application closing...")
            self.destroy()