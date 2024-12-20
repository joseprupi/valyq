from functools import wraps
from flask import request, jsonify, current_app
from asgiref.sync import sync_to_async, async_to_sync
import asyncio

def require_auth():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'No authorization header'}), 401
                
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != 'bearer':
                    return jsonify({'error': 'Invalid authentication scheme'}), 401
            except ValueError:
                return jsonify({'error': 'Invalid authorization header'}), 401
            
            # Get auth_service from app context
            auth_service = current_app.auth_service    
            payload = auth_service.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401
                
            # Add user info to request
            request.user = payload

            # If the decorated function is async, wrap it with async_to_sync
            if asyncio.iscoroutinefunction(f):
                return async_to_sync(f)(*args, **kwargs)
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator