from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
import yaml  # You'll need to install pyyaml
import os
from functools import wraps
from domain.models.template import TemplateMetadata
from domain.models.validation import ValidationModel

# @dataclass
# class ModelMetadata:
#     """Class to hold model metadata and file paths"""
#     documentation: str = ""
#     code: str = ""
#     train_path: str = ""
#     test_path: str = ""
#     pickle_path: str = ""
#     execution_folder: str = ""
#     report_tex_name: str = ""

def reload_templates_in_debug(func):
    """Decorator to reload templates before function execution when in debug mode"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.debug_mode:
            self._templates = self._load_templates(self._templates_path)
        return func(self, *args, **kwargs)
    return wrapper

class TemplateManager:
    """Manages template operations and formatting for model validation"""
    
    CONTENT_TEMPLATES = {"documentation", "code"}
    PATH_TEMPLATES = {"train", "test", "pickle"}
    
    def __init__(self, templates_path: str = "templates.yaml", debug_mode: bool = False,  base_upload_folder: str = None):
        """
        Initialize TemplateManager with templates from external file
        
        Args:
            templates_path: Path to YAML file containing templates
            debug_mode: If True, templates will be reloaded for each call
        """
        self._metadata = TemplateMetadata()
        self._templates_path = templates_path
        self.debug_mode = debug_mode
        self.base_upload_folder = base_upload_folder 
        self._templates = self._load_templates(templates_path)
        
    def _load_templates(self, templates_path: str) -> Dict[str, str]:
        """
        Load templates from YAML file
        
        Args:
            templates_path: Path to YAML file containing templates
            
        Returns:
            Dict[str, str]: Dictionary of template names and their content
            
        Raises:
            FileNotFoundError: If templates file is not found
            yaml.YAMLError: If templates file contains invalid YAML
        """
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
                if self.debug_mode:
                    print(f"[DEBUG] Reloaded templates from {templates_path}")
                return templates
        except FileNotFoundError:
            raise FileNotFoundError(f"Templates file not found: {templates_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in templates file: {templates_path}\n{str(e)}")

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Enable or disable debug mode
        
        Args:
            enabled: True to enable debug mode, False to disable
        """
        self.debug_mode = enabled
        if enabled:
            print("[DEBUG] Debug mode enabled - templates will be reloaded for each call")
        else:
            print("[DEBUG] Debug mode disabled")

    @property
    def metadata(self) -> TemplateMetadata:
        """Get current metadata"""
        return self._metadata

    def set_metadata(self, 
                    documentation: str = "",
                    code: str = "",
                    train_path: str = "",
                    test_path: str = "",
                    pickle_path: str = "",
                    execution_folder: str = "",
                    report_tex_name: str = "") -> None:
        """Set metadata values. Empty strings will maintain existing values."""
        self._metadata = TemplateMetadata(
            documentation=documentation or self._metadata.documentation,
            code=code or self._metadata.code,
            train_path=train_path or self._metadata.train_path,
            test_path=test_path or self._metadata.test_path,
            pickle_path=pickle_path or self._metadata.pickle_path,
            execution_folder=execution_folder or self._metadata.execution_folder,
            report_tex_name=report_tex_name or self._metadata.report_tex_name
        )

    def update_metadata(self, **kwargs) -> None:
        """Update specific metadata fields using keyword arguments."""
        current_values = self._metadata.__dict__.copy()
        current_values.update({k: v for k, v in kwargs.items() if v})
        self._metadata = TemplateMetadata(**current_values)

    def update_from_validation(self, validation: ValidationModel, execution_folder: str) -> None:
        """Update template metadata from validation model"""
        self._metadata = TemplateMetadata(
            documentation=validation.model_files.get('documentation'),
            code=validation.model_files.get('trainingScript'),
            train_path=os.path.join(execution_folder, os.path.basename(validation.model_files.get('trainingDataset', ''))),
            test_path=os.path.join(execution_folder, os.path.basename(validation.model_files.get('testDataset', ''))),
            pickle_path=os.path.join(execution_folder, os.path.basename(validation.model_files.get('trainedModel', ''))),
            execution_folder=execution_folder,
            report_tex_name="report.tex"
        )

    @staticmethod
    def read_file_content(file_path: str) -> str:
        """Safely read content from a file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        return path.read_text(encoding='utf-8')

    @reload_templates_in_debug
    def _format_template_part(self, template_key: str, value: str) -> str:
        """Format a template part based on its type (content or path)."""
        if not value:
            return ""

        template_name = f"{template_key}_template"
        if template_key in self.CONTENT_TEMPLATES:
            try:
                content = self.read_file_content(value)
                if self.debug_mode:
                    print(f"[DEBUG] Using template '{template_name}' with content from {value}")
                return self._templates[template_name].format(content=content)
            except FileNotFoundError:
                print(f"Warning: Could not read file for {template_key}: {value}")
                return ""
        elif template_key in self.PATH_TEMPLATES:
            if self.debug_mode:
                print(f"[DEBUG] Using template '{template_name}' with path {value}")
            return self._templates[template_name].format(path=value)
        else:
            raise ValueError(f"Unknown template key: {template_key}")

    @reload_templates_in_debug
    def generate_test_list_prompt(self) -> str:
        """Generate a prompt for test list generation using current metadata."""
        if self.debug_mode:
            print("[DEBUG] Generating test list prompt")
        formatted_parts = {
            "documentation": self._format_template_part("documentation", self._metadata.documentation),
            "code": self._format_template_part("code", self._metadata.code)
        }
        
        return self._templates["test_generation_template"].format(**formatted_parts)
    
    @reload_templates_in_debug
    def generate_test_list_json_prompt(self) -> str:
        """Generate a prompt for test list generation in JSON format."""
        if self.debug_mode:
            print("[DEBUG] Generating JSON test list prompt")
        formatted_parts = {
            "documentation": self._format_template_part("documentation", self._metadata.documentation),
            "code": self._format_template_part("code", self._metadata.code)
        }
        return self._templates["test_generation_json_template"].format(**formatted_parts)
    
    @reload_templates_in_debug
    def generate_independent_test_prompt(self, test_title: str, test_description: str, i: int) -> str:
        """Generate a prompt for an independent test."""
        if self.debug_mode:
            print(f"[DEBUG] Generating independent test prompt for test {i}: {test_title}")
        
        # Create execution folder file paths
        train_file = Path(self._metadata.execution_folder) / Path(self._metadata.train_path).name
        test_file = Path(self._metadata.execution_folder) / Path(self._metadata.test_path).name
        pickle_file = Path(self._metadata.execution_folder) / Path(self._metadata.pickle_path).name
        
        formatted_parts = {
            "documentation": self._format_template_part("documentation", self._metadata.documentation),
            "code": self._format_template_part("code", self._metadata.code),
            "train": self._format_template_part("train", train_file),
            "test": self._format_template_part("test", test_file),
            "pickle": self._format_template_part("pickle", pickle_file),
            "execution_folder": self._metadata.execution_folder,
            "report_tex_name": self._metadata.report_tex_name,
            "test_title": test_title,
            "test_description": test_description,
            "test_folder": os.path.join(self._metadata.execution_folder, f"test_{i}")
        }
        
        return self._templates["independent_test_template"].format(**formatted_parts)

    @reload_templates_in_debug
    def generate_validation_prompt(self) -> str:
        """Generate a validation prompt using current metadata."""
        if self.debug_mode:
            print("[DEBUG] Generating validation prompt")
        formatted_parts = {
            "documentation": self._format_template_part("documentation", self._metadata.documentation),
            "code": self._format_template_part("code", self._metadata.code),
            "train": self._format_template_part("train", self._metadata.train_path),
            "test": self._format_template_part("test", self._metadata.test_path),
            "pickle": self._format_template_part("pickle", self._metadata.pickle_path),
            "execution_folder": self._metadata.execution_folder,
            "report_tex_name": self._metadata.report_tex_name
        }
        
        return self._templates["validation_template"].format(**formatted_parts)

    @reload_templates_in_debug
    def generate_external_validation_prompt(self, tests: str) -> str:
        """Generate an external validation prompt using current metadata and provided tests."""
        if self.debug_mode:
            print("[DEBUG] Generating external validation prompt")
        formatted_parts = {
            "documentation": self._format_template_part("documentation", self._metadata.documentation),
            "code": self._format_template_part("code", self._metadata.code),
            "train": self._format_template_part("train", self._metadata.train_path),
            "test": self._format_template_part("test", self._metadata.test_path),
            "pickle": self._format_template_part("pickle", self._metadata.pickle_path),
            "execution_folder": self._metadata.execution_folder,
            "report_tex_name": self._metadata.report_tex_name,
            "tests": tests
        }
        
        return self._templates["external_validation_template"].format(**formatted_parts)