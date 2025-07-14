"""
Responsive Analysis Panel - Simple layout with always visible custom query submit button
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class AnalysisPanel(ttk.Frame):
    """Responsive panel containing analysis controls and custom query input"""
    
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
        self.custom_text = None
        self.schematic_loaded = False
        self.datasheet_loaded = False
        
        # Create UI
        self.create_responsive_ui()
        
        # Initial state - all disabled
        self.update_button_states(False, False)
        
        self.logger.info("Analysis panel initialized")
    
    def create_responsive_ui(self):
        """Create responsive analysis interface"""
        # Configure grid weights for responsiveness
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main scrollable container
        main_canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        main_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure scrollable frame
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create content in scrollable frame
        self.create_content(scrollable_frame)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_content(self, parent):
        """Create the main content"""
        # Title section
        self.create_title_section(parent)
        
        # Preset analysis section
        self.create_preset_section(parent)
        
        # Custom query section
        self.create_custom_section(parent)
        
        # Status section
        self.create_status_section(parent)
    
    def create_title_section(self, parent):
        """Create title and status"""
        title_frame = ttk.Frame(parent, padding="10")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_frame.grid_columnconfigure(0, weight=1)
        
        # Main title
        title_label = ttk.Label(
            title_frame,
            text="🔍 Analysis Center",
            font=(config.FONT_FAMILY, 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(
            title_frame,
            text="Select an analysis type or enter a custom query",
            font=(config.FONT_FAMILY, 10)
        )
        subtitle_label.grid(row=1, column=0)
    
    def create_preset_section(self, parent):
        """Create preset analysis buttons section"""
        preset_frame = ttk.LabelFrame(parent, text="🎯 Preset Analysis", padding="15")
        preset_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        preset_frame.grid_columnconfigure(0, weight=1)
        
        # Responsive grid for buttons (2 columns on wide screens, 1 on narrow)
        button_frame = ttk.Frame(preset_frame)
        button_frame.grid(row=0, column=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Create buttons with descriptions
        descriptions = [
            "Verify component values and ratings",
            "Check pin connections and assignments", 
            "Analyze power distribution and decoupling",
            "Verify compliance with design standards",
            "Find missing required components"
        ]
        
        for i, (analysis_type, description) in enumerate(zip(self.PRESET_ANALYSES, descriptions)):
            # Determine row and column for responsive layout
            row = i // 2
            col = i % 2
            
            # Button container
            btn_container = ttk.Frame(button_frame, relief="ridge", borderwidth=1)
            btn_container.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            btn_container.grid_columnconfigure(0, weight=1)
            
            # Analysis type label
            type_label = ttk.Label(
                btn_container,
                text=analysis_type,
                font=(config.FONT_FAMILY, 10, "bold")
            )
            type_label.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
            
            # Description label
            desc_label = ttk.Label(
                btn_container,
                text=description,
                font=(config.FONT_FAMILY, 8),
                wraplength=200
            )
            desc_label.grid(row=1, column=0, sticky="ew", padx=5)
            
            # Action button
            btn = ttk.Button(
                btn_container,
                text=f"▶ Run {analysis_type}",
                command=lambda at=analysis_type: self.on_preset_click(at)
            )
            btn.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
            
            self.preset_buttons.append(btn)
    
    def create_custom_section(self, parent):
        """Create custom query section - ALWAYS VISIBLE"""
        custom_frame = ttk.LabelFrame(parent, text="✍ Custom Analysis Query", padding="15")
        custom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        custom_frame.grid_columnconfigure(0, weight=1)
        
        # Instructions
        inst_label = ttk.Label(
            custom_frame,
            text="Enter your specific analysis question:",
            font=(config.FONT_FAMILY, 10, "bold")
        )
        inst_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Text input area
        text_frame = ttk.Frame(custom_frame)
        text_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        text_frame.grid_columnconfigure(0, weight=1)
        
        # Scrolled text widget
        self.custom_text = scrolledtext.ScrolledText(
            text_frame,
            height=4,
            wrap=tk.WORD,
            font=(config.FONT_FAMILY, 10),
            relief="sunken",
            borderwidth=2
        )
        self.custom_text.grid(row=0, column=0, sticky="ew")
        
        # Button frame - ALWAYS VISIBLE
        button_frame = ttk.Frame(custom_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Clear button
        clear_btn = ttk.Button(
            button_frame,
            text="🗑 Clear",
            command=self.clear_custom_query,
            width=10
        )
        clear_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Submit button - PROMINENT AND ALWAYS VISIBLE
        self.custom_submit_btn = ttk.Button(
            button_frame,
            text="🚀 ANALYZE CUSTOM QUERY",
            command=self.on_custom_query_submit,
            style="Accent.TButton"
        )
        self.custom_submit_btn.grid(row=0, column=2, sticky="e")
        
        # Example queries section
        examples_frame = ttk.Frame(custom_frame)
        examples_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        examples_frame.grid_columnconfigure(0, weight=1)
        
        # Examples label
        ex_label = ttk.Label(
            examples_frame,
            text="💡 Quick Examples (click to use):",
            font=(config.FONT_FAMILY, 9, "bold")
        )
        ex_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Example buttons
        examples = [
            "Check if all bypass capacitors are properly placed",
            "Verify crystal oscillator circuit design",
            "Analyze power supply filtering and regulation",
            "Review grounding and signal integrity",
            "Check for EMI/EMC design considerations"
        ]
        
        for i, example in enumerate(examples):
            ex_btn = ttk.Button(
                examples_frame,
                text=f"📝 {example}",
                command=lambda ex=example: self.insert_example(ex),
                style="Link.TButton"
            )
            ex_btn.grid(row=i+1, column=0, sticky="ew", pady=1)
    
    def create_status_section(self, parent):
        """Create status and info section"""
        status_frame = ttk.Frame(parent, padding="10")
        status_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status indicator
        self.status_label = ttk.Label(
            status_frame,
            text="📁 Upload a schematic to begin analysis",
            font=(config.FONT_FAMILY, 10),
            foreground="blue"
        )
        self.status_label.grid(row=0, column=0, pady=5)
        
        # Tips section
        tips_frame = ttk.LabelFrame(status_frame, text="💡 Tips", padding="10")
        tips_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        tips_text = """• Upload a datasheet (PDF) for more accurate analysis
