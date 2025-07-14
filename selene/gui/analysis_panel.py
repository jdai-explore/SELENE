"""
Analysis control buttons and custom query input - Fixed version
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class AnalysisPanel(ttk.Frame):
    """Panel containing analysis controls and custom query input"""
    
    # Preset analysis types
    PRESET_ANALYSES = [
        "Component Verification",
        "Pin Configuration Check", 
        "Power Supply Analysis",
        "Design Compliance",
        "Missing Components"
    ]
    
    def __init__(self, parent, analysis_callback):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.analysis_callback = analysis_callback
        
        # State variables
        self.preset_buttons = []
        self.custom_submit_btn = None
        self.custom_entry = None
        self.custom_query_var = None
        self.schematic_loaded = False
        self.datasheet_loaded = False
        
        # Create UI
        self.create_ui()
        
        # Initial state - all disabled
        self.update_button_states(False, False)
        
        self.logger.info("Analysis panel initialized")
    
    def create_ui(self):
        """Create the analysis interface"""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Analysis Options",
            font=(config.FONT_FAMILY, 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Create notebook for different sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Preset analysis tab
        preset_frame = ttk.Frame(notebook)
        notebook.add(preset_frame, text="Preset Analysis")
        self.create_preset_buttons(preset_frame)
        
        # Custom query tab
        custom_frame = ttk.Frame(notebook)
        notebook.add(custom_frame, text="Custom Query")
        self.create_custom_query(custom_frame)
        
        # Info label at bottom
        info_label = ttk.Label(
            main_frame,
            text="💡 Tip: Upload a datasheet for more accurate analysis",
            font=(config.FONT_FAMILY, 10)
        )
        info_label.pack(side="bottom", pady=(10, 0))
    
    def create_preset_buttons(self, parent):
        """Create the preset analysis buttons"""
        # Container with padding
        container = ttk.Frame(parent, padding="15")
        container.pack(fill="both", expand=True)
        
        # Instructions
        instructions = ttk.Label(
            container,
            text="Choose an analysis type to run on your schematic:",
            font=(config.FONT_FAMILY, 11)
        )
        instructions.pack(pady=(0, 15))
        
        # Buttons frame
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(fill="both", expand=True)
        
        # Create buttons with descriptions
        descriptions = [
            "Verify component values against datasheet recommendations",
            "Check pin connections and assignments", 
            "Analyze power supply design and decoupling",
            "Check compliance with datasheet recommendations",
            "Identify missing required components"
        ]
        
        for i, (analysis_type, description) in enumerate(zip(self.PRESET_ANALYSES, descriptions)):
            # Button frame for each analysis type
            btn_frame = ttk.LabelFrame(buttons_frame, text=analysis_type, padding="10")
            btn_frame.pack(fill="x", pady=5)
            
            # Description
            desc_label = ttk.Label(
                btn_frame,
                text=description,
                font=(config.FONT_FAMILY, 9),
                wraplength=400
            )
            desc_label.pack(anchor="w")
            
            # Button
            btn = ttk.Button(
                btn_frame,
                text=f"Run {analysis_type}",
                command=lambda at=analysis_type: self.on_preset_click(at),
                style="Accent.TButton"
            )
            btn.pack(anchor="e", pady=(5, 0))
            
            self.preset_buttons.append(btn)
    
    def create_custom_query(self, parent):
        """Create custom query input section"""
        # Container with padding
        container = ttk.Frame(parent, padding="15")
        container.pack(fill="both", expand=True)
        
        # Instructions
        instructions = ttk.Label(
            container,
            text="Enter your own analysis question:",
            font=(config.FONT_FAMILY, 11, "bold")
        )
        instructions.pack(anchor="w", pady=(0, 10))
        
        # Text area frame
        text_frame = ttk.LabelFrame(container, text="Custom Analysis Query", padding="10")
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Text widget with scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill="both", expand=True)
        
        # Create text widget
        self.custom_text = tk.Text(
            text_container,
            height=6,
            wrap=tk.WORD,
            font=(config.FONT_FAMILY, 11),
            relief="sunken",
            borderwidth=1
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.custom_text.yview)
        self.custom_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack text and scrollbar
        self.custom_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Submit button
        self.custom_submit_btn = ttk.Button(
            button_frame,
            text="🔍 Analyze Custom Query",
            command=self.on_custom_query_submit,
            style="Accent.TButton"
        )
        self.custom_submit_btn.pack(side="right")
        
        # Clear button
        clear_btn = ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_custom_query
        )
        clear_btn.pack(side="right", padx=(0, 5))
        
        # Examples section
        examples_frame = ttk.LabelFrame(container, text="Example Queries", padding="10")
        examples_frame.pack(fill="x", pady=(15, 0))
        
        examples = [
            "Check if all bypass capacitors are present and properly placed near power pins",
            "Verify the crystal oscillator circuit meets the microcontroller's requirements",
            "Analyze the grounding scheme and check for proper ground plane connections",
            "Review power supply filtering and ensure adequate decoupling",
            "Check for EMI/EMC design considerations and shielding requirements"
        ]
        
        for example in examples:
            example_btn = ttk.Button(
                examples_frame,
                text=f"📝 {example[:60]}{'...' if len(example) > 60 else ''}",
                command=lambda ex=example: self.insert_example(ex)
            )
            example_btn.pack(anchor="w", pady=2, fill="x")
    
    def insert_example(self, example_text):
        """Insert example text into custom query field"""
        self.custom_text.delete(1.0, tk.END)
        self.custom_text.insert(1.0, example_text)
    
    def clear_custom_query(self):
        """Clear the custom query text"""
        self.custom_text.delete(1.0, tk.END)
    
    def on_preset_click(self, analysis_type):
        """Handle preset button click"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic",
                "Please upload a schematic image first before running analysis."
            )
            return
        
        self.logger.info(f"Preset analysis clicked: {analysis_type}")
        
        # Trigger analysis
        try:
            self.analysis_callback(analysis_type)
        except Exception as e:
            self.logger.error(f"Error triggering analysis: {e}")
            messagebox.showerror("Analysis Error", f"Failed to start analysis: {str(e)}")
    
    def on_custom_query_submit(self):
        """Handle custom query submission"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic",
                "Please upload a schematic image first before running analysis."
            )
            return
        
        # Get query text
        query = self.custom_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning(
                "Empty Query",
                "Please enter an analysis question before submitting."
            )
            return
        
        if len(query) < 10:
            messagebox.showwarning(
                "Query Too Short",
                "Please enter a more detailed analysis question (at least 10 characters)."
            )
            return
        
        self.logger.info(f"Custom query submitted: {query[:100]}...")
        
        # Trigger analysis
        try:
            self.analysis_callback("Custom Query", query)
        except Exception as e:
            self.logger.error(f"Error triggering custom analysis: {e}")
            messagebox.showerror("Analysis Error", f"Failed to start custom analysis: {str(e)}")
    
    def update_button_states(self, schematic_loaded, datasheet_loaded):
        """Enable or disable buttons based on file upload status"""
        self.schematic_loaded = schematic_loaded
        self.datasheet_loaded = datasheet_loaded
        
        # Determine button state
        button_state = "normal" if schematic_loaded else "disabled"
        
        # Update preset buttons
        for button in self.preset_buttons:
            try:
                button.configure(state=button_state)
            except tk.TclError as e:
                self.logger.warning(f"Could not configure preset button state: {e}")
        
        # Update custom query submit button
        if self.custom_submit_btn:
            try:
                self.custom_submit_btn.configure(state=button_state)
            except tk.TclError as e:
                self.logger.warning(f"Could not configure custom submit button state: {e}")
        
        # Update custom text widget
        if hasattr(self, 'custom_text'):
            try:
                text_state = "normal" if schematic_loaded else "disabled"
                self.custom_text.configure(state=text_state)
                
                # Add helpful placeholder text when disabled
                if not schematic_loaded:
                    self.custom_text.configure(state="normal")
                    current_text = self.custom_text.get(1.0, tk.END).strip()
                    if not current_text:
                        self.custom_text.insert(1.0, "Upload a schematic first to enable custom queries...")
                    self.custom_text.configure(state="disabled")
                else:
                    # Clear placeholder text when enabled
                    current_text = self.custom_text.get(1.0, tk.END).strip()
                    if current_text == "Upload a schematic first to enable custom queries...":
                        self.custom_text.delete(1.0, tk.END)
                        
            except tk.TclError as e:
                self.logger.warning(f"Could not configure custom text state: {e}")
        
        # Log status update
        status_msg = f"Button states updated - Schematic: {schematic_loaded}, Datasheet: {datasheet_loaded}"
        self.logger.info(status_msg)
        
        # Update info message based on upload status
        info_text = "💡 Tip: Upload a datasheet for more accurate analysis"
        if schematic_loaded and datasheet_loaded:
            info_text = "✅ Ready for analysis with schematic and datasheet"
        elif schematic_loaded:
            info_text = "📊 Ready for analysis (datasheet optional for better results)"
        else:
            info_text = "📁 Upload a schematic image to begin analysis"
    
    def reset(self):
        """Reset the panel to initial state"""
        # Clear custom query text
        if hasattr(self, 'custom_text'):
            try:
                self.custom_text.configure(state="normal")
                self.custom_text.delete(1.0, tk.END)
            except tk.TclError:
                pass
        
        # Reset button states
        self.update_button_states(False, False)
        
        self.logger.info("Analysis panel reset to initial state")
    
    def get_status_info(self):
        """Get current status information for debugging"""
        return {
            'schematic_loaded': self.schematic_loaded,
            'datasheet_loaded': self.datasheet_loaded,
            'preset_buttons_count': len(self.preset_buttons),
            'has_custom_submit_btn': self.custom_submit_btn is not None,
            'has_custom_text': hasattr(self, 'custom_text')
        }