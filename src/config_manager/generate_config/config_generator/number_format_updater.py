"""
Number Format Updater for the Config Generator.

This module provides functionality to update configuration templates with
number format information extracted from Excel files.
"""

from typing import Dict, Any, List
from .models import SheetData, NumberFormatInfo


class NumberFormatUpdater:
    """
    Updates configuration templates with number format information.
    
    This class takes number format data extracted from Excel analysis
    and applies it to the appropriate columns in the configuration template.
    """
    
    def __init__(self):
        """Initialize the NumberFormatUpdater."""
        pass
    
    def update_config_with_number_formats(self, config: Dict[str, Any], 
                                        sheet_data: SheetData) -> Dict[str, Any]:
        """
        Update configuration with number formats for a specific sheet.
        
        Args:
            config: The configuration dictionary to update
            sheet_data: Sheet data containing number format information
            
        Returns:
            Updated configuration dictionary
        """
        if not sheet_data.number_formats:
            return config
            
        # Find the sheet configuration
        sheet_config = self._find_sheet_config(config, sheet_data.sheet_name)
        if not sheet_config:
            return config
            
        # Update mappings with number formats
        if 'mappings' in sheet_config:
            self._update_mappings_with_formats(sheet_config['mappings'], 
                                             sheet_data.number_formats)
        
        # Also update footer configurations with number formats using same structure
        if 'footer_configurations' in sheet_config:
            self._update_footer_with_formats(sheet_config['footer_configurations'], 
                                           sheet_data.number_formats, sheet_data.sheet_name)
        
        return config
    
    def _find_sheet_config(self, config: Dict[str, Any], sheet_name: str) -> Dict[str, Any]:
        """
        Find the configuration section for a specific sheet.
        
        Args:
            config: Full configuration dictionary
            sheet_name: Name of the sheet to find
            
        Returns:
            Sheet configuration dictionary or None if not found
        """
        # Check if this is a sheet-specific configuration
        if sheet_name in config:
            return config[sheet_name]
            
        # Check data_mapping for sheet configuration
        if 'data_mapping' in config and sheet_name in config['data_mapping']:
            return config['data_mapping'][sheet_name]
            
        return None
    
    def _update_mappings_with_formats(self, mappings: Dict[str, Any], 
                                    number_formats: List[NumberFormatInfo]) -> None:
        """
        Update mappings dictionary with number format information.
        
        Args:
            mappings: The mappings dictionary to update
            number_formats: List of number format information
        """
        # Create a lookup dictionary for quick access
        format_lookup = {fmt.column_id: fmt for fmt in number_formats}
        
        # Update each mapping that has a matching column ID
        for mapping_key, mapping_value in mappings.items():
            if isinstance(mapping_value, dict) and 'id' in mapping_value:
                column_id = mapping_value['id']
                if column_id in format_lookup:
                    # Add number format to the mapping
                    format_info = format_lookup[column_id]
                    mapping_value['number_format'] = format_info.excel_format
                    
                    # Log the update
                    print(f"[NUMBER_FORMAT] Updated {column_id} with format: {format_info.excel_format}")
    
    def _update_footer_with_formats(self, footer_config: Dict[str, Any], 
                                  number_formats: List[NumberFormatInfo],
                                  sheet_name: str) -> None:
        """
        Update footer configuration with number format information using same structure as column styles.
        
        Args:
            footer_config: The footer configuration section
            number_formats: List of number format information
            sheet_name: Name of the sheet for logging
        """
        # Create a lookup dictionary for quick access
        format_lookup = {fmt.column_id: fmt for fmt in number_formats}
        
        # Ensure number_formats section exists in footer_config
        if 'number_formats' not in footer_config:
            footer_config['number_formats'] = {}
        
        footer_number_formats = footer_config['number_formats']
        
        # Update each footer number format that has a matching column ID
        for column_id, format_info in format_lookup.items():
            # Use the same structure as column_id_styles
            footer_number_formats[column_id] = {
                'number_format': format_info.excel_format
            }
            print(f"[FOOTER_FORMAT] Updated {sheet_name} footer: {column_id} with format: {format_info.excel_format}")
    
    def validate_number_formats(self, number_formats: List[NumberFormatInfo]) -> List[str]:
        """
        Validate number format information.
        
        Args:
            number_formats: List of number format information to validate
            
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        
        for fmt in number_formats:
            if not fmt.column_id or not fmt.excel_format:
                errors.append(f"Invalid number format: {fmt}")
                
        return errors
