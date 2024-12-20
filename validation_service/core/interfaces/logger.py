from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Logger(ABC):
    """Abstract interface for logging operations"""

    @abstractmethod
    def log_validation_event(
        self,
        event_type: str,
        validation_id: str,
        details: Dict[str, Any],
        error: Optional[Exception] = None
    ) -> None:
        """Log validation-related events"""
        pass

    @abstractmethod
    def log_llm_interaction(
        self,
        interaction_type: str,
        prompt: str,
        response: Optional[str] = None,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log LLM interactions"""
        pass

    @abstractmethod
    def log_execution(
        self,
        execution_id: str,
        operation: str,
        details: Dict[str, Any],
        error: Optional[Exception] = None
    ) -> None:
        """Log execution-related events"""
        pass