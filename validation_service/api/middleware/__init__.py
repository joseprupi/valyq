from .error_handler import init_error_handlers
from .auth import require_auth

def init_middleware(app):
    """Initialize all middleware"""
    init_error_handlers(app)
    # Add other middleware initialization here