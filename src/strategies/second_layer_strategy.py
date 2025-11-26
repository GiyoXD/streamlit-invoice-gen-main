import streamlit as st
import os
import sys
import subprocess
import openpyxl
import json
import datetime
import tempfile
import zipfile
import io
import re
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from zoneinfo import ZoneInfo
import logging

# Get the directory where this script is located
SCRIPT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add project subdirectories to the Python path to ensure correct module resolution
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "data_parser"))
sys.path.insert(0, str(SCRIPT_DIR / "invoice_generator"))

from .base_strategy import InvoiceGenerationStrategy


class SecondLayerLeatherStrategy(InvoiceGenerationStrategy):
    """Strategy for 2nd Layer Leather invoice generation"""

    def __init__(self):
        super().__init__(
            name="2nd Layer Leather",
            description="Aggregated invoice generation with unit pricing"
        )

    def get_required_fields(self) -> List[str]:
        # 2nd layer leather required fields for mapping
        return ['description', 'item', 'po', 'pcs', 'net', 'gross', 'cbm']

    def validate_excel_data(self, excel_path: Path) -> Tuple[bool, List[str]]:
        """Validate Excel data structure for 2nd layer leather"""
        warnings = []

        try:
            workbook = openpyxl.load_workbook(excel_path, data_only=True)

            # Check if we have worksheets
            if len(workbook.worksheets) == 0:
                warnings.append("❌ Excel file has no worksheets")
                return False, warnings

            # For 2nd layer, we expect aggregated data with unit pricing
            # Check each worksheet for required data structure
            valid_sheets = 0
            for sheet in workbook.worksheets:
                sheet_name = sheet.title

                # Get all values from the sheet
                data = []
                for row in sheet.iter_rows(values_only=True):
                    if any(cell for cell in row):  # Skip empty rows
                        data.append(row)

                if len(data) < 1:
                    warnings.append(f"⚠️ Sheet '{sheet_name}' has no data at all")
                    continue

                # Check for required columns in header using the same mapping as processing script
                header = [str(cell).lower().strip() if cell else "" for cell in data[0]]

                # Import the header mapping from create_json config
                try:
                    import sys
                    data_parser_path = SCRIPT_DIR / "data_parser"
                    if str(data_parser_path) not in sys.path:
                        sys.path.insert(0, str(data_parser_path))
                    from config import TARGET_HEADERS_MAP
                except ImportError:
                    # Fallback to hardcoded mapping if config import fails
                    TARGET_HEADERS_MAP = {
                        "po": ["PO NO.", "po", "PO", "Po", "订单号", "order number", "order no"],
                        "item": ["物料代码", "item no", "ITEM NO.", "item", "Item No"],
                        "pcs": ["pcs", "总张数", "张数", "PCS"],
                        "sqft": ["sqft", "出货数量 (sf)", "尺数", "SF"],
                        "pallet_count": ["pallet count", "拖数", "PALLET", "件数"],
                        "unit": ["unit price", "单价", "price", "unit"],
                        "amount": ["金额 USD", "金额USD", "金额", "USD", "amount", "总价"],
                        "net": ["NW", "net weight", "净重kg", "净重"],
                        "gross": ["GW", "gross weight", "毛重", "gross"],
                        "cbm": ["cbm", "材积", "CBM"],
                        "production_order_no": ["production order number", "生产单号", "po", "入库单号"]
                    }

                # Check which required fields are present - FIXED: Don't break early, check all headers for all fields
                found_fields = set()
                for header_cell in header:
                    header_lower = header_cell.lower().strip()
                    for canonical_name, variations in TARGET_HEADERS_MAP.items():
                        for variation in variations:
                            variation_lower = variation.lower().strip()
                            if variation_lower in header_lower or header_lower in variation_lower:
                                found_fields.add(canonical_name)
                                # Don't break - one header might match multiple canonical names

                # Check for required fields (2nd layer has different requirements than high-quality)
                required_fields = ['description', 'item', 'po', 'pcs', 'net', 'gross', 'cbm']  # Core fields for 2nd layer mapping
                missing_fields = [field for field in required_fields if field not in found_fields]

                if missing_fields:
                    # For 2nd layer processing, warn about missing headers but don't fail validation
                    # The processing script can work with partial headers and will aggregate what it finds
                    warnings.append(f"⚠️ Sheet '{sheet_name}' missing columns: {', '.join(missing_fields)} (processing will use defaults)")
                    valid_sheets += 1
                else:
                    # For 2nd layer processing, we don't require all fields to have data
                    # The processing script can handle partial data and will aggregate what it finds
                    valid_sheets += 1
                    warnings.append(f"✅ Sheet '{sheet_name}' has required headers - processing will handle data aggregation")

                    # Optional: Check data quality but don't fail validation
                    data_rows = data[1:] if len(data) > 1 else []  # Skip header if it exists

                    if not data_rows:
                        warnings.append(f"⚠️ Sheet '{sheet_name}' has headers but no data rows")
                    else:
                        # Count how many required fields have data (informational only)
                        fields_with_data = set()
                        for row in data_rows:
                            for col_idx, cell in enumerate(row):
                                if col_idx < len(header):
                                    header_text = header[col_idx].lower().strip()
                                    for field_name, variations in TARGET_HEADERS_MAP.items():
                                        if any(var.lower().strip() in header_text or header_text in var.lower().strip() for var in variations):
                                            if field_name in required_fields:
                                                if cell is not None and str(cell).strip():
                                                    fields_with_data.add(field_name)

                        fields_without_data = [field for field in required_fields if field not in fields_with_data]
                        if fields_without_data:
                            warnings.append(f"ℹ️ Sheet '{sheet_name}' has no data in fields: {', '.join(fields_without_data)} (processing will use defaults/aggregation)")

                        # Check data quality for 2nd layer (different from high-quality)
                        data_rows = data[1:] if len(data) > 1 else []

                        if not data_rows:
                            warnings.append(f"⚠️ Sheet '{sheet_name}' has headers but no data rows - processing will create data")
                        else:
                            # Check for unit pricing (important for 2nd layer amount calculation)
                            has_unit_pricing = any(any(unit_var in h.lower() for unit_var in ['unit', '单价', 'price']) for h in header)
                            if not has_unit_pricing:
                                warnings.append(f"⚠️ Sheet '{sheet_name}' may be missing unit pricing data")

                            # Check for empty values in key fields
                            empty_count = 0
                            for row_idx, row in enumerate(data_rows, 2):
                                for col_idx, cell in enumerate(row):
                                    if col_idx < len(header):
                                        header_text = header[col_idx].lower().strip()
                                        for field_name, variations in TARGET_HEADERS_MAP.items():
                                            if any(var.lower().strip() in header_text or header_text in var.lower().strip() for var in variations):
                                                if field_name in required_fields:
                                                    if cell is None or str(cell).strip() == "":
                                                        empty_count += 1
                                                break  # Found a match for this header, no need to check other fields

                            if empty_count > 0:
                                warnings.append(f"⚠️ Sheet '{sheet_name}' has {empty_count} empty cells in key fields (Description, Item, PO, PCS, Net, Gross)")

            if valid_sheets == 0:
                warnings.append("❌ No worksheets contain the required data structure for 2nd Layer Leather invoices")
                return False, warnings

            # If we have warnings but at least one valid sheet, allow continuation
            if warnings:
                warnings.insert(0, f"✅ Found {valid_sheets} valid worksheet(s), but there are some issues to review:")
            else:
                warnings.append(f"✅ Excel validation passed! Found {valid_sheets} valid worksheet(s)")

            return True, warnings

        except Exception as e:
            warnings.append(f"❌ Error reading Excel file: {str(e)}")
            return False, warnings

    def validate_json_data(self, json_path: Path) -> List[str]:
        """Validate JSON data for 2nd layer format"""
        # 2nd layer validation is simpler - just check if file exists and is valid JSON
        if not json_path.exists():
            st.error(f"Validation failed: JSON file '{json_path.name}' not found.")
            return ["json_file"]

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return []  # No missing fields for 2nd layer
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"Validation failed due to invalid JSON: {e}")
            return ["json_file"]

    def process_excel_to_json(self, excel_path: Path, json_output_dir: Path, **kwargs) -> Tuple[Path, str]:
        """Process Excel using Second_Layer script - Create initial JSON, invoice details added later"""
        DATA_PARSER_DIR = kwargs.get('data_parser_dir')

        identifier = Path(excel_path).stem
        json_path = json_output_dir / f"{identifier}.json"

        # Call the original script to create initial JSON (without invoice details)
        with st.spinner("Processing Excel file..."):
            cmd = [
                sys.executable, "-m", "data_parser.second_layer_main",
                str(excel_path),
                "-o", str(json_path)
            ]

            try:
                sub_env = os.environ.copy()
                sub_env['PYTHONPATH'] = os.pathsep.join(sys.path)
                self._run_subprocess(cmd, cwd=DATA_PARSER_DIR, identifier_for_error=identifier, env=sub_env)
                # Check if the script actually succeeded (JSON file was created)
                if json_path.exists() and json_path.stat().st_size > 0:
                    st.success(f"Excel processing complete: '{json_path.name}' created.")
                else:
                    st.error("Excel processing FAILED - no JSON file created.")
                    raise RuntimeError("Excel processing failed to create a JSON file.")

            except subprocess.CalledProcessError as e:
                # The _run_subprocess method logs the error to streamlit, but we re-raise
                # a more informative error to halt execution and provide context.
                error_message = f"2nd Layer Excel to JSON script failed for '{identifier}'. STDERR: {e.stderr}"
                raise RuntimeError(error_message) from e

        return json_path, identifier

    def get_override_ui_config(self) -> Dict[str, Any]:
        """Return UI config for 2nd layer overrides"""
        return {
            "inv_ref": {"type": "text_input", "label": "Invoice Reference", "default": "auto", "auto_populate_filename": True},
            "inv_date": {"type": "date_input", "label": "Invoice Date", "default": "today"},
            "unit_price": {"type": "number_input", "label": "Unit Price", "default": 0.61, "min": 0.0, "step": 0.01}
        }

    def _update_and_aggregate_json(self, json_path: Path, po_number: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Read footer_data from JSON (calculated by data parser) and return summary.
        The calculation is now done in the data parser, not here.
        Footer data now has two structures:
        - table_totals: per-table totals
        - grand_total: overall totals across all tables
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get footer_data calculated by the data parser
            footer_data = data.get('footer_data', {})
            aggregated_summary = data.get('aggregated_summary', {})
            
            # Get grand_total from footer_data (new structure)
            # Support both old flat structure and new nested structure
            if 'grand_total' in footer_data:
                grand_total = footer_data.get('grand_total', {})
            else:
                # Fallback for old structure
                grand_total = footer_data
            
            # Build summary_data from grand_total and aggregated_summary
            summary_data = {
                "po_number": po_number,
                "pcs": grand_total.get('total_pcs', 0),
                "sqft": float(grand_total.get('total_sqft', 0)),
                "net": float(grand_total.get('total_net', 0)),
                "gross": float(grand_total.get('total_gross', 0)),
                "cbm": float(grand_total.get('total_cbm', 0)),
                "amount": float(grand_total.get('total_amount', 0)),
                "pallet_count": grand_total.get('total_pallets', 0),
                "item": aggregated_summary.get('item', 'N/A'),
                "po": aggregated_summary.get('po', 'N/A'),
            }
            
            # Update metadata with invoice details from kwargs
            inv_ref = kwargs.get('inv_ref')
            inv_date = kwargs.get('inv_date')
            unit_price = kwargs.get('unit_price')
            
            cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
            creating_date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            # Update JSON with metadata
            if 'metadata' not in data:
                data['metadata'] = {}
            
            data['metadata']['inv_ref'] = inv_ref
            data['metadata']['inv_date'] = inv_date
            data['metadata']['unit_price'] = unit_price
            data['metadata']['creating_date'] = creating_date_str
            data['metadata']['po_number'] = po_number
            
            # Write updated data back to JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False, default=str)
            
            return summary_data
            
        except Exception as e:
            logging.error(f"Error in _update_and_aggregate_json: {e}")
            return None

    def apply_overrides(self, json_path: Path, overrides: Dict[str, Any]) -> bool:
        """Apply overrides to 2nd layer JSON using TARGET_HEADERS_MAP"""
        try:
            with open(json_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                was_modified = False

                cambodia_tz = ZoneInfo("Asia/Phnom_Penh")
                creating_date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d %H:%M:%S")

                # Handle invoice metadata overrides
                if 'metadata' not in data:
                    data['metadata'] = {}

                if overrides.get('inv_no'):
                    data['metadata']['inv_no'] = overrides['inv_no']
                    was_modified = True

                if overrides.get('inv_ref') and overrides['inv_ref'] != 'auto':
                    data['metadata']['inv_ref'] = overrides['inv_ref']
                    was_modified = True

                if overrides.get('unit_price') is not None:
                    try:
                        data['metadata']['unit_price'] = float(overrides['unit_price'])
                        was_modified = True
                    except (ValueError, TypeError):
                        # If conversion fails, skip this override
                        pass

                if overrides.get('inv_date'):
                    if overrides['inv_date'] == 'tomorrow':
                        tomorrow = datetime.datetime.now(cambodia_tz) + datetime.timedelta(days=1)
                        data['metadata']['inv_date'] = tomorrow.strftime("%Y-%m-%d")
                    elif overrides['inv_date'] == 'today':
                        today = datetime.datetime.now(cambodia_tz)
                        data['metadata']['inv_date'] = today.strftime("%Y-%m-%d")
                    else:
                        # Handle date objects from Streamlit date_input
                        if hasattr(overrides['inv_date'], 'strftime'):
                            # It's a date/datetime object
                            data['metadata']['inv_date'] = overrides['inv_date'].strftime("%Y-%m-%d")
                        else:
                            # It's already a string
                            data['metadata']['inv_date'] = str(overrides['inv_date'])
                    was_modified = True

                # Handle field-specific overrides in aggregated_summary
                if 'aggregated_summary' in data:
                    summary = data['aggregated_summary']

                    # Apply field overrides using TARGET_HEADERS_MAP knowledge
                    field_overrides = {k: v for k, v in overrides.items() if k.startswith('override_')}
                    for override_key, override_value in field_overrides.items():
                        if override_value.strip():  # Only apply non-empty overrides
                            field_name = override_key.replace('override_', '')
                            if field_name in summary:
                                summary[field_name] = override_value.strip()
                                was_modified = True

                # Update creating_date if any modifications were made
                if was_modified:
                    data['metadata']['creating_date'] = creating_date_str

                    # Write back to file
                    f.seek(0)
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.truncate()

                return was_modified

        except Exception as e:
            st.error(f"Failed to apply overrides: {e}")
            return False

    def get_generation_options(self) -> List[Dict[str, Any]]:
        """Return generation options for 2nd layer"""
        return [
            {"name": "Standard Invoice", "key": "standard", "flags": []}
        ]

    def generate_documents(self, json_path: Path, output_dir: Path, options: List[str], **kwargs) -> List[Path]:
        """Generate final documents for 2nd layer leather"""
        INVOICE_GEN_DIR = kwargs.get('invoice_gen_dir', SCRIPT_DIR / "invoice_gen")
        TEMPLATE_DIR = kwargs.get('template_dir', INVOICE_GEN_DIR / "TEMPLATE")
        CONFIG_DIR = kwargs.get('config_dir', INVOICE_GEN_DIR / "config")

        po_number = self._get_po_from_json(json_path) or "UNKNOWN"

        # JSON should already be updated with invoice details from the processing step
        # No need to update again here

        # Step 2: Generate documents
        with st.spinner("Generating final documents..."):
            cmd = [
                sys.executable,
                str(INVOICE_GEN_DIR / "hybrid_generate_invoice.py"),
                str(json_path),
                "--outputdir", str(output_dir),
                "--templatedir", str(TEMPLATE_DIR),
                "--configdir", str(CONFIG_DIR)
            ]

            # Add generation options
            for option in options:
                if option == "daf":
                    cmd.append("--daf")
                elif option == "combine":
                    cmd.append("--combine")

            self._run_subprocess(cmd, cwd=INVOICE_GEN_DIR, identifier_for_error=po_number)

            import time
            time.sleep(1.0)  # Allow files to be fully written

            st.success("Documents generated successfully!")

            # Find generated files
            generated_files = list(output_dir.glob(f"* {po_number}.xlsx"))

            if not generated_files:
                st.warning(f"No files found matching pattern '* {po_number}.xlsx' in {output_dir}")
                # Try broader search
                all_files = list(output_dir.glob("*.xlsx"))
                if all_files:
                    st.info(f"Found {len(all_files)} XLSX files: {[f.name for f in all_files]}")
                    generated_files = all_files
                else:
                    st.error("No XLSX files found in output directory")
        return generated_files

    def _get_po_from_json(self, json_path: Path) -> Optional[str]:
        """Extract PO number from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Try to get PO from aggregated_summary first
            if 'aggregated_summary' in data and 'po' in data['aggregated_summary']:
                po_value = data['aggregated_summary']['po']
                if po_value and str(po_value).strip():
                    return str(po_value).strip()

            # Fallback to raw_data
            if 'raw_data' in data:
                for table_data in data['raw_data'].values():
                    if 'po' in table_data and table_data['po']:
                        first_po = table_data['po'][0] if isinstance(table_data['po'], list) and table_data['po'] else table_data['po']
                        if first_po and str(first_po).strip():
                            return str(first_po).strip()

        except Exception:
            pass

        return None