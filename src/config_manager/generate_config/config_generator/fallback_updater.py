"""
FallbackUpdater component for updating fallback values in configuration templates.

This module provides functionality to update fallback_on_none and fallback_on_DAF values
in description mappings, and replace "Des: LEATHER" in initial_static values with
dynamic fallback text placeholders.
"""

from typing import Dict, List, Any, Optional
import copy
from .models import QuantityAnalysisData


class FallbackUpdaterError(Exception):
    """Custom exception for FallbackUpdater errors."""
    pass


class FallbackUpdater:
    """Updates fallback values in configuration templates using extracted fallback data."""

    def __init__(self):
        """Initialize FallbackUpdater."""
        pass

    def update_fallbacks(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update fallback values in the template using extracted fallback data from quantity analysis.

        Args:
            template: Configuration template dictionary
            quantity_data: Quantity analysis data containing fallback information

        Returns:
            Updated template with fallback values replaced
        """
        updated_template = copy.deepcopy(template)

        # Extract fallback data from quantity analysis
        fallback_texts = []
        fallback_daf_texts = []

        # Collect fallback data from all sheets
        for sheet in quantity_data.sheets:
            if sheet.fallbacks:
                fallback_texts.extend(sheet.fallbacks.fallback_texts)
                fallback_daf_texts.extend(sheet.fallbacks.fallback_DAF_texts)

        # Remove duplicates while preserving order
        fallback_texts = list(dict.fromkeys(fallback_texts))
        fallback_daf_texts = list(dict.fromkeys(fallback_daf_texts))

        # Get the primary fallback text (first item or empty string)
        primary_fallback = fallback_texts[0] if fallback_texts else ""
        primary_daf_fallback = fallback_daf_texts[0] if fallback_daf_texts else primary_fallback

        # Update each sheet's mappings
        if 'data_mapping' in updated_template:
            for sheet_name, sheet in updated_template['data_mapping'].items():
                if 'mappings' in sheet:
                    self._update_sheet_mappings(sheet, primary_fallback, primary_daf_fallback)

        return updated_template

    def _update_sheet_mappings(self, sheet: Dict[str, Any], fallback_text: str, daf_fallback_text: str) -> None:
        """
        Update mappings for a single sheet.

        Args:
            sheet: Sheet configuration dictionary
            fallback_text: Primary fallback text for fallback_on_none
            daf_fallback_text: DAF-specific fallback text for fallback_on_DAF
        """
        mappings = sheet.get('mappings', {})

        # Check for description in different possible locations and keys
        desc_mapping = None
        # Check direct mappings
        if 'description' in mappings:
            desc_mapping = mappings['description']
        elif 'desc' in mappings:
            desc_mapping = mappings['desc']
        # Check data_map
        elif 'data_map' in mappings:
            if 'description' in mappings['data_map']:
                desc_mapping = mappings['data_map']['description']
            elif 'desc' in mappings['data_map']:
                desc_mapping = mappings['data_map']['desc']
            desc_mapping = mappings['data_map']['description']

        if desc_mapping:
            # Replace fallback_on_none with the extracted text
            if 'fallback_on_none' in desc_mapping:
                desc_mapping['fallback_on_none'] = fallback_text

            # Add fallback_on_DAF if it doesn't exist
            if 'fallback_on_DAF' not in desc_mapping:
                desc_mapping['fallback_on_DAF'] = daf_fallback_text

        # Update initial_static values
        if 'initial_static' in mappings and 'values' in mappings['initial_static']:
            values = mappings['initial_static']['values']
            # Replace "Des: LEATHER" patterns with "Des: [DAF fallback text]"
            for i, value in enumerate(values):
                if isinstance(value, str) and value.startswith('Des: '):
                    values[i] = f"Des: {daf_fallback_text}"