from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from uuid import UUID

class TestStatus(Enum):
    """Status states for a test"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TestResult:
    """Results from a test execution"""
    output: str
    error: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    generated_files: Optional[List[str]] = None
    images: Optional[List[str]] = None

@dataclass
class TestCase:
    """Core test case model"""
    id: UUID
    validation_id: UUID
    description: str
    status: TestStatus
    created_at: datetime
    updated_at: datetime
    code: Optional[str] = None
    results: Optional[TestResult] = None

    def can_rerun(self) -> bool:
        """Business rule: Can rerun if not currently running"""
        return self.status != TestStatus.RUNNING

    def has_exceeded_time_limit(self, time_limit_seconds: int = 3600) -> bool:
        """Business rule: Test has exceeded time limit"""
        if self.status == TestStatus.RUNNING:
            elapsed = (datetime.utcnow() - self.updated_at).total_seconds()
            return elapsed > time_limit_seconds
        return False