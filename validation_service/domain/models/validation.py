from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class ValidationStatus(Enum):
    """Status states for a validation"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ValidationModel:
    """Core validation model containing business rules"""
    validation_id: UUID
    status: ValidationStatus
    model_files: Dict[str, str]  # file_type -> file_path mapping
    created_at: datetime
    updated_at: datetime
    execution_id: Optional[str] = None
    error_message: Optional[str] = None
    tests: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ValidationModel to dictionary"""
        return {
            'validation_id': str(self.validation_id),
            'status': self.status.value,
            'model_files': self.model_files,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'execution_id': self.execution_id,
            'error_message': self.error_message,
            'tests': self.tests
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationModel':
        """Create ValidationModel from dictionary"""
        return cls(
            validation_id=UUID(data['validation_id']),
            status=ValidationStatus(data['status']),
            model_files=data['model_files'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            execution_id=data.get('execution_id'),
            error_message=data.get('error_message'),
            tests=data.get('tests', {})
        )

    def can_execute_tests(self) -> bool:
        """Business rule: Can only execute tests if validation is complete"""
        return self.status == ValidationStatus.COMPLETED

    def is_expired(self) -> bool:
        """Business rule: Validation expires after 7 days"""
        return (datetime.utcnow() - self.created_at).days > 7

    def requires_documentation(self) -> bool:
        """Business rule: Documentation is required"""
        return not bool(self.documentation.strip())