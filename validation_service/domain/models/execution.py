from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
from uuid import UUID

class ExecutionStatus(Enum):
    """Status states for code execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ExecutionResult:
    """Result of code execution"""
    execution_id: str
    status: ExecutionStatus
    output: Optional[str] = None
    error: Optional[str] = None
    created_files: Optional[List[str]] = None
    metrics: Optional[Dict[str, float]] = None
    directory: Optional[str] = None

@dataclass
class ExecutionContext:
    """Context for code execution"""
    validation_id: UUID
    test_number: Optional[int] = None
    execution_id: Optional[str] = None
    directory: Optional[str] = None
    timeout: int = 300  # 5 minutes default timeout

    def is_test_execution(self) -> bool:
        """Business rule: Check if this is a test execution"""
        return self.test_number is not None