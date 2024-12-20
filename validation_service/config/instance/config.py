"""
Instance-specific configuration overrides.
"""

# Override default upload folder for this specific installation
BASE_UPLOAD_FOLDER = "/Users/yourname/projects/validation_service/local_uploads"

# Local database connection
DATABASE_URL = "postgresql://localhost/validation_dev"

# Development API keys (do not commit real keys!)
CLAUDE_API_KEY = "your-local-development-key"
CHATGPT_API_KEY = "your-local-development-key"

# Local execution service URL
EXECUTION_SERVICE_URL = "http://localhost:5000"

# Override any other settings specific to your installation
LOG_FILE = "/Users/yourname/logs/validation_service.log"
DEBUG = True

# Custom settings specific to your development environment
SKIP_CERTAIN_VALIDATIONS = True
USE_LOCAL_FILE_CACHE = True