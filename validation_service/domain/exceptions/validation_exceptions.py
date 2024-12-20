class ValidationError(Exception):
    """Base exception for validation errors"""
    pass

class ValidationNotFoundError(ValidationError):
    """Raised when validation cannot be found"""
    pass

class ValidationExpiredError(ValidationError):
    """Raised when validation has expired"""
    pass

class TestExecutionError(ValidationError):
    """Raised when test execution fails"""
    pass

class InvalidModelFilesError(ValidationError):
    """Raised when required model files are missing or invalid"""
    pass

class ExecutionError(ValidationError):
    """Raised when code execution fails"""
    pass

class LLMError(ValidationError):
    """Raised when LLM interaction fails"""
    pass