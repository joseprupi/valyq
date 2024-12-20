from typing import Dict, Any, Optional, BinaryIO, List
from datetime import datetime
import uuid
import os
import aiofiles
from pathlib import Path
from werkzeug.utils import secure_filename
import json

from domain.models.validation import ValidationModel, ValidationStatus
from domain.exceptions.validation_exceptions import ValidationError
from ..interfaces.llm_client import LLMClient
from ..interfaces.file_storage import FileStorage
from ..templates.template_manager import TemplateManager
from core.services.logger_service import LoggerService
from core.services.execution_service import ExecutionService
from core.services.logger_decorators import log_validation_operation, log_operation

class ValidationService:
    """Core service for handling model validations"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        file_storage: FileStorage,
        execution_service: ExecutionService,
        template_manager: TemplateManager,
        base_upload_folder: str,
        logger: LoggerService
    ):
        self.llm_client = llm_client
        self.file_storage = file_storage
        self.execution_service = execution_service
        self.template_manager = template_manager
        self.base_upload_folder = base_upload_folder
        self.logger = logger
    
    @log_validation_operation("create_validation")
    async def create_validation(
        self,
        files: Dict[str, BinaryIO]
    ) -> ValidationModel:
        """Create a new validation"""
        try:
            # Create validation ID and folder
            validation_id = str(uuid.uuid4())
            validation_folder = os.path.join(self.base_upload_folder, validation_id)
            os.makedirs(validation_folder, exist_ok=True)

            # Save files within validation folder
            saved_files = {}
            for file_type, file in files.items():
                if not file:
                    continue
                filename = secure_filename(file.filename)
                file_path = os.path.join(validation_folder, filename)
                path = await self.file_storage.save_file(file, file_path)
                saved_files[file_type] = path

            # Create validation model
            validation = ValidationModel(
                validation_id=uuid.UUID(validation_id),
                status=ValidationStatus.PENDING,
                model_files=saved_files,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Execute files in execution service
            execution_files = [
                saved_files['trainedModel'],
                saved_files['trainingDataset'],
                saved_files['testDataset']
            ]
            execution_result = await self.execution_service.create_execution(execution_files)
            validation.execution_id = execution_result.execution_id

            # self.template_manager.set_metadata(
                
            # )
            # Save metadata
            await self._save_metadata(validation.to_dict())

            return validation

        except Exception as e:
            raise ValidationError(f"Error creating validation: {str(e)}")
        
    async def get_validation_status(self, validation_id: str) -> Dict[str, Any]:
        """Get the current status of a validation"""
        try:
            validation_folder = os.path.join(self.base_upload_folder, validation_id)
            if not os.path.exists(validation_folder):
                raise ValidationError(f"Validation not found: {validation_id}")

            metadata_path = os.path.join(validation_folder, 'metadata.json')
            if os.path.exists(metadata_path):
                metadata = await self.file_storage.read_json(metadata_path)
                return {
                    'status': metadata.get('status', 'unknown'),
                    'execution_id': metadata.get('execution_id'),
                    'created_at': metadata.get('created_at'),
                    'updated_at': metadata.get('updated_at')
                }
            
            raise ValidationError("Validation metadata not found")

        except Exception as e:
            raise ValidationError(f"Error getting validation status: {str(e)}")

    async def add_test_metadata(self, validation_id: str, test_id: str, test_data: Dict[str, Any]):
        metadata = await self._load_metadata(validation_id)
        
        # Initialize tests dict if it doesn't exist
        if 'tests' not in metadata:
            metadata['tests'] = {}
            
        # Store test using string key
        metadata['tests'][str(test_id)] = test_data
        metadata['updated_at'] = datetime.utcnow().isoformat()
        await self._save_metadata(metadata)

    async def get_results_file(self, validation_id: str) -> str:
        """Get the path to the validation results file"""
        try:
            validation_folder = os.path.join(self.base_upload_folder, validation_id)
            results_file = os.path.join(validation_folder, f'validation_results_{validation_id}.zip')
            
            if not os.path.exists(results_file):
                raise ValidationError("Results file not found")
            
            return results_file

        except Exception as e:
            raise ValidationError(f"Error getting results file: {str(e)}")

    async def generate_test_list(self) -> str:
        """Generate list of tests based on model documentation and code"""
        try:
            prompt = self.template_manager.generate_test_list_json_prompt()
            response = await self.llm_client.ask_question(prompt, enforce_json=True)
            
            if not response:
                raise ValidationError("Failed to generate test list")
            
            return response

        except Exception as e:
            raise ValidationError(f"Error generating test list: {str(e)}")

    async def generate_external_validation(
        self,
        tests: str,
        execution_result: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate external validation using submitted files and tests"""
        try:
            all_responses = []
            
            for i, test in enumerate(tests):
                # Generate and execute test
                prompt_text = self.template_manager.generate_independent_test_prompt(
                    test['test'],
                    test['description'],
                    i
                )
                
                code = await self.execution_service.ask_and_execute(
                    prompt_text,
                    execution_result,
                    i
                )
                
                # Store response
                response = f"Test {i} - {test['description']}\n{code}"
                all_responses.append(response)
                
                # Notify progress if callback provided
                if progress_callback:
                    progress_callback(i, response)
                    
                # Check for results file
                try:
                    execution_files = await self.execution_service.list_files(execution_result['execution_id'])
                    test_folder = self._find_folder_in_structure(
                        execution_files['structure'],
                        f"test_{i}"
                    )
                    if test_folder:
                        for child in test_folder.get('children', []):
                            if child['type'] == 'file' and child.get('extension') == 'md':
                                if progress_callback:
                                    progress_callback(i, f"Test {i} results available")
                except Exception as e:
                    # Log error but continue with other tests
                    print(f"Error checking test results: {str(e)}")

            return "\n\n".join(all_responses)

        except Exception as e:
            raise ValidationError(f"Error generating external validation: {str(e)}")

    async def load_validation(self, validation_id: str) -> ValidationModel:
        """Load an existing validation"""
        try:
            metadata = await self._load_metadata(validation_id)
            
            # Create ValidationModel from metadata
            validation = ValidationModel(
                validation_id=uuid.UUID(metadata['validation_id']),
                status=ValidationStatus(metadata['status']),
                model_files=metadata['model_files'],
                created_at=datetime.fromisoformat(metadata['created_at']),
                updated_at=datetime.fromisoformat(metadata['updated_at']),
                execution_id=metadata.get('execution_id')
            )

            return validation

        except FileNotFoundError:
            raise ValidationError(f"Validation {validation_id} not found")
        except Exception as e:
            raise ValidationError(f"Error loading validation: {str(e)}")

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
    
    async def _get_validation_metadata(self, validation_id: str) -> Dict[str, Any]:
        """Get metadata for a validation ID"""
        try:
            validation_folder = os.path.join(self.base_upload_folder, validation_id)
            if not os.path.exists(validation_folder):
                raise ValueError(f"Validation folder not found: {validation_id}")

            metadata_path = os.path.join(validation_folder, 'metadata.json')
            if os.path.exists(metadata_path):
                async with aiofiles.open(metadata_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            
            return {
                'directory': validation_folder,
                'execution_id': validation_id
            }

        except Exception as e:
            raise ValueError(f"Failed to get validation metadata: {str(e)}")
        
    async def _save_metadata(self, metadata: Dict) -> None:
        """Save validation metadata to file"""
        metadata_path = os.path.join(self.base_upload_folder, str(metadata['validation_id']), 'metadata.json')
        await self.file_storage.write_json(metadata_path, metadata)
        # metadata = {
        #     'validation_id': str(validation.validation_id),
        #     'status': validation.status.value,
        #     'execution_id': validation.execution_id,
        #     'created_at': validation.created_at.isoformat(),
        #     'updated_at': validation.updated_at.isoformat(),
        #     'files': validation.model_files,
        #     'tests': validation.tests if validation.tests is not None else {}
        # }

        # metadata_path = os.path.join(self.base_upload_folder, str(validation.validation_id), 'metadata.json')
        # await self.file_storage.write_json(metadata_path, metadata)

    async def _load_metadata(self, validation_id: str) -> Dict:
        """Load validation metadata from file"""
        metadata_path = os.path.join(self.base_upload_folder, validation_id, 'metadata.json')
        return await self.file_storage.read_json(metadata_path)
        """Delete a test from validation"""
        try:
            metadata = await self._load_metadata(validation_id)
            
            # Remove test from metadata
            if 'tests' in metadata and test_id in metadata['tests']:
                del metadata['tests'][test_id]
                metadata['updated_at'] = datetime.utcnow().isoformat()
                await self._save_metadata(metadata)
                
                # Delete test folder if it exists
                test_folder = Path(self.base_upload_folder) / validation_id / 'tests' / f'test_{test_id}'
                if test_folder.exists():
                    shutil.rmtree(test_folder)
            else:
                raise ValidationError(f"Test {test_id} not found in validation {validation_id}")

        except Exception as e:
            raise ValidationError(f"Error deleting test: {str(e)}")