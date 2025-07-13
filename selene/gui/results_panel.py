"""
Results display panel with datasheet references highlighting
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from datetime import datetime
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ResultsPanel(ttk.Frame):
    """Panel for displaying analysis results with datasheet references"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.current_results = None
        
        # Create UI
        self.create_ui()
        
        # Configure text tags for formatting
        self.configure_text_tags()
        
        self.logger.info("Results panel initialized")
    
    def create_ui(self):
        """Create the results display interface"""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header with title and controls
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Analysis Results",
            font=(config.FONT_FAMILY, 14, "bold")
        )
        title_label.pack(side="left")
        
        # Control buttons
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side="right")
        
        # Export button
        self.export_button = ttk.Button(
            controls_frame,
            text="Export",
            command=self.export_results,
            state="disabled"
        )
        self.export_button.pack(side="left", padx=2)
        
        # Copy button
        self.copy_button = ttk.Button(
            controls_frame,
            text="Copy",
            command=self.copy_results,
            state="disabled"
        )
        self.copy_button.pack(side="left", padx=2)
        
        # Clear button
        self.clear_button = ttk.Button(
            controls_frame,
            text="Clear",
            command=self.clear_results,
            state="disabled"
        )
        self.clear_button.pack(side="left", padx=2)
        
        # Results text area with scrolling
        text_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1)
        text_frame.grid(row=1, column=0, sticky="nsew")
        
        # Create text widget with scrollbars
        self.results_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE),
            bg=config.COLORS['bg_secondary'],
            fg=config.COLORS['text_primary'],
            padx=10,
            pady=10,
            state="disabled",
            cursor="arrow"
        )
        self.results_text.pack(fill="both", expand=True)
        
        # Status bar
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="No results to display",
            font=(config.FONT_FAMILY, 9),
            foreground=config.COLORS['text_secondary']
        )
        self.status_label.pack(side="left")
        
        # Timestamp label
        self.timestamp_label = ttk.Label(
            self.status_frame,
            text="",
            font=(config.FONT_FAMILY, 9),
            foreground=config.COLORS['text_secondary']
        )
        self.timestamp_label.pack(side="right")
    
    def configure_text_tags(self):
        """Configure text tags for formatting"""
        # Headers
        self.results_text.tag_configure(
            "header",
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE + 2, "bold"),
            foreground=config.COLORS['accent']
        )
        
        # Subheaders
        self.results_text.tag_configure(
            "subheader",
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE + 1, "bold"),
            foreground=config.COLORS['text_primary']
        )
        
        # Datasheet references
        self.results_text.tag_configure(
            "datasheet_ref",
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE, "italic"),
            foreground="#0066cc",
            background="#e6f2ff"
        )
        
        # Issues/warnings
        self.results_text.tag_configure(
            "warning",
            foreground=config.COLORS['error'],
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE, "bold")
        )
        
        # Recommendations
        self.results_text.tag_configure(
            "recommendation",
            foreground="#28a745",
            font=(config.FONT_FAMILY, config.RESULT_FONT_SIZE)
        )
        
        # Code/values
        self.results_text.tag_configure(
            "code",
            font=("Courier New", config.RESULT_FONT_SIZE),
            background="#f5f5f5"
        )
        
        # Success indicators
        self.results_text.tag_configure(
            "success",
            foreground=config.COLORS['success']
        )
    
    def display_results(self, analysis_data):
        """Display analysis results with formatting"""
        self.current_results = analysis_data
        
        # Enable text widget for editing
        self.results_text.configure(state="normal")
        self.results_text.delete(1.0, tk.END)
        
        try:
            # Add header
            self.add_header(analysis_data)
            
            # Add main content
            self.add_content(analysis_data)
            
            # Add footer with metadata
            self.add_footer(analysis_data)
            
            # Update status
            self.update_status(analysis_data)
            
            # Enable buttons
            self.enable_controls(True)
            
        except Exception as e:
            self.logger.error(f"Error displaying results: {e}")
            self.results_text.insert(tk.END, f"Error displaying results: {str(e)}\n")
        
        finally:
            # Disable text widget
            self.results_text.configure(state="disabled")
            
            # Scroll to top
            self.results_text.see("1.0")
    
    def add_header(self, analysis_data):
        """Add header section to results"""
        # Analysis type
        analysis_type = analysis_data.get('analysis_type', 'Analysis')
        self.results_text.insert(tk.END, f"{analysis_type} Results\n", "header")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Summary if available
        if 'summary' in analysis_data:
            self.results_text.insert(tk.END, "Summary: ", "subheader")
            self.results_text.insert(tk.END, f"{analysis_data['summary']}\n\n")
    
    def add_content(self, analysis_data):
        """Add main content with formatting"""
        content = analysis_data.get('content', '')
        
        if isinstance(content, str):
            # Process and format the content
            self.format_and_insert(content)
        elif isinstance(content, dict):
            # Structured content
            self.add_structured_content(content)
        elif isinstance(content, list):
            # List of findings
            self.add_findings_list(content)
        else:
            # Raw content
            self.results_text.insert(tk.END, str(content))
    
    def format_and_insert(self, text):
        """Format and insert text with appropriate tags"""
        # Split into lines for processing
        lines = text.split('\n')
        
        for line in lines:
            # Check for different patterns and apply formatting
            
            # Headers (lines starting with #, **, or all caps)
            if line.startswith('#') or line.startswith('**') or (line.isupper() and len(line) > 3):
                clean_line = line.strip('#*').strip()
                self.results_text.insert(tk.END, f"\n{clean_line}\n", "subheader")
                continue
            
            # Datasheet references
            if 'datasheet' in line.lower() or 'section' in line.lower() or 'page' in line.lower():
                self.insert_with_datasheet_highlighting(line)
                continue
            
            # Issues/warnings
            if any(word in line.lower() for word in ['error', 'warning', 'issue', 'problem', 'missing']):
                self.results_text.insert(tk.END, f"⚠️ {line}\n", "warning")
                continue
            
            # Recommendations
            if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'consider']):
                self.results_text.insert(tk.END, f"💡 {line}\n", "recommendation")
                continue
            
            # Success indicators
            if any(word in line.lower() for word in ['correct', 'good', 'verified', 'passed']):
                self.results_text.insert(tk.END, f"✓ {line}\n", "success")
                continue
            
            # Component values (e.g., "10kΩ", "100nF", "3.3V")
            if re.search(r'\d+[kMGT]?[ΩFH]|[\d.]+V|[\d.]+A', line):
                self.insert_with_value_highlighting(line)
                continue
            
            # Default
            self.results_text.insert(tk.END, line + '\n')
    
    def insert_with_datasheet_highlighting(self, text):
        """Insert text with datasheet references highlighted"""
        # Pattern to match datasheet references
        pattern = r'(datasheet|section|page|table|figure)\s*[\d.]+|datasheet\s+\w+'
        
        last_end = 0
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Insert text before match
            if match.start() > last_end:
                self.results_text.insert(tk.END, text[last_end:match.start()])
            
            # Insert highlighted match
            self.results_text.insert(tk.END, match.group(), "datasheet_ref")
            last_end = match.end()
        
        # Insert remaining text
        if last_end < len(text):
            self.results_text.insert(tk.END, text[last_end:])
        
        self.results_text.insert(tk.END, '\n')
    
    def insert_with_value_highlighting(self, text):
        """Insert text with component values highlighted"""
        # Pattern to match component values
        pattern = r'\d+[kMGT]?[ΩFH]|[\d.]+[mμnp]?[VAWH]|[\d.]+[kMG]?Hz'
        
        last_end = 0
        for match in re.finditer(pattern, text):
            # Insert text before match
            if match.start() > last_end:
                self.results_text.insert(tk.END, text[last_end:match.start()])
            
            # Insert highlighted match
            self.results_text.insert(tk.END, match.group(), "code")
            last_end = match.end()
        
        # Insert remaining text
        if last_end < len(text):
            self.results_text.insert(tk.END, text[last_end:])
        
        self.results_text.insert(tk.END, '\n')
    
    def add_structured_content(self, content_dict):
        """Add structured content from dictionary"""
        for key, value in content_dict.items():
            # Add key as subheader
            self.results_text.insert(tk.END, f"\n{key}:\n", "subheader")
            
            if isinstance(value, list):
                for item in value:
                    self.results_text.insert(tk.END, f"  • {item}\n")
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    self.results_text.insert(tk.END, f"  {sub_key}: {sub_value}\n")
            else:
                self.results_text.insert(tk.END, f"  {value}\n")
    
    def add_findings_list(self, findings):
        """Add a list of findings"""
        for i, finding in enumerate(findings, 1):
            self.results_text.insert(tk.END, f"\n{i}. ", "subheader")
            
            if isinstance(finding, dict):
                # Structured finding
                if 'issue' in finding:
                    self.results_text.insert(tk.END, f"{finding['issue']}\n", "warning")
                if 'recommendation' in finding:
                    self.results_text.insert(tk.END, f"   → {finding['recommendation']}\n", "recommendation")
                if 'reference' in finding:
                    self.results_text.insert(tk.END, f"   Reference: {finding['reference']}\n", "datasheet_ref")
            else:
                # Simple text finding
                self.format_and_insert(str(finding))
    
    def add_footer(self, analysis_data):
        """Add footer with metadata"""
        self.results_text.insert(tk.END, "\n" + "-" * 60 + "\n")
        
        # Add metadata if available
        if 'metadata' in analysis_data:
            meta = analysis_data['metadata']
            if 'datasheet_used' in meta:
                self.results_text.insert(tk.END, f"Datasheet: {meta['datasheet_used']}\n", "datasheet_ref")
            if 'confidence' in meta:
                self.results_text.insert(tk.END, f"Confidence: {meta['confidence']}\n")
    
    def update_status(self, analysis_data):
        """Update status bar with analysis info"""
        # Update status
        analysis_type = analysis_data.get('analysis_type', 'Analysis')
        self.status_label.configure(text=f"{analysis_type} complete")
        
        # Update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp_label.configure(text=f"Generated: {timestamp}")
    
    def enable_controls(self, enable):
        """Enable or disable control buttons"""
        state = "normal" if enable else "disabled"
        self.export_button.configure(state=state)
        self.copy_button.configure(state=state)
        self.clear_button.configure(state=state)
    
    def clear_results(self):
        """Clear the results display"""
        self.results_text.configure(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.configure(state="disabled")
        
        self.current_results = None
        self.status_label.configure(text="No results to display")
        self.timestamp_label.configure(text="")
        
        self.enable_controls(False)
        
        self.logger.info("Results cleared")
    
    def copy_results(self):
        """Copy results to clipboard"""
        if not self.current_results:
            return
        
        try:
            # Get text content
            text = self.results_text.get(1.0, tk.END).strip()
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(text)
            
            # Show feedback
            self.status_label.configure(text="Results copied to clipboard")
            self.after(2000, lambda: self.status_label.configure(text=f"{self.current_results.get('analysis_type', 'Analysis')} complete"))
            
            self.logger.info("Results copied to clipboard")
            
        except Exception as e:
            self.logger.error(f"Error copying results: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy results:\n{str(e)}")
    
    def export_results(self):
        """Export results to file"""
        if not self.current_results:
            return
        
        try:
            # Get filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"SELENE_Analysis_{timestamp}.txt"
            
            filename = filedialog.asksaveasfilename(
                title="Export Analysis Results",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Markdown files", "*.md"),
                    ("All files", "*.*")
                ]
            )
            
            if not filename:
                return
            
            # Get content
            content = self.results_text.get(1.0, tk.END).strip()
            
            # Add header
            header = f"SELENE Analysis Report\n"
            header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"Analysis Type: {self.current_results.get('analysis_type', 'Unknown')}\n"
            header += "=" * 60 + "\n\n"
            
            # Write file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(content)
            
            # Show success
            self.status_label.configure(text=f"Exported to: {os.path.basename(filename)}")
            self.logger.info(f"Results exported to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def has_results(self):
        """Check if there are results to export"""
        return self.current_results is not None