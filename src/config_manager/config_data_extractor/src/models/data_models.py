"""
Core data models for Excel analysis tool.

This module contains simplified dataclasses for representing Excel font analysis results.
Focus is on extracting font name, font size, and start row information.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class FontInfo:
    """Represents basic font information (name and size only)."""
    name: str
    size: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class AlignmentInfo:
    """Represents alignment information for a column."""
    column_id: str
    horizontal: str
    vertical: str = "center"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class HeaderMatch:
    """Represents a detected header keyword match."""
    keyword: str
    row: int
    column: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class NumberFormatInfo:
    """Number format information for a column."""
    column_id: str
    excel_format: str
    description: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class FallbackInfo:
    """Fallback description information for a column."""
    column_id: str
    fallback_texts: List[str]
    fallback_DAF_texts: List[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SheetAnalysis:
    """Analysis results for a single Excel sheet."""
    sheet_name: str
    header_font: FontInfo
    data_font: FontInfo
    start_row: int
    header_positions: List[HeaderMatch]
    number_formats: List[NumberFormatInfo]
    alignments: List[AlignmentInfo] = None
    fallbacks: Optional[FallbackInfo] = None
    fob_summary_description: bool = False
    weight_summary_enabled: bool = False
    
    def to_text(self) -> str:
        """Convert analysis results to simple text format."""
        result = f"""Sheet: {self.sheet_name}
Header Font: {self.header_font.name}, Size: {self.header_font.size}
Data Font: {self.data_font.name}, Size: {self.data_font.size}
Start Row: {self.start_row}"""
        
        if self.number_formats:
            result += "\nNumber Formats:"
            for fmt in self.number_formats:
                result += f"\n  {fmt.column_id}: {fmt.excel_format} ({fmt.description})"
        
        if self.alignments:
            result += "\nAlignments:"
            for align in self.alignments:
                result += f"\n  {align.column_id}: {align.horizontal} ({align.vertical})"
        
        if self.fallbacks:
            result += "\nFallback Descriptions:"
            for fallback_text in self.fallbacks.fallback_texts:
                result += f"\n  {fallback_text}"
        
        return result
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'sheet_name': self.sheet_name,
            'header_font': self.header_font.to_dict(),
            'data_font': self.data_font.to_dict(),
            'start_row': self.start_row,
            'header_positions': [pos.to_dict() for pos in self.header_positions],
            'number_formats': [fmt.to_dict() for fmt in self.number_formats],
            'alignments': [align.to_dict() for align in self.alignments],
            'fallbacks': self.fallbacks.to_dict() if self.fallbacks else None,
            'fob_summary_description': self.fob_summary_description,
            'weight_summary_enabled': self.weight_summary_enabled
        }


@dataclass
class AnalysisResult:
    """Complete analysis results for an Excel file."""
    file_path: str
    sheets: List[SheetAnalysis]
    timestamp: datetime
    
    def to_text(self) -> str:
        """Convert all analysis results to simple text format."""
        result = f"Excel Analysis Results\nFile: {self.file_path}\nAnalyzed: {self.timestamp}\n\n"
        for sheet in self.sheets:
            result += sheet.to_text() + "\n\n"
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert all analysis results to JSON format."""
        data = {
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat(),
            'sheets': [sheet.to_dict() for sheet in self.sheets]
        }
        return json.dumps(data, indent=indent)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat(),
            'sheets': [sheet.to_dict() for sheet in self.sheets]
        }