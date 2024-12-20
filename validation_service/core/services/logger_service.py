# core/services/logger_service.py
from pathlib import Path
from datetime import datetime
import json
import uuid
from typing import Any, Dict, Optional

class LoggerService:
    def __init__(self, log_dir: str):
        self.base_log_dir = Path(log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        
        # General logs for non-validation-specific events
        self.general_log_file = self.base_log_dir / 'general.log'

    def _get_validation_dir(self, validation_id: str) -> Path:
        """Get or create validation-specific directory"""
        validation_dir = self.base_log_dir / validation_id
        validation_dir.mkdir(exist_ok=True)
        
        # Create content subdirectories
        content_dir = validation_dir / 'content'
        for subdir in ['prompts', 'responses', 'code', 'results']:
            (content_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        return validation_dir

    def _save_content(self, content: Any, content_type: str, validation_id: str) -> str:
        """Save content to validation-specific directory"""
        if content is None:
            return None
            
        validation_dir = self._get_validation_dir(validation_id)
        content_path = validation_dir / 'content' / content_type / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.txt"
        
        content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
        content_path.write_text(content_str, encoding='utf-8')
        
        return str(content_path.relative_to(validation_dir))

    def _write_log(self, entry: Dict[str, Any], validation_id: Optional[str] = None):
        """Write log entry to appropriate log file"""
        if validation_id:
            validation_dir = self._get_validation_dir(validation_id)
            log_file = validation_dir / 'main.log'
        else:
            log_file = self.general_log_file

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def log_validation_event(
        self,
        event_type: str,
        validation_id: str,
        details: Dict[str, Any],
        error: Optional[Exception] = None
    ):
        """Log validation-related events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'validation_id': validation_id,
            'details': details
        }
        
        self._write_log(log_entry, validation_id)

    def log_llm_interaction(
        self,
        interaction_type: str,
        prompt: str,
        validation_id: str,
        response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        prompt_ref = self._save_content(prompt, 'prompts', validation_id)
        response_ref = self._save_content(response, 'responses', validation_id) if response else None

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'llm_interaction',
            'interaction_type': interaction_type,
            'prompt_ref': prompt_ref,
            'response_ref': response_ref,
            'metadata': metadata or {}
        }

        self._write_log(log_entry, validation_id)

    def log_execution(
        self,
        execution_id: str,
        validation_id: str,
        code: str,
        result: Optional[str] = None
    ):
        code_ref = self._save_content(code, 'code', validation_id)
        result_ref = self._save_content(result, 'results', validation_id) if result else None

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'execution',
            'execution_id': execution_id,
            'code_ref': code_ref,
            'result_ref': result_ref
        }

        self._write_log(log_entry, validation_id)