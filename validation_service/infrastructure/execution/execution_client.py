from typing import Dict, Any, List, Optional, BinaryIO
import requests
import aiohttp
import asyncio
from pathlib import Path

from domain.exceptions.validation_exceptions import ExecutionError
from domain.models.execution import ExecutionResult, ExecutionStatus
from config import get_settings

class ExecutionClient:
    """Client for interacting with the execution service"""

    def __init__(self):
        self.settings = get_settings()
        # Use direct attributes instead of nested structure
        self.base_url = self.settings.execution_service_url
        self.session = None

    async def __aenter__(self):
        """Set up async context"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context"""
        if self.session:
            await self.session.close()

    async def create_execution(self, files: List[Path]) -> ExecutionResult:
        """Create new execution environment and upload files"""
        try:
            data = aiohttp.FormData()
            for file_path in files:
                if file_path.exists():
                    data.add_field(
                        'files',
                        open(file_path, 'rb'),
                        filename=file_path.name
                    )

            async with self.session.post(
                f"{self.base_url}/create-execution",
                data=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExecutionError(f"Failed to create execution: {error_text}")
                
                result = await response.json()
                return ExecutionResult(
                    execution_id=result['execution_id'],
                    status=ExecutionStatus.PENDING,
                    directory=result['directory']
                )

        except Exception as e:
            raise ExecutionError(f"Error creating execution: {str(e)}")

    async def execute_code(
        self,
        code: str,
        execution_id: Optional[str] = None
    ) -> ExecutionResult:
        """Execute code in the execution environment"""
        try:
            async with self.session.post(
                f"{self.base_url}/execute",
                json={"code": code, "execution_id": execution_id}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExecutionError(f"Code execution failed: {error_text}")
                
                result = await response.json()
                return ExecutionResult(
                    execution_id=execution_id or result.get('execution_id'),
                    status=ExecutionStatus.COMPLETED if not result.get('error') else ExecutionStatus.FAILED,
                    output=result.get('output'),
                    error=result.get('error'),
                    created_files=result.get('created_files')
                )

        except Exception as e:
            raise ExecutionError(f"Error executing code: {str(e)}")

    async def list_files(self, execution_id: str) -> Dict[str, Any]:
        """List files in execution directory"""
        try:
            async with self.session.get(
                f"{self.base_url}/list-execution-files/{execution_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExecutionError(f"Failed to list files: {error_text}")
                
                return await response.json()

        except Exception as e:
            raise ExecutionError(f"Error listing files: {str(e)}")

    async def get_file(self, execution_id: str, file_path: str) -> bytes:
        """Get file content from execution directory"""
        try:
            async with self.session.get(
                f"{self.base_url}/app/uploads/{execution_id}/{file_path}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExecutionError(f"Failed to get file: {error_text}")
                
                return await response.read()

        except Exception as e:
            raise ExecutionError(f"Error getting file: {str(e)}")

    async def compile_latex(
        self,
        execution_id: str,
        filename: str
    ) -> bytes:
        """Compile LaTeX file and return PDF content"""
        try:
            async with self.session.post(
                f"{self.base_url}/compile-existing-latex",
                json={
                    "execution_id": execution_id,
                    "filename": filename
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ExecutionError(f"LaTeX compilation failed: {error_text}")
                
                return await response.read()

        except Exception as e:
            raise ExecutionError(f"Error compiling LaTeX: {str(e)}")

