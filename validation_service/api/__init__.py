from flask import Flask, send_from_directory
from flask_cors import CORS
from config import get_settings


def init_app(services) -> Flask:
    settings = get_settings()

    # app = Flask(__name__)
    app = Flask(
        __name__, static_folder='/root/llm_validation/validation/validation_frontend/build', static_url_path='')
    CORS(app)

    # Add auth_service to app context
    app.auth_service = services.auth_service

    # Initialize routes
    from .routes.validation_routes import init_validation_routes
    from .routes.test_routes import init_test_routes
    from .routes.auth_routes import init_auth_routes

    app.register_blueprint(init_validation_routes(
        services.validation_service, services.test_service, services.document_service))
    app.register_blueprint(init_test_routes(services.test_service))
    app.register_blueprint(init_auth_routes(services.auth_service))

    # Initialize error handlers
    from .middleware.error_handler import init_error_handlers
    init_error_handlers(app)

    @app.route('/')
    def home():
        """Serve React App"""
        return send_from_directory(app.static_folder, 'index.html')

    return app
