"""
Main settings implementation for the validation service.
Handles loading and managing configuration from different sources.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import os
from functools import lru_cache
from dataclasses import dataclass, field

# Import environment-specific settings
from .development import development_settings
# from .production import production_settings
# from .testing import testing_settings

class ConfigurationError(Exception):
    """Raised when there's a configuration error."""
    pass

@dataclass
class Settings:
    """
    Main settings class that holds all configuration.
    Uses dataclass for type safety and automatic initialization.
    """
    # Environment
    environment: str
    host: str
    port: str
    debug: bool
    testing: bool

    # File Storage
    base_upload_folder: str
    temp_folder: str
    image_cache_folder: str
    max_content_length: int
    allowed_extensions: Dict[str, list]

    # LLM
    llm_provider: str
    llm_api_key: str
    llm_max_retries: int
    llm_timeout: int
    llm_temperature: float
    #llm_max_tokens: int

    # Execution Service
    execution_service_url: str
    execution_timeout: int
    execution_max_retries: int
    execution_folder: str

    # Security
    secret_key: str
    allowed_origins: list
    require_authentication: bool
    upload_rate_limit: int

    # Auth
    auth_secret_key: str
    auth_store_path: str

    # Logging
    log_level: str
    log_dir: str
    interaction_logs_dir: str = field(default="/tmp/logs/interactions")
    #enable_request_logging: bool
    #enable_performance_logging: bool

    # Development Tools
    development_tools: Dict[str, bool] = field(default_factory=dict)

    # Template settings
    templates_path: str = field(default="core/templates/templates.yaml")

    @classmethod
    def load(cls) -> 'Settings':
        """
        Load settings from the appropriate source based on environment.
        Priority: instance config > environment variables > environment-specific settings
        """
        # Get base settings from environment
        env = os.getenv('ENVIRONMENT', 'development').lower()
        
        # Load base configuration based on environment
        if env == 'production':
            base_settings = production_settings
        elif env == 'testing':
            base_settings = testing_settings
        else:
            base_settings = development_settings

        # Load instance config if it exists
        instance_config = {}
        instance_path = Path(__file__).parent.parent / 'instance' / 'config.py'
        if instance_path.exists():
            with open(instance_path) as f:
                exec(f.read(), {}, instance_config)

        # Merge configurations
        final_settings = {
            # Start with base settings
            **base_settings,
            # Override with environment variables
            **{k: v for k, v in os.environ.items() if k.isupper()},
            # Override with instance config
            **instance_config
        }

        try:
            return cls(
                # Environment
                environment=final_settings['ENVIRONMENT'],
                debug=final_settings['DEBUG'],
                testing=final_settings['TESTING'],
                host=final_settings['FLASK_SERVICE_URL'],
                port=final_settings['FLASK_SERVICE_PORT'],

                # File Storage
                base_upload_folder=final_settings['BASE_UPLOAD_FOLDER'],
                temp_folder=final_settings['TEMP_FOLDER'],
                image_cache_folder=final_settings['IMAGE_CACHE_FOLDER'],
                max_content_length=final_settings['MAX_CONTENT_LENGTH'],
                allowed_extensions=final_settings['ALLOWED_EXTENSIONS'],

                # LLM
                llm_provider=final_settings['LLM_PROVIDER'],
                llm_api_key=final_settings['LLM_API_KEY'],
                llm_max_retries=final_settings['LLM_MAX_RETRIES'],
                llm_timeout=final_settings['LLM_TIMEOUT'],
                llm_temperature=final_settings['LLM_TEMPERATURE'],
                #llm_max_tokens=final_settings['LLM_MAX_TOKENS'],

                # Execution Service
                execution_service_url=final_settings['EXECUTION_SERVICE_URL'],
                execution_timeout=final_settings['EXECUTION_TIMEOUT'],
                execution_max_retries=final_settings['EXECUTION_MAX_RETRIES'],
                execution_folder=final_settings['EXECUTION_FOLDER'],

                # Security
                secret_key=final_settings['SECRET_KEY'],
                allowed_origins=final_settings['ALLOWED_ORIGINS'],
                require_authentication=final_settings['REQUIRE_AUTHENTICATION'],
                upload_rate_limit=final_settings['UPLOAD_RATE_LIMIT'],

                # Logging
                log_level=final_settings['LOG_LEVEL'],
                log_dir=final_settings['LOG_DIR'],
                #enable_request_logging=final_settings['ENABLE_REQUEST_LOGGING'],
                #enable_performance_logging=final_settings['ENABLE_PERFORMANCE_LOGGING'],

                # Development Tools
                development_tools=final_settings.get('DEVELOPMENT_TOOLS', {}),

                # Auth
                auth_secret_key=final_settings['AUTH_SECRET_KEY'],
                auth_store_path=final_settings['AUTH_STORE_PATH'],
            )
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}")

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.base_upload_folder,
            self.temp_folder,
            self.image_cache_folder,
            self.execution_folder,
            os.path.dirname(self.log_dir)
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'development'

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == 'testing'

# Cache settings instance
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings.load()
    settings.ensure_directories()
    return settings