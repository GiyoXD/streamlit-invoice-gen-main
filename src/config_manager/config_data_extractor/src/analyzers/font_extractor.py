"""
Font extraction functionality for Excel analysis tool.

This module provides the FontExtractor class that extracts font name and size
from header cells and their corresponding data cells (2 rows below).
"""

from typing import List, Tuple, Optional
from openpyxl.worksheet.worksheet import Worksheet
from models.data_models import FontInfo, HeaderMatch


class FontExtractor:
    """Extracts font information from Excel cells."""
    
    def __init__(self):
        """Initialize the FontExtractor."""
        pass
    
    def get_font_info(self, worksheet: Worksheet, row: int, col: int) -> FontInfo:
        """
        Extract font name and size from a specific cell.
        
        Args:
            worksheet: The openpyxl worksheet
            row: Row number (1-based)
            col: Column number (1-based)
            
        Returns:
            FontInfo object with font name and size
        """
        try:
            cell = worksheet.cell(row=row, column=col)
            
            # Get font information from the cell
            font = cell.font
            
            # Extract font name (default to 'Calibri' if None)
            font_name = font.name if font.name else 'Calibri'
            
            # Extract font size (default to 11.0 if None)
            font_size = float(font.size) if font.size else 11.0
            
            return FontInfo(name=font_name, size=font_size)
            
        except Exception:
            # Return default font info if extraction fails
            return FontInfo(name='Calibri', size=11.0)
    
    def extract_header_and_data_fonts(self, worksheet: Worksheet, header_positions: List[HeaderMatch]) -> Tuple[FontInfo, FontInfo]:
        """
        Extract font information from header cells and their corresponding data cells.
        
        Args:
            worksheet: The openpyxl worksheet
            header_positions: List of HeaderMatch objects
            
        Returns:
            Tuple of (header_font, data_font) FontInfo objects
        """
        if not header_positions:
            # Return default fonts if no headers found
            default_font = FontInfo(name='Calibri', size=11.0)
            return default_font, default_font
        
        # Use the first header position for font extraction
        first_header = header_positions[0]
        
        # Get font info from header cell
        header_font = self.get_font_info(
            worksheet, 
            first_header.row, 
            first_header.column
        )
        
        # Get font info from cell exactly 2 rows below the header
        data_row = first_header.row + 2
        data_font = self.get_font_info(
            worksheet, 
            data_row, 
            first_header.column
        )
        
        return header_font, data_font
    
    def get_header_font(self, worksheet: Worksheet, header_positions: List[HeaderMatch]) -> FontInfo:
        """
        Get font information from header cells.
        
        Args:
            worksheet: The openpyxl worksheet
            header_positions: List of HeaderMatch objects
            
        Returns:
            FontInfo object for the header font
        """
        if not header_positions:
            return FontInfo(name='Calibri', size=11.0)
        
        # Use the first header position
        first_header = header_positions[0]
        return self.get_font_info(worksheet, first_header.row, first_header.column)
    
    def get_data_font(self, worksheet: Worksheet, header_positions: List[HeaderMatch]) -> FontInfo:
        """
        Get font information from data cells (2 rows below headers).
        
        Args:
            worksheet: The openpyxl worksheet
            header_positions: List of HeaderMatch objects
            
        Returns:
            FontInfo object for the data font
        """
        if not header_positions:
            return FontInfo(name='Calibri', size=11.0)
        
        # Use the first header position and go 2 rows below
        first_header = header_positions[0]
        data_row = first_header.row + 2
        return self.get_font_info(worksheet, data_row, first_header.column)