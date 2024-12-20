import requests
import json
import re
from typing import Optional, List, Union, Dict, Any
from openai import OpenAI

class ChatGPTClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
        )
        self.conversation_history: List[Dict[str, str]] = []
        
    def extract_code(self, text: str) -> List[str]:
        """Extract Python code blocks from text using regex."""
        # Match both ``` and ```python code blocks
        pattern = r'```(?:[Pp]ython)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    def ask_question_fixed(        self, 
        prompt: str, 
        enforce_json: bool = False,
        continue_conversation: bool = False):
        with open("/root/llm_validation/code_block_cache.py", 'r') as file:
            return file.read() 
    
    def ask_question(
        self, 
        prompt: str, 
        enforce_json: bool = False,
        continue_conversation: bool = False
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Send a question to ChatGPT API and get the response.
        
        Args:
            prompt: Question to ask ChatGPT
            enforce_json: If True, enforces JSON response from the model
            continue_conversation: If True, includes conversation history
            
        Returns:
            If enforce_json is True, returns parsed JSON as dict
            If enforce_json is False, returns raw string response
            Returns None if request fails
        """
        messages = []
        
        # Add system message to enforce JSON response if requested
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
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.2
            )

            answer = response.choices[0].message.content.strip()
            
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
                    print(f"Error parsing JSON response: {e}")
                    return None
            
            return answer
            
        except Exception as e:
            print(f"Error making request: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text}")
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
        
        Args:
            prompt: Follow-up question to ask
            enforce_json: If True, enforces JSON response
            
        Returns:
            Response from ChatGPT with conversation context
        """
        return self.ask_question(prompt, enforce_json, continue_conversation=True)