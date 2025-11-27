"""
Bundle Config Generator

This module provides the BundleConfigGenerator class that generates configuration files
in the new "JF bundle format" required by the invoice generator.
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config_generator.quantity_data_loader import QuantityDataLoader, QuantityDataLoaderError
from ..config_generator.models import QuantityAnalysisData, SheetData

class BundleConfigGenerator:
    """
    Generator for creating invoice configurations in the new bundle format.
    
    This class takes quantity analysis data and produces a JSON configuration
    that follows the structure defined in JF_config.json, including:
    - _meta
    - processing
    - styling_bundle
    - layout_bundle
    - defaults
    """
    
    def __init__(self, mapping_config_path: str = None):
        """
        Initialize the BundleConfigGenerator.
        
        Args:
            mapping_config_path: Path to the mapping configuration file.
                               If None, attempts to find it relative to this file.
        """
        self.logger = logging.getLogger('BundleConfigGenerator')
        self._setup_logger()
        
        self.quantity_data_loader = QuantityDataLoader()
        
        if mapping_config_path is None:
            # Default path: src/config_manager/mapping_config.json
            # Current file: src/config_manager/generate_config/bundle_generator/bundle_generator.py
            base_dir = Path(__file__).resolve().parent.parent.parent
            mapping_config_path = str(base_dir / "mapping_config.json")
            
        self.mapping_config = self._load_mapping_config(mapping_config_path)
        
    def _setup_logger(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _load_mapping_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load mapping config from {path}: {e}")
            return {}

    def generate_config(self, quantity_data_path: str, output_path: str) -> bool:
        """
        Generate the bundle configuration file.
        
        Args:
            quantity_data_path: Path to the quantity analysis JSON file.
            output_path: Path where the generated configuration should be written.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.logger.info(f"Generating bundle config from {quantity_data_path}")
            
            # Load quantity data
            quantity_data = self.quantity_data_loader.load_quantity_data(quantity_data_path)
            
            # Build the bundle structure
            bundle_config = self._build_bundle_config(quantity_data)
            
            # Write to file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(bundle_config, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Bundle config written to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate bundle config: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _build_bundle_config(self, quantity_data: QuantityAnalysisData) -> Dict[str, Any]:
        """Construct the complete bundle configuration dictionary."""
        
        # Map sheet names to standard names (Invoice, Contract, Packing list)
        sheet_map = self._map_sheets(quantity_data.sheets)
        
        return {
            "_meta": {
                "config_version": "2.1_generated",
                "customer": "Generated", # TODO: Extract from filename or input
                "created": datetime.now().strftime("%Y-%m-%d"),
                "description": f"Auto-generated from {Path(quantity_data.file_path).name}"
            },
            "data_preparation_module_hint": {
                "priority": ["po"],
                "numbers_per_group_by_po": 7
            },
            "features": {
                "enable_text_replacement": False,
                "enable_auto_calculations": True,
                "debug_mode": False
            },
            "processing": self._build_processing_section(sheet_map),
            "styling_bundle": self._build_styling_bundle(quantity_data.sheets, sheet_map),
            "layout_bundle": self._build_layout_bundle(quantity_data.sheets, sheet_map),
            "defaults": {
                "footer": {
                    "show_total": True,
                    "show_pallet_count": True,
                    "total_text": "TOTAL:",
                    "merge_total_cells": True,
                    "sum_columns": ["col_qty_pcs", "col_qty_sf", "col_net", "col_gross", "col_cbm"]
                }
            }
        }

    def _map_sheets(self, sheets: List[SheetData]) -> Dict[str, str]:
        """Map actual sheet names to standard template names (Invoice, Contract, Packing list)."""
        mapping = {}
        name_mappings = self.mapping_config.get("sheet_name_mappings", {}).get("mappings", {})
        
        for sheet in sheets:
            # Try exact match
            if sheet.sheet_name in name_mappings:
                mapping[sheet.sheet_name] = name_mappings[sheet.sheet_name]
                continue
                
            # Try case-insensitive
            found = False
            for k, v in name_mappings.items():
                if k.lower() == sheet.sheet_name.lower():
                    mapping[sheet.sheet_name] = v
                    found = True
                    break
            
            if not found:
                # Fallback: if name contains "invoice", map to Invoice, etc.
                lower_name = sheet.sheet_name.lower()
                if "invoice" in lower_name:
                    mapping[sheet.sheet_name] = "Invoice"
                elif "contract" in lower_name:
                    mapping[sheet.sheet_name] = "Contract"
                elif "packing" in lower_name:
                    mapping[sheet.sheet_name] = "Packing list"
                else:
                    self.logger.warning(f"Could not map sheet '{sheet.sheet_name}' to a standard type.")
        
        # If only one sheet exists and it wasn't mapped, assume it's the Invoice
        if len(sheets) == 1 and not mapping:
            sheet_name = sheets[0].sheet_name
            self.logger.info(f"Only one sheet found ('{sheet_name}'). Defaulting mapping to 'Invoice'.")
            mapping[sheet_name] = "Invoice"
            
        return mapping

    def _build_processing_section(self, sheet_map: Dict[str, str]) -> Dict[str, Any]:
        """Build the processing section."""
        standard_sheets = list(set(sheet_map.values()))
        
        data_sources = {}
        for std_name in standard_sheets:
            if std_name == "Packing list":
                data_sources[std_name] = "processed_tables_multi"
            else:
                data_sources[std_name] = "aggregation"
                
        return {
            "sheets": standard_sheets,
            "data_sources": data_sources
        }

    def _build_styling_bundle(self, sheets: List[SheetData], sheet_map: Dict[str, str]) -> Dict[str, Any]:
        """Build the styling bundle."""
        styling = {
            "defaults": {
                "borders": {
                    "default_border": "full_grid",
                    "default_style": "thin",
                    "exceptions": {
                        "col_static": "side_only"
                    }
                }
            }
        }
        
        for sheet in sheets:
            std_name = sheet_map.get(sheet.sheet_name)
            if not std_name:
                continue
                
            # Build columns styling
            columns_style = {}
            for header in sheet.header_positions:
                col_id = self._map_header_to_col_id(header.keyword)
                if col_id == "col_unknown":
                    continue
                    
                col_style = {
                    "format": "@", # Default text
                    "alignment": "center",
                    "width": 15 # Default width
                }
                
                # Apply specific formats based on col_id
                if col_id in ["col_qty_sf", "col_unit_price", "col_amount", "col_net", "col_gross"]:
                    col_style["format"] = "#,##0.00"
                elif col_id == "col_cbm":
                    col_style["format"] = "0.00"
                elif col_id == "col_qty_pcs":
                    col_style["format"] = "#,##0"
                elif col_id == "col_desc":
                    col_style["wrap_text"] = True
                    col_style["width"] = 25
                elif col_id == "col_static":
                    col_style["width"] = 25
                    
                columns_style[col_id] = col_style

            # Build row contexts
            row_contexts = {
                "header": {
                    "bold": True,
                    "font_size": sheet.header_font.size,
                    "font_name": sheet.header_font.name,
                    "border_style": "thin",
                    "row_height": 35 # Default
                },
                "data": {
                    "bold": False,
                    "font_size": sheet.data_font.size,
                    "font_name": sheet.data_font.name,
                    "border_style": "thin",
                    "row_height": 35 # Default
                },
                "footer": {
                    "bold": True,
                    "font_size": sheet.header_font.size, # Usually same as header
                    "font_name": sheet.header_font.name,
                    "border_style": "thin",
                    "row_height": 35
                }
            }
            
            styling[std_name] = {
                "columns": columns_style,
                "row_contexts": row_contexts
            }
            
        return styling

    def _build_layout_bundle(self, sheets: List[SheetData], sheet_map: Dict[str, str]) -> Dict[str, Any]:
        """Build the layout bundle."""
        layout = {}
        
        for sheet in sheets:
            std_name = sheet_map.get(sheet.sheet_name)
            if not std_name:
                continue
                
            # 1. Structure
            columns_structure = []
            # Sort headers by column index to ensure correct order
            sorted_headers = sorted(sheet.header_positions, key=lambda x: x.column)
            
            for header in sorted_headers:
                col_id = self._map_header_to_col_id(header.keyword)
                col_def = {
                    "id": col_id,
                    "header": header.keyword
                }
                
                # Add format to structure if needed (some builders look here)
                if col_id in ["col_qty_sf", "col_unit_price", "col_amount"]:
                    col_def["format"] = "#,##0.00"
                elif col_id == "col_po":
                    col_def["format"] = "@"
                    
                columns_structure.append(col_def)

            structure = {
                "header_row": sheet.start_row,
                "columns": columns_structure
            }
            
            # 2. Data Flow
            mappings = self._generate_mappings(std_name)
            
            # 3. Content (Static)
            content = {}
            if std_name in ["Invoice", "Packing list"]:
                content["static"] = {
                    "col_static": [
                        "VENDOR#:",
                        "Des: LEATHER",
                        "MADE IN CAMBODIA"
                    ]
                }
            
            # 4. Footer
            footer = self._generate_footer_config(std_name, sheet)

            layout[std_name] = {
                "structure": structure,
                "data_flow": {"mappings": mappings},
                "content": content,
                "footer": footer
            }
            
        return layout

    def _map_header_to_col_id(self, header_text: str) -> str:
        """Map header text to column ID using mapping config."""
        mappings = self.mapping_config.get("header_text_mappings", {}).get("mappings", {})
        
        # Exact match
        if header_text in mappings:
            return mappings[header_text]
            
        # Normalized match (replace newlines)
        normalized = header_text.replace('\n', '\\n')
        if normalized in mappings:
            return mappings[normalized]
            
        # Case insensitive
        header_lower = header_text.lower()
        for k, v in mappings.items():
            if k.lower() == header_lower:
                return v
                
        return "col_unknown"

    def _generate_mappings(self, sheet_type: str) -> Dict[str, Any]:
        """Generate default mappings based on sheet type."""
        # These are standard mappings that usually work if column IDs are correct
        base_mappings = {
            "po": {"column": "col_po", "source_key": 0},
            "item": {"column": "col_item", "source_key": 1},
            "description": {
                "column": "col_desc", 
                "source_key": 3,
                "fallback_on_none": "LEATHER",
                "fallback_on_DAF": "LEATHER"
            },
            "sqft": {"column": "col_qty_sf", "source_value": "sqft_sum"},
            "unit_price": {"column": "col_unit_price", "source_key": 2},
            "amount": {"column": "col_amount", "formula": "{col_qty_sf} * {col_unit_price}"}
        }
        
        if sheet_type == "Packing list":
            # Packing list often has specific mappings
            base_mappings.update({
                "pcs": {"column": "col_qty_pcs"},
                "net": {"column": "col_net"},
                "gross": {"column": "col_gross"},
                "cbm": {"column": "col_cbm"}
            })
            
        return base_mappings

    def _generate_footer_config(self, sheet_type: str, sheet_data: SheetData) -> Dict[str, Any]:
        """Generate footer configuration."""
        
        # Default footer config
        footer = {
            "total_text_column_id": "col_po",
            "total_text": "TOTAL OF:",
            "pallet_count_column_id": "col_item", # Default guess
            "sum_column_ids": ["col_qty_sf", "col_amount"],
            "add_ons": {
                "weight_summary": {
                    "enabled": sheet_data.weight_summary_enabled,
                    "label_col_id": "col_po",
                    "value_col_id": "col_item",
                    "mode": ["daf", "standard"]
                },
                "leather_summary": {
                    "enabled": True, # Default to true for now
                    "mode": ["daf", "standard"]
                }
            }
        }
        
        if sheet_type == "Packing list":
            footer["sum_column_ids"].extend(["col_qty_pcs", "col_net", "col_gross", "col_cbm"])
            footer["pallet_count_column_id"] = "col_desc"
            
        return footer
