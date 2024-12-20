from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class TemplateMetadata:
    """Model for template metadata"""
    documentation: Optional[str] = None
    code: Optional[str] = None
    train_path: Optional[str] = None
    test_path: Optional[str] = None
    pickle_path: Optional[str] = None
    execution_folder: Optional[str] = None
    report_tex_name: Optional[str] = None