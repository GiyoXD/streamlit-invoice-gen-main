# High-Quality Leather Strategy
# Refactored to use composition with reusable components

import streamlit as st
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from zoneinfo import ZoneInfo
import sys
import os
import subprocess # Added for subprocess.CalledProcessError

from .base_strategy import InvoiceGenerationStrategy, SCRIPT_DIR
from .components.excel_processor import ExcelProcessor
from .components.calculator import Calculator


class HighQualityLeatherStrategy(InvoiceGenerationStrategy):
    """Strategy for High-Quality Leather invoice generation using composition"""

    def __init__(self):
        super().__init__(
            name="High-Quality Leather",
            description="Standard invoice generation with Normal/DAF/Combine options"
        )
        # Compose with components
        self.excel_processor = ExcelProcessor()
        self.calculator = Calculator()

    def get_required_fields(self) -> List[str]:
        return ['col_po', 'col_item', 'col_qty_pcs', 'col_qty_sf', 'col_pallet_count', 'col_unit_price', 'col_amount', 'col_net', 'col_gross', 'col_cbm', 'col_production_order_no']

    def validate_excel_data(self, excel_path: Path) -> Tuple[bool, List[str]]:
        """Validate Excel data structure for high-quality leather"""
        required_cols = ['po', 'item', 'pcs', 'sqft', 'pallet_count', 'unit', 'amount', 'net', 'gross', 'cbm']
        return self.excel_processor.validate_excel_structure(excel_path, required_cols)

    def validate_json_data(self, json_path: Path) -> List[str]:
        """Validate JSON data for high-quality leather format"""
        if not json_path.exists():
            st.error(f"Validation failed: JSON file '{json_path.name}' not found.")
            return self.get_required_fields()

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            missing_or_empty_keys = set(self.get_required_fields())

            if 'processed_tables_data' in data and isinstance(data['processed_tables_data'], dict):
                all_tables_data = {k: v for table in data['processed_tables_data'].values()
                                 for k, v in table.items()}

                for key in self.get_required_fields():
                    if key in all_tables_data and isinstance(all_tables_data[key], list) and \
                       any(item is not None and str(item).strip() for item in all_tables_data[key]):
                        missing_or_empty_keys.discard(key)

            return sorted(list(missing_or_empty_keys))

        except (json.JSONDecodeError, Exception) as e:
            st.error(f"Validation failed due to invalid JSON: {e}")
            return self.get_required_fields()

    def process_excel_to_json(self, excel_path: Path, json_output_dir: Path, **kwargs) -> Tuple[Path, str]:
        """Process Excel using ExcelProcessor component"""
        return self.excel_processor.process_to_json(excel_path, json_output_dir, self.name)

    def get_override_ui_config(self) -> Dict[str, Any]:
        """Return UI config for high-quality leather overrides"""
        return {
            "col_inv_no": {"type": "text_input", "label": "Invoice No", "default": "", "auto_populate_filename": True},
            "col_inv_ref": {"type": "text_input", "label": "Invoice Ref", "default": "auto"},
            "col_inv_date": {"type": "date_input", "label": "Invoice Date", "default": "tomorrow"},
            "containers": {"type": "text_area", "label": "Container / Truck (One per line)", "default": ""}
        }

    def apply_overrides(self, json_path: Path, overrides: Dict[str, Any]) -> bool:
        """
        Apply overrides to high-quality leather JSON.
        Refactored to store overrides in memory instead of writing to disk.
        """
        try:
            # We will store the overridden data in a cache to be used by generate_documents
            if not hasattr(self, '_memory_overrides'):
                self._memory_overrides = {}

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
            creating_date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")

            was_modified = False
            if 'processed_tables_data' in data:
                for table_data in data['processed_tables_data'].values():
                    num_rows = len(table_data.get('amount', []))
                    if num_rows == 0:
                        continue

                if 'invoice_info' not in data:
                    data['invoice_info'] = {}

                # Apply user overrides (Using col_ prefix for UI consistency, but mapped to invoice_info)
                if overrides.get('col_inv_no'):
                    data['invoice_info']['col_inv_no'] = overrides['col_inv_no'].strip()
                    was_modified = True
                if overrides.get('col_inv_ref'):
                    data['invoice_info']['col_inv_ref'] = overrides['col_inv_ref'].strip()
                    was_modified = True
                if overrides.get('col_inv_date'):
                    # Convert date object to string format DD/MM/YYYY
                    if isinstance(overrides['col_inv_date'], datetime.date):
                        date_str = overrides['col_inv_date'].strftime("%d/%m/%Y")
                    else:
                        date_str = str(overrides['col_inv_date'])
                    data['invoice_info']['col_inv_date'] = date_str
                    was_modified = True
                if overrides.get('containers'):
                     # Container is often table-specific, but if it applies to all, we can put it here too
                     # or keep it on tables. For now, let's keep it on tables but ALSO put it on invoice_info
                     # if needed for header replacement. The user's request focused on metadata.
                     pass
                
                # Still populate tables for safety/backward compatibility if needed, 
                # OR we can assume text replacement rules will handle it now.
                # Let's keep table population for 'container' as it varies per implementation,
                # but map inv_no/date/ref to invoice_info.
                
                # --- Legacy/Table Support (Optional: keep or remove based on pure purity) ---
                # For now, we REMOVE the table iteration for Inv No/Date/Ref because 
                # we want to enforce usage of invoice_info.
                
                if 'processed_tables_data' in data:
                    for table_data in data['processed_tables_data'].values():
                        num_rows = len(table_data.get('amount', []))
                        if num_rows == 0: continue

                        # Only add creating_date if it doesn't already exist
                        if 'creating_date' not in table_data or not table_data['creating_date']:
                            table_data['creating_date'] = [creating_date_str] * num_rows
                            was_modified = True
                        
                        # Container override (Table Level)
                        if overrides.get('containers'):
                             container_list = [line.strip() for line in overrides['containers'].split('\n') if line.strip()]
                             table_data['container_type'] = [', '.join(container_list)] * num_rows
                             was_modified = True
            
            # Store in memory
            self._memory_overrides[str(json_path)] = data
            return True

        except Exception as e:
            st.error(f"Error during JSON Override: {e}")
            return False

    def get_generation_options(self) -> List[Dict[str, Any]]:
        """Return generation options for high-quality leather"""
        return [
            {"name": "Normal Invoice", "key": "normal", "flags": []},
            {"name": "DAF Version", "key": "daf", "flags": ["--DAF"]},
            {"name": "Combine Version", "key": "combine", "flags": ["--custom"]}
        ]

    def generate_documents(self, json_path: Path, output_dir: Path, options: List[str], **kwargs) -> List[Path]:
        """Generate documents using Orchestrator"""
        # Lazy import
        from core.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        generated_files = []
        identifier = kwargs.get('identifier', json_path.stem)

        # Get and resolve paths to ensure they work correctly
        # Default to None to let Orchestrator/Generator use its internal defaults (database/blueprints/...)
        template_dir = kwargs.get('template_dir')
        config_dir = kwargs.get('config_dir')
        
        # Convert to absolute paths if provided and they aren't already
        if template_dir:
            if isinstance(template_dir, str):
                template_dir = Path(template_dir)
            if not template_dir.is_absolute():
                template_dir = template_dir.resolve()
        
        if config_dir:
            if isinstance(config_dir, str):
                config_dir = Path(config_dir)
            if not config_dir.is_absolute():
                config_dir = config_dir.resolve()
            
            
        # Make sure they're absolute paths (Handled above now)

        # Retrieve in-memory overrides if available
        input_data_dict = None
        if hasattr(self, '_memory_overrides') and str(json_path) in self._memory_overrides:
             input_data_dict = self._memory_overrides[str(json_path)]

        for option in options:
            option_config = next((opt for opt in self.get_generation_options() if opt['key'] == option), None)
            if not option_config:
                continue

            output_file_for_option = output_dir / f"{identifier}_{option}.xlsx"
            flags = option_config.get('flags', [])

            try:
                # Use Orchestrator to generate invoice
                orchestrator.generate_invoice(
                    json_path=json_path,
                    output_path=output_file_for_option,
                    template_dir=template_dir,
                    config_dir=config_dir,
                    flags=flags,
                    input_data_dict=input_data_dict # Pass appropriate data
                )
                
                generated_files.append(output_file_for_option)
                st.success(f"Generated {option_config['name']}: {output_file_for_option.name}")

            except subprocess.CalledProcessError as e:
                st.error(f"Failed to generate {option_config['name']}.")
            except Exception as e:
                st.error(f"An unexpected error occurred while generating {option_config['name']}: {e}")
                import traceback
                st.code(traceback.format_exc())

        return generated_files

    def calculate_cbm_and_truck(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate CBM, pallet count and recommend truck/container"""
        return self.calculator.compute_cbm_pallet_truck(invoice_data)