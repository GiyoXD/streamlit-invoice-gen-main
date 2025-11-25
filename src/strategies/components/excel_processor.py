# Excel Processor Component
# Handles Excel file processing and validation

import streamlit as st
import openpyxl
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, List
from abc import ABC, abstractmethod


class ExcelProcessor:
    """Component for processing Excel files to JSON format"""

    def __init__(self):
        # Get the project root directory
        self.script_dir = Path(__file__).parent.parent.parent.parent

    def validate_excel_structure(self, excel_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate Excel data structure and return (is_valid, warnings_list)"""
        warnings = []

        try:
            workbook = openpyxl.load_workbook(excel_path, data_only=True)

            # Check if we have worksheets
            if len(workbook.worksheets) == 0:
                warnings.append("❌ Excel file has no worksheets")
                return False, warnings

            # Check each worksheet for required data structure
            valid_sheets = 0
            for sheet in workbook.worksheets:
                sheet_name = sheet.title

                # Get all values from the sheet
                data = []
                for row in sheet.iter_rows(values_only=True):
                    if any(cell for cell in row):  # Skip empty rows
                        data.append(row)

                if len(data) < 2:  # Need at least header + 1 data row
                    warnings.append(f"⚠️ Sheet '{sheet_name}' has insufficient data (less than 2 rows)")
                    continue

                # Check for required columns in header
                header = [str(cell).lower().strip() if cell else "" for cell in data[0]]

                missing_cols = []
                for col in required_columns:
                    if not any(col in h or h in col for h in header):
                        missing_cols.append(col)

                if missing_cols:
                    warnings.append(f"⚠️ Sheet '{sheet_name}' missing columns: {', '.join(missing_cols)}")
                else:
                    valid_sheets += 1

                    # Check data quality
                    data_rows = data[1:]  # Skip header
                    if len(data_rows) == 0:
                        warnings.append(f"⚠️ Sheet '{sheet_name}' has header but no data rows")
                    else:
                        # Check for empty values in required columns
                        empty_count = 0
                        for row_idx, row in enumerate(data_rows, 2):  # Start from row 2 (1-indexed)
                            for col_idx, cell in enumerate(row):
                                if col_idx < len(header) and any(req in header[col_idx] for req in required_columns):
                                    if cell is None or str(cell).strip() == "":
                                        empty_count += 1

                        if empty_count > 0:
                            warnings.append(f"⚠️ Sheet '{sheet_name}' has {empty_count} empty cells in required columns")

            if valid_sheets == 0:
                warnings.append("❌ No worksheets contain the required data structure")
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

    def process_to_json(self, excel_path: Path, json_output_dir: Path, strategy_name: str = "default") -> Tuple[Path, str]:
        """Process Excel file to JSON using create_json automation script"""
        identifier = Path(excel_path).stem
        json_path = json_output_dir / f"{identifier}.json"

        # Get the path to create_json/main.py
        create_json_script = self.script_dir / "data_parser" / "main.py"

        with st.spinner(f"Processing '{identifier}' to generate JSON..."):
            # Use the correct CLI arguments that main.py actually supports
            command = [
                sys.executable,
                "-m", "data_parser.main",
                "--input-excel", str(excel_path),
                "--output-dir", str(json_output_dir)
            ]
            try:
                # We use the generic subprocess runner from base strategy
                # For now, we'll implement a basic subprocess call
                sub_env = os.environ.copy()
                sub_env['PYTHONPATH'] = os.pathsep.join(sys.path)
                
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.script_dir,
                    encoding='utf-8',
                    errors='replace',
                    env=sub_env
                )
                st.success("Excel processing completed.")
            except subprocess.CalledProcessError as e:
                error_msg = ((e.stdout or '') + (e.stderr or '')).lower()
                if any(keyword in error_msg for keyword in ['config', 'template', 'not found', 'missing', 'no such file']):
                    st.error(f"**Configuration Error:** No company configuration found for PO **{identifier}**.")
                    st.warning("Please ensure a company is assigned to this PO in the **Company Setup** page before generating documents.")
                    if st.button("🏢 Go to Company Setup", key=f"setup_{strategy_name}_{identifier}", use_container_width=True):
                        st.switch_page("pages/3_SHIPPING_HEADER.py")
                else:
                    st.error(f"A process failed to execute. Error: {e.stderr or e.stdout or 'Unknown error'}")
                    st.error(f"Command that failed: {' '.join(command)}")
                    st.error(f"Working directory: {self.script_dir}")
                    st.error(f"Return code: {e.returncode}")
                raise RuntimeError("Excel to JSON processing script failed.") from e

        # Verify that the JSON file was created and is not empty
        if not json_path.exists() or json_path.stat().st_size == 0:
            st.error("The processing script ran but did not create a valid JSON file.")
            raise RuntimeError("Excel processing failed to create a JSON file.")

        return json_path, identifier