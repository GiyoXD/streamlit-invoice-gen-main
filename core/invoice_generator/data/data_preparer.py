from typing import Any, Union, Dict, List, Tuple
from decimal import Decimal
import logging
logger = logging.getLogger(__name__)

def parse_mapping_rules(
    mapping_rules: Dict[str, Any],
    column_id_map: Dict[str, int],
    idx_to_header_map: Dict[int, str]
) -> Dict[str, Any]:
    """
    Parses the mapping rules from a standardized, ID-based configuration.

    This function is refined to handle different mapping structures, such as a
    flat structure for aggregation sheets and a nested 'data_map' for table-based sheets.

    Args:
        mapping_rules: The raw mapping rules dictionary from the sheet's configuration.
        column_id_map: A dictionary mapping column IDs to their 1-based column index.
        idx_to_header_map: A dictionary mapping a column index back to its header text.

    Returns:
        A dictionary containing all the parsed information required for data filling.
    """
    # --- Initialize all return values ---
    parsed_result = {
        "static_value_map": {},
        "initial_static_col1_values": [],
        "dynamic_mapping_rules": {},
        "formula_rules": {},
        "col1_index": -1,
        "num_static_labels": 0,
        "static_column_header_name": None,
        "apply_special_border_rule": False
    }

    covered_col_ids = set()

    # --- Process all rules in a single, intelligent pass ---
    for rule_key, rule_value in mapping_rules.items():
        if not isinstance(rule_value, dict):
            continue # Skip non-dictionary rules

        # --- Handler for nested 'data_map' (used by 'processed_tables_multi') ---
        if rule_key == "data_map":
            # The entire dictionary under "data_map" is our set of dynamic rules.
            parsed_result["dynamic_mapping_rules"].update(rule_value)
            continue

        rule_type = rule_value.get("type")

        # --- Handler for Initial Static Rows ---
        if rule_type == "initial_static_rows":
            static_column_id = rule_value.get("column_header_id")
            target_col_idx = column_id_map.get(static_column_id)

            if target_col_idx:
                parsed_result["static_column_header_name"] = idx_to_header_map.get(target_col_idx)
                parsed_result["col1_index"] = target_col_idx
                parsed_result["initial_static_col1_values"] = rule_value.get("values", [])
                parsed_result["num_static_labels"] = len(parsed_result["initial_static_col1_values"])
                
                parsed_result["formula_rules"][target_col_idx] = {
                    "template": rule_value.get("formula_template"),
                    "input_ids": rule_value.get("inputs", [])
                }
            else:
                logger.warning(f"Warning: Initial static rows column with ID '{static_column_id}' not found.")
            continue

        # For all other rules, get the target column index using the RELIABLE ID
        # Support both legacy 'id' and bundled 'column' keys
        target_id = rule_value.get("id") or rule_value.get("column")
        if target_id:
            covered_col_ids.add(target_id)
        target_col_idx = column_id_map.get(target_id)

        # --- Handler for Formulas ---
        if rule_type == "formula":
            if target_col_idx:
                parsed_result["formula_rules"][target_col_idx] = {
                    "template": rule_value.get("formula_template"),
                    "input_ids": rule_value.get("inputs", [])
                }
            else:
                logger.warning(f"Warning: Could not find target column for formula rule with id '{target_id}'.")

        # --- Handler for Static Values ---
        elif "static_value" in rule_value:
            if target_col_idx:
                parsed_result["static_value_map"][target_col_idx] = rule_value["static_value"]
            else:
                logger.warning(f"Warning: Could not find target column for static_value rule with id '{target_id}'.")
        
        # --- Handler for top-level Dynamic Rules (used by 'aggregation') ---
        else:
            # If it's not a special rule, it's a dynamic mapping rule for the aggregation data type.
            parsed_result["dynamic_mapping_rules"][rule_key] = rule_value
            
    # --- Auto-Mapping: Add default rules for any column ID not explicitly covered ---
    for col_id in column_id_map:
        if col_id not in covered_col_ids and col_id != "col_static":
            # Create a default rule where the key is the col_id itself
            # This enables "Auto-Mapping" where data keys match column IDs
            parsed_result["dynamic_mapping_rules"][col_id] = {"column": col_id}

    return parsed_result

def _to_numeric(value: Any) -> Union[int, float, None, Any]:
    """
    Safely attempts to convert a value to a float or int.
    Handles strings with commas and returns the original value on failure.
    """
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            cleaned_val = value.replace(',', '').strip()
            if not cleaned_val:
                return None
            return float(cleaned_val) if '.' in cleaned_val else int(cleaned_val)
        except (ValueError, TypeError):
            return value # Return original string if conversion fails
    if isinstance(value, Decimal):
        return float(value)
    return value # Return original value for other types

