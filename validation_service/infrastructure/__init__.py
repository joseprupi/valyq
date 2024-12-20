from dataclasses import dataclass
from .storage import LocalFileStorage
from .execution import ExecutionClient
from .llm import LLMClient  
from core.services.logger_service import LoggerService
from core.services.auth_service import AuthService
from infrastructure.auth.auth_store import AuthStore

@dataclass
class Infrastructure:
    """Container for infrastructure components"""
    storage: LocalFileStorage
    execution_client: ExecutionClient
    llm_client: LLMClient
    logger_service: LoggerService
    auth_store: AuthStore
    auth_service: AuthService  

def init_infrastructure(settings: 'Settings') -> Infrastructure:
    """Initialize all infrastructure components"""
    storage = LocalFileStorage(base_path=settings.base_upload_folder)
    execution_client = ExecutionClient()
    llm_client = LLMClient(
        provider=settings.llm_provider,
        api_key=settings.llm_api_key,  # Make sure this is in your settings
        max_retries=settings.llm_max_retries
    )
    logger_service = LoggerService(
        log_dir=settings.log_dir
        #log_level=settings.log_level
    )

    # Initialize auth components
    auth_store = AuthStore(
        file_path=settings.auth_store_path  # You'll need to add this to settings
    )
    
    auth_service = AuthService(
        secret_key=settings.auth_secret_key,  # You'll need to add this to settings
        auth_store=auth_store
    )
    
    return Infrastructure(
        storage=storage,
        execution_client=execution_client,
        llm_client=llm_client,
        logger_service=logger_service,
        auth_store=auth_store,
        auth_service=auth_service
    )