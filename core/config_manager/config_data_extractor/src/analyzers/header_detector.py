"""
Header detection functionality for Excel analysis tool.

This module provides the HeaderDetector class that searches for specific header keywords
and determines the start row for data insertion.
"""

from typing import List, Optional, Dict
import json
import os
from pathlib import Path
from openpyxl.worksheet.worksheet import Worksheet
from models.data_models import HeaderMatch


class HeaderDetector:
    """Detects header keywords and calculates start row positions."""
    
    def __init__(self, quantity_mode: bool = False, mapping_config: Optional[Dict] = None):
        """Initialize the HeaderDetector.
        
        Args:
            quantity_mode: If True, adds PCS and SQFT columns for packing list sheets
            mapping_config: Optional mapping configuration dictionary
        """
        self.quantity_mode = quantity_mode
        self.mapping_config = mapping_config
        # We don't need header keywords anymore for the new logic, but keeping init clean
    
    def find_headers(self, worksheet: Worksheet) -> List[HeaderMatch]:
        """
        Search for the header row based on table width and content type.
        
        Logic:
        1. Find the row that extends to the highest column index (widest row) and contains only text.
        2. If multiple such rows exist, pick the one with the most filled columns.
        3. Check the row below for double header detection.
        
        Args:
            worksheet: The openpyxl worksheet to analyze
            
        Returns:
            List of HeaderMatch objects containing keyword, row, and column positions
        """
        header_matches = []
        
        # 1. Analyze all rows to find candidates
        max_rows_to_check = 50 # Limit search to first 50 rows
        candidates = []
        
        for row in worksheet.iter_rows(max_row=max_rows_to_check):
            # Get non-empty cells in this row
            non_empty_cells = [cell for cell in row if cell.value is not None and str(cell.value).strip()]
            
            if not non_empty_cells:
                continue
                
            # Check if row is a potential header (mostly text)
            if not self._is_potential_header_row(non_empty_cells):
                continue
                
            # Get the rightmost column index for this row
            max_col_index = max(cell.column for cell in non_empty_cells)
            
            candidates.append({
                'row_obj': row,
                'row_num': row[0].row,
                'max_col': max_col_index,
                'cell_count': len(non_empty_cells)
            })
            
        if not candidates:
            return []
            
        # 2. Find the max width among the CANDIDATES (not global max which might be data)
        max_candidate_width = max(c['max_col'] for c in candidates)
            
        # 3. Filter candidates that are close to the max CANDIDATE width
        # Allow a small tolerance (e.g., 1-2 columns less than max candidate width)
        width_tolerance = 2
        wide_candidates = [c for c in candidates if c['max_col'] >= (max_candidate_width - width_tolerance)]
        
        if not wide_candidates:
            # Fallback to any candidate if none are wide enough (shouldn't happen if logic is correct)
            wide_candidates = candidates
            
        # 4. Select the best candidate (most filled columns)
        # Sort by cell_count descending, then by row_num ascending (prefer top row if counts are equal)
        wide_candidates.sort(key=lambda x: (-x['cell_count'], x['row_num']))
        best_candidate = wide_candidates[0]
        header_row = best_candidate['row_num']
        
        # 5. Check for double header
        # Check row immediately below
        next_row_num = header_row + 1
        is_double = False
        
        if next_row_num <= worksheet.max_row:
            next_row_cells = [cell for cell in worksheet[next_row_num] if cell.value is not None and str(cell.value).strip()]
            if next_row_cells:
                # If next row has text, it's a double header
                # If it has numbers, it's data (so single header)
                if self._is_potential_header_row(next_row_cells):
                    is_double = True
        
        # 6. Extract headers
        if is_double:
            header_matches = self._extract_double_header(worksheet, header_row)
        else:
            header_matches = self._extract_all_headers_from_row(worksheet, header_row)
            
        # Apply quantity mode enhancement if enabled
        if self.quantity_mode:
            header_matches = self._apply_quantity_mode_enhancement(header_matches, worksheet)
            
        return header_matches

    def _is_potential_header_row(self, cells) -> bool:
        """
        Check if a row is a potential header row.
        Allows for a small percentage of numeric values (e.g. years '2024', column numbers '1', '2').
        Rejects rows that are primarily numeric (data rows).
        """
        if not cells:
            return False
            
        numeric_count = 0
        total_count = len(cells)
        
        import re
        
        for cell in cells:
            val = cell.value
            if val is None:
                continue
                
            is_numeric = False
            if isinstance(val, (int, float)):
                is_numeric = True
            else:
                s_val = str(val).strip()
                if s_val and re.match(r'^-?\d+(\.\d+)?$', s_val):
                    is_numeric = True
            
            if is_numeric:
                numeric_count += 1
        
        # Calculate numeric ratio
        numeric_ratio = numeric_count / total_count
        
        # If more than 30% of cells are numeric, it's likely a data row, not a header
        # Headers might have 1-2 numeric columns (like Year), but not the majority
        return numeric_ratio <= 0.3
    
    def calculate_start_row(self, header_positions: List[HeaderMatch]) -> int:
        """
        Calculate the start row where headers begin.
        
        Args:
            header_positions: List of HeaderMatch objects
            
        Returns:
            The row number where headers start (min_header_row)
        """
        if not header_positions:
            return 1  # Default to row 1 if no headers found
        
        # Find the minimum header row (where headers start)
        min_header_row = min(match.row for match in header_positions)
        return min_header_row
    
    def _extract_all_headers_from_row(self, worksheet: Worksheet, header_row: int) -> List[HeaderMatch]:
        """
        Extract all non-empty headers from the specified row.
        
        Args:
            worksheet: The openpyxl worksheet to analyze
            header_row: The row number containing headers
            
        Returns:
            List of HeaderMatch objects for all headers in the row
        """
        header_matches = []
        
        # Get the specific row and extract all non-empty cells
        for cell in worksheet[header_row]:
            if cell.value is not None:
                cell_value = str(cell.value).strip()
                if cell_value:  # Only include non-empty values
                    header_match = HeaderMatch(
                        keyword=cell_value,  # Use the actual cell value as the keyword
                        row=cell.row,
                        column=cell.column
                    )
                    header_matches.append(header_match)
        
        return header_matches
    
    def _apply_quantity_mode_enhancement(self, header_matches: List[HeaderMatch], worksheet: Worksheet) -> List[HeaderMatch]:
        """
        Apply quantity mode enhancement for packing list sheets.
        Adds PCS and SQFT columns after Quantity column.
        
        Args:
            header_matches: Original list of header matches
            worksheet: The worksheet being analyzed
            
        Returns:
            Enhanced list of header matches with PCS and SQFT columns
        """
        # Check if this is a packing list sheet
        sheet_name = worksheet.title.lower()
        if not any(keyword in sheet_name for keyword in ['packing', 'pkl', 'packing list']):
            return header_matches  # Not a packing list, return original
        
        # Find the Quantity column
        quantity_match = None
        for match in header_matches:
            if 'quantity' in match.keyword.lower():
                quantity_match = match
                break
        
        if not quantity_match:
            return header_matches  # No quantity column found
        
        # Create enhanced header list with original headers
        enhanced_headers = header_matches.copy()
        
        # Add PCS and SQFT in the row BELOW the Quantity header
        # PCS: same column as Quantity, but row + 1
        pcs_header = HeaderMatch(
            keyword="PCS",
            row=quantity_match.row + 1,
            column=quantity_match.column
        )
        enhanced_headers.append(pcs_header)
        
        # SQFT: same row as PCS, but next column
        sqft_header = HeaderMatch(
            keyword="SF", 
            row=quantity_match.row + 1,
            column=quantity_match.column + 1
        )
        enhanced_headers.append(sqft_header)
        
        return enhanced_headers
    
    def _extract_double_header(self, worksheet: Worksheet, header_row: int) -> List[HeaderMatch]:
        """
        Extract headers from a two-row header structure.
        
        Args:
            worksheet: The openpyxl worksheet to analyze
            header_row: The first row of the header
            
        Returns:
            List of HeaderMatch objects for all headers in both rows
        """
        header_matches = []
        
        # Extract headers from the first row
        for cell in worksheet[header_row]:
            if cell.value is not None:
                cell_value = str(cell.value).strip()
                if cell_value:
                    header_match = HeaderMatch(
                        keyword=cell_value,
                        row=cell.row,
                        column=cell.column
                    )
                    header_matches.append(header_match)
        
        # Extract headers from the second row (header_row + 1)
        second_row = header_row + 1
        for cell in worksheet[second_row]:
            if cell.value is not None:
                cell_value = str(cell.value).strip()
                if cell_value:
                    header_match = HeaderMatch(
                        keyword=cell_value,
                        row=cell.row,
                        column=cell.column
                    )
                    header_matches.append(header_match)
        
        return header_matches