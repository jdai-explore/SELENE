#!/usr/bin/env python3
"""
SELENE - Schematic Review Tool with Datasheet Integration
Main entry point for the application
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox
import requests
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
import config


def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("SELENE Application Started")
    logger.info("=" * 50)
    
    return logger


def check_dependencies():
    """Verify that required dependencies are available"""
    logger = logging.getLogger(__name__)
    missing_deps = []
    
    # Check Python packages
    required_packages = {
        'tkinter': 'tkinter',
        'PIL': 'Pillow',
        'PyPDF2': 'PyPDF2',
        'requests': 'requests',
        'pdfplumber': 'pdfplumber'
    }
    
    for module, package_name in required_packages.items():
        try:
            __import__(module)
            logger.info(f"✓ {package_name} is installed")
        except ImportError:
            missing_deps.append(package_name)
            logger.error(f"✗ {package_name} is not installed")
    
    # Check Ollama connection
    ollama_status = check_ollama_connection()
    
    if missing_deps:
        error_msg = f"Missing dependencies: {', '.join(missing_deps)}\n\n"
        error_msg += "Please install them using:\npip install -r requirements.txt"
        logger.error(error_msg)
        
        # Show GUI error message
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", error_msg)
        root.destroy()
        return False
    
    if not ollama_status:
        warning_msg = "Ollama is not running or llava model is not available.\n\n"
        warning_msg += "Please:\n1. Install Ollama from https://ollama.ai\n"
        warning_msg += "2. Start Ollama\n3. Run: ollama pull llava"
        logger.warning(warning_msg)
        
        # Show GUI warning but don't exit
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(
            "Ollama Not Available", 
            warning_msg + "\n\nDo you want to continue anyway?",
            icon='warning'
        )
        root.destroy()
        
        if not result:
            return False
    
    logger.info("All dependencies verified successfully")
    return True


def check_ollama_connection():
    """Check if Ollama is running and llava model is available"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check if Ollama is running
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            logger.warning("Ollama API is not responding correctly")
            return False
        
        # Check if llava model is available
        models = response.json().get('models', [])
        model_names = [model.get('name', '') for model in models]
        
        if not any('llava' in name for name in model_names):
            logger.warning("llava model is not installed in Ollama")
            return False
        
        logger.info("✓ Ollama is running and llava model is available")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot connect to Ollama at " + config.OLLAMA_BASE_URL)
        return False
    except Exception as e:
        logger.error(f"Error checking Ollama: {str(e)}")
        return False


def create_directories():
    """Create necessary directories for the application"""
    directories = ['temp', 'logs', 'exports']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.info("Created application directories")


def cleanup_temp_files():
    """Clean up temporary files from previous sessions"""
    logger = logging.getLogger(__name__)
    temp_dir = Path("temp")
    
    if temp_dir.exists():
        for file in temp_dir.iterdir():
            try:
                file.unlink()
                logger.debug(f"Cleaned up temp file: {file}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {file}: {e}")


def main():
    """Main application entry point"""
    # Setup logging first
    logger = setup_logging()
    
    try:
        # Create necessary directories
        create_directories()
        
        # Clean up temp files
        cleanup_temp_files()
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Dependency check failed, exiting...")
            sys.exit(1)
        
        # Log system information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Create and run the main application
        logger.info("Starting GUI application...")
        app = MainWindow()
        
        # Set up graceful shutdown
        def on_closing():
            logger.info("Application shutdown requested")
            cleanup_temp_files()
            app.destroy()
            logger.info("SELENE Application Closed")
            sys.exit(0)
        
        app.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Run the application
        app.mainloop()
        
    except Exception as e:
        logger.exception(f"Fatal error in main: {str(e)}")
        
        # Show error dialog
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Fatal Error", 
            f"An unexpected error occurred:\n\n{str(e)}\n\nPlease check the logs for details."
        )
        root.destroy()
        
        sys.exit(1)


if __name__ == "__main__":
    main()