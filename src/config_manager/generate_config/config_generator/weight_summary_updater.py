"""
WeightSummaryUpdater component for updating weight_summary_config in configuration templates.

This module handles updating the "weight_summary_config.enabled" field in the Invoice configuration
based on the weight_summary_enabled value from quantity analysis data.
"""

import copy
from typing import Dict, Any
from .models import QuantityAnalysisData


class WeightSummaryUpdaterError(Exception):
    """Custom exception for WeightSummaryUpdater errors."""
    pass


class WeightSummaryUpdater:
    """Updates weight_summary_config.enabled in Invoice configuration based on NW(KGS) detection."""

    def __init__(self):
        """Initialize WeightSummaryUpdater."""
        pass

    def update_weight_summary(self, template: Dict[str, Any], quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """
        Update weight_summary_config.enabled in the template configuration using quantity analysis data.

        This method checks for weight_summary_enabled in the quantity data and updates
        the "weight_summary_config.enabled" field in the Invoice configuration accordingly.

        Args:
            template: The configuration template dictionary
            quantity_data: Quantity analysis data containing weight_summary_enabled

        Returns:
            Updated template with weight_summary_config.enabled updated if NW(KGS) was detected

        Raises:
            WeightSummaryUpdaterError: If template structure is invalid
        """
        try:
            if not isinstance(template, dict):
                raise WeightSummaryUpdaterError("Template must be a dictionary")
            if not isinstance(quantity_data, QuantityAnalysisData):
                raise WeightSummaryUpdaterError("Quantity data must be a QuantityAnalysisData instance")

            # Make a deep copy to avoid modifying the original
            updated_template = copy.deepcopy(template)

            # Check if we have data_mapping in the template
            if 'data_mapping' not in updated_template:
                print("[WEIGHT_SUMMARY_UPDATER] Warning: No data_mapping found in template")
                return updated_template

            # Look for Invoice sheet in quantity data
            invoice_sheet = None
            for sheet in quantity_data.sheets:
                if sheet.sheet_name.lower() == 'invoice':
                    invoice_sheet = sheet
                    break

            if not invoice_sheet:
                print("[WEIGHT_SUMMARY_UPDATER] Warning: No Invoice sheet found in quantity data")
                return updated_template

            # Check if weight_summary_enabled is True
            if hasattr(invoice_sheet, 'weight_summary_enabled') and invoice_sheet.weight_summary_enabled:
                # Update the weight_summary_config.enabled field in Invoice configuration
                if 'Invoice' in updated_template['data_mapping']:
                    invoice_config = updated_template['data_mapping']['Invoice']

                    # Check if weight_summary_config exists
                    if 'weight_summary_config' not in invoice_config:
                        invoice_config['weight_summary_config'] = {
                            "enabled": False,
                            "label_col_id": "col_po",
                            "value_col_id": "col_item"
                        }

                    # Update enabled from false to true
                    if invoice_config['weight_summary_config']['enabled'] == False:
                        invoice_config['weight_summary_config']['enabled'] = True
                        print(f"[WEIGHT_SUMMARY_UPDATER] ✅ Updated Invoice weight_summary_config.enabled: false → true (NW(KGS) detected)")
                    else:
                        print(f"[WEIGHT_SUMMARY_UPDATER] ℹ️  Invoice weight_summary_config.enabled already set to: {invoice_config['weight_summary_config']['enabled']}")
                else:
                    print("[WEIGHT_SUMMARY_UPDATER] Warning: Invoice configuration not found in template")
            else:
                print("[WEIGHT_SUMMARY_UPDATER] ℹ️  No NW(KGS) text detected, keeping weight_summary_config.enabled as false")

            return updated_template

        except Exception as e:
            error_msg = f"Weight summary update failed: {str(e)}"
            print(f"[WEIGHT_SUMMARY_UPDATER] Error: {error_msg}")
            raise WeightSummaryUpdaterError(error_msg) from e