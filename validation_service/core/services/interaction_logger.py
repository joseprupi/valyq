# core/services/interaction_logger.py
import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Optional, Dict, Any
import uuid

class InteractionLogger:
    """Logger for tracking all LLM and execution interactions"""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("interaction_logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Create handlers for different log types
        self._setup_handlers()

    def _setup_handlers(self):
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler for full logs
        fh = logging.FileHandler(self.log_dir / "interactions.log")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console handler for important info
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)

    def _save_content(self, content: str, filename: str) -> str:
        """Save content to a file and return the path"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        filepath = self.log_dir / f"{timestamp}_{unique_id}_{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return str(filepath)

    def log_llm_interaction(
        self,
        interaction_id: str,
        prompt: str,
        response: Optional[str] = None,
        extracted_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a complete LLM interaction"""
        timestamp = datetime.utcnow().isoformat()
        
        # Save prompt and response to separate files
        prompt_path = self._save_content(prompt, 'prompt.txt')
        response_path = self._save_content(response, 'response.txt') if response else None
        code_path = self._save_content(extracted_code, 'code.py') if extracted_code else None
        
        # Create detailed log entry
        log_entry = {
            'timestamp': timestamp,
            'interaction_id': interaction_id,
            'type': 'llm_interaction',
            'prompt_file': prompt_path,
            'response_file': response_path,
            'extracted_code_file': code_path,
            'metadata': metadata or {}
        }
        
        # Log summary to main log file
        self.logger.info(f"LLM Interaction {interaction_id}:")
        self.logger.info(f"- Prompt saved to: {prompt_path}")
        if response_path:
            self.logger.info(f"- Response saved to: {response_path}")
        if code_path:
            self.logger.info(f"- Extracted code saved to: {code_path}")
            
        # Save detailed log entry
        self._save_content(
            json.dumps(log_entry, indent=2),
            f'interaction_{interaction_id}.json'
        )

    def log_execution(
        self,
        interaction_id: str,
        code: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log code execution results"""
        timestamp = datetime.utcnow().isoformat()
        
        # Save execution artifacts
        code_path = self._save_content(code, 'executed_code.py')
        output_path = self._save_content(output, 'execution_output.txt') if output else None
        error_path = self._save_content(error, 'execution_error.txt') if error else None
        
        # Create detailed log entry
        log_entry = {
            'timestamp': timestamp,
            'interaction_id': interaction_id,
            'type': 'execution',
            'code_file': code_path,
            'output_file': output_path,
            'error_file': error_path,
            'metadata': metadata or {}
        }
        
        # Log summary
        self.logger.info(f"Code Execution for interaction {interaction_id}:")
        self.logger.info(f"- Code saved to: {code_path}")
        if output_path:
            self.logger.info(f"- Output saved to: {output_path}")
        if error_path:
            self.logger.warning(f"- Error saved to: {error_path}")
            
        # Save detailed log entry
        self._save_content(
            json.dumps(log_entry, indent=2),
            f'execution_{interaction_id}.json'
        )