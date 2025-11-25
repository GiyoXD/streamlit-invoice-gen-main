# Invoice Generation Strategies - Base Strategy Class
# Refactored from invoice_strategies.py for better organization

import streamlit as st
import os
import sys
import subprocess
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
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
# Add project subdirectories to the Python path to ensure correct module resolution
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "src" / "data_parser"))
sys.path.insert(0, str(SCRIPT_DIR / "src" / "invoice_generator"))


class InvoiceGenerationStrategy(ABC):
    """Abstract base class for invoice generation strategies"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Return list of required fields for validation"""
        pass

    @abstractmethod
    def validate_excel_data(self, excel_path: Path) -> Tuple[bool, List[str]]:
        """Validate Excel data structure and return (is_valid, warnings_list)"""
        pass

    @abstractmethod
    def validate_json_data(self, json_path: Path) -> List[str]:
        """Validate JSON data and return list of missing fields"""
        pass

    @abstractmethod
    def process_excel_to_json(self, excel_path: Path, json_output_dir: Path, **kwargs) -> Tuple[Path, str]:
        """Process Excel file to JSON and return (json_path, identifier)"""
        pass

    @abstractmethod
    def get_override_ui_config(self) -> Dict[str, Any]:
        """Return UI configuration for manual overrides"""
        pass

    @abstractmethod
    def apply_overrides(self, json_path: Path, overrides: Dict[str, Any]) -> bool:
        """Apply user overrides to JSON data"""
        pass

    @abstractmethod
    def get_generation_options(self) -> List[Dict[str, Any]]:
        """Return available generation options (Normal, DAF, Combine, etc.)"""
        pass

    @abstractmethod
    def generate_documents(self, json_path: Path, output_dir: Path, options: List[str], **kwargs) -> List[Path]:
        """Generate final documents and return list of generated files"""
        pass

    def _run_subprocess(self, command: List[str], cwd: Path, identifier_for_error: str, env: Optional[Dict[str, str]] = None) -> None:
        """A shared helper to run a subprocess and handle common errors."""
        sub_env = env if env is not None else os.environ.copy()
        sub_env['PYTHONIOENCODING'] = 'utf-8'

        # Ensure the subprocess has the same Python path as the main process
        if 'PYTHONPATH' not in sub_env:
            sub_env['PYTHONPATH'] = str(SCRIPT_DIR)
        else:
            # Prepend our project directory to existing PYTHONPATH
            existing_paths = sub_env['PYTHONPATH'].split(os.pathsep)
            if str(SCRIPT_DIR) not in existing_paths:
                sub_env['PYTHONPATH'] = os.pathsep.join([str(SCRIPT_DIR)] + existing_paths)

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                errors='replace',
                env=sub_env
            )
            # Optional: Log success if needed
            # st.info(f"Subprocess executed successfully: {result.stdout}")

        except subprocess.CalledProcessError as e:
            error_msg = ((e.stdout or '') + (e.stderr or '')).lower()
            if any(keyword in error_msg for keyword in ['config', 'template', 'not found', 'missing', 'no such file']):
                self._show_config_error(identifier_for_error)
            else:
                st.error(f"A process failed to execute. Error: {e.stderr or e.stdout or 'Unknown error'}")
                st.error(f"Command that failed: {' '.join(command)}")
                st.error(f"Working directory: {cwd}")
                st.error(f"Return code: {e.returncode}")
            raise # Re-raise the exception to halt execution

    def _show_config_error(self, po_number: str):
        """Displays a consistent, formatted error message when a PO config is missing."""
        st.error(f"**Configuration Error:** No company configuration found for PO **{po_number}**.")
        st.warning(
            "Please ensure a company is assigned to this PO in the **Company Setup** page "
            "before generating documents."
        )
        # Append po_number to the key to ensure uniqueness when called multiple times
        if st.button("🏢 Go to Company Setup", key=f"setup_{self.name.replace(' ', '_')}_{po_number}", use_container_width=True):
            st.switch_page("pages/3_SHIPPING_HEADER.py")