"""
Data models for the Config Generator module.

This module contains dataclasses for representing quantity analysis data
and configuration data structures used in the config generation process.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FontInfo:
    """Represents font information with name and size."""
    name: str
    size: float
    
    def __post_init__(self):
        """Validate font data after initialization."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Font name must be a non-empty string")
        if not isinstance(self.size, (int, float)) or self.size <= 0:
            raise ValueError("Font size must be a positive number")


@dataclass
class HeaderPosition:
    """Represents a header position with keyword, row, and column."""
    keyword: str
    row: int
    column: int
    
    def __post_init__(self):
        """Validate header position data after initialization."""
        if not isinstance(self.keyword, str) or not self.keyword.strip():
            raise ValueError("Header keyword must be a non-empty string")
        if not isinstance(self.row, int) or self.row < 0:
            raise ValueError("Row must be a non-negative integer")
        if not isinstance(self.column, int) or self.column < 0:
            raise ValueError("Column must be a non-negative integer")


@dataclass
class SheetData:
    """Represents analysis data for a single sheet."""
    sheet_name: str
    header_font: FontInfo
    data_font: FontInfo
    start_row: int
    header_positions: List[HeaderPosition]
    
    def __post_init__(self):
        """Validate sheet data after initialization."""
        if not isinstance(self.sheet_name, str) or not self.sheet_name.strip():
            raise ValueError("Sheet name must be a non-empty string")
        if not isinstance(self.start_row, int) or self.start_row < 0:
            raise ValueError("Start row must be a non-negative integer")
        if not isinstance(self.header_positions, list):
            raise ValueError("Header positions must be a list")


@dataclass
class QuantityAnalysisData:
    """Represents the complete quantity mode analysis data."""
    file_path: str
    timestamp: str
    sheets: List[SheetData]
    
    def __post_init__(self):
        """Validate quantity analysis data after initialization."""
        if not isinstance(self.file_path, str) or not self.file_path.strip():
            raise ValueError("File path must be a non-empty string")
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("Timestamp must be a non-empty string")
        if not isinstance(self.sheets, list):
            raise ValueError("Sheets must be a list")
        if not self.sheets:
            raise ValueError("At least one sheet must be provided")


@dataclass
class HeaderEntry:
    """Represents a header entry in the header_to_write configuration."""
    row: int
    col: int
    text: str
    id: str
    rowspan: Optional[int] = None
    colspan: Optional[int] = None
    
    def __post_init__(self):
        """Validate header entry data after initialization."""
        if not isinstance(self.row, int) or self.row < 0:
            raise ValueError("Row must be a non-negative integer")
        if not isinstance(self.col, int) or self.col < 0:
            raise ValueError("Column must be a non-negative integer")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Text must be a non-empty string")
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("ID must be a non-empty string")
        if self.rowspan is not None and (not isinstance(self.rowspan, int) or self.rowspan <= 0):
            raise ValueError("Rowspan must be a positive integer if provided")
        if self.colspan is not None and (not isinstance(self.colspan, int) or self.colspan <= 0):
            raise ValueError("Colspan must be a positive integer if provided")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "row": self.row,
            "col": self.col,
            "text": self.text,
            "id": self.id
        }
        if self.rowspan is not None:
            result["rowspan"] = self.rowspan
        if self.colspan is not None:
            result["colspan"] = self.colspan
        return result


@dataclass
class SheetConfig:
    """Represents configuration for a single sheet."""
    start_row: int
    header_to_write: List[HeaderEntry]
    mappings: Dict[str, Any]
    footer_configurations: Dict[str, Any]
    styling: Dict[str, Any]
    
    def __post_init__(self):
        """Validate sheet configuration data after initialization."""
        if not isinstance(self.start_row, int) or self.start_row < 0:
            raise ValueError("Start row must be a non-negative integer")
        if not isinstance(self.header_to_write, list):
            raise ValueError("Header to write must be a list")
        if not isinstance(self.mappings, dict):
            raise ValueError("Mappings must be a dictionary")
        if not isinstance(self.footer_configurations, dict):
            raise ValueError("Footer configurations must be a dictionary")
        if not isinstance(self.styling, dict):
            raise ValueError("Styling must be a dictionary")


@dataclass
class ConfigurationData:
    """Represents the complete configuration data structure."""
    sheets_to_process: List[str]
    sheet_data_map: Dict[str, str]
    data_mapping: Dict[str, SheetConfig]
    
    def __post_init__(self):
        """Validate configuration data after initialization."""
        if not isinstance(self.sheets_to_process, list):
            raise ValueError("Sheets to process must be a list")
        if not isinstance(self.sheet_data_map, dict):
            raise ValueError("Sheet data map must be a dictionary")
        if not isinstance(self.data_mapping, dict):
            raise ValueError("Data mapping must be a dictionary")
        
        # Validate that all sheets in sheets_to_process have corresponding data_mapping entries
        for sheet_name in self.sheets_to_process:
            if sheet_name not in self.data_mapping:
                raise ValueError(f"Sheet '{sheet_name}' in sheets_to_process must have corresponding data_mapping entry")