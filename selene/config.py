"""
Configuration settings for SELENE application
"""

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llava"
OLLAMA_TIMEOUT = 30

# File settings
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp']
SUPPORTED_PDF_FORMATS = ['.pdf']
MAX_FILE_SIZE_MB = 50

# GUI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "SELENE - Schematic Review Tool"
RESULT_FONT_SIZE = 11
FONT_FAMILY = "Arial"

# Analysis settings
MAX_CONTEXT_LENGTH = 4000
ANALYSIS_TIMEOUT = 60

# Color scheme
COLORS = {
    'bg_primary': '#f0f0f0',
    'bg_secondary': '#ffffff',
    'accent': '#0066cc',
    'success': '#28a745',
    'error': '#dc3545',
    'text_primary': '#333333',
    'text_secondary': '#666666'
}

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "selene.log"
