from typing import Dict, Any, Optional, List, BinaryIO, Tuple
from datetime import datetime
import uuid
import os
import requests
from pathlib import Path

from domain.models.execution import ExecutionResult
from domain.exceptions.validation_exceptions import ExecutionError
from ..interfaces.file_storage import FileStorage
from ..interfaces.llm_client import LLMClient
from infrastructure.execution import ExecutionClient
from core.services.interaction_logger import InteractionLogger

class ExecutionService:
    """Service for managing code execution and file operations"""

    def __init__(
        self,
        file_storage: FileStorage,
        llm_client: LLMClient,
        execution_client: ExecutionClient,
        service_url: str,
        base_path: str,
        interaction_logger: InteractionLogger,
        max_retries: int = 3
    ):
        self.file_storage = file_storage
        self.llm_client = llm_client
        self.execution_client = execution_client
        self.service_url = service_url
        self.base_path = base_path
        self.interaction_logger = interaction_logger
        self.max_retries = max_retries

    async def create_execution(self, files: List[str]) -> ExecutionResult:
        """Create new execution environment and upload files"""
        try:
            file_paths = [Path(f) for f in files]
            async with self.execution_client as client:
                return await client.create_execution(file_paths)
        except Exception as e:
            raise ExecutionError(f"Failed to create execution: {str(e)}")
    
    async def execute_code(
        self,
        code: str,
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute provided code in the execution environment"""
        try:
            response = await self._make_request(
                'POST',
                f"{self.service_url}/execute",
                False,
                json={"code": code}
            )
            return response

        except Exception as e:
            raise ExecutionError(f"Code execution failed: {str(e)}")

    async def ask_and_execute(
        self,
        question: str,  # This is the full prompt with conversation history
        execution_result: Dict[str, Any],
        test_number: int,
        validation_id: str
    ) -> Optional[str]:
        
        if not execution_result or execution_result['execution_id'] is None:
            raise ExecutionError("Invalid execution result")
        
        interaction_id = str(uuid.uuid4())
        
        try:
            self.interaction_logger.log_llm_interaction(
                interaction_id=interaction_id,
                prompt=question,
                metadata={
                    'test_number': test_number,
                    'execution_id': execution_result.get('execution_id'),
                    'type': 'initial_prompt'
                }
            )

            response = await self.llm_client.ask_question(question)
            
            self.interaction_logger.log_llm_interaction(
                interaction_id=interaction_id,
                prompt=question,
                response=response,
                metadata={'type': 'llm_response'}
            )
            
            code_blocks = await self.llm_client.extract_code(response)

            if not code_blocks:
                raise ExecutionError("No code blocks generated")
            
            self.interaction_logger.log_llm_interaction(
                interaction_id=interaction_id,
                prompt=question,
                response=response,
                extracted_code=code_blocks[0],
                metadata={'type': 'code_extraction'}
            )

            execution_id = execution_result['execution_id']
            test_folder_name = f"test_{test_number}"

            for code in code_blocks:
                code_file_path = Path(self.base_path) / validation_id / 'tests' / test_folder_name / 'test_code.py'
                code_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                await self.file_storage.write_text(
                    str(code_file_path),
                    code
                )

                final_code = await self._try_execute_and_verify(
                    code,
                    execution_id,
                    test_folder_name,
                    question,
                    interaction_id,
                )
                if final_code:
                    return final_code

            return None

        except Exception as e:
            self.interaction_logger.log_execution(
                interaction_id=interaction_id,
                code="",
                error=str(e),
                metadata={'type': 'error'}
            )
            raise ExecutionError(f"Ask and execute failed: {str(e)}")

    async def list_files(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """List files in execution directory"""
        try:
            response = await self._make_request(
                'GET',
                f"{self.service_url}/list-execution-files/{execution_id}",
                False
            )
            return response

        except Exception as e:
            raise ExecutionError(f"Failed to list files: {str(e)}")

    async def get_file(
        self,
        execution_id: str,
        file_path: str
    ) -> bytes:
        """Get file content from execution directory"""
        try:
            response = await self._make_request(
                'GET',
                f"{self.service_url}/app/uploads/{execution_id}/{str(file_path)}",
                True
            )
            return response.content

        except Exception as e:
            raise ExecutionError(f"Failed to get file: {str(e)}")

    async def compile_latex(
        self,
        execution_id: str,
        filename: str
    ) -> bytes:
        """Compile LaTeX file and return PDF content"""
        try:
            response = await self._make_request(
                'POST',
                f"{self.service_url}/compile-existing-latex",
                True,
                json={
                    "execution_id": execution_id,
                    "filename": filename
                }
            )
            return response.content

        except Exception as e:
            raise ExecutionError(f"LaTeX compilation failed: {str(e)}")

    async def get_execution_metadata(
        self,
        validation_id: str
    ) -> Dict[str, Any]:
        """Get metadata for a validation ID"""
        try:
            # First get the validation metadata to find the execution_id
            validation_folder = os.path.join(self.base_path, validation_id)
            if not os.path.exists(validation_folder):
                raise ExecutionError(f"Validation folder not found: {validation_id}")

            metadata_path = os.path.join(validation_folder, 'metadata.json')
            if not os.path.exists(metadata_path):
                raise ExecutionError(f"Metadata not found for validation: {validation_id}")

            validation_metadata = await self.file_storage.read_json(metadata_path)
            execution_id = validation_metadata.get('execution_id')
            
            if not execution_id:
                raise ExecutionError(f"No execution_id found for validation: {validation_id}")

            # Get the execution directory from the execution server
            async with self.execution_client as client:
                files_response = await client.list_files(execution_id)
            
            return {
                'execution_id': execution_id,
                'directory': files_response.get('directory', ''),
                'validation_id': validation_id
            }

        except Exception as e:
            raise ExecutionError(f"Failed to get execution metadata: {str(e)}")

    async def _try_execute_and_verify(
        self,
        code: str,
        execution_id: str,
        test_folder_name: str,
        prompt: str,  # Add prompt parameter to preserve context
        interaction_id: str,
        current_attempt: int = 0
    ) -> Optional[str]:
        """Execute code and verify results, preserving conversation context on retries"""
        try:
            result = await self.execute_code(code)

            self.interaction_logger.log_execution(
                interaction_id=interaction_id,
                code=code,
                output=result.get('output'),
                error=result.get('error'),
                metadata={
                    'attempt': current_attempt,
                    'execution_id': execution_id
                }
            )
            
            if result.get('error') or result.get('output'):
                if current_attempt < self.max_retries:
                    fixed_code = await self._handle_execution_error(
                        code=code,
                        error_message=result['error'] + result['output'],
                        prompt=prompt  # Pass original prompt for context
                    )
                    if fixed_code:
                        return await self._try_execute_and_verify(
                            fixed_code,
                            execution_id,
                            test_folder_name,
                            prompt,
                            interaction_id,
                            current_attempt + 1
                        )
                return None

            # Verify test folder and report
            files = await self.list_files(execution_id)
            if not self._verify_test_structure(files, test_folder_name):
                if current_attempt < self.max_retries:
                    fixed_code = await self._handle_missing_folder(
                        code=code,
                        folder_name=test_folder_name,
                        prompt=prompt  # Pass original prompt for context
                    )
                    if fixed_code:
                        return await self._try_execute_and_verify(
                            fixed_code,
                            execution_id,
                            test_folder_name,
                            prompt,
                            interaction_id,
                            current_attempt + 1,
                            
                        )
                return None

            return code

        except Exception as e:
            self.interaction_logger.log_execution(
                interaction_id=interaction_id,
                code=code,
                error=str(e),
                metadata={'type': 'verification_error'}
            )
            raise ExecutionError(f"Execution verification failed: {str(e)}")

    async def _handle_execution_error(
        self,
        code: str,
        error_message: str,
        prompt: str  # Add prompt parameter
    ) -> Optional[str]:
        """Handle code execution errors using LLM"""
        # Include original prompt and conversation context
        followup_prompt = f"""The code generated had the following error:
        {error_message}
        
        Original conversation and context:
        {prompt}
        
        Please provide a corrected version of this code:
        {code}"""

        response = await self.llm_client.ask_followup(followup_prompt)
        code_blocks = await self.llm_client.extract_code(response)
        return code_blocks[0] if code_blocks else None

    async def _handle_missing_folder(
        self,
        code: str,
        folder_name: str,
        prompt: str  # Add prompt parameter
    ) -> Optional[str]:
        """Handle missing test folder case"""
        # Include original prompt and conversation context
        followup_prompt = f"""The code executed successfully but did not create the required test folder.
        
        Original conversation and context:
        {prompt}
        
        The code should create a '{folder_name}' folder and write results to '{folder_name}/report.md'.
        
        Current code:
        {code}
        
        Please modify the code to ensure it creates the folder and report file."""

        response = await self.llm_client.ask_followup(followup_prompt)
        code_blocks = await self.llm_client.extract_code(response)
        return code_blocks[0] if code_blocks else None

    def _verify_test_structure(
        self,
        files: Dict[str, Any],
        test_folder_name: str
    ) -> bool:
        """Verify test folder structure and report existence"""
        folder = self._find_folder_in_structure(files['structure'], test_folder_name)
        if not folder:
            return False

        return any(
            child['type'] == 'file' and child['name'] == 'report.md'
            for child in folder.get('children', [])
        )

    def _find_folder_in_structure(
        self,
        structure: Dict[str, Any],
        folder_name: str
    ) -> Optional[Dict[str, Any]]:
        """Helper method to find a folder in the directory structure"""
        if structure['type'] == 'directory' and structure['name'] == folder_name:
            return structure

        if structure['type'] == 'directory' and 'children' in structure:
            for child in structure['children']:
                result = self._find_folder_in_structure(child, folder_name)
                if result:
                    return result

        return None

    async def _make_request(
        self,
        method: str,
        url: str,
        raw_response,
        **kwargs
    ) -> Any:
        """Make HTTP request with retries"""
        attempts = 0
        last_error = None

        while attempts < self.max_retries:
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()

                if raw_response:
                    return response

                return response.json()

            except Exception as e:
                last_error = e
                attempts += 1
                if attempts == self.max_retries:
                    break

        raise ExecutionError(f"Request failed after {self.max_retries} attempts: {str(last_error)}")