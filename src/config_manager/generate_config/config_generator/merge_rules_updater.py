"""
MergeRulesUpdater component for extracting and updating cell merging rules.

This module provides functionality to extract cell merging patterns from Excel analysis data
and update configuration templates with the actual merge rules used in the source Excel files.
"""

from typing import Dict, List, Any, Optional
import copy
from .models import QuantityAnalysisData, SheetData
from .mapping_manager import MappingManager, MappingManagerError


class MergeRulesUpdaterError(Exception):
    """Custom exception for MergeRulesUpdater errors."""
    pass


class MergeRulesUpdater:
    """Extracts and updates cell merging rules in configuration templates."""
    
    def __init__(self, mapping_config_path: str = "mapping_config.json"):
        """Initialize MergeRulesUpdater with mapping manager."""
        # Initialize mapping manager
        try:
            self.mapping_manager = MappingManager(mapping_config_path)
        except MappingManagerError as e:
            print(f"Warning: Could not load mapping config: {e}")
            self.mapping_manager = None
    
    def update_data_cell_merging_rules(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update data_cell_merging_rule in configuration using actual Excel merge patterns.
        
        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing merge information
            
        Returns:
            Updated template with data_cell_merging_rule extracted from Excel
            
        Raises:
            MergeRulesUpdaterError: If template structure is invalid or update fails
        """
        print("🔍 [DEBUG] update_data_cell_merging_rules() method called!")
        
        try:
            if not isinstance(template, dict):
                raise MergeRulesUpdaterError("Template must be a dictionary")
            
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise MergeRulesUpdaterError("Quantity data must be QuantityAnalysisData instance")
            
            print(f"🔍 [DEBUG] Processing {len(quantity_data.sheets)} sheets for merge rules")
            
            # Create deep copy to avoid modifying original template
            updated_template = copy.deepcopy(template)
            
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
                
                print(f"🔍 [DEBUG] Extracting merge rules for {mapped_sheet_name}")
                
                # Extract merge rules from the sheet data
                merge_rules = self._extract_merge_rules_from_sheet(sheet_data, mapped_sheet_name)
                
                # Update the configuration with extracted merge rules
                if merge_rules:
                    sheet_config['data_cell_merging_rule'] = merge_rules
                    print(f"✅ [MERGE_RULES] Updated {mapped_sheet_name}: {merge_rules}")
                else:
                    print(f"⚠️ [MERGE_RULES] No merge rules found for {mapped_sheet_name}")
            
            return updated_template
            
        except Exception as e:
            if isinstance(e, MergeRulesUpdaterError):
                raise
            raise MergeRulesUpdaterError(f"Merge rules update failed: {str(e)}") from e
    
    def _extract_merge_rules_from_sheet(self, sheet_data: SheetData, sheet_name: str) -> Dict[str, Dict[str, int]]:
        """
        Extract cell merging rules from sheet data by analyzing merge patterns.
        
        Args:
            sheet_data: Sheet data containing merge information
            sheet_name: Name of the sheet for logging
            
        Returns:
            Dictionary mapping column identifiers to merge span information
        """
        merge_rules = {}
        
        # Check if sheet has merge data
        if not hasattr(sheet_data, 'merged_cells') or not sheet_data.merged_cells:
            print(f"[MERGE_RULES] No merge data found for {sheet_name}")
            return self._get_default_merge_rules(sheet_name)
        
        # Analyze merged cells to extract patterns
        for merge_info in sheet_data.merged_cells:
            if not isinstance(merge_info, dict):
                continue
                
            column_id = merge_info.get('column_id')
            rowspan = merge_info.get('rowspan', 1)
            colspan = merge_info.get('colspan', 1)
            
            if column_id and (rowspan > 1 or colspan > 1):
                merge_rule = {}
                
                if rowspan > 1:
                    merge_rule['rowspan'] = rowspan
                    
                if colspan > 1:
                    merge_rule['colspan'] = colspan
                
                if merge_rule:
                    merge_rules[column_id] = merge_rule
                    print(f"[MERGE_RULES] Found {column_id}: {merge_rule}")
        
        # Apply fallback merge rules if none found
        if not merge_rules:
            merge_rules = self._get_default_merge_rules(sheet_name)
            print(f"[MERGE_RULES] Applied default merge rules for {sheet_name}")
        
        return merge_rules
    
    def _get_default_merge_rules(self, sheet_name: str) -> Dict[str, Dict[str, int]]:
        """
        Get default merge rules based on sheet type and common patterns.
        
        Args:
            sheet_name: Name of the sheet
            
        Returns:
            Dictionary with default merge rule patterns
        """
        # Default merge rules based on common patterns
        default_rules = {}
        
        # Common merge patterns by sheet type
        if sheet_name == 'Invoice':
            # Invoice typically merges item descriptions across multiple rows
            default_rules = {
                'col_item': {'rowspan': 1},
                'col_description': {'rowspan': 1}
            }
        elif sheet_name == 'Contract':
            # Contract may merge product info across rows
            default_rules = {
                'col_product': {'rowspan': 1},
                'col_specification': {'rowspan': 1}
            }
        elif sheet_name == 'Packing list':
            # Packing list may merge package info
            default_rules = {
                'col_package': {'rowspan': 1},
                'col_contents': {'rowspan': 1}
            }
        
        print(f"[MERGE_RULES] Applied default rules: {default_rules}")
        return default_rules
    
    def _analyze_column_merge_patterns(self, sheet_data: SheetData, column_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Analyze merge patterns for specific column IDs.
        
        Args:
            sheet_data: Sheet data containing merge information
            column_ids: List of column identifiers to analyze
            
        Returns:
            Dictionary mapping column IDs to their merge patterns
        """
        merge_patterns = {}
        
        if not hasattr(sheet_data, 'merged_cells') or not sheet_data.merged_cells:
            return merge_patterns
        
        # Loop through each column ID to detect merging patterns
        for col_id in column_ids:
            col_merges = []
            
            # Find all merges for this column
            for merge_info in sheet_data.merged_cells:
                if isinstance(merge_info, dict) and merge_info.get('column_id') == col_id:
                    col_merges.append(merge_info)
            
            if col_merges:
                # Analyze the merge pattern for this column
                pattern = self._determine_merge_pattern(col_merges)
                if pattern:
                    merge_patterns[col_id] = pattern
                    print(f"[MERGE_PATTERNS] {col_id}: {pattern}")
        
        return merge_patterns
    
    def _determine_merge_pattern(self, merges: List[Dict[str, Any]]) -> Optional[Dict[str, int]]:
        """
        Determine the merge pattern from a list of merge operations.
        
        Args:
            merges: List of merge information dictionaries
            
        Returns:
            Dictionary with merge pattern (rowspan/colspan) or None
        """
        if not merges:
            return None
        
        # Find the most common merge pattern
        rowspans = []
        colspans = []
        
        for merge in merges:
            if isinstance(merge, dict):
                rowspan = merge.get('rowspan', 1)
                colspan = merge.get('colspan', 1)
                
                if rowspan > 1:
                    rowspans.append(rowspan)
                if colspan > 1:
                    colspans.append(colspan)
        
        pattern = {}
        
        # Use the most common rowspan
        if rowspans:
            most_common_rowspan = max(set(rowspans), key=rowspans.count)
            pattern['rowspan'] = most_common_rowspan
        
        # Use the most common colspan
        if colspans:
            most_common_colspan = max(set(colspans), key=colspans.count)
            pattern['colspan'] = most_common_colspan
        
        return pattern if pattern else None
    
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

    def update_data_cell_merging_col(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update data_cell_merging_rule section with colspan information from header_to_write.
        
        This method extracts all headers with colspan > 1 from header_to_write sections
        and adds corresponding entries to the existing data_cell_merging_rule for consistent document merging.
        
        Args:
            template: Configuration template dictionary (after header_text_updater processing)
            
        Returns:
            Updated template with data_cell_merging_rule enhanced with colspan data
            
        Raises:
            MergeRulesUpdaterError: If template structure is invalid
        """
        try:
            if not isinstance(template, dict):
                raise MergeRulesUpdaterError("Template must be a dictionary")
            
            print("🔍 [MERGE_RULES_UPDATER] Updating data_cell_merging_rule with colspan from header_to_write...")
            
            # Create deep copy to avoid modifying original template
            updated_template = copy.deepcopy(template)
            
            # Process each sheet in the template
            data_mapping = updated_template.get('data_mapping', {})
            
            for sheet_name, sheet_config in data_mapping.items():
                if not isinstance(sheet_config, dict):
                    continue
                
                print(f"🔍 [MERGE_RULES_UPDATER] Processing sheet: {sheet_name}")
                
                # Get header_to_write section
                headers_to_write = sheet_config.get('header_to_write', [])
                if not headers_to_write:
                    print(f"⚠️ [MERGE_RULES_UPDATER] No header_to_write found for {sheet_name}")
                    continue
                
                # Extract colspan information from headers
                colspan_rules = self._extract_colspan_from_headers(headers_to_write, sheet_name)
                
                # Update existing data_cell_merging_rule section
                if colspan_rules:
                    # Get existing data_cell_merging_rule or create new one
                    existing_merge_rules = sheet_config.get('data_cell_merging_rule', {})
                    
                    # Merge colspan rules with existing rules
                    for col_id, colspan_rule in colspan_rules.items():
                        if col_id in existing_merge_rules:
                            # Update existing rule with colspan
                            existing_merge_rules[col_id].update(colspan_rule)
                        else:
                            # Add new rule
                            existing_merge_rules[col_id] = colspan_rule
                    
                    sheet_config['data_cell_merging_rule'] = existing_merge_rules
                    print(f"✅ [MERGE_RULES_UPDATER] Updated {sheet_name} data_cell_merging_rule with colspan: {colspan_rules}")
                else:
                    print(f"ℹ️ [MERGE_RULES_UPDATER] No colspan rules found for {sheet_name}")
            
            return updated_template
            
        except Exception as e:
            if isinstance(e, MergeRulesUpdaterError):
                raise
            raise MergeRulesUpdaterError(f"Data cell merging rule update failed: {str(e)}") from e

    def _extract_colspan_from_headers(self, headers_to_write: List[Dict[str, Any]], sheet_name: str) -> Dict[str, Dict[str, int]]:
        """
        Extract colspan information from header_to_write entries.
        
        Args:
            headers_to_write: List of header dictionaries from header_to_write
            sheet_name: Name of the sheet for logging
            
        Returns:
            Dictionary mapping column IDs to their colspan rules in data_cell_merging_rule format
        """
        colspan_rules = {}
        
        for header in headers_to_write:
            if not isinstance(header, dict):
                continue
            
            # Get header properties
            header_id = header.get('id')
            colspan = header.get('colspan', 1)
            header_text = header.get('text', 'N/A')
            
            # Only include headers with colspan > 1 and valid ID
            if header_id and colspan > 1:
                colspan_rules[header_id] = {'rowspan': colspan}
                print(f"🎯 [MERGE_RULES_UPDATER] {sheet_name}: Found colspan rule '{header_text}' ({header_id}) → colspan: {colspan}")
        
        return colspan_rules