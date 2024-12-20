# infrastructure/storage/file_storage.py
from typing import BinaryIO, List, Dict, Any
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import aiofiles
import aiofiles.os
import uuid

from core.interfaces.file_storage import FileStorage
from domain.exceptions.validation_exceptions import ValidationError

class LocalFileStorage(FileStorage):
    """Implementation of FileStorage for local filesystem"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: BinaryIO, path: str) -> str:
        """Save a file to local storage"""
        try:
            
            # Create unique filename to avoid collisions
            #filename = f"{uuid.uuid4()}_{Path(path).name}"
            filename = f"{Path(path).name}"
            full_path = Path(path).parent / filename

            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read the content first
            if hasattr(file, 'read'):
                content = file.read()
            else:
                content = file

            # Save file asynchronously
            async with aiofiles.open(str(full_path), 'wb') as f:
                await f.write(content)

            return str(full_path)

        except Exception as e:
            raise ValidationError(f"Failed to save file: {str(e)}")

    async def get_file(self, path: str) -> bytes:
        """Retrieve a file from storage"""
        try:
            full_path = Path(path)
            if not full_path.exists():
                raise ValidationError(f"File not found: {path}")

            async with aiofiles.open(str(full_path), 'rb') as f:
                return await f.read()

        except Exception as e:
            raise ValidationError(f"Failed to get file: {str(e)}")

    async def delete_file(self, path: str) -> None:
        """Delete a file from storage"""
        try:
            full_path = Path(path)
            if full_path.exists():
                await aiofiles.os.remove(str(full_path))

        except Exception as e:
            raise ValidationError(f"Failed to delete file: {str(e)}")

    async def list_files(self, directory: str) -> List[str]:
        """List files in a directory"""
        try:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                return []

            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append(str(item))
            return files

        except Exception as e:
            raise ValidationError(f"Failed to list files: {str(e)}")

    async def create_directory(self, directory: str) -> str:
        """Create a new directory"""
        try:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            return str(dir_path)

        except Exception as e:
            raise ValidationError(f"Failed to create directory: {str(e)}")

    async def read_json(self, path: str) -> Dict[str, Any]:
        """Read JSON file"""
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
                return json.loads(content)

        except Exception as e:
            raise ValidationError(f"Failed to read JSON file: {str(e)}")

    async def write_json(self, path: str, data: Dict[str, Any]) -> None:
        """Write JSON file"""
        try:
            async with aiofiles.open(path, 'w') as f:
                content = json.dumps(data, indent=2)
                await f.write(content)

        except Exception as e:
            raise ValidationError(f"Failed to write JSON file: {str(e)}")
        
    async def write_text(self, path: str, content: str) -> None:
        """Write text content to a file"""
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except Exception as e:
            raise ValidationError(f"Failed to write text file: {str(e)}")

class FileStorageFactory:
    """Factory for creating file storage instances"""

    @staticmethod
    def create_storage(storage_type: str, **kwargs) -> FileStorage:
        if storage_type == 'local':
            return LocalFileStorage(**kwargs)
        # Could add more storage types (S3, Azure, etc.)
        raise ValueError(f"Unsupported storage type: {storage_type}")

