"""
HeaderTextUpdater component for updating header text values in configuration templates.

This module provides functionality to update header_to_write sections in configuration
templates with actual header text from quantity analysis data while preserving all
other attributes like positioning, spanning, and IDs.
"""

from typing import Dict, List, Any, Optional
import copy
from .models import QuantityAnalysisData, SheetData, HeaderPosition
from .mapping_manager import MappingManager, MappingManagerError


class HeaderTextUpdaterError(Exception):
    """Custom exception for HeaderTextUpdater errors."""
    pass


from pathlib import Path

class HeaderTextUpdater:
    """Updates header text values in header_to_write sections of configuration templates."""
    
    def __init__(self, mapping_config_path: str = "mapping_config.json"):
        """Initialize HeaderTextUpdater with mapping manager."""
        # Initialize mapping manager
        try:
            self.mapping_manager = MappingManager(str(mapping_config_path))
        except MappingManagerError as e:
            print(f"Warning: Could not load mapping config: {e}")
            # Fallback to default mappings
            self.mapping_manager = None
        
        # Fallback header text mapping for when mapping manager is not available
        self.fallback_header_mappings = {
            # Mark & Nº variations
            'Mark & Nº': 'col_static',
            'Mark & N°': 'col_static',
            
            # P.O Nº variations  
            'P.O Nº': 'col_po',
            'P.O. Nº': 'col_po',
            'P.O N°': 'col_po',
            'P.O. N°': 'col_po',
            'P.O. Nº': 'col_po2',  # Contract sheet variation - use different column
            
            # ITEM Nº variations
            'ITEM Nº': 'col_item',
            'ITEM N°': 'col_item',
            'HL ITEM': 'col_item',
            
            # Description variations - special case handling
            'Description': 'col_desc2',  # Contract sheet second description
            'Name of\nCormodity': 'col_desc',  # Contract sheet variation
            'Cargo Descprition': 'col_po',  # Special mapping per requirement 3.4
            
            # Quantity variations
            'Quantity': 'col_qty_sf',
            'Quantity\n(SF)': 'col_qty_sf',
            
            # Unit price variations
            'Unit price': 'col_unit_price',
            'Unit price (USD)': 'col_unit_price',
            'Unit price\n(USD)': 'col_unit_price',
            'Unit Price(USD)': 'col_unit_price',
            'FCA': 'col_unit_price',
            'FCA\nSVAY RIENG': 'col_unit_price',
            
            # Amount variations
            'Amount': 'col_amount',
            'Amount (USD)': 'col_amount',
            'Amount(USD)': 'col_amount',
            'Total value(USD)': 'col_amount',
            
            # Weight variations
            'N.W (kgs)': 'col_net',
            'G.W (kgs)': 'col_gross',
            
            # CBM variations
            'CBM': 'col_cbm',
            
            # Sub-header variations for quantity
            'PCS': 'col_qty_pcs',
            'SF': 'col_qty_sf',
            
            # Other common headers
            'No.': 'col_no',
            'Pallet\nNO.': 'col_pallet',
            'PALLET\nNO.': 'col_pallet',
            'REMARKS': 'col_remarks'
        }
    
    def update_header_texts(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData, interactive_mode: bool = False) -> Dict[str, Any]:
        """
        Update header text values in header_to_write sections using quantity analysis data.
        
        This method now generates header structures dynamically based on actual Excel data
        rather than trying to fit Excel data into predefined template structures.
        
        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing header positions
            interactive_mode: If True, enable interactive fallbacks for header mapping with user validation
            
        Returns:
            Updated template with header texts replaced
            
        Raises:
            HeaderTextUpdaterError: If template structure is invalid or update fails
        """
        try:
            if not isinstance(template, dict):
                raise HeaderTextUpdaterError("Template must be a dictionary")

            if not isinstance(quantity_data, QuantityAnalysisData):
                raise HeaderTextUpdaterError("Quantity data must be QuantityAnalysisData instance")

            # Validate template structure
            self._validate_template_structure(template)

            # Create deep copy to avoid modifying original template
            updated_template = copy.deepcopy(template)

            # Process each sheet in the template
            data_mapping = updated_template.get('data_mapping', {})

            # Track unrecognized headers for fallback strategies
            unrecognized_headers = []

            for sheet_data in quantity_data.sheets:
                quantity_sheet_name = sheet_data.sheet_name
                mapped_sheet_name = self._map_sheet_name(quantity_sheet_name)

                if mapped_sheet_name not in data_mapping:
                    # Log missing sheet but continue processing
                    continue
                    
                sheet_config = data_mapping[mapped_sheet_name]
                
                # CRITICAL CHANGE: Generate headers dynamically instead of updating template
                generated_headers = self._generate_headers_from_excel_data(
                    sheet_data.header_positions, mapped_sheet_name, interactive_mode
                )
                
                # Replace template headers with dynamically generated ones
                sheet_config['header_to_write'] = generated_headers

            return updated_template
            
        except Exception as e:
            if isinstance(e, HeaderTextUpdaterError):
                raise
            raise HeaderTextUpdaterError(f"Header text update failed: {str(e)}") from e

    def _generate_headers_from_excel_data(self, header_positions: List[HeaderPosition], sheet_name: str, interactive_mode: bool = False) -> List[Dict[str, Any]]:
        """
        Generate header_to_write structure dynamically from actual Excel header data.
        
        This replaces the template-based approach with a data-driven approach.
        Properly handles multi-row headers by detecting row patterns and creating appropriate structure.
        
        Args:
            header_positions: Header positions from quantity analysis
            sheet_name: Name of the sheet being processed
            interactive_mode: If True, enable interactive fallbacks for header mapping with user validation
            
        Returns:
            List of header entries generated from actual Excel data
        """
        generated_headers = []
        unrecognized_headers = []
        
        if not header_positions:
            return generated_headers
        
        # Group headers by their actual row numbers
        headers_by_row = {}
        for i, header_pos in enumerate(header_positions):
            if not isinstance(header_pos, HeaderPosition):
                continue
                
            keyword = header_pos.keyword
            if not keyword or not isinstance(keyword, str):
                continue
            
            actual_row = header_pos.row
            actual_col = header_pos.column
            
            if actual_row not in headers_by_row:
                headers_by_row[actual_row] = []
            
            headers_by_row[actual_row].append({
                'keyword': keyword,
                'excel_row': actual_row,
                'excel_col': actual_col,
                'index': i
            })
        
        # Sort rows to process in order
        sorted_rows = sorted(headers_by_row.keys())
        
        # Check if we have multi-row headers
        has_multi_row = len(sorted_rows) > 1
        print(f"[DEBUG] Sheet {sheet_name}: has_multi_row={has_multi_row}, rows={sorted_rows}")
        
        if has_multi_row:
            print(f"[INFO] Detected multi-row headers in {sheet_name}: rows {sorted_rows}")
            
            # Process first row headers
            first_row_headers = headers_by_row[sorted_rows[0]]
            second_row_headers = headers_by_row.get(sorted_rows[1], []) if len(sorted_rows) > 1 else []
            
            # Create a map of second row column positions to find parent headers
            second_row_cols = {h['excel_col'] for h in second_row_headers}
            
            # Remove duplicates from second row (same column, same keyword)
            unique_second_row = {}
            for h in second_row_headers:
                key = (h['excel_col'], h['keyword'])
                if key not in unique_second_row:
                    unique_second_row[key] = h
            second_row_headers = list(unique_second_row.values())
            
            # Sort second row headers by Excel column position
            second_row_headers = sorted(second_row_headers, key=lambda h: h['excel_col'])
            
            # Identify which first-row headers should become parent headers with colspan
            first_row_cols = {h['excel_col'] for h in first_row_headers}
            
            # Sort first row headers by Excel column position to ensure correct ordering
            first_row_headers = sorted(first_row_headers, key=lambda h: h['excel_col'])
            debug_info = [f"{h['keyword']} (col {h['excel_col']})" for h in first_row_headers]
            print(f"[DEBUG] First row headers after sorting: {debug_info}")
            
            # Process first row headers
            for i, header_info in enumerate(first_row_headers):
                keyword = header_info['keyword']
                excel_col = header_info['excel_col']
                
                column_id = self.map_header_to_column_id(keyword, strict_mode=not interactive_mode)
                
                if column_id:
                    # Check if there are second-row headers that should be under this one
                    # Look for headers in columns directly under this column
                    child_headers = [h for h in second_row_headers if h['excel_col'] == excel_col]
                    
                    if child_headers:
                        # This should be a parent header with colspan
                        # Count consecutive child columns starting from this position
                        consecutive_children = []
                        for col_offset in range(2):  # Check this column and next
                            child = next((h for h in second_row_headers if h['excel_col'] == excel_col + col_offset), None)
                            if child:
                                consecutive_children.append(child)
                            else:
                                break
                        
                        if len(consecutive_children) > 1:
                            header_entry = {
                                "row": 0,
                                "col": excel_col - 1,  # Convert to 0-based indexing using actual Excel column
                                "text": keyword,
                                "colspan": len(consecutive_children)
                            }
                            print(f"[INFO] Generated parent header for '{keyword}' at col {excel_col - 1} with colspan={len(consecutive_children)}")
                        else:
                            # Regular header with rowspan=2 to span both rows
                            header_entry = {
                                "row": 0,
                                "col": excel_col - 1,  # Convert to 0-based indexing using actual Excel column
                                "text": keyword,
                                "id": column_id,
                                "rowspan": 2
                            }
                            print(f"[INFO] Generated spanning header for '{keyword}' → {column_id} at col {excel_col - 1}")
                    else:
                        # Regular header with rowspan=2 to span both rows
                        header_entry = {
                            "row": 0,
                            "col": excel_col - 1,  # Convert to 0-based indexing using actual Excel column
                            "text": keyword,
                            "id": column_id,
                            "rowspan": 2
                        }
                        print(f"[INFO] Generated spanning header for '{keyword}' → {column_id} at col {excel_col - 1}")
                    
                    generated_headers.append(header_entry)
                else:
                    unrecognized_headers.append(f"{sheet_name}:{keyword}")
                    print(f"[WARNING] Unrecognized header '{keyword}' in sheet '{sheet_name}' - skipping")
            
            # Process second row headers (unique only)
            for header_info in second_row_headers:
                keyword = header_info['keyword']
                excel_col = header_info['excel_col']
                
                column_id = self.map_header_to_column_id(keyword, strict_mode=not interactive_mode)
                
                if column_id:
                    # Find the sequential position by matching with first row headers
                    sequential_col = None
                    for i, first_header in enumerate(first_row_headers):
                        if first_header['excel_col'] == excel_col:
                            sequential_col = i
                            break
                    
                    # If not found under a first row header, use the excel column logic
                    if sequential_col is None:
                        sequential_col = excel_col - 1
                    
                    header_entry = {
                        "row": 1,  # Second row
                        "col": sequential_col,  # Use sequential position
                        "text": keyword,
                        "id": column_id
                    }
                    generated_headers.append(header_entry)
                    print(f"[INFO] Generated second-row header for '{keyword}' → {column_id} at row 1, col {sequential_col}")
                else:
                    unrecognized_headers.append(f"{sheet_name}:{keyword}")
                    print(f"[WARNING] Unrecognized second-row header '{keyword}' in sheet '{sheet_name}' - skipping")
        else:
            # Single row headers - use the original logic
            for i, header_pos in enumerate(header_positions):
                if not isinstance(header_pos, HeaderPosition):
                    continue
                    
                keyword = header_pos.keyword
                if not keyword or not isinstance(keyword, str):
                    continue
                    
                column_id = self.map_header_to_column_id(keyword, strict_mode=not interactive_mode)
                
                if column_id:
                    header_entry = {
                        "row": 0,
                        "col": i,
                        "text": keyword,
                        "id": column_id,
                        "rowspan": 1
                    }
                    generated_headers.append(header_entry)
                    print(f"[INFO] Generated header for '{keyword}' → {column_id} at position {i}")
                else:
                    unrecognized_headers.append(f"{sheet_name}:{keyword}")
                    print(f"[WARNING] Unrecognized header '{keyword}' in sheet '{sheet_name}' - skipping")
        
        if unrecognized_headers:
            print(f"[WARNING] Unrecognized headers: {unrecognized_headers}")
            
        return generated_headers
    
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
    
    def _update_sheet_headers_with_fallback(self, header_to_write: List[Dict[str, Any]], 
                                           header_positions: List[HeaderPosition], sheet_name: str) -> List[str]:
        """
        Update header texts for a single sheet with fallback handling.
        
        Args:
            header_to_write: List of header entries to update
            header_positions: Header positions from quantity analysis
            sheet_name: Name of the sheet being processed
            
        Returns:
            List of unrecognized header keywords
        """
        try:
            # Validate inputs
            if not isinstance(header_to_write, list):
                raise HeaderTextUpdaterError(f"header_to_write for sheet '{sheet_name}' must be a list")
            
            if not isinstance(header_positions, list):
                raise HeaderTextUpdaterError(f"header_positions for sheet '{sheet_name}' must be a list")
            
            # Create mapping of column IDs to actual header texts from analysis data
            column_id_to_text = {}
            unrecognized_headers = []
            
            for i, header_pos in enumerate(header_positions):
                if not isinstance(header_pos, HeaderPosition):
                    raise HeaderTextUpdaterError(f"header_position {i} for sheet '{sheet_name}' must be HeaderPosition instance")
                
                keyword = header_pos.keyword
                if not keyword or not isinstance(keyword, str):
                    continue  # Skip invalid keywords
                
                column_id = self.map_header_to_column_id(keyword, strict_mode=True)
                
                if column_id:
                    column_id_to_text[column_id] = keyword
                else:
                    unrecognized_headers.append(f"{sheet_name}:{keyword}")
            
            # Update header_to_write entries with actual header texts and remove non-existent ones
            headers_to_keep = []
            
            for i, header_entry in enumerate(header_to_write):
                if not isinstance(header_entry, dict):
                    raise HeaderTextUpdaterError(f"header_entry {i} for sheet '{sheet_name}' must be a dictionary")
                
                # Check if this header has an ID and exists in actual data
                if 'id' in header_entry:
                    header_id = header_entry['id']
                    
                    if header_id in column_id_to_text:
                        # Header exists in actual data - update text and keep it
                        if 'text' not in header_entry:
                            raise HeaderTextUpdaterError(f"header_entry {i} for sheet '{sheet_name}' missing 'text' field")
                        
                        # Update text while preserving all other attributes
                        header_entry['text'] = column_id_to_text[header_id]
                        headers_to_keep.append(header_entry)
                    else:
                        # Header doesn't exist in actual data - remove it
                        try:
                            print(f"[INFO] Removing header '{header_entry.get('text', 'unknown')}' (id: {header_id}) from sheet '{sheet_name}' - not found in actual data")
                        except UnicodeEncodeError:
                            print(f"[INFO] Removing header (id: {header_id}) from sheet '{sheet_name}' - not found in actual data")
                else:
                    # Header without ID (parent headers with colspan) - keep them
                    headers_to_keep.append(header_entry)
            
            # CRITICAL FIX: Don't modify original template - work on copy only
            # Replace the original list with filtered headers
            header_to_write.clear()
            header_to_write.extend(headers_to_keep)
            
            return unrecognized_headers
            
        except Exception as e:
            if isinstance(e, HeaderTextUpdaterError):
                raise
            raise HeaderTextUpdaterError(f"Failed to update headers for sheet '{sheet_name}': {str(e)}") from e
    
    def _update_sheet_headers(self, header_to_write: List[Dict[str, Any]], header_positions: List[HeaderPosition]) -> None:
        """
        Update header texts for a single sheet (legacy method for backward compatibility).
        
        Args:
            header_to_write: List of header entries to update
            header_positions: Header positions from quantity analysis
        """
        self._update_sheet_headers_with_fallback(header_to_write, header_positions, "unknown")
    
    def map_header_to_column_id(self, header_text: str, strict_mode: bool = True) -> Optional[str]:
        """
        Map header text to column ID using exact mappings only (strict mode) or with fallbacks (interactive mode).
        
        Args:
            header_text: Header text from quantity analysis
            strict_mode: If True, only use exact mappings. If False, use fuzzy matching and patterns.
            
        Returns:
            Column ID string or None if no mapping found
        """
        if not isinstance(header_text, str):
            return None
        
        # Use mapping manager if available - always try exact match first
        if self.mapping_manager:
            mapped_id = self.mapping_manager.map_header_to_column_id(header_text)
            if mapped_id:
                return mapped_id
        
        # Try exact match from fallback mappings
        if header_text in self.fallback_header_mappings:
            return self.fallback_header_mappings[header_text]
        
        # STRICT MODE: Only use exact mappings (for production config generation)
        if strict_mode:
            print(f"[STRICT] No exact mapping found for header '{header_text}' - skipping")
            print(f"[HINT] Add mapping with: python generate_config/add_mapping.py --add-header \"{header_text}:col_id\"")
            return None
        
        # INTERACTIVE MODE: Use fuzzy matching and patterns (requires user validation)
        print(f"[INTERACTIVE] Trying fallback matching for header '{header_text}'...")
        
        # Normalize header text for fuzzy matching
        normalized_header = self._normalize_header_text(header_text)
        
        # Try fuzzy matching with normalized text
        best_match = self._find_best_fuzzy_match(normalized_header)
        if best_match:
            print(f"[FUZZY] Found potential match: '{header_text}' → {best_match}")
            if self._confirm_mapping_with_user(header_text, best_match, "fuzzy matching"):
                return best_match
        
        # Smart pattern matching with flexible rules
        pattern_match = self._smart_pattern_matching(normalized_header, header_text)
        if pattern_match:
            print(f"[PATTERN] Found potential match: '{header_text}' → {pattern_match}")
            if self._confirm_mapping_with_user(header_text, pattern_match, "pattern matching"):
                return pattern_match
        
        # No automatic suggestions - ask user for manual mapping
        return self._ask_user_for_mapping(header_text)
    
    def _normalize_header_text(self, header_text: str) -> str:
        """
        Normalize header text for better matching by removing special characters and formatting.
        
        Args:
            header_text: Original header text
            
        Returns:
            Normalized header text
        """
        import re
        
        # Convert to lowercase
        normalized = header_text.lower().strip()
        
        # Replace common special characters and variations
        replacements = {
            'nº': 'no',
            'n°': 'no',
            'º': 'o',
            '°': 'o',
            '\n': ' ',
            '\r': ' ',
            '\t': ' ',
            '.': '',
            '&': 'and',
            '(': '',
            ')': '',
            '[': '',
            ']': '',
            '{': '',
            '}': '',
            '/': ' ',
            '\\': ' ',
            '-': ' ',
            '_': ' ',
            ':': '',
            ';': '',
            ',': '',
            '!': '',
            '?': '',
            '"': '',
            "'": '',
            '`': ''
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces and normalize
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _find_best_fuzzy_match(self, normalized_header: str) -> Optional[str]:
        """
        Find the best fuzzy match for a normalized header.
        
        Args:
            normalized_header: Normalized header text
            
        Returns:
            Column ID if good match found, None otherwise
        """
        # Create normalized versions of all known headers
        normalized_mappings = {}
        for header, col_id in self.fallback_header_mappings.items():
            norm_key = self._normalize_header_text(header)
            normalized_mappings[norm_key] = col_id
        
        # Try exact match on normalized text
        if normalized_header in normalized_mappings:
            return normalized_mappings[normalized_header]
        
        # Try partial matching with high confidence
        for norm_key, col_id in normalized_mappings.items():
            if self._calculate_similarity(normalized_header, norm_key) > 0.8:
                return col_id
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple similarity based on common words and characters
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            # Character-based similarity for short strings
            common_chars = sum(1 for c in text1 if c in text2)
            max_len = max(len(text1), len(text2))
            return common_chars / max_len if max_len > 0 else 0.0
        
        # Word-based similarity
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        word_similarity = len(common_words) / len(total_words) if total_words else 0.0
        
        # Character-based similarity as backup
        common_chars = sum(1 for c in text1 if c in text2)
        max_len = max(len(text1), len(text2))
        char_similarity = common_chars / max_len if max_len > 0 else 0.0
        
        # Weighted combination
        return (word_similarity * 0.7) + (char_similarity * 0.3)
    
    def _smart_pattern_matching(self, normalized_header: str, original_header: str) -> Optional[str]:
        """
        Smart pattern matching for headers using flexible rules.
        
        Args:
            normalized_header: Normalized header text
            original_header: Original header text
            
        Returns:
            Column ID if pattern matches, None otherwise
        """
        # Define flexible patterns with multiple variations
        patterns = {
            'col_static': [
                ['mark', 'no'], ['mark', 'number'], ['mark', 'num']
            ],
            'col_po': [
                ['po', 'no'], ['po', 'number'], ['po', 'num'], 
                ['purchase', 'order'], ['p', 'o'], ['pon']
            ],
            'col_item': [
                ['item', 'no'], ['item', 'number'], ['item', 'num'],
                ['hl', 'item'], ['item']
            ],
            'col_desc': [
                ['description'], ['desc'], ['commodity'], ['name', 'commodity'],
                ['cargo', 'description'], ['product', 'description']
            ],
            'col_qty_sf': [
                ['quantity', 'sf'], ['qty', 'sf'], ['quantity'], ['qty']
            ],
            'col_qty_pcs': [
                ['quantity', 'pcs'], ['qty', 'pcs'], ['pcs'], ['pieces']
            ],
            'col_unit_price': [
                ['unit', 'price'], ['price', 'unit'], ['unit', 'cost'],
                ['price'], ['fca'], ['unit']
            ],
            'col_amount': [
                ['amount'], ['total', 'value'], ['total', 'amount'],
                ['value'], ['total']
            ],
            'col_no': [
                ['no'], ['number'], ['num'], ['seq'], ['sequence']
            ],
            'col_net': [
                ['net', 'weight'], ['nw'], ['n', 'w'], ['net']
            ],
            'col_gross': [
                ['gross', 'weight'], ['gw'], ['g', 'w'], ['gross']
            ],
            'col_cbm': [
                ['cbm'], ['cubic', 'meter'], ['volume']
            ],
            'col_pallet': [
                ['pallet'], ['pallet', 'no'], ['pallet', 'number']
            ],
            'col_remarks': [
                ['remarks'], ['remark'], ['note'], ['notes'], ['comment']
            ]
        }
        
        # Check each pattern
        for col_id, pattern_groups in patterns.items():
            for pattern_words in pattern_groups:
                if self._matches_pattern(normalized_header, pattern_words):
                    return col_id
        
        # Log unrecognized header for user review
        print(f"[WARNING] Unrecognized header: '{original_header}' (normalized: '{normalized_header}')")
        print(f"[HINT] You can add custom mapping in mapping_config.json")
        
        return None
    
    def _matches_pattern(self, normalized_header: str, pattern_words: list) -> bool:
        """
        Check if normalized header matches a pattern of words.
        
        Args:
            normalized_header: Normalized header text
            pattern_words: List of words that should be present
            
        Returns:
            True if pattern matches
        """
        header_words = normalized_header.split()
        
        # All pattern words should be present (flexible order)
        for pattern_word in pattern_words:
            found = False
            for header_word in header_words:
                if pattern_word in header_word or header_word in pattern_word:
                    found = True
                    break
            if not found:
                return False
        
        return True
    
    def _validate_template_structure(self, template: Dict[str, Any]) -> None:
        """
        Validate template structure for header text updates.
        
        Args:
            template: Template dictionary to validate
            
        Raises:
            HeaderTextUpdaterError: If template structure is invalid
        """
        if 'data_mapping' not in template:
            raise HeaderTextUpdaterError("Template missing 'data_mapping' section")
        
        data_mapping = template['data_mapping']
        if not isinstance(data_mapping, dict):
            raise HeaderTextUpdaterError("Template 'data_mapping' must be a dictionary")
        
        # Validate each sheet configuration has header_to_write
        for sheet_name, sheet_config in data_mapping.items():
            if not isinstance(sheet_config, dict):
                raise HeaderTextUpdaterError(f"Sheet config for '{sheet_name}' must be a dictionary")
            
            if 'header_to_write' not in sheet_config:
                raise HeaderTextUpdaterError(f"Sheet '{sheet_name}' missing 'header_to_write' section")
            
            header_to_write = sheet_config['header_to_write']
            if not isinstance(header_to_write, list):
                raise HeaderTextUpdaterError(f"'header_to_write' for sheet '{sheet_name}' must be a list")
    
    def _apply_fallback_strategies(self, template: Dict[str, Any], unrecognized_headers: List[str]) -> None:
        """
        Apply fallback strategies for unrecognized headers.
        
        Args:
            template: Template dictionary to update
            unrecognized_headers: List of unrecognized header strings in format "sheet:header"
        """
        if not unrecognized_headers:
            return
        
        # Log unrecognized headers for manual review
        # In a production system, this could write to a log file or send alerts
        try:
            print(f"Warning: Unrecognized headers found: {unrecognized_headers}")
        except UnicodeEncodeError:
            print(f"Warning: Unrecognized headers found: {len(unrecognized_headers)} items")
        
        # Apply position-based fallback mapping
        data_mapping = template.get('data_mapping', {})
        
        for unrecognized in unrecognized_headers:
            if ':' not in unrecognized:
                continue
                
            sheet_name, header_text = unrecognized.split(':', 1)
            
            if sheet_name not in data_mapping:
                continue
            
            # Try position-based fallback
            self._apply_position_based_fallback(data_mapping[sheet_name], header_text)
    
    def _apply_position_based_fallback(self, sheet_config: Dict[str, Any], header_text: str) -> None:
        """
        Apply position-based fallback for unrecognized headers.
        
        Args:
            sheet_config: Sheet configuration dictionary
            header_text: Unrecognized header text
        """
        header_to_write = sheet_config.get('header_to_write', [])
        
        # Find headers without IDs (parent headers) and try to match by position
        for header_entry in header_to_write:
            if 'id' not in header_entry and 'text' in header_entry:
                # For parent headers, we can update text if it's similar
                existing_text = header_entry['text']
                if self._is_similar_header(existing_text, header_text):
                    header_entry['text'] = header_text
                    break
    
    def _is_similar_header(self, existing_text: str, new_text: str) -> bool:
        """
        Check if two header texts are similar enough to be considered the same.
        
        Args:
            existing_text: Existing header text
            new_text: New header text to compare
            
        Returns:
            True if headers are similar enough to match
        """
        if not isinstance(existing_text, str) or not isinstance(new_text, str):
            return False
        
        # Normalize both texts for comparison
        existing_norm = existing_text.lower().strip().replace(' ', '').replace('\n', '')
        new_norm = new_text.lower().strip().replace(' ', '').replace('\n', '')
        
        # Check for exact match after normalization
        if existing_norm == new_norm:
            return True
        
        # Check for partial matches (at least 70% similarity)
        if len(existing_norm) > 0 and len(new_norm) > 0:
            # Simple similarity check based on common characters
            common_chars = sum(1 for c in existing_norm if c in new_norm)
            similarity = common_chars / max(len(existing_norm), len(new_norm))
            return similarity >= 0.7
        
        return False
    
    def _confirm_mapping_with_user(self, header_text: str, suggested_column_id: str, match_type: str) -> bool:
        """
        Ask user to confirm a suggested mapping in interactive mode.
        
        Args:
            header_text: Original header text from Excel
            suggested_column_id: Suggested column ID to map to
            match_type: Type of matching used (e.g., "fuzzy matching", "pattern matching")
            
        Returns:
            True if user confirms the mapping, False otherwise
        """
        print(f"\n[INTERACTIVE] Found potential mapping via {match_type}:")
        print(f"  Excel Header: '{header_text}'")
        print(f"  Suggested Column ID: '{suggested_column_id}'")
        
        while True:
            response = input("Accept this mapping? (y/n/s to save permanently): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['s', 'save']:
                # Save the mapping permanently to mapping_config.json
                if self._save_mapping_to_config(header_text, suggested_column_id):
                    print(f"[SAVED] Mapping saved permanently: '{header_text}' → '{suggested_column_id}'")
                    return True
                else:
                    print("[ERROR] Failed to save mapping to config file")
                    return False
            else:
                print("Please enter 'y' for yes, 'n' for no, or 's' to save permanently")
    
    def _ask_user_for_mapping(self, header_text: str) -> Optional[str]:
        """
        Ask user to manually specify a column ID for an unknown header.
        
        Args:
            header_text: Header text that couldn't be automatically mapped
            
        Returns:
            Column ID specified by user, or None if user chooses to skip
        """
        print(f"\n[INTERACTIVE] No automatic mapping found for header: '{header_text}'")
        print("Available column IDs: col_po, col_item, col_dc, col_desc, col_quantity, col_unit_price, col_total_price, col_net_weight, col_gross_weight")
        print("Or enter 'skip' to ignore this header")
        
        while True:
            response = input("Enter column ID for this header (or 'skip'): ").lower().strip()
            if response == 'skip':
                return None
            elif response.startswith('col_'):
                # Validate that it's a known column ID
                valid_columns = ['col_po', 'col_item', 'col_desc', 'col_quantity', 'col_unit_price', 
                               'col_total_price', 'col_net_weight', 'col_gross_weight']
                if response in valid_columns:
                    # Ask if user wants to save this mapping permanently
                    save_response = input(f"Save this mapping permanently? (y/n): ").lower().strip()
                    if save_response in ['y', 'yes']:
                        if self._save_mapping_to_config(header_text, response):
                            print(f"[SAVED] Mapping saved permanently: '{header_text}' → '{response}'")
                    return response
                else:
                    print(f"Invalid column ID. Must be one of: {', '.join(valid_columns)}")
            else:
                print("Please enter a valid column ID (starting with 'col_') or 'skip'")
    
    def _save_mapping_to_config(self, header_text: str, column_id: str) -> bool:
        """
        Save a new header mapping to the mapping_config.json file.
        
        Args:
            header_text: Header text to add to mapping
            column_id: Column ID to map to
            
        Returns:
            True if successfully saved, False otherwise
        """
        try:
            import json
            import os
            
            # Path to mapping config file
            config_path = os.path.join(os.path.dirname(__file__), "..", "mapping_config.json")
            
            # Load existing config
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {"header_mappings": {}}
            
            # Ensure header_mappings section exists
            if "header_mappings" not in config:
                config["header_mappings"] = {}
            
            # Add the new mapping
            config["header_mappings"][header_text] = column_id
            
            # Save back to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save mapping to config: {e}")
            return False