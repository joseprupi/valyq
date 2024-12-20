from flask import Blueprint
from .validation_routes import init_validation_routes
from .test_routes import init_test_routes
from .execution_routes import init_execution_routes

def init_routes(app, services):
    """Initialize all route blueprints"""
    app.register_blueprint(init_validation_routes(services.validation_service, services.test_service, services.document_service))
    app.register_blueprint(init_test_routes(services.test_service))
    app.register_blueprint(init_execution_routes(
        services.execution_service,
        services.file_storage
    ))