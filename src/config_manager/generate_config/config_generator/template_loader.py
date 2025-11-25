"""
Template loader component for the Config Generator.

This module provides functionality to load and validate the sample_config.json
template file that serves as the base configuration structure.
"""

import json
import os
from typing import Dict, Any
from .models import ConfigurationData, SheetConfig, HeaderEntry


class TemplateLoaderError(Exception):
    """Custom exception for template loading errors."""
    pass


class TemplateLoader:
    """
    Loads and validates sample_config.json as the base template.
    
    This class handles loading the template configuration file and validating
    its structure to ensure it contains all required sections and fields.
    """
    
    def __init__(self):
        """Initialize the TemplateLoader."""
        pass
    
    def load_template(self, template_path: str) -> Dict[str, Any]:
        """
        Load the template configuration from a JSON file.
        
        Args:
            template_path: Path to the template JSON file
            
        Returns:
            Dictionary containing the loaded template configuration
            
        Raises:
            TemplateLoaderError: If file cannot be loaded or parsed
        """
        if not template_path or not isinstance(template_path, str):
            raise TemplateLoaderError("Template path must be a non-empty string")
        
        if not os.path.exists(template_path):
            raise TemplateLoaderError(f"Template file not found: {template_path}")
        
        if not os.path.isfile(template_path):
            raise TemplateLoaderError(f"Template path is not a file: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                template_data = json.load(file)
        except json.JSONDecodeError as e:
            raise TemplateLoaderError(f"Invalid JSON in template file: {e}")
        except IOError as e:
            raise TemplateLoaderError(f"Error reading template file: {e}")
        
        # Validate the loaded template structure
        if not self.validate_template_structure(template_data):
            raise TemplateLoaderError("Template structure validation failed")
        
        return template_data
    
    def validate_template_structure(self, template: Dict[str, Any]) -> bool:
        """
        Validate that the template has the required structure.
        
        Args:
            template: The template dictionary to validate
            
        Returns:
            True if template structure is valid
            
        Raises:
            TemplateLoaderError: If template structure is invalid
        """
        if not isinstance(template, dict):
            raise TemplateLoaderError("Template must be a dictionary")
        
        # Check for required top-level keys
        required_keys = ["sheets_to_process", "sheet_data_map", "data_mapping"]
        for key in required_keys:
            if key not in template:
                raise TemplateLoaderError(f"Missing required key: {key}")
        
        # Validate sheets_to_process
        sheets_to_process = template["sheets_to_process"]
        if not isinstance(sheets_to_process, list) or len(sheets_to_process) == 0:
            raise TemplateLoaderError("sheets_to_process must be a non-empty list")
        
        for sheet in sheets_to_process:
            if not isinstance(sheet, str) or not sheet.strip():
                raise TemplateLoaderError("All sheets in sheets_to_process must be non-empty strings")
        
        # Validate sheet_data_map
        sheet_data_map = template["sheet_data_map"]
        if not isinstance(sheet_data_map, dict):
            raise TemplateLoaderError("sheet_data_map must be a dictionary")
        
        # Validate data_mapping
        data_mapping = template["data_mapping"]
        if not isinstance(data_mapping, dict):
            raise TemplateLoaderError("data_mapping must be a dictionary")
        
        # Validate that all sheets in sheets_to_process have corresponding entries
        for sheet_name in sheets_to_process:
            if sheet_name not in data_mapping:
                raise TemplateLoaderError(f"Sheet '{sheet_name}' missing from data_mapping")
            
            if sheet_name not in sheet_data_map:
                raise TemplateLoaderError(f"Sheet '{sheet_name}' missing from sheet_data_map")
        
        # Validate each sheet configuration
        for sheet_name, sheet_config in data_mapping.items():
            self._validate_sheet_config(sheet_name, sheet_config)
        
        return True
    
    def _validate_sheet_config(self, sheet_name: str, sheet_config: Dict[str, Any]) -> None:
        """
        Validate the configuration for a single sheet.
        
        Args:
            sheet_name: Name of the sheet being validated
            sheet_config: Configuration dictionary for the sheet
            
        Raises:
            TemplateLoaderError: If sheet configuration is invalid
        """
        if not isinstance(sheet_config, dict):
            raise TemplateLoaderError(f"Configuration for sheet '{sheet_name}' must be a dictionary")
        
        # Check for required keys in sheet configuration
        # Accept either "styling" (new format) or "sheet_styling_config" (old format)
        has_styling = "styling" in sheet_config
        has_sheet_styling = "sheet_styling_config" in sheet_config
        
        if not has_styling and not has_sheet_styling:
            raise TemplateLoaderError(f"Sheet '{sheet_name}' missing required key: 'styling' or 'sheet_styling_config'")
        
        # If we have sheet_styling_config but not styling, convert it
        if has_sheet_styling and not has_styling:
            sheet_config["styling"] = self._convert_sheet_styling_to_styling(sheet_config["sheet_styling_config"])
            # Remove the old format key after conversion
            del sheet_config["sheet_styling_config"]
        
        required_keys = ["start_row", "header_to_write", "mappings", "footer_configurations", "styling"]
        for key in required_keys:
            if key not in sheet_config:
                raise TemplateLoaderError(f"Sheet '{sheet_name}' missing required key: {key}")
        
        # Validate start_row
        start_row = sheet_config["start_row"]
        if not isinstance(start_row, int) or start_row < 0:
            raise TemplateLoaderError(f"start_row for sheet '{sheet_name}' must be a non-negative integer")
        
        # Validate header_to_write
        header_to_write = sheet_config["header_to_write"]
        if not isinstance(header_to_write, list):
            raise TemplateLoaderError(f"header_to_write for sheet '{sheet_name}' must be a list")
        
        for i, header_entry in enumerate(header_to_write):
            self._validate_header_entry(sheet_name, i, header_entry)
        
        # Validate other sections are dictionaries
        for section_name in ["mappings", "footer_configurations", "styling"]:
            section = sheet_config[section_name]
            if not isinstance(section, dict):
                raise TemplateLoaderError(f"{section_name} for sheet '{sheet_name}' must be a dictionary")
    
    def _validate_header_entry(self, sheet_name: str, index: int, header_entry: Dict[str, Any]) -> None:
        """
        Validate a single header entry.
        
        Args:
            sheet_name: Name of the sheet containing this header
            index: Index of the header entry in the list
            header_entry: The header entry dictionary to validate
            
        Raises:
            TemplateLoaderError: If header entry is invalid
        """
        if not isinstance(header_entry, dict):
            raise TemplateLoaderError(f"Header entry {index} in sheet '{sheet_name}' must be a dictionary")
        
        # Check for required keys - id is optional for headers with colspan (parent headers)
        required_keys = ["row", "col", "text"]
        for key in required_keys:
            if key not in header_entry:
                raise TemplateLoaderError(f"Header entry {index} in sheet '{sheet_name}' missing required key: {key}")
        
        # If header has colspan but no id, it's a parent header (valid case)
        # If header has no colspan, it must have an id
        if "colspan" not in header_entry and "id" not in header_entry:
            raise TemplateLoaderError(f"Header entry {index} in sheet '{sheet_name}' must have either 'id' or 'colspan'")
        
        # Validate row and col
        for coord in ["row", "col"]:
            value = header_entry[coord]
            if not isinstance(value, int) or value < 0:
                raise TemplateLoaderError(f"{coord} in header entry {index} of sheet '{sheet_name}' must be a non-negative integer")
        
        # Validate text (required)
        text = header_entry["text"]
        if not isinstance(text, str) or not text.strip():
            raise TemplateLoaderError(f"text in header entry {index} of sheet '{sheet_name}' must be a non-empty string")
        
        # Validate id (optional, but must be non-empty string if present)
        if "id" in header_entry:
            id_value = header_entry["id"]
            if not isinstance(id_value, str) or not id_value.strip():
                raise TemplateLoaderError(f"id in header entry {index} of sheet '{sheet_name}' must be a non-empty string when provided")
        
        # Validate optional rowspan and colspan
        for span in ["rowspan", "colspan"]:
            if span in header_entry:
                value = header_entry[span]
                if not isinstance(value, int) or value <= 0:
                    raise TemplateLoaderError(f"{span} in header entry {index} of sheet '{sheet_name}' must be a positive integer")
    
    def convert_to_configuration_data(self, template: Dict[str, Any]) -> ConfigurationData:
        """
        Convert the loaded template dictionary to a ConfigurationData object.
        
        Args:
            template: The template dictionary to convert
            
        Returns:
            ConfigurationData object representing the template
        """
        # Convert header entries to HeaderEntry objects
        data_mapping = {}
        for sheet_name, sheet_config in template["data_mapping"].items():
            header_entries = []
            for header_dict in sheet_config["header_to_write"]:
                header_entry = HeaderEntry(
                    row=header_dict["row"],
                    col=header_dict["col"],
                    text=header_dict["text"],
                    id=header_dict.get("id"),
                    rowspan=header_dict.get("rowspan"),
                    colspan=header_dict.get("colspan")
                )
                header_entries.append(header_entry)
            
            sheet_config_obj = SheetConfig(
                start_row=sheet_config["start_row"],
                header_to_write=header_entries,
                mappings=sheet_config["mappings"],
                footer_configurations=sheet_config["footer_configurations"],
                styling=sheet_config["styling"]
            )
            data_mapping[sheet_name] = sheet_config_obj
        
        return ConfigurationData(
            sheets_to_process=template["sheets_to_process"],
            sheet_data_map=template["sheet_data_map"],
            data_mapping=data_mapping
        )
    
    def _convert_sheet_styling_to_styling(self, sheet_styling_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert old sheet_styling_config format to new styling format.
        
        Args:
            sheet_styling_config: The old format with nested "styles" -> "by_column_id"
            
        Returns:
            The new flat styling format
        """
        styling = {}
        
        # Copy over direct keys that are the same
        direct_keys = ["force_text_format_ids", "column_ids_with_full_grid", "column_id_widths", "row_heights"]
        for key in direct_keys:
            if key in sheet_styling_config:
                styling[key] = sheet_styling_config[key]
        
        # Handle the nested styles structure
        if "styles" in sheet_styling_config:
            styles = sheet_styling_config["styles"]
            
            # Extract default styling
            if "default" in styles:
                default_style = styles["default"]
                if "font" in default_style:
                    styling["default_font"] = default_style["font"]
                if "alignment" in default_style:
                    styling["default_alignment"] = default_style["alignment"]
            
            # Extract header styling
            if "header" in styles:
                header_style = styles["header"]
                if "font" in header_style:
                    styling["header_font"] = header_style["font"]
                if "alignment" in header_style:
                    styling["header_alignment"] = header_style["alignment"]
            
            # Extract footer styling (if present)
            if "footer" in styles:
                footer_style = styles["footer"]
                if "font" in footer_style:
                    styling["footer_font"] = footer_style["font"]
                if "alignment" in footer_style:
                    styling["footer_alignment"] = footer_style["alignment"]
            
            # Extract column-specific styling
            if "by_column_id" in styles:
                styling["column_id_styles"] = styles["by_column_id"]
        
        # If column_id_styles wasn't set from by_column_id, check if it exists directly
        if "column_id_styles" not in styling and "column_id_styles" in sheet_styling_config:
            styling["column_id_styles"] = sheet_styling_config["column_id_styles"]
        
        return styling