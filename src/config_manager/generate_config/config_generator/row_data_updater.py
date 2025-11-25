"""
RowDataUpdater component for updating start_row and row heights in configuration templates.

This module provides functionality to update start_row values and row heights in
header_to_write sections while preserving template structure.

NOTE: Column positions are now handled by HeaderLayoutUpdater.
"""

from typing import Dict, List, Any, Optional
import copy
from .models import QuantityAnalysisData, SheetData, HeaderPosition
from .mapping_manager import MappingManager, MappingManagerError


class RowDataUpdaterError(Exception):
    """Custom exception for RowDataUpdater errors."""
    pass


class RowDataUpdater:
    """Updates start_row and row heights in configuration templates."""
    
    def __init__(self, mapping_config_path: str = "mapping_config.json"):
        """Initialize RowDataUpdater with mapping manager."""
        # Start row mappings based on analysis data (Contract: 18, Invoice: 21, Packing list: 22)
        self.start_row_mappings = {
            'Contract': 18,
            'Invoice': 21,
            'Packing list': 22
        }
        
        # Initialize mapping manager
        try:
            self.mapping_manager = MappingManager(mapping_config_path)
        except MappingManagerError as e:
            print(f"Warning: Could not load mapping config: {e}")
            # Fallback to default mappings
            self.mapping_manager = None
    
    def update_positions(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update start_row values and row heights using analysis data.
        NOTE: Column positions are now handled by HeaderLayoutUpdater.
        
        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing position information
            
        Returns:
            Updated template with start_row and row heights updated
            
        Raises:
            RowDataUpdaterError: If template structure is invalid or update fails
        """
        # First update start rows
        updated_template = self.update_start_rows(template, quantity_data)
        
        # Then update row heights (column positions are handled by HeaderLayoutUpdater)
        updated_template = self.update_row_heights(updated_template, quantity_data)
        
        return updated_template
    
    def update_start_rows(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update start_row values using analysis data while preserving template structure.
        
        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing start row information
            
        Returns:
            Updated template with start_row values replaced
            
        Raises:
            RowDataUpdaterError: If template structure is invalid or update fails
        """
        try:
            if not isinstance(template, dict):
                raise RowDataUpdaterError("Template must be a dictionary")
            
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise RowDataUpdaterError("Quantity data must be QuantityAnalysisData instance")
            
            # Validate template structure
            self._validate_template_structure(template)
            
            # Create deep copy to avoid modifying original template
            updated_template = copy.deepcopy(template)
            
            # Process each sheet in the template
            data_mapping = updated_template.get('data_mapping', {})
            
            # Track sheets with missing start row data
            missing_start_row_sheets = []
            
            for sheet_data in quantity_data.sheets:
                quantity_sheet_name = sheet_data.sheet_name
                mapped_sheet_name = self._map_sheet_name(quantity_sheet_name)
                
                if mapped_sheet_name not in data_mapping:
                    missing_start_row_sheets.append(f"{quantity_sheet_name} -> {mapped_sheet_name}")
                    continue
                
                # Validate start row data
                self._validate_start_row_data(sheet_data, quantity_sheet_name)
                    
                sheet_config = data_mapping[mapped_sheet_name]
                
                # Validate sheet config structure
                if not isinstance(sheet_config, dict):
                    raise RowDataUpdaterError(f"Sheet config for '{mapped_sheet_name}' must be a dictionary")
                
                # Update start_row using analysis data
                sheet_config['start_row'] = sheet_data.start_row
            
            # Apply fallback strategies for missing start row data
            if missing_start_row_sheets:
                self._apply_start_row_fallback_strategies(updated_template, missing_start_row_sheets)
            
            return updated_template
            
        except Exception as e:
            if isinstance(e, RowDataUpdaterError):
                raise
            raise RowDataUpdaterError(f"Start row update failed: {str(e)}") from e
    
    def _apply_start_row_fallback_strategies(self, template: Dict[str, Any], missing_sheets: List[str]) -> None:
        """
        Apply fallback strategies for sheets with missing start row data.
        
        Args:
            template: Template dictionary to update
            missing_sheets: List of sheets that are missing start row data
        """
        print(f"[START_ROW_FALLBACK] Applying fallback strategies for {len(missing_sheets)} sheets")
        
        for sheet_info in missing_sheets:
            print(f"[START_ROW_FALLBACK] Missing start row data for: {sheet_info}")
            
            # Extract sheet name from mapping info (format: "quantity_name -> template_name")
            if " -> " in sheet_info:
                quantity_name, template_name = sheet_info.split(" -> ", 1)
            else:
                template_name = sheet_info
            
            # Apply default start row based on sheet type
            if template_name in self.start_row_mappings:
                default_start_row = self.start_row_mappings[template_name]
                if template_name in template.get('data_mapping', {}):
                    template['data_mapping'][template_name]['start_row'] = default_start_row
                    print(f"[START_ROW_FALLBACK] Applied default start_row {default_start_row} for {template_name}")
            else:
                print(f"[START_ROW_FALLBACK] No default mapping found for {template_name}")
    
    def _validate_template_structure(self, template: Dict[str, Any]) -> None:
        """
        Validate that the template has the required structure.
        
        Args:
            template: Template dictionary to validate
            
        Raises:
            RowDataUpdaterError: If template structure is invalid
        """
        required_keys = ['data_mapping']
        for key in required_keys:
            if key not in template:
                raise RowDataUpdaterError(f"Template missing required key: {key}")
        
        if not isinstance(template['data_mapping'], dict):
            raise RowDataUpdaterError("Template 'data_mapping' must be a dictionary")
    
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
    
    def _validate_start_row_data(self, sheet_data, sheet_name: str) -> None:
        """
        Validate start row data from quantity analysis.
        
        Args:
            sheet_data: Sheet data containing start row information
            sheet_name: Name of the sheet for error messages
            
        Raises:
            RowDataUpdaterError: If start row data is invalid
        """
        if not hasattr(sheet_data, 'start_row'):
            raise RowDataUpdaterError(f"Sheet '{sheet_name}' missing start_row data")
        
        if not isinstance(sheet_data.start_row, int) or sheet_data.start_row < 0:
            raise RowDataUpdaterError(f"Sheet '{sheet_name}' start_row must be a non-negative integer")
    
    def update_row_heights(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update row_heights in styling sections using actual Excel row heights.
        
        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing row height information
            
        Returns:
            Updated template with row_heights extracted from Excel
            
        Raises:
            RowDataUpdaterError: If template structure is invalid or update fails
        """
        print("🔍 [DEBUG] update_row_heights() method called!")
        
        try:
            if not isinstance(template, dict):
                raise RowDataUpdaterError("Template must be a dictionary")
            
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise RowDataUpdaterError("Quantity data must be QuantityAnalysisData instance")
            
            print(f"🔍 [DEBUG] Processing {len(quantity_data.sheets)} sheets for row heights")
            
            # Store Excel file path for height extraction
            self._excel_file_path = quantity_data.file_path
            print(f"📏 [HEIGHT_SETUP] Excel file path: {self._excel_file_path}")
            
            # Create deep copy to avoid modifying original template
            updated_template = copy.deepcopy(template)
            
            # Update footer configurations with correct total text column IDs
            self.update_footer_configurations(updated_template, quantity_data)
            
            # Process each sheet in the template
            data_mapping = updated_template.get('data_mapping', {})
            
            for sheet_data in quantity_data.sheets:
                quantity_sheet_name = sheet_data.sheet_name
                mapped_sheet_name = self._map_sheet_name(quantity_sheet_name)
                
                print(f"🔍 [DEBUG] Processing sheet: {quantity_sheet_name} -> {mapped_sheet_name}")
                
                if mapped_sheet_name not in data_mapping:
                    print(f"🔍 [DEBUG] Sheet {mapped_sheet_name} not found in data_mapping, skipping")
                    continue
                    
                sheet_config = data_mapping[mapped_sheet_name]
                
                print(f"🔍 [DEBUG] Extracting row heights for {mapped_sheet_name}")
                
                # Extract row heights from the sheet data
                row_heights = self._extract_row_heights_from_sheet(sheet_data, mapped_sheet_name)
                
                # Update the styling section with extracted row heights
                if 'styling' not in sheet_config:
                    sheet_config['styling'] = {}
                    print(f"🔍 [DEBUG] Created styling section for {mapped_sheet_name}")
                
                sheet_config['styling']['row_heights'] = row_heights
                
                print(f"✅ [ROW_HEIGHTS] Updated {mapped_sheet_name}: {row_heights}")
            
            return updated_template
            
        except Exception as e:
            if isinstance(e, RowDataUpdaterError):
                raise
            raise RowDataUpdaterError(f"Row height update failed: {str(e)}") from e
    
    def _extract_row_heights_from_sheet(self, sheet_data: SheetData, sheet_name: str) -> Dict[str, float]:
        """
        Extract row heights from sheet data using actual Excel row heights when possible.
        
        Args:
            sheet_data: Sheet data containing row height information
            sheet_name: Name of the sheet for logging
            
        Returns:
            Dictionary with row height information
        """
        row_heights = {}
        
        # Try to use actual Excel heights first
        excel_heights = self._get_actual_excel_heights(sheet_data, sheet_name)
        if excel_heights:
            row_heights.update(excel_heights)
            print(f"📏 [HEIGHT_EXCEL] Using actual Excel heights for {sheet_name}: {excel_heights}")
        else:
            # Fallback to font-based estimation
            print(f"📏 [HEIGHT_FALLBACK] Using font-based estimation for {sheet_name}")
            row_heights = self._get_font_based_heights(sheet_data, sheet_name)
        
        # Special case for Packing list - add before_footer height
        if sheet_name == 'Packing list':
            row_heights['before_footer'] = row_heights['data_default']
        
        print(f"[ROW_HEIGHTS] Extracted for {sheet_name}: header={row_heights['header']}, data={row_heights['data_default']}, footer={row_heights['footer']}")
        
        return row_heights
    
    def _get_actual_excel_heights(self, sheet_data: SheetData, sheet_name: str) -> Optional[Dict[str, float]]:
        """
        Get actual Excel row heights using ExcelHeightAnalyzer.
        
        Args:
            sheet_data: Sheet data containing row information
            sheet_name: Name of the sheet
            
        Returns:
            Dictionary with actual heights or None if Excel access fails
        """
        try:
            # Import here to avoid circular imports
            from .excel_height_analyzer import ExcelHeightAnalyzer
            
            # Get the Excel file path from quantity_data if available
            excel_file_path = getattr(sheet_data, 'excel_file_path', None)
            if not excel_file_path and hasattr(self, '_excel_file_path'):
                excel_file_path = self._excel_file_path
            
            if not excel_file_path:
                print(f"📏 [HEIGHT_EXCEL] No Excel file path available for {sheet_name}")
                return None
            
            analyzer = ExcelHeightAnalyzer(excel_file_path)
            
            # Get sheet structure
            structure = analyzer.analyze_sheet_structure(sheet_name)
            
            if structure['heights']:
                actual_heights = structure['heights']
                
                # Validate heights are within reasonable ranges
                validated_heights = self._validate_height_ranges(actual_heights, sheet_name)
                return validated_heights
            else:
                print(f"📏 [HEIGHT_EXCEL] Could not extract structure for {sheet_name}")
                return None
                
        except Exception as e:
            print(f"📏 [HEIGHT_EXCEL] Error accessing Excel heights for {sheet_name}: {e}")
            return None
    
    def _validate_height_ranges(self, heights: Dict[str, float], sheet_name: str) -> Dict[str, float]:
        """
        Validate and adjust height values to be within reasonable ranges.
        
        Args:
            heights: Dictionary of height values
            sheet_name: Name of the sheet for logging
            
        Returns:
            Dictionary with validated height values
        """
        validated = {}
        
        # Height validation ranges (expanded to accommodate real Excel files)
        ranges = {
            'header': (10, 80),      # Headers can be quite tall
            'data_default': (10, 60), # Data rows typically smaller
            'footer': (10, 70),      # Footers can be medium height
            'before_footer': (10, 60)
        }
        
        for key, value in heights.items():
            if key in ranges:
                min_val, max_val = ranges[key]
                if min_val <= value <= max_val:
                    validated[key] = value
                    print(f"📏 [HEIGHT_VALIDATION] {sheet_name} {key}: {value}pt ✅ VALID")
                else:
                    # Use the closest valid value
                    validated[key] = max(min_val, min(value, max_val))
                    print(f"📏 [HEIGHT_VALIDATION] {sheet_name} {key}: {value}pt -> {validated[key]}pt (clamped to range {min_val}-{max_val})")
            else:
                validated[key] = value
        
        return validated
    
    def _get_font_based_heights(self, sheet_data: SheetData, sheet_name: str) -> Dict[str, float]:
        """
        Get row heights based on font sizes (fallback method).
        
        Args:
            sheet_data: Sheet data containing font information
            sheet_name: Name of the sheet for logging
            
        Returns:
            Dictionary with font-based height estimates
        """
        row_heights = {}
        
        # Extract header row height (from the header font)
        if hasattr(sheet_data, 'header_font') and sheet_data.header_font:
            header_font_size = sheet_data.header_font.size
            # Rule of thumb: row height ≈ font size * 1.8 + padding for headers
            estimated_header_height = max(header_font_size * 1.8, 25)
            row_heights['header'] = round(estimated_header_height)
        else:
            row_heights['header'] = 30  # Default fallback
        
        # Extract data row height (from the data font)
        if hasattr(sheet_data, 'data_font') and sheet_data.data_font:
            data_font_size = sheet_data.data_font.size
            # Rule of thumb: data row height ≈ font size * 1.6 + padding for data
            estimated_data_height = max(data_font_size * 1.6, 20)
            row_heights['data_default'] = round(estimated_data_height)
        else:
            row_heights['data_default'] = 25  # Default fallback
        
        # Extract footer height (from actual footer font if available)
        if hasattr(sheet_data, 'footer_info') and sheet_data.footer_info:
            footer_font_size = sheet_data.footer_info.font.size
            # Footer with formulas (SUM) may need more height for readability
            if sheet_data.footer_info.has_formulas:
                # Formula rows need extra height for better visibility
                estimated_footer_height = max(footer_font_size * 2.0, 30)
                print(f"[FOOTER_DETECTION] {sheet_name}: Formula footer detected at row {sheet_data.footer_info.row}")
            else:
                # Regular footer height
                estimated_footer_height = max(footer_font_size * 1.8, 25)
            
            row_heights['footer'] = round(estimated_footer_height)
            print(f"[FOOTER_DETECTION] {sheet_name}: Footer font size {footer_font_size}, height {row_heights['footer']}")
        else:
            # Fallback: Use header height for footer (common pattern)
            row_heights['footer'] = row_heights['header']
            print(f"[FOOTER_DETECTION] {sheet_name}: No footer info found, using header height {row_heights['footer']}")
        
        return row_heights
    
    def update_footer_configurations(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> None:
        """
        Update footer configurations with correct total_text_column_id based on actual Excel footer analysis.
        
        Args:
            template: Template dictionary to update
            quantity_data: Processed quantity analysis data containing footer information
        """
        print("🔍 [FOOTER_CONFIG] Starting footer configuration updates...")
        
        data_mapping = template.get('data_mapping', {})
        
        for sheet_name, sheet_config in data_mapping.items():
            print(f"🔍 [FOOTER_CONFIG] Processing sheet: {sheet_name}")
            
            # Find corresponding sheet data
            sheet_data = None
            for data_sheet in quantity_data.sheets:
                if data_sheet.sheet_name == sheet_name:
                    sheet_data = data_sheet
                    break
            
            if not sheet_data:
                print(f"🔍 [FOOTER_CONFIG] Sheet '{sheet_name}' not found in quantity data, skipping")
                continue
            
            # Check if sheet has footer info with total text column or pallet count column
            footer_updates = {}
            
            # Handle total text column - now using raw index format
            if hasattr(sheet_data, 'footer_info') and sheet_data.footer_info and sheet_data.footer_info.total_text_column:
                total_text_column = sheet_data.footer_info.total_text_column
                total_text_value = sheet_data.footer_info.total_text_value
                
                print(f"📊 [FOOTER_CONFIG] Found total text '{total_text_value}' in column {total_text_column} for {sheet_name}")
                
                # Convert Excel column (1-based) to raw index (0-based)
                total_text_raw_index = total_text_column - 1
                
                footer_updates['total_text_column_id'] = total_text_raw_index
                footer_updates['total_text'] = total_text_value
                print(f"✅ [FOOTER_CONFIG] Will update {sheet_name}: total_text_column_id → {total_text_raw_index} (raw index)")
            
            # Handle pallet count column - now using raw index format
            if hasattr(sheet_data, 'footer_info') and sheet_data.footer_info and sheet_data.footer_info.pallet_count_column:
                pallet_count_column = sheet_data.footer_info.pallet_count_column
                pallet_count_value = sheet_data.footer_info.pallet_count_value
                
                print(f"📦 [FOOTER_CONFIG] Found pallet count '{pallet_count_value}' in column {pallet_count_column} for {sheet_name}")
                
                # Convert Excel column (1-based) to raw index (0-based)
                pallet_count_raw_index = pallet_count_column - 1
                
                footer_updates['pallet_count_column_id'] = pallet_count_raw_index
                print(f"✅ [FOOTER_CONFIG] Will update {sheet_name}: pallet_count_column_id → {pallet_count_raw_index} (raw index)")
            
            # Apply updates if any were found
            if footer_updates:
                footer_config = sheet_config.get('footer_configurations', {})
                
                for key, value in footer_updates.items():
                    old_value = footer_config.get(key, 'none')
                    footer_config[key] = value
                    print(f"✅ [FOOTER_CONFIG] Updated {sheet_name}: {key}: '{old_value}' → '{value}'")
            else:
                print(f"📊 [FOOTER_CONFIG] No footer updates needed for {sheet_name}")
