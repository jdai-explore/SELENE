"""
Analysis control buttons and custom query input
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
        {
            "name": "Component Verification",
            "icon": "🔍",
            "tooltip": "Verify component values against datasheet recommendations"
        },
        {
            "name": "Pin Configuration Check",
            "icon": "📌",
            "tooltip": "Check pin connections and assignments"
        },
        {
            "name": "Power Supply Analysis",
            "icon": "⚡",
            "tooltip": "Analyze power supply design and decoupling"
        },
        {
            "name": "Design Compliance",
            "icon": "✅",
            "tooltip": "Check compliance with datasheet recommendations"
        },
        {
            "name": "Missing Components",
            "icon": "❓",
            "tooltip": "Identify missing required components"
        }
    ]
    
    def __init__(self, parent, analysis_callback):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.analysis_callback = analysis_callback
        
        # State variables
        self.buttons = {}
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
        
        # Create preset buttons frame
        self.create_preset_buttons(main_frame)
        
        # Separator
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill="x", pady=15)
        
        # Create custom query section
        self.create_custom_query(main_frame)
        
        # Info label at bottom
        info_label = ttk.Label(
            main_frame,
            text="💡 Tip: Upload a datasheet for more accurate analysis",
            font=(config.FONT_FAMILY, 10),
            foreground=config.COLORS['text_secondary']
        )
        info_label.pack(side="bottom", pady=(10, 0))
    
    def create_preset_buttons(self, parent):
        """Create the preset analysis buttons"""
        # Frame for buttons
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill="both", expand=True)
        
        # Configure grid
        for i in range(3):
            buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Create buttons in a grid layout
        for idx, analysis in enumerate(self.PRESET_ANALYSES):
            row = idx // 3
            col = idx % 3
            
            # Button frame for styling
            btn_frame = tk.Frame(
                buttons_frame,
                relief="raised",
                borderwidth=1,
                bg=config.COLORS['bg_secondary']
            )
            btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Make the row expandable
            buttons_frame.grid_rowconfigure(row, weight=1)
            
            # Create button content
            btn_content = tk.Frame(btn_frame, bg=config.COLORS['bg_secondary'])
            btn_content.pack(expand=True)
            
            # Icon
            icon_label = tk.Label(
                btn_content,
                text=analysis["icon"],
                font=(config.FONT_FAMILY, 24),
                bg=config.COLORS['bg_secondary']
            )
            icon_label.pack()
            
            # Name
            name_label = tk.Label(
                btn_content,
                text=analysis["name"],
                font=(config.FONT_FAMILY, 11, "bold"),
                bg=config.COLORS['bg_secondary'],
                wraplength=120
            )
            name_label.pack(pady=(5, 0))
            
            # Store button reference
            self.buttons[analysis["name"]] = {
                "frame": btn_frame,
                "content": btn_content,
                "icon": icon_label,
                "name": name_label
            }
            
            # Bind click events
            for widget in [btn_frame, btn_content, icon_label, name_label]:
                widget.bind("<Button-1>", lambda e, a=analysis["name"]: self.on_preset_click(a))
                widget.bind("<Enter>", lambda e, f=btn_frame: self.on_button_hover(f, True))
                widget.bind("<Leave>", lambda e, f=btn_frame: self.on_button_hover(f, False))
            
            # Add tooltip
            self.create_tooltip(btn_frame, analysis["tooltip"])
    
    def create_custom_query(self, parent):
        """Create custom query input section"""
        # Container frame
        custom_frame = ttk.LabelFrame(parent, text="Custom Query", padding="10")
        custom_frame.pack(fill="x")
        
        # Description
        desc_label = ttk.Label(
            custom_frame,
            text="Enter your own analysis question:",
            font=(config.FONT_FAMILY, 10)
        )
        desc_label.pack(anchor="w")
        
        # Input frame
        input_frame = ttk.Frame(custom_frame)
        input_frame.pack(fill="x", pady=(5, 0))
        
        # Text entry
        self.custom_query_var = tk.StringVar()
        self.custom_entry = ttk.Entry(
            input_frame,
            textvariable=self.custom_query_var,
            font=(config.FONT_FAMILY, 11)
        )
        self.custom_entry.pack(side="left", fill="x", expand=True)
        
        # Submit button
        self.custom_submit_btn = ttk.Button(
            input_frame,
            text="Analyze",
            command=self.on_custom_query_submit,
            state="disabled"
        )
        self.custom_submit_btn.pack(side="right", padx=(5, 0))
        
        # Bind Enter key
        self.custom_entry.bind("<Return>", lambda e: self.on_custom_query_submit())
        
        # Example queries
        examples_label = ttk.Label(
            custom_frame,
            text="Examples: \"Check if all bypass capacitors are present\" | "
                 "\"Verify crystal oscillator circuit\" | \"Analyze grounding\"",
            font=(config.FONT_FAMILY, 9),
            foreground=config.COLORS['text_secondary'],
            wraplength=400
        )
        examples_label.pack(anchor="w", pady=(5, 0))
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=(config.FONT_FAMILY, 9)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def on_button_hover(self, button_frame, entering):
        """Handle button hover effects"""
        if button_frame.cget("state") == "disabled":
            return
        
        if entering:
            button_frame.configure(bg=config.COLORS['accent'])
        else:
            button_frame.configure(bg=config.COLORS['bg_secondary'])
    
    def on_preset_click(self, analysis_type):
        """Handle preset button click"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic",
                "Please upload a schematic image first"
            )
            return
        
        self.logger.info(f"Preset analysis clicked: {analysis_type}")
        
        # Visual feedback
        self.flash_button(analysis_type)
        
        # Trigger analysis
        self.analysis_callback(analysis_type)
    
    def on_custom_query_submit(self):
        """Handle custom query submission"""
        if not self.schematic_loaded:
            messagebox.showwarning(
                "No Schematic",
                "Please upload a schematic image first"
            )
            return
        
        query = self.custom_query_var.get().strip()
        if not query:
            messagebox.showwarning(
                "Empty Query",
                "Please enter an analysis question"
            )
            return
        
        self.logger.info(f"Custom query submitted: {query}")
        
        # Trigger analysis
        self.analysis_callback("Custom Query", query)
    
    def flash_button(self, analysis_type):
        """Flash button for visual feedback"""
        if analysis_type not in self.buttons:
            return
        
        button = self.buttons[analysis_type]["frame"]
        original_bg = button.cget("bg")
        
        # Flash effect
        button.configure(bg=config.COLORS['success'])
        self.after(100, lambda: button.configure(bg=original_bg))
    
    def update_button_states(self, schematic_loaded, datasheet_loaded):
        """Enable or disable buttons based on file upload status"""
        self.schematic_loaded = schematic_loaded
        self.datasheet_loaded = datasheet_loaded
        
        # Update preset buttons
        for analysis_name, button_info in self.buttons.items():
            frame = button_info["frame"]
            
            if schematic_loaded:
                # Enable button
                frame.configure(relief="raised", bg=config.COLORS['bg_secondary'])
                for widget in button_info.values():
                    if isinstance(widget, tk.Widget):
                        widget.configure(state="normal")
                        if hasattr(widget, 'configure'):
                            try:
                                widget.configure(cursor="hand2")
                            except:
                                pass
            else:
                # Disable button
                frame.configure(relief="flat", bg="#e0e0e0")
                for widget in button_info.values():
                    if isinstance(widget, tk.Widget):
                        widget.configure(state="disabled")
                        if hasattr(widget, 'configure'):
                            try:
                                widget.configure(cursor="")
                            except:
                                pass
        
        # Update custom query button
        if schematic_loaded:
            self.custom_submit_btn.configure(state="normal")
            self.custom_entry.configure(state="normal")
        else:
            self.custom_submit_btn.configure(state="disabled")
            self.custom_entry.configure(state="disabled")
        
        # Update visual indicators for datasheet status
        if datasheet_loaded:
            # Add visual indicator that datasheet is loaded
            for button_info in self.buttons.values():
                icon_label = button_info["icon"]
                # Could add a small indicator here if desired
        
        self.logger.info(f"Button states updated - Schematic: {schematic_loaded}, Datasheet: {datasheet_loaded}")
    
    def reset(self):
        """Reset the panel to initial state"""
        self.custom_query_var.set("")
        self.update_button_states(False, False)