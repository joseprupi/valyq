# core/services/__init__.py
from dataclasses import dataclass
from typing import Optional

from core.services.validation_service import ValidationService
from core.services.test_service import TestService
from core.services.execution_service import ExecutionService
from core.templates.template_manager import TemplateManager
from core.services.logger_service import LoggerService
from core.services.interaction_logger import InteractionLogger
from core.services.auth_service import AuthService
from core.services.document_service import DocumentService
from infrastructure.auth.auth_store import AuthStore
from infrastructure.storage import LocalFileStorage
from infrastructure.execution import ExecutionClient
from ..interfaces.llm_client import LLMClient

@dataclass
class Services:
    """Container for all services"""
    validation_service: ValidationService
    test_service: TestService
    execution_service: ExecutionService
    template_manager: TemplateManager
    interaction_logger: InteractionLogger
    auth_service: AuthService
    document_service: DocumentService

def init_services(
    storage: LocalFileStorage,
    execution_client: ExecutionClient,
    llm_client: LLMClient,
    logger_service: LoggerService,
    settings: 'Settings'
) -> Services:
    """Initialize all services with their dependencies"""
    
    # Initialize template manager first
    template_manager = TemplateManager(
        templates_path=settings.templates_path,
        debug_mode=settings.debug,
        base_upload_folder=settings.base_upload_folder
    )

    interaction_logger = InteractionLogger(
        log_dir=settings.interaction_logs_dir
    )
    
    # Initialize execution service with all required parameters
    execution_service = ExecutionService(
        file_storage=storage,
        llm_client=llm_client,  # We need to create this
        execution_client=execution_client,
        service_url=settings.execution_service_url,
        base_path=settings.base_upload_folder,
        #logger=logger_service,
        interaction_logger=interaction_logger,
        max_retries=settings.execution_max_retries
    )
    
    # Initialize validation service
    validation_service = ValidationService(
        llm_client=llm_client,
        file_storage=storage,
        execution_service=execution_service,
        template_manager=template_manager,
        base_upload_folder=settings.base_upload_folder,
        logger=logger_service
    )

        # Initialize test service
    test_service = TestService(
        llm_client=llm_client,
        file_storage=storage,
        execution_service=execution_service,
        validation_service=validation_service,
        template_manager=template_manager,
        image_cache_dir=settings.image_cache_folder
    )

    auth_store = AuthStore()
    auth_service = AuthService(
        secret_key=settings.auth_secret_key,
        auth_store=auth_store
    )

    document_service = DocumentService(
        base_path=settings.base_upload_folder
    )
    
    return Services(
        validation_service=validation_service,
        test_service=test_service,
        execution_service=execution_service,
        template_manager=template_manager,
        interaction_logger=interaction_logger,
        auth_service=auth_service,
        document_service=document_service
    )