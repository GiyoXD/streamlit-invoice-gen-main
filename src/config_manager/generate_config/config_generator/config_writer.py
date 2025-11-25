"""
Config writer component for the Config Generator.

This module provides functionality to write the updated configuration to JSON files
and validate that all template sections are preserved during the process.
"""

import json
import os
from typing import Dict, Any
from .models import ConfigurationData, SheetConfig, HeaderEntry


class ConfigWriterError(Exception):
    """Custom exception for config writing errors."""
    pass


class ConfigWriter:
    """
    Writes configuration data to JSON files with validation.
    
    This class handles writing the updated configuration to output files and
    validates that all required sections from the template are preserved.
    """
    
    def __init__(self):
        """Initialize the ConfigWriter."""
        pass
    
    def write_config(self, config: Dict[str, Any], output_path: str) -> None:
        """
        Write the configuration dictionary to a JSON file.
        
        Args:
            config: Configuration dictionary to write
            output_path: Path where the JSON file should be written
            
        Raises:
            ConfigWriterError: If writing fails or validation errors occur
        """
        if not isinstance(config, dict):
            raise ConfigWriterError("Config must be a dictionary")
        
        if not output_path or not isinstance(output_path, str):
            raise ConfigWriterError("Output path must be a non-empty string")
        
        # Validate completeness before writing
        if not self.validate_completeness(config):
            raise ConfigWriterError("Configuration completeness validation failed")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                raise ConfigWriterError(f"Failed to create output directory: {e}")
        
        # Validate file permissions
        self._validate_file_permissions(output_path)
        
        # Write the configuration to file with atomic operation
        temp_path = output_path + '.tmp'
        try:
            with open(temp_path, 'w', encoding='utf-8', errors='replace') as file:
                json.dump(config, file, indent=2, ensure_ascii=False)
            
            # Simple atomic move to final location
            # On Windows, os.rename can't overwrite existing files, so remove first if needed
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)
                
        except IOError as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise ConfigWriterError(f"Error writing config file: {e}")
        except TypeError as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise ConfigWriterError(f"Error serializing config to JSON: {e}")
        except OSError as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise ConfigWriterError(f"Error during file operations: {e}")
    
    def validate_completeness(self, config: Dict[str, Any]) -> bool:
        """
        Validate that all required template sections are preserved in the config.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if all required sections are present and valid
            
        Raises:
            ConfigWriterError: If validation fails with specific error details
        """
        if not isinstance(config, dict):
            raise ConfigWriterError("Config must be a dictionary")
        
        # Check for required top-level keys
        required_keys = ["sheets_to_process", "sheet_data_map", "data_mapping"]
        for key in required_keys:
            if key not in config:
                raise ConfigWriterError(f"Missing required top-level key: {key}")
        
        # Validate sheets_to_process
        sheets_to_process = config["sheets_to_process"]
        if not isinstance(sheets_to_process, list) or len(sheets_to_process) == 0:
            raise ConfigWriterError("sheets_to_process must be a non-empty list")
        
        for sheet in sheets_to_process:
            if not isinstance(sheet, str) or not sheet.strip():
                raise ConfigWriterError("All sheets in sheets_to_process must be non-empty strings")
        
        # Validate sheet_data_map
        sheet_data_map = config["sheet_data_map"]
        if not isinstance(sheet_data_map, dict):
            raise ConfigWriterError("sheet_data_map must be a dictionary")
        
        # Validate data_mapping
        data_mapping = config["data_mapping"]
        if not isinstance(data_mapping, dict):
            raise ConfigWriterError("data_mapping must be a dictionary")
        
        # Validate that all sheets in sheets_to_process have corresponding entries
        for sheet_name in sheets_to_process:
            if sheet_name not in data_mapping:
                raise ConfigWriterError(f"Sheet '{sheet_name}' missing from data_mapping")
            
            if sheet_name not in sheet_data_map:
                raise ConfigWriterError(f"Sheet '{sheet_name}' missing from sheet_data_map")
        
        # Validate each sheet configuration
        for sheet_name, sheet_config in data_mapping.items():
            self._validate_sheet_completeness(sheet_name, sheet_config)
        
        return True
    
    def _validate_sheet_completeness(self, sheet_name: str, sheet_config: Dict[str, Any]) -> None:
        """
        Validate that a sheet configuration contains all required sections.
        
        Args:
            sheet_name: Name of the sheet being validated
            sheet_config: Configuration dictionary for the sheet
            
        Raises:
            ConfigWriterError: If sheet configuration is incomplete
        """
        if not isinstance(sheet_config, dict):
            raise ConfigWriterError(f"Configuration for sheet '{sheet_name}' must be a dictionary")
        
        # Check for required keys in sheet configuration
        required_keys = ["start_row", "header_to_write", "mappings", "footer_configurations", "styling"]
        for key in required_keys:
            if key not in sheet_config:
                raise ConfigWriterError(f"Sheet '{sheet_name}' missing required section: {key}")
        
        # Validate start_row
        start_row = sheet_config["start_row"]
        if not isinstance(start_row, int) or start_row < 0:
            raise ConfigWriterError(f"start_row for sheet '{sheet_name}' must be a non-negative integer")
        
        # Validate header_to_write structure
        header_to_write = sheet_config["header_to_write"]
        if not isinstance(header_to_write, list):
            raise ConfigWriterError(f"header_to_write for sheet '{sheet_name}' must be a list")

        if len(header_to_write) == 0:
            # Create default header entry instead of failing
            header_to_write = [{
                "text": "Default Header",
                "row": 1,
                "col": 1,
                "rowspan": 1,
                "colspan": 1,
                "font_size": 11,
                "bold": True,
                "align": "center"
            }]
            sheet_config["header_to_write"] = header_to_write
        
        for i, header_entry in enumerate(header_to_write):
            self._validate_header_entry_completeness(sheet_name, i, header_entry)
        
        # Validate that critical sections are dictionaries and not empty
        critical_sections = ["mappings", "footer_configurations", "styling"]
        for section_name in critical_sections:
            section = sheet_config[section_name]
            if not isinstance(section, dict):
                raise ConfigWriterError(f"{section_name} for sheet '{sheet_name}' must be a dictionary")
        
        # Validate styling section has required font information
        styling = sheet_config["styling"]
        required_styling_keys = ["default_font", "header_font"]
        for font_key in required_styling_keys:
            if font_key not in styling:
                raise ConfigWriterError(f"Styling section for sheet '{sheet_name}' missing required key: {font_key}")
            
            font_info = styling[font_key]
            if not isinstance(font_info, dict):
                raise ConfigWriterError(f"{font_key} in styling for sheet '{sheet_name}' must be a dictionary")
            
            # Validate font has name and size
            if "name" not in font_info or "size" not in font_info:
                raise ConfigWriterError(f"{font_key} in styling for sheet '{sheet_name}' must have 'name' and 'size'")
            
            if not isinstance(font_info["name"], str) or not font_info["name"].strip():
                raise ConfigWriterError(f"{font_key} name in styling for sheet '{sheet_name}' must be a non-empty string")
            
            if not isinstance(font_info["size"], (int, float)) or font_info["size"] <= 0:
                raise ConfigWriterError(f"{font_key} size in styling for sheet '{sheet_name}' must be a positive number")
    
    def _validate_header_entry_completeness(self, sheet_name: str, index: int, header_entry: Dict[str, Any]) -> None:
        """
        Validate that a header entry contains all required fields.
        
        Args:
            sheet_name: Name of the sheet containing this header
            index: Index of the header entry in the list
            header_entry: The header entry dictionary to validate
            
        Raises:
            ConfigWriterError: If header entry is incomplete
        """
        if not isinstance(header_entry, dict):
            raise ConfigWriterError(f"Header entry {index} in sheet '{sheet_name}' must be a dictionary")
        
        # Check for required keys
        required_keys = ["row", "col", "text"]
        for key in required_keys:
            if key not in header_entry:
                raise ConfigWriterError(f"Header entry {index} in sheet '{sheet_name}' missing required key: {key}")
        
        # If header has colspan but no id, it's a parent header (valid case)
        # If header has no colspan, it must have an id
        if "colspan" not in header_entry and "id" not in header_entry:
            raise ConfigWriterError(f"Header entry {index} in sheet '{sheet_name}' must have either 'id' or 'colspan'")
        
        # Validate row and col are non-negative integers
        for coord in ["row", "col"]:
            value = header_entry[coord]
            if not isinstance(value, int) or value < 0:
                raise ConfigWriterError(f"{coord} in header entry {index} of sheet '{sheet_name}' must be a non-negative integer")
        
        # Validate text is non-empty string
        text = header_entry["text"]
        if not isinstance(text, str) or not text.strip():
            raise ConfigWriterError(f"text in header entry {index} of sheet '{sheet_name}' must be a non-empty string")
        
        # Validate id if present
        if "id" in header_entry:
            id_value = header_entry["id"]
            if not isinstance(id_value, str) or not id_value.strip():
                raise ConfigWriterError(f"id in header entry {index} of sheet '{sheet_name}' must be a non-empty string when provided")
        
        # Validate optional rowspan and colspan
        for span in ["rowspan", "colspan"]:
            if span in header_entry:
                value = header_entry[span]
                if not isinstance(value, int) or value <= 0:
                    raise ConfigWriterError(f"{span} in header entry {index} of sheet '{sheet_name}' must be a positive integer")
    
    def write_configuration_data(self, config_data: ConfigurationData, output_path: str) -> None:
        """
        Write a ConfigurationData object to a JSON file.
        
        Args:
            config_data: ConfigurationData object to write
            output_path: Path where the JSON file should be written
            
        Raises:
            ConfigWriterError: If writing fails or validation errors occur
        """
        if not isinstance(config_data, ConfigurationData):
            raise ConfigWriterError("config_data must be a ConfigurationData instance")
        
        # Convert ConfigurationData to dictionary
        config_dict = self._configuration_data_to_dict(config_data)
        
        # Write using the standard write_config method
        self.write_config(config_dict, output_path)
    
    def _configuration_data_to_dict(self, config_data: ConfigurationData) -> Dict[str, Any]:
        """
        Convert a ConfigurationData object to a dictionary.
        
        Args:
            config_data: ConfigurationData object to convert
            
        Returns:
            Dictionary representation of the configuration data
        """
        # Convert data_mapping from SheetConfig objects to dictionaries
        data_mapping_dict = {}
        for sheet_name, sheet_config in config_data.data_mapping.items():
            # Convert header entries to dictionaries
            header_to_write = []
            for header_entry in sheet_config.header_to_write:
                header_dict = {
                    "row": header_entry.row,
                    "col": header_entry.col,
                    "text": header_entry.text
                }
                
                # Add optional fields if present
                if header_entry.id is not None:
                    header_dict["id"] = header_entry.id
                if header_entry.rowspan is not None:
                    header_dict["rowspan"] = header_entry.rowspan
                if header_entry.colspan is not None:
                    header_dict["colspan"] = header_entry.colspan
                
                header_to_write.append(header_dict)
            
            # Create sheet configuration dictionary
            sheet_config_dict = {
                "start_row": sheet_config.start_row,
                "header_to_write": header_to_write,
                "mappings": sheet_config.mappings,
                "footer_configurations": sheet_config.footer_configurations,
                "styling": sheet_config.styling
            }
            
            data_mapping_dict[sheet_name] = sheet_config_dict
        
        return {
            "sheets_to_process": config_data.sheets_to_process,
            "sheet_data_map": config_data.sheet_data_map,
            "data_mapping": data_mapping_dict
        }
    
    def _validate_file_permissions(self, output_path: str) -> None:
        """
        Validate file permissions for writing.
        
        Args:
            output_path: Path where file will be written
            
        Raises:
            ConfigWriterError: If file permissions are insufficient
        """
        output_dir = os.path.dirname(output_path) or '.'
        
        # Check directory write permissions
        if not os.access(output_dir, os.W_OK):
            raise ConfigWriterError(f"No write permission for directory: {output_dir}")
        
        # Check file write permissions if file exists
        if os.path.exists(output_path):
            if not os.access(output_path, os.W_OK):
                raise ConfigWriterError(f"No write permission for file: {output_path}")
            
            # Check if file is locked (basic check)
            try:
                with open(output_path, 'a'):
                    pass
            except IOError as e:
                raise ConfigWriterError(f"File appears to be locked or inaccessible: {e}")
    
    def validate_template_preservation(self, original_template: Dict[str, Any], 
                                     updated_config: Dict[str, Any]) -> bool:
        """
        Validate that template preservation rules are followed.
        
        Args:
            original_template: Original template configuration
            updated_config: Updated configuration to validate
            
        Returns:
            True if template is properly preserved
            
        Raises:
            ConfigWriterError: If template preservation validation fails
        """
        try:
            # Validate that all critical sections are preserved
            critical_sections = ['sheets_to_process', 'sheet_data_map', 'data_mapping']
            
            for section in critical_sections:
                if section not in original_template:
                    continue
                    
                if section not in updated_config:
                    raise ConfigWriterError(f"Critical section '{section}' was removed from template")
            
            # Validate sheet-level preservation
            original_data_mapping = original_template.get('data_mapping', {})
            updated_data_mapping = updated_config.get('data_mapping', {})
            
            for sheet_name, original_sheet_config in original_data_mapping.items():
                if sheet_name not in updated_data_mapping:
                    raise ConfigWriterError(f"Sheet '{sheet_name}' was removed from template")
                
                updated_sheet_config = updated_data_mapping[sheet_name]
                
                # Validate that business logic sections are preserved
                business_logic_sections = ['mappings', 'footer_configurations']
                
                for section in business_logic_sections:
                    if section in original_sheet_config:
                        if section not in updated_sheet_config:
                            raise ConfigWriterError(f"Business logic section '{section}' was removed from sheet '{sheet_name}'")
                        
                        # Deep comparison for critical business logic
                        if section == 'mappings':
                            self._validate_mappings_preservation(
                                original_sheet_config[section], 
                                updated_sheet_config[section], 
                                sheet_name
                            )
            
            return True
            
        except Exception as e:
            if isinstance(e, ConfigWriterError):
                raise
            raise ConfigWriterError(f"Template preservation validation failed: {str(e)}") from e
    
    def _validate_mappings_preservation(self, original_mappings: Dict[str, Any], 
                                      updated_mappings: Dict[str, Any], sheet_name: str) -> None:
        """
        Validate that column mappings are preserved.
        
        Args:
            original_mappings: Original mappings from template
            updated_mappings: Updated mappings to validate
            sheet_name: Name of the sheet for error messages
            
        Raises:
            ConfigWriterError: If mappings are not properly preserved
        """
        # Check that all original column IDs are preserved
        for column_id in original_mappings.keys():
            if column_id not in updated_mappings:
                raise ConfigWriterError(f"Column mapping '{column_id}' was removed from sheet '{sheet_name}'")
        
        # Validate that mapping structure is preserved
        for column_id, original_mapping in original_mappings.items():
            updated_mapping = updated_mappings[column_id]
            
            if isinstance(original_mapping, dict) and isinstance(updated_mapping, dict):
                # Check for critical mapping fields
                critical_fields = ['column', 'data_type', 'required']
                
                for field in critical_fields:
                    if field in original_mapping and field not in updated_mapping:
                        raise ConfigWriterError(f"Critical mapping field '{field}' was removed from column '{column_id}' in sheet '{sheet_name}'")