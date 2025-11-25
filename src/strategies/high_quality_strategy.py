# High-Quality Leather Strategy
# Refactored to use composition with reusable components

import streamlit as st
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from zoneinfo import ZoneInfo

from .base_strategy import InvoiceGenerationStrategy
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
        return ['po', 'item', 'pcs', 'sqft', 'pallet_count', 'unit', 'amount', 'net', 'gross', 'cbm', 'production_order_no']

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
            "inv_no": {"type": "text_input", "label": "Invoice No", "default": "", "auto_populate_filename": True},
            "inv_ref": {"type": "text_input", "label": "Invoice Ref", "default": "auto"},
            "inv_date": {"type": "date_input", "label": "Invoice Date", "default": "tomorrow"},
            "containers": {"type": "text_area", "label": "Container / Truck (One per line)", "default": ""}
        }

    def apply_overrides(self, json_path: Path, overrides: Dict[str, Any]) -> bool:
        """Apply overrides to high-quality leather JSON"""
        try:
            with open(json_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                was_modified = False

                cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
                creating_date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")

                if 'processed_tables_data' in data:
                    for table_data in data['processed_tables_data'].values():
                        num_rows = len(table_data.get('amount', []))
                        if num_rows == 0:
                            continue

                        # Only add creating_date if it doesn't already exist
                        if 'creating_date' not in table_data or not table_data['creating_date']:
                            table_data['creating_date'] = [creating_date_str] * num_rows
                            was_modified = True

                        # Apply user overrides
                        if overrides.get('inv_no'):
                            table_data['inv_no'] = [overrides['inv_no'].strip()] * num_rows
                            was_modified = True
                        if overrides.get('inv_ref'):
                            table_data['inv_ref'] = [overrides['inv_ref'].strip()] * num_rows
                            was_modified = True
                        if overrides.get('inv_date'):
                            # Convert date object to string format DD/MM/YYYY
                            if isinstance(overrides['inv_date'], datetime.date):
                                date_str = overrides['inv_date'].strftime("%d/%m/%Y")
                            else:
                                date_str = str(overrides['inv_date'])
                            table_data['inv_date'] = [date_str] * num_rows
                            was_modified = True
                        if overrides.get('containers'):
                            container_list = [line.strip() for line in overrides['containers'].split('\n') if line.strip()]
                            table_data['container_type'] = [', '.join(container_list)] * num_rows
                            was_modified = True

                if was_modified:
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()

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
        """Generate documents for high-quality leather"""
        generated_files = []
        identifier = kwargs.get('identifier', json_path.stem)

        # Get and resolve paths to ensure they work correctly
        template_dir = kwargs.get('template_dir', './TEMPLATE')
        config_dir = kwargs.get('config_dir', './config')
        
        # Convert to absolute paths if they aren't already
        if isinstance(template_dir, str):
            template_dir = Path(template_dir)
        if isinstance(config_dir, str):
            config_dir = Path(config_dir)
            
        # Make sure they're absolute paths
        if not template_dir.is_absolute():
            template_dir = template_dir.resolve()
        if not config_dir.is_absolute():
            config_dir = config_dir.resolve()

        # Import here to avoid circular imports
        from src.invoice_generator import generate_invoice

        for option in options:
            option_config = next((opt for opt in self.get_generation_options() if opt['key'] == option), None)
            if not option_config:
                continue

            flags = option_config.get('flags', [])
            output_file = output_dir / f"{identifier}_{option}.xlsx"

            try:
                generate_invoice(
                    json_file_path=json_path,
                    output_file_path=output_file,
                    flags=flags,
                    template_dir=str(template_dir),
                    config_dir=str(config_dir),
                    verbose=True
                )
                generated_files.append(output_file)
                st.success(f"Generated {option_config['name']}: {output_file.name}")

            except Exception as e:
                st.error(f"Failed to generate {option_config['name']}: {e}")

        return generated_files

    def calculate_cbm_and_truck(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate CBM, pallet count and recommend truck/container"""
        return self.calculator.compute_cbm_pallet_truck(invoice_data)