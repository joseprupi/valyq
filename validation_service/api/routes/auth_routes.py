from flask import Blueprint, request, jsonify
from core.services.auth_service import AuthService
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def init_auth_routes(auth_service: AuthService) -> Blueprint:
    
    @auth_bp.route('/login', methods=['POST'])
    async def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
            
        token = auth_service.authenticate(username, password)
        if not token:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        return jsonify({'token': token})
    
    @auth_bp.route('/verify', methods=['GET'])
    async def verify():
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
            
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid authentication scheme'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header'}), 401
            
        payload = auth_service.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
            
        return jsonify({'valid': True, 'username': payload['sub']})
        
    return auth_bp