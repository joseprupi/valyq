import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from infrastructure.auth.auth_store import AuthStore

class AuthService:
    """Authentication service"""
    
    def __init__(self, secret_key: str, auth_store: AuthStore):
        self.secret_key = secret_key
        self.auth_store = auth_store
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        if not self.auth_store.verify_credentials(username, password):
            return None
            
        # Generate JWT token
        payload = {
            'sub': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.InvalidTokenError:
            return None