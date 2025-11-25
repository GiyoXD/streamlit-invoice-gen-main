"""
SummaryUpdater component for updating summary field in configuration templates.

This module handles updating the "summary" field in the Packing list configuration
based on the fob_summary_description value from quantity analysis data.
"""

import copy
from typing import Dict, Any
from .models import QuantityAnalysisData


class SummaryUpdaterError(Exception):
    """Custom exception for SummaryUpdater errors."""
    pass


class SummaryUpdater:
    """Updates summary field in Packing list configuration based on FOB summary detection."""

    def __init__(self):
        """Initialize SummaryUpdater."""
        pass

    def update_summary(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update summary field in the template configuration using quantity analysis data.

        This method checks for fob_summary_description in the quantity data and updates
        the "summary" field in the Packing list configuration accordingly.

        Args:
            template: The configuration template dictionary
            quantity_data: Quantity analysis data containing fob_summary_description

        Returns:
            Updated template with summary field updated if buffalo text was detected

        Raises:
            SummaryUpdaterError: If template structure is invalid
        """
        try:
            if not isinstance(template, dict):
                raise SummaryUpdaterError("Template must be a dictionary")
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise SummaryUpdaterError("Quantity data must be a QuantityAnalysisData instance")

            # Make a deep copy to avoid modifying the original
            updated_template = copy.deepcopy(template)

            # Check if we have data_mapping in the template
            if 'data_mapping' not in updated_template:
                print("[SUMMARY_UPDATER] Warning: No data_mapping found in template")
                return updated_template

            # Look for Packing list sheet in quantity data
            packing_list_sheet = None
            for sheet in quantity_data.sheets:
                if sheet.sheet_name.lower() == 'packing list':
                    packing_list_sheet = sheet
                    break

            if not packing_list_sheet:
                print("[SUMMARY_UPDATER] Warning: No Packing list sheet found in quantity data")
                return updated_template

            # Check if fob_summary_description is True
            if hasattr(packing_list_sheet, 'fob_summary_description') and packing_list_sheet.fob_summary_description:
                # Update the summary field in Packing list configuration
                if 'Packing list' in updated_template['data_mapping']:
                    packing_list_config = updated_template['data_mapping']['Packing list']

                    # Update summary from false to true
                    if 'summary' in packing_list_config and packing_list_config['summary'] == False:
                        packing_list_config['summary'] = True
                        print(f"[SUMMARY_UPDATER] ✅ Updated Packing list summary: false → true (buffalo text detected)")
                    elif 'summary' not in packing_list_config:
                        # Add summary field if it doesn't exist
                        packing_list_config['summary'] = True
                        print(f"[SUMMARY_UPDATER] ✅ Added Packing list summary: true (buffalo text detected)")
                    else:
                        print(f"[SUMMARY_UPDATER] ℹ️  Packing list summary already set to: {packing_list_config['summary']}")
                else:
                    print("[SUMMARY_UPDATER] Warning: Packing list configuration not found in template")
            else:
                print("[SUMMARY_UPDATER] ℹ️  No buffalo text detected, keeping summary as false")

            return updated_template

        except Exception as e:
            error_msg = f"Summary update failed: {str(e)}"
            print(f"[SUMMARY_UPDATER] Error: {error_msg}")
            raise SummaryUpdaterError(error_msg) from e