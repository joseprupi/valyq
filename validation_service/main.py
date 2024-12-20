from pathlib import Path
from flask import Flask
from api import init_app
from config import get_settings
from core.services import init_services
from infrastructure import init_infrastructure

def create_app() -> Flask:
    """Create and configure the Flask application"""
    # Load settings
    settings = get_settings()
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Initialize infrastructure
    infrastructure = init_infrastructure(settings)
    
    # Initialize services with all components
    services = init_services(
        storage=infrastructure.storage,
        execution_client=infrastructure.execution_client,
        llm_client=infrastructure.llm_client,
        logger_service=infrastructure.logger_service,
        settings=settings
    )
    
    # Initialize Flask app with services
    app = init_app(services)
    #app = init_app()
    
    return app

def main():
    settings = get_settings()
    app = create_app()
    
    app.run(
        host=settings.host,
        port=settings.port,
        debug=False
    )

if __name__ == "__main__":
    main()