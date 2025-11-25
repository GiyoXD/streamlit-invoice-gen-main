"""
MappingManager component for handling sheet name and header text mappings.

This module provides centralized mapping management that can be configured
through external JSON files, allowing for easy customization of mappings
without code changes.
"""

import json
import os
from typing import Dict, Optional, List, Tuple
from difflib import SequenceMatcher


class MappingManagerError(Exception):
    """Custom exception for MappingManager errors."""
    pass


class MappingManager:
    """
    Manages sheet name and header text mappings with configurable fallback strategies.
    
    This class loads mapping configurations from JSON files and provides
    methods for mapping sheet names and header texts with fallback handling.
    """
    
    def __init__(self, mapping_config_path: str = "mapping_config.json"):
        """
        Initialize MappingManager with configuration file.
        
        Args:
            mapping_config_path: Path to the mapping configuration JSON file
        """
        self.mapping_config_path = mapping_config_path
        self.sheet_mappings = {}
        self.header_mappings = {}
        self.fallback_config = {}
        self.unrecognized_items = []
        
        # Load configuration
        self._load_mapping_config()
    
    def _load_mapping_config(self) -> None:
        """
        Load mapping configuration from JSON file.
        
        Raises:
            MappingManagerError: If configuration file cannot be loaded
        """
        try:
            if not os.path.exists(self.mapping_config_path):
                # Create default config if it doesn't exist
                self._create_default_config()
            
            with open(self.mapping_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load sheet name mappings
            sheet_config = config.get('sheet_name_mappings', {})
            self.sheet_mappings = sheet_config.get('mappings', {})
            
            # Load header text mappings
            header_config = config.get('header_text_mappings', {})
            self.header_mappings = header_config.get('mappings', {})
            
            # Load fallback configuration
            self.fallback_config = config.get('fallback_strategies', {})
            
        except json.JSONDecodeError as e:
            raise MappingManagerError(f"Invalid JSON in mapping config: {e}")
        except Exception as e:
            raise MappingManagerError(f"Error loading mapping config: {e}")
    
    def _create_default_config(self) -> None:
        """Create a default mapping configuration file."""
        default_config = {
            "sheet_name_mappings": {
                "comment": "Map quantity data sheet names to template config sheet names",
                "mappings": {
                    "INV": "Invoice",
                    "PAK": "Packing list",
                    "CON": "Contract"
                }
            },
            "header_text_mappings": {
                "comment": "Map header texts from quantity data to column IDs in template",
                "mappings": {
                    "Mark & Nº": "col_static",
                    "P.O Nº": "col_po",
                    "ITEM Nº": "col_item",
                    "Description": "col_desc",
                    "Quantity": "col_qty_sf",
                    "Unit price": "col_unit_price",
                    "Amount": "col_amount"
                }
            },
            "fallback_strategies": {
                "case_insensitive_matching": True,
                "partial_matching_threshold": 0.7,
                "log_unrecognized_items": True,
                "create_suggestions": True
            }
        }
        
        with open(self.mapping_config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def map_sheet_name(self, quantity_sheet_name: str) -> str:
        """
        Map quantity data sheet name to template config sheet name.
        
        Args:
            quantity_sheet_name: Sheet name from quantity data
            
        Returns:
            Mapped sheet name for template config, or original name if no mapping found
        """
        if not isinstance(quantity_sheet_name, str):
            return str(quantity_sheet_name)
        
        # Try exact match first
        if quantity_sheet_name in self.sheet_mappings:
            return self.sheet_mappings[quantity_sheet_name]
        
        # Try case-insensitive match if enabled
        if self.fallback_config.get('case_insensitive_matching', True):
            for mapped_name, target_name in self.sheet_mappings.items():
                if mapped_name.lower() == quantity_sheet_name.lower():
                    return target_name
        
        # Try partial matching if enabled
        if self.fallback_config.get('create_suggestions', True):
            suggestion = self._find_best_sheet_match(quantity_sheet_name)
            if suggestion:
                self._log_suggestion('sheet', quantity_sheet_name, suggestion)
        
        # Log unrecognized item
        if self.fallback_config.get('log_unrecognized_items', True):
            self.unrecognized_items.append(f"Sheet: {quantity_sheet_name}")
        
        # Return original name if no mapping found
        return quantity_sheet_name
    
    def map_header_to_column_id(self, header_text: str) -> Optional[str]:
        """
        Map header text to column ID using the header mappings.
        
        Args:
            header_text: Header text from quantity analysis
            
        Returns:
            Column ID string or None if no mapping found
        """
        if not isinstance(header_text, str):
            return None
        
        # Try exact match first
        if header_text in self.header_mappings:
            return self.header_mappings[header_text]
        
        # Try case-insensitive match if enabled
        if self.fallback_config.get('case_insensitive_matching', True):
            for mapped_header, column_id in self.header_mappings.items():
                if mapped_header.lower() == header_text.lower():
                    return column_id
        
        # Try partial matching if enabled
        threshold = self.fallback_config.get('partial_matching_threshold', 0.7)
        best_match = self._find_best_header_match(header_text, threshold)
        if best_match:
            return self.header_mappings[best_match]
        
        # Try pattern-based fallback
        pattern_match = self._pattern_based_header_matching(header_text)
        if pattern_match:
            return pattern_match
        
        # Log unrecognized item
        if self.fallback_config.get('log_unrecognized_items', True):
            self.unrecognized_items.append(f"Header: {header_text}")
        
        return None
    
    def _find_best_sheet_match(self, sheet_name: str) -> Optional[str]:
        """
        Find the best matching sheet name using similarity scoring.
        
        Args:
            sheet_name: Sheet name to match
            
        Returns:
            Best matching sheet name or None
        """
        threshold = self.fallback_config.get('partial_matching_threshold', 0.7)
        best_match = None
        best_score = 0
        
        for mapped_name in self.sheet_mappings.keys():
            score = SequenceMatcher(None, sheet_name.lower(), mapped_name.lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = mapped_name
        
        return best_match
    
    def _find_best_header_match(self, header_text: str, threshold: float) -> Optional[str]:
        """
        Find the best matching header text using similarity scoring.
        
        Args:
            header_text: Header text to match
            threshold: Minimum similarity threshold
            
        Returns:
            Best matching header text or None
        """
        best_match = None
        best_score = 0
        
        for mapped_header in self.header_mappings.keys():
            score = SequenceMatcher(None, header_text.lower(), mapped_header.lower()).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = mapped_header
        
        return best_match
    
    def _pattern_based_header_matching(self, header_text: str) -> Optional[str]:
        """
        Apply pattern-based matching for common header variations.
        
        Args:
            header_text: Header text to match
            
        Returns:
            Column ID if pattern matches, None otherwise
        """
        header_lower = header_text.lower().strip()
        
        # Pattern matching for common cases
        if 'mark' in header_lower and ('nº' in header_lower or 'n°' in header_lower or 'note' in header_lower):
            return 'col_static'
        elif 'p.o' in header_lower and ('nº' in header_lower or 'n°' in header_lower or 'no' in header_lower):
            return 'col_po'
        elif 'item' in header_lower and ('nº' in header_lower or 'n°' in header_lower):
            return 'col_item'
        elif 'description' in header_lower or 'desc' in header_lower:
            return 'col_desc'
        elif 'quantity' in header_lower or 'qty' in header_lower:
            return 'col_qty_sf'
        elif 'unit price' in header_lower or 'unit_price' in header_lower or 'price' in header_lower:
            return 'col_unit_price'
        elif 'amount' in header_lower or 'total' in header_lower:
            return 'col_amount'
        elif 'n.w' in header_lower and 'kg' in header_lower:
            return 'col_net'
        elif 'g.w' in header_lower and 'kg' in header_lower:
            return 'col_gross'
        elif header_lower == 'cbm' or '(cbm)' in header_lower:
            return 'col_cbm'
        elif header_lower == 'pcs':
            return 'col_qty_pcs'
        elif header_lower == 'sf':
            return 'col_qty_sf'
        elif 'hs code' in header_lower or 'hscode' in header_lower:
            return 'col_hs_code'
        
        return None
    
    def _log_suggestion(self, item_type: str, original: str, suggestion: str) -> None:
        """
        Log a mapping suggestion for manual review.
        
        Args:
            item_type: Type of item ('sheet' or 'header')
            original: Original text
            suggestion: Suggested mapping
        """
        suggestion_text = f"Suggestion: {item_type} '{original}' -> '{suggestion}'"
        self.unrecognized_items.append(suggestion_text)
    
    def get_unrecognized_items(self) -> List[str]:
        """
        Get list of unrecognized items and suggestions.
        
        Returns:
            List of unrecognized items and suggestions
        """
        return self.unrecognized_items.copy()
    
    def clear_unrecognized_items(self) -> None:
        """Clear the list of unrecognized items."""
        self.unrecognized_items.clear()
    
    def add_sheet_mapping(self, quantity_name: str, template_name: str) -> None:
        """
        Add a new sheet name mapping.
        
        Args:
            quantity_name: Sheet name from quantity data
            template_name: Sheet name in template config
        """
        self.sheet_mappings[quantity_name] = template_name
    
    def add_header_mapping(self, header_text: str, column_id: str) -> None:
        """
        Add a new header text mapping.
        
        Args:
            header_text: Header text from quantity data
            column_id: Column ID in template config
        """
        self.header_mappings[header_text] = column_id
    
    def save_mappings(self) -> None:
        """
        Save current mappings back to the configuration file.
        
        Raises:
            MappingManagerError: If saving fails
        """
        try:
            config = {
                "sheet_name_mappings": {
                    "comment": "Map quantity data sheet names to template config sheet names",
                    "mappings": self.sheet_mappings
                },
                "header_text_mappings": {
                    "comment": "Map header texts from quantity data to column IDs in template",
                    "mappings": self.header_mappings
                },
                "fallback_strategies": self.fallback_config
            }
            
            with open(self.mapping_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise MappingManagerError(f"Error saving mapping config: {e}")
    
    def generate_mapping_report(self, output_path: str = "mapping_report.txt") -> None:
        """
        Generate a report of unrecognized items for manual review.
        
        Args:
            output_path: Path to save the report
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Mapping Report\n")
                f.write("=" * 50 + "\n\n")
                
                if self.unrecognized_items:
                    f.write("Unrecognized Items and Suggestions:\n")
                    f.write("-" * 40 + "\n")
                    for item in self.unrecognized_items:
                        f.write(f"• {item}\n")
                    f.write("\n")
                else:
                    f.write("No unrecognized items found.\n\n")
                
                f.write("Current Sheet Mappings:\n")
                f.write("-" * 25 + "\n")
                for quantity_name, template_name in self.sheet_mappings.items():
                    f.write(f"'{quantity_name}' -> '{template_name}'\n")
                
                f.write(f"\nCurrent Header Mappings ({len(self.header_mappings)} total):\n")
                f.write("-" * 25 + "\n")
                for header_text, column_id in sorted(self.header_mappings.items()):
                    f.write(f"'{header_text}' -> '{column_id}'\n")
                
        except Exception as e:
            raise MappingManagerError(f"Error generating mapping report: {e}")