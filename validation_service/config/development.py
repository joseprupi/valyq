# config/development.py
from pathlib import Path
from . import ROOT_DIR
import os

development_settings = {
    # Environment
    'ENVIRONMENT': 'development',
    'DEBUG': True,
    'TESTING': False,

    # File Storage
    'BASE_UPLOAD_FOLDER': str(ROOT_DIR / 'submissions'),
    'TEMP_FOLDER': str(ROOT_DIR / 'submissions/temp'),
    'IMAGE_CACHE_FOLDER': str(ROOT_DIR / 'submissions/image_cache'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024 * 1024,  # 16GB
    'ALLOWED_EXTENSIONS': {
        'trainingScript': ['.py'],
        'trainedModel': ['.pkl', '.h5', '.model', '.txt'],
        'trainingDataset': ['.csv', '.pkl', '.json', '.pickle'],
        'testDataset': ['.csv', '.pkl', '.json', '.pickle']
    },

    # LLM Settings
    'LLM_PROVIDER': 'claude',  # or 'chatgpt'
    'LLM_API_KEY': os.getenv('CLAUDE_API_KEY', ''),  # Get from environment variable
    'LLM_MAX_RETRIES': 3,
    'LLM_TIMEOUT': 30,
    'LLM_TEMPERATURE': 0.7,
    #'LLM_MAX_TOKENS': 2000,

    # Execution Service
    'EXECUTION_SERVICE_URL': 'http://localhost:5000',
    'EXECUTION_TIMEOUT': 300,
    'EXECUTION_MAX_RETRIES': 3,
    'EXECUTION_FOLDER': str(ROOT_DIR / 'submissions/executions'),

    # Security
    'SECRET_KEY': 'dev-secret-key-change-in-production',
    'ALLOWED_ORIGINS': ['http://localhost:3000'],
    'REQUIRE_AUTHENTICATION': False,
    'UPLOAD_RATE_LIMIT': 10,

    # Logger Settings
    'LOG_DIR': str(ROOT_DIR / 'logs'),
    'LOG_LEVEL': 'DEBUG',
    'LOG_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
    'LOG_BACKUP_COUNT': 5,  # Keep 5 backup files

    # Development Tools
    'DEVELOPMENT_TOOLS': {
        'enable_debugger': True,
        'enable_reloader': True,
        'use_evalex': True,
        'enable_profiler': False,
    },
    
    # Template settings
    'TEMPLATES_PATH': str(ROOT_DIR / 'core/templates/templates.yaml'),
    'AUTH_SECRET_KEY': 'xxxxxx',
    'AUTH_STORE_PATH': 'xxxxxx'
}