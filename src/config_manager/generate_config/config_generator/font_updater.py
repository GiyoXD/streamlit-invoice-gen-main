"""
FontUpdater component for updating font information in configuration templates.

This module handles updating font information in styling sections of the configuration
template using font data extracted from quantity analysis data.
"""

import copy
from typing import Dict, Any
from .models import QuantityAnalysisData, FontInfo
from .mapping_manager import MappingManager, MappingManagerError


class FontUpdaterError(Exception):
    """Custom exception for FontUpdater errors."""
    pass


class FontUpdater:
    """Updates font information in configuration styling sections."""
    
    def __init__(self, mapping_config_path: str = "mapping_config.json"):
        """Initialize FontUpdater with mapping manager."""
        # Initialize mapping manager
        try:
            self.mapping_manager = MappingManager(mapping_config_path)
        except MappingManagerError as e:
            print(f"Warning: Could not load mapping config: {e}")
            # Fallback to default mappings
            self.mapping_manager = None
    
    def update_fonts(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update font information in the template configuration using quantity analysis data.
        
        Args:
            template: The configuration template dictionary
            quantity_data: Quantity analysis data containing font information
            
        Returns:
            Updated template with font information replaced
            
        Raises:
            FontUpdaterError: If template structure is invalid or font data is missing
        """
        try:
            if not isinstance(template, dict):
                raise FontUpdaterError("Template must be a dictionary")
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise FontUpdaterError("Quantity data must be a QuantityAnalysisData instance")
            
            # Validate template structure
            self._validate_template_structure(template)
            
            # Create a deep copy to avoid modifying the original template
            updated_template = copy.deepcopy(template)
            
            # Update fonts for each sheet in the template
            data_mapping = updated_template.get('data_mapping', {})
            
            # Track sheets with missing font data
            missing_font_sheets = []
            
            for sheet_name, sheet_config in data_mapping.items():
                # Find corresponding sheet data in quantity analysis
                sheet_data = self._find_sheet_data(quantity_data, sheet_name)
                if sheet_data is None:
                    missing_font_sheets.append(sheet_name)
                    continue
                
                # Validate font data before using
                self._validate_font_data(sheet_data, sheet_name)
                    
                # Update styling section if it exists
                styling = sheet_config.get('styling', {})
                if styling:
                    self._update_sheet_fonts_with_validation(styling, sheet_data.header_font, sheet_data.data_font, sheet_name)
                    
                # Update footer font information to match header font
                footer_config = sheet_config.get('footer_configurations', {})
                if footer_config:
                    # Ensure footer has style configuration that matches header font
                    self._ensure_footer_style_configuration(footer_config, sheet_data.header_font, sheet_name)
                    
                    # Update footer font if style exists
                    if 'style' in footer_config and 'font' in footer_config['style']:
                        self._update_footer_font_with_validation(footer_config['style']['font'], sheet_data.header_font, sheet_name)
            
            # Apply fallback strategies for missing font data
            if missing_font_sheets:
                self._apply_font_fallback_strategies(updated_template, missing_font_sheets, quantity_data)
            
            return updated_template
            
        except Exception as e:
            if isinstance(e, FontUpdaterError):
                raise
            raise FontUpdaterError(f"Font update failed: {str(e)}") from e
    
    def _map_sheet_name(self, quantity_sheet_name: str) -> str:
        """
        Map quantity data sheet name to template config sheet name.
        
        Args:
            quantity_sheet_name: Sheet name from quantity data
            
        Returns:
            Mapped sheet name for template config, or original name if no mapping found
        """
        if self.mapping_manager:
            return self.mapping_manager.map_sheet_name(quantity_sheet_name)
        
        # Fallback to hardcoded mappings if mapping manager is not available
        fallback_mappings = {
            'INV': 'Invoice',
            'PAK': 'Packing list',
            'CON': 'Contract',
            'CONTRACT': 'Contract',
            'INVOICE': 'Invoice',
            'PACKING': 'Packing list',
            'PACKING LIST': 'Packing list'
        }
        
        return fallback_mappings.get(quantity_sheet_name.upper(), quantity_sheet_name)
    
    def _find_sheet_data(self, quantity_data: QuantityAnalysisData, template_sheet_name: str):
        """Find sheet data for a given template sheet name in quantity analysis data."""
        # First try to find by mapped name (reverse lookup)
        if self.mapping_manager:
            # Use mapping manager for reverse lookup
            for sheet in quantity_data.sheets:
                mapped_name = self.mapping_manager.map_sheet_name(sheet.sheet_name)
                if mapped_name == template_sheet_name:
                    return sheet
        else:
            # Fallback to hardcoded mappings
            fallback_mappings = {
                'INV': 'Invoice',
                'PAK': 'Packing list',
                'CON': 'Contract',
                'CONTRACT': 'Contract',
                'INVOICE': 'Invoice',
                'PACKING': 'Packing list',
                'PACKING LIST': 'Packing list'
            }
            
            for quantity_sheet_name, mapped_name in fallback_mappings.items():
                if mapped_name == template_sheet_name:
                    # Look for the quantity sheet name
                    for sheet in quantity_data.sheets:
                        if sheet.sheet_name == quantity_sheet_name:
                            return sheet
        
        # If no mapping found, try direct match
        for sheet in quantity_data.sheets:
            if sheet.sheet_name == template_sheet_name:
                return sheet
        return None
    
    def _update_sheet_fonts(self, styling: Dict[str, Any], header_font: FontInfo, data_font: FontInfo) -> None:
        """
        Update header_font and default_font in a styling section.
        
        Args:
            styling: The styling dictionary to update
            header_font: Font information for headers
            data_font: Font information for data cells
        """
        # Update header font
        if 'header_font' in styling:
            styling['header_font']['name'] = header_font.name
            styling['header_font']['size'] = header_font.size
        
        # Update default font (data font)
        if 'default_font' in styling:
            styling['default_font']['name'] = data_font.name
            styling['default_font']['size'] = data_font.size
    
    def _update_footer_font(self, footer_font: Dict[str, Any], header_font: FontInfo) -> None:
        """
        Update footer font to match header font information.
        
        Args:
            footer_font: The footer font dictionary to update
            header_font: Font information for headers
        """
        footer_font['name'] = header_font.name
        footer_font['size'] = header_font.size
    
    def _validate_template_structure(self, template: Dict[str, Any]) -> None:
        """
        Validate template structure for font updates.
        
        Args:
            template: Template dictionary to validate
            
        Raises:
            FontUpdaterError: If template structure is invalid
        """
        if 'data_mapping' not in template:
            raise FontUpdaterError("Template missing 'data_mapping' section")
        
        data_mapping = template['data_mapping']
        if not isinstance(data_mapping, dict):
            raise FontUpdaterError("Template 'data_mapping' must be a dictionary")
        
        # Validate each sheet configuration has styling section
        for sheet_name, sheet_config in data_mapping.items():
            if not isinstance(sheet_config, dict):
                raise FontUpdaterError(f"Sheet config for '{sheet_name}' must be a dictionary")
            
            if 'styling' in sheet_config:
                styling = sheet_config['styling']
                if not isinstance(styling, dict):
                    raise FontUpdaterError(f"'styling' for sheet '{sheet_name}' must be a dictionary")
    
    def _validate_font_data(self, sheet_data, sheet_name: str) -> None:
        """
        Validate font data from quantity analysis.
        
        Args:
            sheet_data: Sheet data containing font information
            sheet_name: Name of the sheet for error messages
            
        Raises:
            FontUpdaterError: If font data is invalid
        """
        if not hasattr(sheet_data, 'header_font') or sheet_data.header_font is None:
            raise FontUpdaterError(f"Sheet '{sheet_name}' missing header_font data")
        
        if not hasattr(sheet_data, 'data_font') or sheet_data.data_font is None:
            raise FontUpdaterError(f"Sheet '{sheet_name}' missing data_font data")
        
        if not isinstance(sheet_data.header_font, FontInfo):
            raise FontUpdaterError(f"Sheet '{sheet_name}' header_font must be FontInfo instance")
        
        if not isinstance(sheet_data.data_font, FontInfo):
            raise FontUpdaterError(f"Sheet '{sheet_name}' data_font must be FontInfo instance")
    
    def _update_sheet_fonts_with_validation(self, styling: Dict[str, Any], header_font: FontInfo, 
                                          data_font: FontInfo, sheet_name: str) -> None:
        """
        Update header_font and default_font in a styling section with validation.
        
        Args:
            styling: The styling dictionary to update
            header_font: Font information for headers
            data_font: Font information for data cells
            sheet_name: Name of the sheet for error messages
            
        Raises:
            FontUpdaterError: If styling structure is invalid
        """
        try:
            # Update header font
            if 'header_font' in styling:
                if not isinstance(styling['header_font'], dict):
                    raise FontUpdaterError(f"header_font in styling for sheet '{sheet_name}' must be a dictionary")
                
                styling['header_font']['name'] = header_font.name
                styling['header_font']['size'] = header_font.size
            
            # Update default font (data font)
            if 'default_font' in styling:
                if not isinstance(styling['default_font'], dict):
                    raise FontUpdaterError(f"default_font in styling for sheet '{sheet_name}' must be a dictionary")
                
                styling['default_font']['name'] = data_font.name
                styling['default_font']['size'] = data_font.size
                
        except Exception as e:
            if isinstance(e, FontUpdaterError):
                raise
            raise FontUpdaterError(f"Failed to update fonts for sheet '{sheet_name}': {str(e)}") from e
    
    def _ensure_footer_style_configuration(self, footer_config: Dict[str, Any], 
                                         header_font: FontInfo, sheet_name: str) -> None:
        """
        Ensure footer configuration has style settings that match header font.
        Creates the style configuration if it doesn't exist.
        
        Args:
            footer_config: The footer configuration dictionary to update
            header_font: Font information for headers
            sheet_name: Name of the sheet for error messages
            
        Raises:
            FontUpdaterError: If footer configuration structure is invalid
        """
        try:
            if not isinstance(footer_config, dict):
                raise FontUpdaterError(f"footer_config for sheet '{sheet_name}' must be a dictionary")
            
            # Create style object if it doesn't exist
            if 'style' not in footer_config:
                footer_config['style'] = {}
            
            style_config = footer_config['style']
            
            # Create font object if it doesn't exist
            if 'font' not in style_config:
                style_config['font'] = {}
            
            font_config = style_config['font']
            
            # Set font properties to match header font
            font_config['name'] = header_font.name
            font_config['size'] = header_font.size
            font_config['bold'] = True  # Footer should be bold like header
            
            # Add default alignment and border if not present
            if 'alignment' not in style_config:
                style_config['alignment'] = {
                    'horizontal': 'center',
                    'vertical': 'center'
                }
            
            if 'border' not in style_config:
                style_config['border'] = {
                    'apply': True
                }
            
        except Exception as e:
            if isinstance(e, FontUpdaterError):
                raise
            raise FontUpdaterError(f"Failed to ensure footer style configuration for sheet '{sheet_name}': {str(e)}") from e
    
    def _update_footer_font_with_validation(self, footer_font: Dict[str, Any], 
                                          header_font: FontInfo, sheet_name: str) -> None:
        """
        Update footer font to match header font information with validation.
        
        Args:
            footer_font: The footer font dictionary to update
            header_font: Font information for headers
            sheet_name: Name of the sheet for error messages
            
        Raises:
            FontUpdaterError: If footer font structure is invalid
        """
        try:
            if not isinstance(footer_font, dict):
                raise FontUpdaterError(f"footer_font for sheet '{sheet_name}' must be a dictionary")
            
            footer_font['name'] = header_font.name
            footer_font['size'] = header_font.size
            
        except Exception as e:
            if isinstance(e, FontUpdaterError):
                raise
            raise FontUpdaterError(f"Failed to update footer font for sheet '{sheet_name}': {str(e)}") from e
    
    def _apply_font_fallback_strategies(self, template: Dict[str, Any], 
                                      missing_font_sheets: list, quantity_data: QuantityAnalysisData) -> None:
        """
        Apply fallback strategies for sheets with missing font data.
        
        Args:
            template: Template dictionary to update
            missing_font_sheets: List of sheet names missing font data
            quantity_data: Quantity analysis data
        """
        if not missing_font_sheets:
            return
        
        # Log missing font data for manual review
        print(f"Warning: Missing font data for sheets: {missing_font_sheets}")
        
        # For now, just log the missing sheets but don't apply fallback fonts
        # This preserves the original template fonts when no matching data is found
        # In a production system, this could be configured to apply fallbacks or not
    
    def _get_available_fonts(self, quantity_data: QuantityAnalysisData) -> Dict[str, FontInfo]:
        """
        Get available font data from quantity analysis.
        
        Args:
            quantity_data: Quantity analysis data
            
        Returns:
            Dictionary with available font information
        """
        available_fonts = {}
        
        for sheet in quantity_data.sheets:
            if hasattr(sheet, 'header_font') and sheet.header_font:
                available_fonts['header'] = sheet.header_font
            if hasattr(sheet, 'data_font') and sheet.data_font:
                available_fonts['data'] = sheet.data_font
            
            # Use first available fonts as fallback
            if 'header' in available_fonts and 'data' in available_fonts:
                break
        
        return available_fonts
    
    def _apply_default_fonts(self, sheet_config: Dict[str, Any], 
                           available_fonts: Dict[str, FontInfo], sheet_name: str) -> None:
        """
        Apply default fonts to a sheet configuration.
        
        Args:
            sheet_config: Sheet configuration dictionary
            available_fonts: Available font information
            sheet_name: Name of the sheet
        """
        styling = sheet_config.get('styling', {})
        if not styling:
            return
        
        try:
            # Apply header font if available
            if 'header' in available_fonts and 'header_font' in styling:
                header_font = available_fonts['header']
                styling['header_font']['name'] = header_font.name
                styling['header_font']['size'] = header_font.size
            
            # Apply data font if available
            if 'data' in available_fonts and 'default_font' in styling:
                data_font = available_fonts['data']
                styling['default_font']['name'] = data_font.name
                styling['default_font']['size'] = data_font.size
                
        except Exception as e:
            print(f"Warning: Failed to apply default fonts for sheet '{sheet_name}': {str(e)}")