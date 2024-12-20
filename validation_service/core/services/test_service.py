from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil
import os
from pathlib import Path

from domain.models.test import TestCase, TestResult, TestStatus
from domain.exceptions.validation_exceptions import TestExecutionError
from ..interfaces.llm_client import LLMClient
from ..interfaces.file_storage import FileStorage
from ..templates.template_manager import TemplateManager
from core.services.validation_service import ValidationService
from core.services.execution_service import ExecutionService

class TestService:
    """Core service for handling test execution and management"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        file_storage: FileStorage,
        execution_service: ExecutionService,
        validation_service: ValidationService,
        template_manager: TemplateManager,
        image_cache_dir: str

    ):
        self.llm_client = llm_client
        self.file_storage = file_storage
        self.execution_service = execution_service
        self.validation_service = validation_service
        self.template_manager = template_manager
        self.image_cache_dir = image_cache_dir
        self.test_conversations = {}

    async def execute_test(
        self,
        validation_id: str,
        description: str = None,
        test_id: Optional[str] = None,
        follow_up_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a test case with conversation support"""
        try:
            # Validate input parameters
            if not test_id and not description:
                
                raise ValidationError("Either test_id or description must be provided")
                
            if test_id and not follow_up_message and not description:
                raise ValidationError("Follow-up message required for existing test")

            # Initialize test ID and conversation if new test
            if not test_id:
                test_id = str(int(datetime.utcnow().timestamp()))
                self.test_conversations[test_id] = {
                    'messages': [],
                    'test_results': []
                }

            # Ensure conversation exists for existing test
            if test_id and test_id not in self.test_conversations:
                self.test_conversations[test_id] = {
                    'messages': [],
                    'test_results': []
                }

            # Add user message to conversation
            if follow_up_message:
                self.test_conversations[test_id]['messages'].append({
                    'role': 'user',
                    'content': follow_up_message
                })
            elif description:
                self.test_conversations[test_id]['messages'].append({
                    'role': 'user',
                    'content': description
                })

            # Load validation and prepare execution environment
            validation = await self.validation_service.load_validation(validation_id)
            execution_result = await self.execution_service.get_execution_metadata(validation_id)

            self.template_manager.update_from_validation(
                validation=validation,
                execution_folder=execution_result['directory']
            )

            test_dir = Path(self.validation_service.base_upload_folder) / validation_id / 'tests' / f'test_{test_id}'
            test_dir.mkdir(parents=True, exist_ok=True)

            # Build conversation context
            conversation_prompt = self._build_conversation_prompt(test_id)

            # Generate test prompt including conversation history for context
            prompt = self.template_manager.generate_independent_test_prompt(
                test_title="Improve existing test based on feedback" if follow_up_message else description,
                test_description=conversation_prompt,  # Include full conversation history
                i=test_id
            )

            await self.file_storage.write_text(str(test_dir / 'prompt.txt'), prompt)

            try:
                # Generate and execute code
                generated_code = await self.execution_service.ask_and_execute(
                    prompt,
                    execution_result={'execution_id': validation.execution_id, 'directory': execution_result['directory']},
                    test_number=test_id,
                    validation_id=validation_id
                )

                if not generated_code:
                    raise ExecutionError("No code was generated or execution failed")

                # Process results
                results = await self.process_test_results(
                    execution_id=execution_result['execution_id'],
                    test_number=test_id,
                    execution_dir=test_dir,
                    validation_id=validation_id,
                    execution_directory=str(execution_result['directory'])
                )

                # Store assistant's response in conversation (clean version for UI)
                self.test_conversations[test_id]['messages'].append({
                    'role': 'assistant',
                    'content': "Test execution completed. Results have been generated and can be viewed in the results tab."
                })
                
                # Store full test results in history (for context in future prompts)
                self.test_conversations[test_id]['test_results'].append({
                    'code': generated_code,
                    'results': results,
                    'timestamp': datetime.utcnow().timestamp()
                })

                # Save test metadata
                await self.validation_service.add_test_metadata(
                    validation_id=validation_id,
                    test_id=test_id,
                    test_data={
                        'description': description or follow_up_message,
                        'prompt': prompt,
                        'code': generated_code,
                        'results': results,
                        'conversation': self.test_conversations[test_id]
                    }
                )

                return {
                    'status': 'success',
                    'test_id': test_id,
                    'results': results,
                    'testCode': generated_code,
                    'conversation': self.test_conversations[test_id]
                }

            except Exception as e:
                # Add error message to conversation
                self.test_conversations[test_id]['messages'].append({
                    'role': 'assistant',
                    'content': f"Error executing test: {str(e)}"
                })
                raise

        except Exception as e:
            print(f"Execute test error: {str(e)}")
            raise TestExecutionError(f"Failed to execute test: {str(e)}")

    async def process_test_results(
        self,
        execution_id: str,
        test_number: str,
        execution_dir: str,
        validation_id: str,
        execution_directory: str
    ) -> List[Dict[str, str]]:
        """Process test results including downloading and caching images"""
        try:
            test_folder_name = f"test_{test_number}"
            results = []

            # Create test directory in application server
            test_dir = Path(self.validation_service.base_upload_folder) / validation_id / 'tests' / test_folder_name
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Get files list from execution service
            execution_files = await self.execution_service.list_files(execution_id)
            if not execution_files:
                return results
            
            test_folder = self.find_folder_in_structure(execution_files['structure'], test_folder_name)

            if test_folder:
                images_dir = execution_dir / 'images'
                images_dir.mkdir(exist_ok=True)
                for child in test_folder.get('children', []):
                    if child['type'] == 'file' and child.get('extension') == 'md':
                        content = await self.execution_service.get_file(
                            execution_id=execution_id,
                            file_path=f"{test_folder['name']}/{child['name']}"
                        )
                    
                        # Process content to handle images
                        processed_content = await self._process_markdown_content(
                            content.decode('utf-8'),
                            execution_id,
                            test_number,
                            validation_id,
                            execution_directory
                        )

                        # Save markdown in application server
                        markdown_path = test_dir / child['name']
                        await self.file_storage.write_text(
                            str(markdown_path),
                            processed_content
                        )
                        
                        results.append({
                            'filename': child['name'],
                            'content': processed_content
                        })
            
            return results

        except Exception as e:
            print(f"Execute test: {str(e)}")
            raise

    @staticmethod
    def find_folder_in_structure(structure: Dict[str, Any], folder_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a folder in the directory structure.
        
        Args:
            structure: Directory structure dictionary from list_execution_files
            folder_name: Name of the folder to find
            
        Returns:
            Dictionary containing the folder information, or None if not found
        """
        def search_recursive(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # Check if current node is the folder we're looking for
            if node['type'] == 'directory' and node['name'] == folder_name:
                return node
            
            # If this is a directory, search its children
            if node['type'] == 'directory' and 'children' in node:
                for child in node['children']:
                    result = search_recursive(child)
                    if result:
                        return result
            
            return None

        return search_recursive(structure)

    async def get_test_results(
        self,
        execution_id: str,
        test_number: str
    ) -> List[Dict[str, Any]]:
        """Retrieve markdown results for a specific test"""
        try:
            test_folder = os.path.join(
                self.execution_service.base_path,
                'uploads',
                execution_id,
                f'test_{test_number}'
            )

            if not os.path.exists(test_folder):
                return []

            results = []
            for filename in os.listdir(test_folder):
                if filename.endswith('.md'):
                    with open(os.path.join(test_folder, filename), 'r') as f:
                        content = f.read()
                    
                    # Process content to handle images
                    processed_content = await self._process_markdown_content(
                        content,
                        execution_id,
                        test_number,
                        validation_id
                    )
                    
                    results.append({
                        'filename': filename,
                        'content': processed_content
                    })

            return results

        except Exception as e:
            raise TestExecutionError(f"Error retrieving test results: {str(e)}")

    async def _process_markdown_content(
            self,
            content: str,
            execution_id: str,
            test_number: str,
            validation_id: str,
            execution_directory: str
        ) -> str:
        """Process markdown content to handle images asynchronously"""
        import re
        
        # Match markdown image syntax
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        # Keep track of all replacements
        replacements = []
        last_end = 0
        result = ""
        
        # Find all matches
        for match in re.finditer(image_pattern, content):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Add the text between the last match and this one
            result += content[last_end:match.start()]
            
            # Skip external URLs
            if image_path.startswith(('http://', 'https://')):
                result += match.group(0)
            else:
                try:
                    # Download and cache the image
                    cached_filename = await self.fetch_and_cache_image(
                        execution_id,
                        image_path,
                        test_number,
                        validation_id,
                        execution_directory
                    )
                    
                    if cached_filename:
                        result += f'![{alt_text}](/test-images/{cached_filename})'
                    else:
                        result += match.group(0)
                    
                except Exception as e:
                    print(f"Error processing image {image_path}: {str(e)}")
                    result += match.group(0)
            
            last_end = match.end()
        
        # Add any remaining content after the last match
        result += content[last_end:]
        
        return result

    # async def _process_markdown_content(
    #     self,
    #     content: str,
    #     execution_id: str,
    #     test_number: str
    # ) -> str:
    #     """Process markdown content to handle images"""
    #     import re
        
    #     async def replace_image_url(match):
    #         alt_text = match.group(1)
    #         image_path = match.group(2)
            
    #         # Skip external URLs
    #         if image_path.startswith(('http://', 'https://')):
    #             return match.group(0)
            
    #         try:
    #             # Download and cache the image
    #             cached_filename = await self.fetch_and_cache_image(
    #                 execution_id,
    #                 image_path,
    #                 test_number
    #             )
                
    #             if cached_filename:
    #                 return f'![{alt_text}](/test-images/{cached_filename})'
                
    #         except Exception as e:
    #             print(f"Error processing image {image_path}: {str(e)}")
                
    #         return match.group(0)
        
    #     # Match markdown image syntax
    #     image_pattern = r'!\[(.*?)\]\((.*?)\)'
    #     return re.sub(image_pattern, replace_image_url, content)

    async def fetch_and_cache_image(
        self,
        execution_id: str,
        image: str,
        test_number: str,
        validation_id: str,
        execution_directory: str
    ) -> Optional[str]:
        """Fetch image from execution server and save in validation test folder"""
        try:
            # Create test-specific image directory
            test_image_dir = Path(self.validation_service.base_upload_folder) / validation_id / 'tests' / f'test_{test_number}' / 'images'
            test_image_dir.mkdir(parents=True, exist_ok=True)
            image_path = Path(test_image_dir / image)

            # Get image from execution server
            image_data = await self.execution_service.get_file(
                execution_id,
                f"test_{test_number}/{image}"
            )

            # Save to test directory
            with open(image_path, 'wb') as f:
                f.write(image_data)

            # Return relative path for serving
            return f"{validation_id}/tests/test_{test_number}/images/{image}"

        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return None

    def _build_conversation_prompt(self, test_id: str) -> str:
        """Build a prompt that includes conversation history"""
        if test_id not in self.test_conversations:
            return ""
            
        conversation = self.test_conversations[test_id]['messages']
        prompt = "Previous conversation and test history:\n\n"
        
        # Add conversation messages
        for msg in conversation:
            prefix = "User: " if msg['role'] == 'user' else "Assistant: "
            prompt += f"{prefix}{msg['content']}\n\n"
        
        # Add latest test results if available
        test_results = self.test_conversations[test_id].get('test_results', [])
        if test_results:
            latest_results = test_results[-1]
            prompt += "Latest test code:\n"
            prompt += latest_results['code'] + "\n\n"
            prompt += "Latest test results:\n"
            for result in latest_results['results']:
                prompt += result['content'] + "\n"
        
        prompt += "\nPlease improve the test based on the above conversation and previous results."
        return prompt
    
    async def get_test_metadata(self, validation_id: str) -> Dict[str, Any]:
        """Get all tests metadata for a validation"""
        try:
            metadata = await self.validation_service._load_metadata(validation_id)
            return metadata.get('tests', {})
        except Exception as e:
            raise TestExecutionError(f"Error getting test metadata: {str(e)}")

    async def delete_test(self, validation_id: str, test_id: str) -> None:
        """Delete a test from validation"""
        try:
            # Get validation metadata
            metadata = await self.validation_service._load_metadata(validation_id)
            
            # Remove test from metadata
            if 'tests' in metadata and test_id in metadata['tests']:
                del metadata['tests'][test_id]
                metadata['updated_at'] = datetime.utcnow().isoformat()
                await self.validation_service._save_metadata(metadata)
                
                # Delete test folder if it exists
                test_folder = Path(self.validation_service.base_upload_folder) / validation_id / 'tests' / f'test_{test_id}'
                if test_folder.exists():
                    shutil.rmtree(test_folder)
            else:
                raise TestExecutionError(f"Test {test_id} not found in validation {validation_id}")

        except Exception as e:
            raise TestExecutionError(f"Error deleting test: {str(e)}")

    async def load_tests(self, validation_id: str) -> List[Dict[str, Any]]:
        """Load all tests for a validation"""
        try:
            metadata = await self.get_test_metadata(validation_id)
            tests = []
            
            for test_id, test_data in metadata.items():
                test = {
                    'test_id': test_id,
                    'description': test_data.get('description', ''),
                    'prompt': test_data.get('prompt', ''),
                    'code': test_data.get('code', ''),
                    'results': test_data.get('results', []),
                    'conversation': test_data.get('conversation', {'messages': []})
                }
                tests.append(test)
                
            return tests
            
        except Exception as e:
            raise TestExecutionError(f"Error loading tests: {str(e)}")