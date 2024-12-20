import json
import bcrypt
from pathlib import Path
from typing import Optional, Dict

class AuthStore:
    """Simple file-based authentication store"""
    
    def __init__(self, file_path: str = "auth_store.json"):
        self.file_path = Path(file_path)
        self._ensure_store_exists()
    
    def _ensure_store_exists(self) -> None:
        """Create auth store if it doesn't exist"""
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps({"users": {}}))
    
    def _read_store(self) -> Dict:
        """Read the auth store"""
        return json.loads(self.file_path.read_text())
    
    def _write_store(self, data: Dict) -> None:
        """Write to the auth store"""
        self.file_path.write_text(json.dumps(data, indent=2))
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        store = self._read_store()
        user = store["users"].get(username)
        if not user:
            return False
        
        return bcrypt.checkpw(
            password.encode('utf-8'),
            user["password_hash"].encode('utf-8')
        )
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user details"""
        store = self._read_store()
        return store["users"].get(username)