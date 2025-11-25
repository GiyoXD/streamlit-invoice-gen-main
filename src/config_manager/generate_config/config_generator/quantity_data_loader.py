"""
QuantityDataLoader component for loading and validating quantity analysis data.

This module provides functionality to load quantity mode analysis JSON files
and validate their structure according to the expected format.
"""

import json
import os
from typing import Dict, Any
from .models import QuantityAnalysisData, SheetData, HeaderPosition, FontInfo, FooterInfo, NumberFormatInfo, AlignmentInfo, FallbackInfo
from .footer_detector import FooterDetector, FooterDetectorError


class QuantityDataLoaderError(Exception):
    """Custom exception for QuantityDataLoader errors."""
    pass


class QuantityDataLoader:
    """
    Loads and validates quantity mode analysis data from JSON files.
    
    This class handles loading JSON files containing quantity analysis data
    and validates the structure to ensure it matches the expected format
    for the config generator system.
    """
    
    def __init__(self):
        """Initialize the QuantityDataLoader with footer detector."""
        self.footer_detector = FooterDetector()
    
    def load_quantity_data(self, file_path: str) -> QuantityAnalysisData:
        """
        Load quantity analysis data from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing quantity analysis data
            
        Returns:
            QuantityAnalysisData: Parsed and validated quantity analysis data
            
        Raises:
            QuantityDataLoaderError: If file operations fail or data is invalid
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise QuantityDataLoaderError(f"File not found: {file_path}")
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
                
        except json.JSONDecodeError as e:
            raise QuantityDataLoaderError(f"Invalid JSON format in {file_path}: {e}")
        except IOError as e:
            raise QuantityDataLoaderError(f"Error reading file {file_path}: {e}")
        
        # Validate and parse the data structure
        try:
            return self._parse_quantity_data(raw_data)
        except (ValueError, KeyError, TypeError) as e:
            raise QuantityDataLoaderError(f"Invalid data structure in {file_path}: {e}")
    
    def validate_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate the structure of quantity analysis data.
        
        Args:
            data: Raw dictionary data to validate
            
        Returns:
            bool: True if structure is valid
            
        Raises:
            QuantityDataLoaderError: If structure is invalid
        """
        try:
            self._validate_root_structure(data)
            self._validate_sheets_structure(data.get('sheets', []))
            return True
        except (ValueError, KeyError, TypeError) as e:
            raise QuantityDataLoaderError(f"Structure validation failed: {e}")
    
    def _parse_quantity_data(self, raw_data: Dict[str, Any]) -> QuantityAnalysisData:
        """
        Parse raw JSON data into QuantityAnalysisData object.
        
        Args:
            raw_data: Raw dictionary data from JSON
            
        Returns:
            QuantityAnalysisData: Parsed data object
        """
        # Validate structure first
        self.validate_structure(raw_data)
        
        # Parse sheets data
        sheets = []
        for sheet_data in raw_data['sheets']:
            # Parse header positions
            header_positions = []
            for pos_data in sheet_data['header_positions']:
                header_positions.append(HeaderPosition(
                    keyword=pos_data['keyword'],
                    row=pos_data['row'],
                    column=pos_data['column']
                ))
            
            # Parse font information
            header_font = FontInfo(
                name=sheet_data['header_font']['name'],
                size=sheet_data['header_font']['size']
            )
            
            data_font = FontInfo(
                name=sheet_data['data_font']['name'],
                size=sheet_data['data_font']['size']
            )
            
            # Detect footer information if Excel file is available
            footer_info = None
            if 'file_path' in raw_data and os.path.exists(raw_data['file_path']):
                try:
                    # Use the header row from header_positions to detect footer
                    if header_positions:
                        header_row = header_positions[0].row  # Use first header position as reference
                        footer_info = self.footer_detector.detect_footer_from_file(
                            raw_data['file_path'], 
                            sheet_data['sheet_name'], 
                            header_row
                        )
                        if footer_info:
                            print(f"[FOOTER_DETECTION] Successfully detected footer for {sheet_data['sheet_name']}")
                        else:
                            print(f"[FOOTER_DETECTION] No footer found for {sheet_data['sheet_name']}")
                except FooterDetectorError as e:
                    print(f"[FOOTER_DETECTION] Error detecting footer for {sheet_data['sheet_name']}: {e}")
                except Exception as e:
                    print(f"[FOOTER_DETECTION] Unexpected error for {sheet_data['sheet_name']}: {e}")
            
            # Parse number formats if available
            number_formats = []
            if 'number_formats' in sheet_data and sheet_data['number_formats']:
                for fmt_data in sheet_data['number_formats']:
                    number_formats.append(NumberFormatInfo(
                        column_id=fmt_data['column_id'],
                        excel_format=fmt_data['excel_format'],
                        description=fmt_data['description']
                    ))
            
            # Parse alignments if available
            alignments = []
            if 'alignments' in sheet_data and sheet_data['alignments']:
                for align_data in sheet_data['alignments']:
                    alignments.append(AlignmentInfo(
                        column_id=align_data['column_id'],
                        horizontal=align_data['horizontal'],
                        vertical=align_data.get('vertical', 'center')
                    ))
            
            # Parse fallbacks if available
            fallbacks = None
            if 'fallbacks' in sheet_data and sheet_data['fallbacks']:
                fallbacks_data = sheet_data['fallbacks']
                fallbacks = FallbackInfo(
                    column_id=fallbacks_data['column_id'],
                    fallback_texts=fallbacks_data['fallback_texts'],
                    fallback_DAF_texts=fallbacks_data['fallback_DAF_texts']
                )
            
            # Parse fob_summary_description if available
            fob_summary_description = sheet_data.get('fob_summary_description', False)
            
            # Parse weight_summary_enabled if available
            weight_summary_enabled = sheet_data.get('weight_summary_enabled', False)
            
            # Create sheet data object
            sheet = SheetData(
                sheet_name=sheet_data['sheet_name'],
                header_font=header_font,
                data_font=data_font,
                start_row=sheet_data['start_row'],
                header_positions=header_positions,
                footer_info=footer_info,
                number_formats=number_formats,
                alignments=alignments,
                fallbacks=fallbacks,
                fob_summary_description=fob_summary_description,
                weight_summary_enabled=weight_summary_enabled
            )
            sheets.append(sheet)
        
        # Create and return the complete data object
        return QuantityAnalysisData(
            file_path=raw_data['file_path'],
            timestamp=raw_data['timestamp'],
            sheets=sheets
        )
    
    def _validate_root_structure(self, data: Dict[str, Any]) -> None:
        """
        Validate the root structure of quantity analysis data.
        
        Args:
            data: Raw dictionary data to validate
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['file_path', 'timestamp', 'sheets']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate field types
        if not isinstance(data['file_path'], str) or not data['file_path'].strip():
            raise ValueError("file_path must be a non-empty string")
        
        if not isinstance(data['timestamp'], str) or not data['timestamp'].strip():
            raise ValueError("timestamp must be a non-empty string")
        
        if not isinstance(data['sheets'], list) or len(data['sheets']) == 0:
            raise ValueError("sheets must be a non-empty list")
    
    def _validate_sheets_structure(self, sheets: list) -> None:
        """
        Validate the structure of sheets data.
        
        Args:
            sheets: List of sheet data dictionaries
            
        Raises:
            ValueError: If sheet structure is invalid
        """
        for i, sheet in enumerate(sheets):
            if not isinstance(sheet, dict):
                raise ValueError(f"Sheet {i} must be a dictionary")
            
            # Validate required sheet fields
            required_sheet_fields = ['sheet_name', 'header_font', 'data_font', 'start_row', 'header_positions']
            
            for field in required_sheet_fields:
                if field not in sheet:
                    raise ValueError(f"Sheet {i} missing required field: {field}")
            
            # Validate sheet field types
            if not isinstance(sheet['sheet_name'], str) or not sheet['sheet_name'].strip():
                raise ValueError(f"Sheet {i} sheet_name must be a non-empty string")
            
            if not isinstance(sheet['start_row'], int) or sheet['start_row'] < 0:
                raise ValueError(f"Sheet {i} start_row must be a non-negative integer")
            
            if not isinstance(sheet['header_positions'], list):
                raise ValueError(f"Sheet {i} header_positions must be a list")
            
            # Validate font structures
            self._validate_font_structure(sheet['header_font'], f"Sheet {i} header_font")
            self._validate_font_structure(sheet['data_font'], f"Sheet {i} data_font")
            
            # Validate header positions
            self._validate_header_positions(sheet['header_positions'], f"Sheet {i}")
    
    def _validate_font_structure(self, font_data: Dict[str, Any], context: str) -> None:
        """
        Validate font data structure.
        
        Args:
            font_data: Font data dictionary
            context: Context string for error messages
            
        Raises:
            ValueError: If font structure is invalid
        """
        if not isinstance(font_data, dict):
            raise ValueError(f"{context} must be a dictionary")
        
        required_font_fields = ['name', 'size']
        
        for field in required_font_fields:
            if field not in font_data:
                raise ValueError(f"{context} missing required field: {field}")
        
        if not isinstance(font_data['name'], str) or not font_data['name'].strip():
            raise ValueError(f"{context} name must be a non-empty string")
        
        if not isinstance(font_data['size'], (int, float)) or font_data['size'] <= 0:
            raise ValueError(f"{context} size must be a positive number")
    
    def _validate_header_positions(self, positions: list, context: str) -> None:
        """
        Validate header positions structure.
        
        Args:
            positions: List of header position dictionaries
            context: Context string for error messages
            
        Raises:
            ValueError: If header positions structure is invalid
        """
        for i, position in enumerate(positions):
            if not isinstance(position, dict):
                raise ValueError(f"{context} header_position {i} must be a dictionary")
            
            required_position_fields = ['keyword', 'row', 'column']
            
            for field in required_position_fields:
                if field not in position:
                    raise ValueError(f"{context} header_position {i} missing required field: {field}")
            
            if not isinstance(position['keyword'], str) or not position['keyword'].strip():
                raise ValueError(f"{context} header_position {i} keyword must be a non-empty string")
            
            if not isinstance(position['row'], int) or position['row'] < 0:
                raise ValueError(f"{context} header_position {i} row must be a non-negative integer")
            
            if not isinstance(position['column'], int) or position['column'] < 0:
                raise ValueError(f"{context} header_position {i} column must be a non-negative integer")