• Use specific component references (e.g., R1, C2, U1) in custom queries  
• Mention specific concerns (power, timing, EMI, etc.) for targeted analysis
• The AI can identify component values, pin connections, and design issues"""
        
        tips_label = ttk.Label(
            tips_frame,
            text=tips_text,
            font=(config.FONT_FAMILY, 9),
            wraplength=400,
            justify="left"
        )
        tips_label.grid(row=0, column=0, sticky="w")
    
    def insert_example(self, example_text):
        """Insert example text into custom query field"""
        self.custom_text.delete(1.0, tk.END)
        self.custom_text.insert(1.0, example_text)
        self.custom_text.focus_set()
    
    def clear_custom_query(self):
        """Clear the custom query text"""
        self.custom_text.delete(1.0, tk.END)
        self.custom_text.focus_set()
    
    def on_preset_click(self, analysis_type):
        """Handle preset button click"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic Uploaded",
                "Please upload a schematic image first.\n\nUse the 'Upload Files' section to select your schematic."
            )
            return
        
        self.logger.info(f"Preset analysis clicked: {analysis_type}")
        
        # Visual feedback
        self.show_analysis_starting(analysis_type)
        
        # Trigger analysis
        try:
            self.analysis_callback(analysis_type)
        except Exception as e:
            self.logger.error(f"Error triggering analysis: {e}")
            messagebox.showerror("Analysis Error", f"Failed to start analysis:\n{str(e)}")
    
    def on_custom_query_submit(self):
        """Handle custom query submission"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic Uploaded",
                "Please upload a schematic image first.\n\nUse the 'Upload Files' section to select your schematic."
            )
            return
        
        # Get and validate query text
        query = self.custom_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning(
                "Empty Query",
                "Please enter an analysis question.\n\nTry one of the example queries or describe what you want to check."
            )
            self.custom_text.focus_set()
            return
        
        if len(query) < 10:
            messagebox.showwarning(
                "Query Too Short",
                "Please enter a more detailed question (at least 10 characters).\n\nDescribe specifically what you want to analyze."
            )
            self.custom_text.focus_set()
            return
        
        self.logger.info(f"Custom query submitted: {query[:100]}...")
        
        # Visual feedback
        self.show_analysis_starting("Custom Query")
        
        # Trigger analysis
        try:
            self.analysis_callback("Custom Query", query)
        except Exception as e:
            self.logger.error(f"Error triggering custom analysis: {e}")
            messagebox.showerror("Analysis Error", f"Failed to start custom analysis:\n{str(e)}")
    
    def show_analysis_starting(self, analysis_type):
        """Show visual feedback that analysis is starting"""
        # Temporarily disable buttons to prevent multiple submissions
        for btn in self.preset_buttons:
            btn.configure(state="disabled")
        
        if self.custom_submit_btn:
            self.custom_submit_btn.configure(text="🔄 Analyzing...", state="disabled")
        
        # Re-enable after a short delay (the main window will handle the actual analysis)
        self.after(3000, self.restore_button_states)
    
    def restore_button_states(self):
        """Restore button states after analysis starts"""
        self.update_button_states(self.schematic_loaded, self.datasheet_loaded)
    
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
                self.logger.warning(f"Could not configure preset button: {e}")
        
        # Update custom query submit button
        if self.custom_submit_btn:
            try:
                self.custom_submit_btn.configure(
                    state=button_state,
                    text="🚀 ANALYZE CUSTOM QUERY"
                )
            except tk.TclError as e:
                self.logger.warning(f"Could not configure custom submit button: {e}")
        
        # Update custom text widget
        if self.custom_text:
            try:
                text_state = "normal" if schematic_loaded else "disabled"
                self.custom_text.configure(state=text_state)
                
                # Update placeholder text
                if not schematic_loaded:
                    current_text = self.custom_text.get(1.0, tk.END).strip()
                    if not current_text or current_text == "Upload a schematic first to enable custom queries...":
                        self.custom_text.configure(state="normal")
                        self.custom_text.delete(1.0, tk.END)
                        self.custom_text.insert(1.0, "Upload a schematic first to enable custom queries...")
                        self.custom_text.configure(state="disabled")
                else:
                    # Clear placeholder text when enabled
                    current_text = self.custom_text.get(1.0, tk.END).strip()
                    if current_text == "Upload a schematic first to enable custom queries...":
                        self.custom_text.delete(1.0, tk.END)
                        
            except tk.TclError as e:
                self.logger.warning(f"Could not configure custom text: {e}")
        
        # Update status label
        if schematic_loaded and datasheet_loaded:
            status_text = "✅ Ready for analysis with schematic and datasheet"
            status_color = "green"
        elif schematic_loaded:
            status_text = "📊 Ready for analysis (datasheet optional for enhanced results)"
            status_color = "blue"
        else:
            status_text = "📁 Upload a schematic image to begin analysis"
            status_color = "red"
        
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=status_text, foreground=status_color)
        
        # Log status update
        self.logger.info(f"Button states updated - Schematic: {schematic_loaded}, Datasheet: {datasheet_loaded}")
    
    def reset(self):
        """Reset the panel to initial state"""
        # Clear custom query text
        if self.custom_text:
            try:
                self.custom_text.configure(state="normal")
                self.custom_text.delete(1.0, tk.END)
            except tk.TclError:
                pass
        
        # Reset button states
        self.update_button_states(False, False)
        
        self.logger.info("Analysis panel reset to initial state")
    
    def get_debug_info(self):
        """Get debugging information"""
        return {
            'schematic_loaded': self.schematic_loaded,
            'datasheet_loaded': self.datasheet_loaded,
            'preset_buttons_count': len(self.preset_buttons),
            'has_custom_submit_btn': self.custom_submit_btn is not None,
            'has_custom_text': self.custom_text is not None,
            'custom_submit_btn_text': self.custom_submit_btn.cget('text') if self.custom_submit_btn else 'None',
            'custom_text_state': self.custom_text.cget('state') if self.custom_text else 'None'
        }
    
    def configure_responsive_layout(self, event=None):
        """Configure layout based on window size"""
        # This can be called when window is resized
        try:
            window_width = self.winfo_width()
            
            # Adjust layout based on width
            if window_width < 600:
                # Narrow layout - stack buttons vertically
                pass
            else:
                # Wide layout - use 2-column grid
                pass
                
        except Exception as e:
            self.logger.debug(f"Error in responsive layout: {e}")


# Add custom button styles for better visibility
def setup_custom_styles():
    """Setup custom ttk styles"""
    try:
        style = ttk.Style()
        
        # Accent button style for submit button
        style.configure(
            "Accent.TButton",
            foreground="white",
            background="blue",
            font=("Arial", 10, "bold"),
            padding=(10, 5)
        )
        
        # Link button style for examples
        style.configure(
            "Link.TButton",
            foreground="blue",
            background="white",
            font=("Arial", 9),
            relief="flat"
        )
        
    except Exception:
        pass  # Ignore style errors


# Initialize styles when module is imported
setup_custom_styles()