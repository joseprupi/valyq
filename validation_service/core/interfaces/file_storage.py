from abc import ABC, abstractmethod
from typing import BinaryIO, List
from pathlib import Path

class FileStorage(ABC):
    """Abstract interface for file storage operations"""
    
    @abstractmethod
    async def save_file(self, file: BinaryIO, path: str) -> str:
        """Save a file and return its path"""
        pass
    
    @abstractmethod
    async def get_file(self, path: str) -> BinaryIO:
        """Retrieve a file by path"""
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """List files in a directory"""
        pass
    
    @abstractmethod
    async def write_text(self, path: str, content: str) -> None:
        """Write text content to a file"""
        pass