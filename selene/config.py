"""
Configuration settings for SELENE application
"""

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llava-llama3:8b"  # Updated for your available model
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

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = "selene.log"

# Application metadata
APP_NAME = "SELENE"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Schematic Review Tool with Datasheet Integration"

# Performance settings
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
THUMBNAIL_SIZE = (200, 150)

# Analysis configuration
ANALYSIS_RETRY_COUNT = 3
ANALYSIS_RETRY_DELAY = 2

# Cache settings
ENABLE_ANALYSIS_CACHE = True
CACHE_MAX_SIZE = 100
CACHE_EXPIRY_HOURS = 24

# Debug settings
DEBUG_MODE = False
VERBOSE_LOGGING = False

# Model-specific settings for llava-llama3:8b
MODEL_SETTINGS = {
    'temperature': 0.1,
    'top_p': 0.9,
    'top_k': 40,
    'num_predict': 2048,
    'repeat_penalty': 1.1
}

# File processing settings
PDF_MAX_PAGES = 50
PDF_MAX_SIZE_MB = 100
TEXT_MAX_LENGTH = 50000

# UI responsiveness settings
UI_UPDATE_INTERVAL = 100  # milliseconds
PROGRESS_UPDATE_INTERVAL = 500  # milliseconds

# Network settings
REQUEST_TIMEOUT = 30
CONNECTION_TIMEOUT = 10
MAX_RETRIES = 3

# Export settings
EXPORT_FORMATS = ['txt', 'md', 'html']
DEFAULT_EXPORT_FORMAT = 'txt'

# Workspace settings
WORKSPACE_DIR = "workspace"
TEMP_DIR = "temp"
EXPORTS_DIR = "exports"
LOGS_DIR = "logs"
CACHE_DIR = "cache"

# Safety limits
MAX_CONCURRENT_ANALYSES = 1
MAX_IMAGE_SIZE_PIXELS = 10000000  # 10 megapixels
MIN_IMAGE_SIZE_PIXELS = 10000     # 100x100 minimum

# Feature flags
ENABLE_DATASHEET_PARSING = True
ENABLE_CUSTOM_QUERIES = True
ENABLE_ANALYSIS_CACHING = True
ENABLE_RESULT_EXPORT = True
ENABLE_DEBUG_INFO = True

# Advanced analysis settings
COMPONENT_DETECTION_THRESHOLD = 0.7
PIN_DETECTION_THRESHOLD = 0.8
TEXT_RECOGNITION_THRESHOLD = 0.6

# Model fallback options (in order of preference)
FALLBACK_MODELS = [
    "llava-llama3:8b",
    "llava:latest", 
    "llava:13b",
    "llava:7b",
    "bakllava:latest"
]

# Error handling
MAX_ERROR_RETRIES = 3
ERROR_COOLDOWN_SECONDS = 5
SHOW_ERROR_DETAILS = True

# Performance optimization
ENABLE_IMAGE_OPTIMIZATION = True
ENABLE_TEXT_PREPROCESSING = True
ENABLE_RESPONSE_CACHING = True

# Internationalization (future use)
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en"]

# API rate limiting
API_RATE_LIMIT_REQUESTS = 100
API_RATE_LIMIT_WINDOW = 3600  # 1 hour

# Development settings
DEV_MODE = False
MOCK_OLLAMA_RESPONSES = False
SKIP_MODEL_VALIDATION = False

# Backup and recovery
AUTO_BACKUP_RESULTS = True
BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_FILES = 100

# User experience
SHOW_TOOLTIPS = True
ENABLE_KEYBOARD_SHORTCUTS = True
REMEMBER_WINDOW_SIZE = True
AUTO_SAVE_PREFERENCES = True

# Quality assurance
MIN_RESPONSE_LENGTH = 10
MAX_RESPONSE_LENGTH = 10000
VALIDATE_RESPONSES = True

# Compatibility settings
FORCE_COMPATIBLE_MODE = False
LEGACY_FILE_SUPPORT = True
STRICT_TYPE_CHECKING = True