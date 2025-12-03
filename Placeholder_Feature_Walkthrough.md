# Walkthrough - Placeholder Processor Implementation

I have successfully implemented the `PlaceholderProcessor` to allow simple text replacement in Excel templates without complex table generation.

## Changes

### 1. New Processor Class
Created `core/invoice_generator/processors/placeholder_processor.py`.
-   **Logic**:
    1.  Copies the entire template sheet (cells, styles, dimensions, merges) to the output.
    2.  Iterates through all cells.
    3.  Replaces `{{KEY}}` with values from the input JSON.

### 2. Integration
Modified `core/invoice_generator/generate_invoice.py`.
-   Added logic to check for `data_source_indicator == "placeholder"`.
-   Instantiates `PlaceholderProcessor` instead of the table processors when this flag is set.

## Verification Results

### Automated Test
I created a test script `tests/verify_placeholder.py` that:
1.  Generates a dummy `PlaceholderTest.xlsx` template with `{{INVOICE_NUM}}`, `{{CUSTOMER}}`, `{{AMOUNT}}`.
2.  Generates a dummy `PlaceholderTest.json` data file.
3.  Generates a `PlaceholderTest_bundle_config.json` with `data_sources: {"Sheet1": "placeholder"}`.
4.  Runs the invoice generation.
5.  Verifies the output Excel file contains the replaced values.

**Result**:
```
INFO:core.invoice_generator.processors.placeholder_processor:Completed Placeholder Processing. Replaced 3 values.
Generation completed. Verifying output...
B1: INV-TEST-001
B2: Test Customer
B3: 999.99
SUCCESS: All placeholders replaced correctly.
```

## Mapping Logic (How it works)

The `PlaceholderProcessor` uses **Direct Key Matching**. You do **not** need a separate mapping configuration in the bundle config.

1.  **Input Data (JSON)**:
    ```json
    {
        "INVOICE_NUM": "INV-2025-001",
        "CUSTOMER_NAME": "Acme Corp"
    }
    ```

2.  **Excel Template**:
    Simply use the JSON keys inside double curly braces:
    -   Cell A1: `Invoice: {{INVOICE_NUM}}`
    -   Cell B1: `Customer: {{CUSTOMER_NAME}}`

The processor automatically finds `{{INVOICE_NUM}}` and replaces it with `"INV-2025-001"`.
**Rule**: The text inside `{{...}}` must EXACTLY match the key in your JSON data.

## How to Use
To use this new feature, ensure your bundle config has:
```json
"processing": {
    "processing_order": ["YourSheetName"],
    "sheet_processing_types": {
        "YourSheetName": "placeholder"
    }
}
```

> [!TIP]
> **New Clearer Configuration Names**
> We've updated the configuration to use more descriptive names:
> *   `processing_order` (formerly `sheets`): Defines the **Order** of execution.
> *   `sheet_processing_types` (formerly `data_sources`): Defines the **Type** of processing.
>
> *Note: The old names (`sheets`, `data_sources`) still work for backward compatibility.*
And your Excel template uses `{{KEY}}` placeholders matching your JSON data keys.