def _apply_fallback(
    row_dict: Dict[int, Any],
    target_col_idx: int,
    mapping_rule: Dict[str, Any],
    DAF_mode: bool
):
    """
    Applies a fallback value to the row_dict based on the DAF_mode.
    
    Supports multiple fallback formats:
    1. Bundled config with mode-specific fallbacks:
       "fallback_on_none": "LEATHER", "fallback_on_DAF": "LEATHER"
    2. Bundled config with single fallback (same for both modes):
       "fallback": "LEATHER"
    3. Legacy format (same as #1)
    """
    # Priority 1: Check for mode-specific fallback keys (supports both DAF and non-DAF)
    if DAF_mode:
        if 'fallback_on_DAF' in mapping_rule:
            row_dict[target_col_idx] = mapping_rule['fallback_on_DAF']
            return
    else:
        if 'fallback_on_none' in mapping_rule:
            row_dict[target_col_idx] = mapping_rule['fallback_on_none']
            return
    
    # Priority 2: Try single 'fallback' key (same value for both modes)
    if 'fallback' in mapping_rule:
        row_dict[target_col_idx] = mapping_rule['fallback']
        return
    
    # Priority 3: Fallback to fallback_on_none if nothing else found
    row_dict[target_col_idx] = mapping_rule.get("fallback_on_none")

def prepare_data_rows(
    data_source_type: str,
    data_source: Union[Dict, List],
    dynamic_mapping_rules: Dict[str, Any],
    column_id_map: Dict[str, int],
    idx_to_header_map: Dict[int, str],
    desc_col_idx: int,
    num_static_labels: int,
    static_value_map: Dict[int, Any],
    DAF_mode: bool,
) -> Tuple[List[Dict[int, Any]], List[int], bool, int]:
    """
    Corrected version with typo fix and improved fallback flexibility.
    
    Validates that description field has fallback values defined.
    """
    # Validate description field has fallback - CRITICAL for proper invoice generation
    desc_mapping = None
    for field_name, mapping_rule in dynamic_mapping_rules.items():
        # Find description field (can be named 'description', 'desc', etc.)
        if 'desc' in field_name.lower() and isinstance(mapping_rule, dict):
            desc_mapping = mapping_rule
            break
    
    if desc_mapping:
        has_fallback = any(key in desc_mapping for key in ['fallback_on_none', 'fallback_on_DAF', 'fallback'])
        if not has_fallback:
            logger.error(f"❌ CRITICAL: Description field '{field_name}' is missing fallback configuration!")
            logger.error(f"   Description mapping: {desc_mapping}")
            logger.error(f"   REQUIRED: At least one of 'fallback_on_none', 'fallback_on_DAF', or 'fallback' must be defined")
            logger.error(f"   This can cause empty description cells when source data is None/missing")
            logger.warning(f"warning!!  Add fallback to config: \"fallback_on_none\": \"LEATHER\", \"fallback_on_DAF\": \"LEATHER\"")
    else:
        logger.warning(f"warning!!  No description field found in dynamic_mapping_rules - this may cause issues")
    
    data_rows_prepared = []
    pallet_counts_for_rows = []
    num_data_rows_from_source = 0
    dynamic_desc_used = False
    
    NUMERIC_IDS = {"col_pcs", "col_sqft", "col_unit_price", "col_amount", "col_net", "col_gross", "col_cbm"}

    # --- Handler for DAF Aggregation (Uses new fallback logic) ---
    if data_source_type == 'DAF_aggregation':
        DAF_data = data_source or {}
        num_data_rows_from_source = len(DAF_data)
        id_to_data_key_map = {"col_po": "col_po", "col_item": "col_item", "col_desc": "col_desc", "col_qty_sf": "col_qty_sf", "col_amount": "col_amount"}
        price_col_idx = column_id_map.get("col_unit_price")
        
        for row_key in sorted(DAF_data.keys()):
            row_value_dict = DAF_data.get(row_key, {})
            row_dict = {}
            for col_id, data_key in id_to_data_key_map.items():
                target_col_idx = column_id_map.get(col_id)
                if not target_col_idx: continue
                
                # Assign value from source data
                val = row_value_dict.get(data_key)
                row_dict[target_col_idx] = val

            # Apply static values
            for col_idx, static_val in static_value_map.items():
                if col_idx not in row_dict:
                    row_dict[col_idx] = static_val
            
            data_rows_prepared.append(row_dict)
    
    if num_static_labels > len(data_rows_prepared):
        data_rows_prepared.extend([{}] * (num_static_labels - len(data_rows_prepared)))
    
    return data_rows_prepared, pallet_counts_for_rows, dynamic_desc_used, num_data_rows_from_source