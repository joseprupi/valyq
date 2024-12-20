# infrastructure/llm/llm_client.py
from typing import Optional, Dict, Any, List, Union
from core.interfaces.llm_client import LLMClient as LLMClientInterface
from .claude_client import ClaudeClient
from .chatgpt_client import ChatGPTClient
from domain.exceptions.validation_exceptions import LLMError

class LLMClient(LLMClientInterface):
    """Wrapper for different LLM clients"""

    def __init__(
        self,
        provider: str,
        api_key: str,
        max_retries: int = 3
    ):
        self.provider = provider.lower()
        
        if self.provider == 'claude':
            self.client = ClaudeClient(
                api_key=api_key,
                max_retries=max_retries
            )
        elif self.provider == 'chatgpt':
            self.client = ChatGPTClient(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def ask_question(
        self,
        prompt: str,
        enforce_json: bool = False,
        continue_conversation: bool = False
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Delegate to underlying client"""
        try:
            return self.client.ask_question(
                prompt=prompt,
                enforce_json=enforce_json,
                continue_conversation=continue_conversation
            )
        except Exception as e:
            raise LLMError(f"Error in LLM request: {str(e)}")

    async def ask_followup(
        self,
        prompt: str,
        enforce_json: bool = False
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Delegate to underlying client"""
        try:
            return self.client.ask_followup(
                prompt=prompt,
                enforce_json=enforce_json
            )
        except Exception as e:
            raise LLMError(f"Error in follow-up request: {str(e)}")

    async def extract_code(self, text: str) -> List[str]:
        """Delegate to underlying client"""
        return self.client.extract_code(text)

# infrastructure/llm/__init__.py
from .llm_client import LLMClient
from .claude_client import ClaudeClient
from .chatgpt_client import ChatGPTClient

__all__ = ['LLMClient', 'ClaudeClient', 'ChatGPTClient']