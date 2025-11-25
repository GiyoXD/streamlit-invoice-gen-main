from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# This model now directly represents the structure of the input JSON data file.
class InvoiceData(BaseModel):
    """
    Represents the raw data loaded from an input JSON file,
    matching the structure used by the original invoice_generator.

    This model is intentionally flexible to accommodate the complex,
    nested data structures used by the original system. It uses Pydantic's
    'extra = "allow"' configuration to accept any fields without validation,
    ensuring compatibility with existing data formats.

    The original invoice_generator expects data with structures like:
    - metadata: General invoice information
    - processed_tables_data: Table data organized by table number
    - raw_data: Original unprocessed data

    Example:
        >>> data = InvoiceData(
        ...     metadata={"workbook_filename": "CLW250039.xlsx"},
        ...     processed_tables_data={
        ...         "1": {
        ...             "po": ["PT25P82", "PT26797"],
        ...             "item": [140489, 140519]
        ...         }
        ...     }
        ... )
    """
    # Using Dict[str, Any] to flexibly handle any data structure.
    class Config:
        extra = 'allow'

# This model represents the structure of the company-specific configuration files.
class CompanyConfig(BaseModel):
    """
    Represents the configuration for a specific company, mirroring the
    structure of the config files in invoice_generator/config.

    This model is also flexible to accommodate the complex configuration
    structures used by the original system. Company configurations typically
    include template information, data mappings, styling rules, and processing
    instructions.

    The original system uses configurations with structures like:
    - template_filename: Name of the Excel template file
    - sheets_to_process: List of worksheet names to process
    - data_mapping: How to map data fields to Excel columns
    - styling: Font, color, and formatting rules

    Example:
        >>> config = CompanyConfig(
        ...     template_filename="CLW_template.xlsx",
        ...     sheets_to_process=["Invoice", "Packing List"],
        ...     data_mapping={
        ...         "Invoice": {
        ...             "start_row": 10,
        ...             "mappings": {"po": "PO Number", "item": "Item Code"}
        ...         }
        ...     }
        ... )
    """
    # Using Dict[str, Any] to flexibly handle any config structure.
    class Config:
        extra = 'allow'
