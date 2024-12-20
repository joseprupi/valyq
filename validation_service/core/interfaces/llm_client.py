from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMClient(ABC):
    """Abstract interface for LLM interactions"""
    
    @abstractmethod
    async def ask_question(
        self, 
        prompt: str,
        enforce_json: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Ask a question to the LLM"""
        pass

    @abstractmethod
    async def ask_followup(
        self,
        prompt: str,
        enforce_json: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Ask a follow-up question"""
        pass