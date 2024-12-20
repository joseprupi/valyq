import requests
import json
import re
import time
import random
import logging
from typing import Optional, List, Union, Dict, Any
from dataclasses import dataclass
from requests.exceptions import RequestException


@dataclass
class CodeBlock:
    """Represents a code block extracted from text."""
    language: Optional[str]
    content: str
    start_line: int
    end_line: int


class CodeBlockParser:
    """Parser for extracting code blocks from markdown text."""

    def __init__(self):
        # Matches: ```language (optional) \n content \n```
        self.code_block_pattern = re.compile(
            r'^```\s*([a-zA-Z0-9+#_-]*)\s*\n(.*?)\n\s*```',
            re.MULTILINE | re.DOTALL
        )

    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """
        Extract all code blocks from text, handling nested cases.
        Returns list of CodeBlock objects with language and content.
        """
        blocks = []
        position = 0
        while True:
            match = self.code_block_pattern.search(text, position)
            if not match:
                break

            start_line = text[:match.start()].count('\n') + 1
            end_line = text[:match.end()].count('\n') + 1

            language = match.group(1).strip() or None
            content = match.group(2)

            blocks.append(CodeBlock(
                language=language,
                content=content,
                start_line=start_line,
                end_line=end_line
            ))

            position = match.end()

        return blocks


class ClaudeClient:
    """Client for interacting with Claude API with compatible ChatGPT interface"""

    RETRIABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504, 529}
    OVERLOADED_ERROR_MESSAGES = [
        "claude is currently overloaded",
        "service temporarily unavailable",
        "too many requests"
    ]

    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-beta": "messages-2023-12-15"
        }

        self.code_parser = CodeBlockParser()

        # Retry configuration
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        # Match ChatGPT client's conversation history structure
        self.conversation_history: List[Dict[str, str]] = []

        self.logger = logging.getLogger(__name__)

    def extract_code(self, text: str, python_only: bool = True) -> List[str]:
        """
        Extract code blocks from text using the CodeBlockParser.

        Args:
            text: The text to extract code blocks from
            python_only: If True, only return Python code blocks

        Returns:
            List of code block contents
        """
        blocks = self.code_parser.extract_code_blocks(text)

        if python_only:
            return [
                block.content for block in blocks
                if block.language is None or block.language.lower() == 'python'
            ]

        return [block.content for block in blocks]

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if the request should be retried based on the exception"""
        if isinstance(exception, RequestException):
            if not hasattr(exception, 'response'):
                return True

            status_code = exception.response.status_code
            if status_code in self.RETRIABLE_STATUS_CODES:
                return True

            try:
                response_json = exception.response.json()
                error_message = str(response_json.get(
                    'error', {}).get('message', '')).lower()
                return any(msg in error_message for msg in self.OVERLOADED_ERROR_MESSAGES)
            except (json.JSONDecodeError, AttributeError):
                error_message = str(exception.response.text).lower()
                return any(msg in error_message for msg in self.OVERLOADED_ERROR_MESSAGES)

        return False

    def _get_retry_delay(self, attempt: int) -> float:
        """Calculate the delay before the next retry attempt"""
        delay = min(
            self.max_delay,
            self.initial_delay * (self.exponential_base ** attempt)
        )

        if self.jitter:
            delay *= (1 + random.random() * 0.25)

        return delay

    def _make_request(self, messages: List[Dict[str, str]], enforce_json: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Claude API with retry logic"""
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "temperature": 0.2 if enforce_json else 0.7,
            "max_tokens": 4096
        }

        attempt = 0
        last_exception = None

        while attempt <= self.max_retries:
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries or not self._should_retry(e):
                    raise

                delay = self._get_retry_delay(attempt)
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}). "
                    f"Retrying in {delay:.2f} seconds. Error: {str(e)}"
                )

                time.sleep(delay)
                attempt += 1

        raise last_exception

    def ask_question(
        self,
        prompt: str,
        enforce_json: bool = False,
        continue_conversation: bool = False
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Send a question to Claude API and get the response.

        Args:
            prompt: Question to ask Claude
            enforce_json: If True, enforces JSON response from the model
            continue_conversation: If True, includes conversation history

        Returns:
            If enforce_json is True, returns parsed JSON as dict
            If enforce_json is False, returns raw string response
            Returns None if request fails
        """
        messages = []

        # Add system message for JSON response if requested
        if enforce_json:
            messages.append({
                "role": "system",
                "content": "Respond only in JSON format with no additional explanation or text."
            })

        # Add conversation history if continuing conversation
        if continue_conversation:
            messages.extend(self.conversation_history)

        # Add user prompt
        user_message = {"role": "user", "content": prompt}
        messages.append(user_message)

        try:
            response = self._make_request(messages, enforce_json)
            answer = response['content'][0]['text'].strip()

            # Store the exchange in conversation history if continuing conversation
            if continue_conversation:
                self.conversation_history.append(user_message)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })

            # If JSON is enforced, try to parse the response
            if enforce_json:
                try:
                    return json.loads(answer)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing JSON response: {e}")
                    return None

            return answer

        except Exception as e:
            self.logger.error(f"Error making request: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"Response text: {e.response.text}")
            return None

    def clear_conversation(self) -> None:
        """Clear the conversation history"""
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history"""
        return self.conversation_history

    def ask_followup(
        self,
        prompt: str,
        enforce_json: bool = False
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Send a follow-up question that includes conversation history.
        """
        if not self.conversation_history:
            return self.ask_question(prompt, enforce_json=enforce_json)

        messages = []
        if enforce_json:
            messages.append({
                "role": "system",
                "content": "Respond only in JSON format with no additional explanation or text."
            })

        # Add all previous conversation history
        messages.extend(self.conversation_history)

        # Add the follow-up question
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._make_request(messages, enforce_json)
            answer = response['content'][0]['text'].strip()

            # Store the exchange
            self.conversation_history.append(
                {"role": "user", "content": prompt})
            self.conversation_history.append(
                {"role": "assistant", "content": answer})

            if enforce_json:
                try:
                    return json.loads(answer)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing JSON response: {e}")
                    return None

            return answer

        except Exception as e:
            self.logger.error(f"Error in follow-up request: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"Response text: {e.response.text}")
            return None
