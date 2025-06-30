import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Configuration
DEFAULT_MODEL = "deepseek/deepseek-r1-0528-qwen3-8b:free"

# File Upload Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'image': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'],
    'text': ['.txt', '.csv', '.xlsx', '.xls']
}

# OCR Configuration
TESSERACT_CONFIG = '--oem 3 --psm 6' 