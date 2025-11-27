# Config Manager Rewrite Plan

## Current State

### Problem
The current config manager in `src/config_manager/` generates configs in the **old format** (like `config/CLW_config.json`) which is NOT compatible with the invoice generator.

The invoice generator requires configs in the **JF bundle format** stored in `src/invoice_generator/src/config_bundled/`.

### Working Example: JF Config Bundle
Location: `src/invoice_generator/src/config_bundled/JF_config/JF_config.json`

---

## JF Bundle Config Structure Analysis

```
{
  "_meta": { version, customer, description },
  
  "data_preparation_module_hint": { priority, numbers_per_group },
  
  "features": { 
    enable_text_replacement, enable_auto_calculations, debug_mode, etc.
  },
  
  "processing": {
    "sheets": ["Invoice", "Contract", "Packing list"],
    "data_sources": {
      "Invoice": "aggregation",
      "Contract": "aggregation", 
      "Packing list": "processed_tables_multi"
    }
  },
  
  "styling_bundle": {
    "defaults": { borders config },
    "Invoice": {
      "columns": { col_id -> { format, alignment, width } },
      "row_contexts": { header/data/footer -> { bold, font_size, row_height } }
    },
    "Contract": { ... },
    "Packing list": { ... }
  },
  
  "layout_bundle": {
    "Invoice": {
      "structure": { header_row, columns: [{ id, header, format }] },
      "data_flow": { mappings: { field -> { column, source_key/source_value } } },
      "content": { static: { col_id -> [lines] } },
      "footer": { 
        total_text_column_id, sum_column_ids, 
        add_ons: { weight_summary, leather_summary }
      }
    },
    "Contract": { ... },
    "Packing list": { ... }
  },
  
  "defaults": { footer defaults }
}
```

---

## Key Config Sections

### 1. `processing.data_sources`
Maps sheets to data source types:
- `"aggregation"` → Uses `standard_aggregation_results` or `custom_aggregation_results`
- `"processed_tables_multi"` → Uses `processed_tables_data` (row-level data)

### 2. `layout_bundle.{sheet}.structure`
Defines column layout:
```json
{
  "header_row": 21,
  "columns": [
    { "id": "col_po", "header": "P.O. Nº", "format": "@" },
    { "id": "col_qty_sf", "header": "Quantity(SF)", "format": "#,##0.00" }
  ]
}
```

### 3. `layout_bundle.{sheet}.data_flow.mappings`
Maps data fields to columns:
```json
{
  "po": { "column": "col_po", "source_key": 0 },
  "sqft": { "column": "col_qty_sf", "source_value": "sqft_sum" },
  "amount": { "column": "col_amount", "formula": "{col_qty_sf} * {col_unit_price}" }
}
```

### 4. `layout_bundle.{sheet}.footer`
Footer configuration with add-ons:
```json
{
  "total_text_column_id": "col_po",
  "total_text": "TOTAL OF:",
  "pallet_count_column_id": "col_desc",
  "sum_column_ids": ["col_qty_pcs", "col_qty_sf", "col_net", "col_gross", "col_cbm"],
  "add_ons": {
    "leather_summary": { "enabled": true, "mode": ["daf", "standard"] },
    "weight_summary": { "enabled": true }
  }
}
```

---

## New Data Parser Output (CLW.json)

The data parser now outputs:
```json
{
  "metadata": { ... },
  "processed_tables_data": { "1": {...}, "2": {...} },
  
  "footer_data": {
    "table_totals": { "1": {...}, "2": {...} },
    "grand_total": { total_pcs, total_sqft, total_net, total_gross, total_cbm, total_amount, total_pallets },
    "add_ons": {
      "leather_summary_addon": {
        "BUFFALO": { pcs, sqft, net, gross, pallet_count },
        "COW": { pcs, sqft, net, gross, pallet_count }
      }
    }
  },
  
  "standard_aggregation_results": { ... },
  "custom_aggregation_results": { ... },
  "normal_aggregate_per_po_with_pallets": [ { po, item, desc, unit_price, sqft, amount, pallet_count, net, gross, cbm } ],
  "final_DAF_compounded_result": { ... }
}
```

---

## Rewrite Options

### Option A: Minimal - Just Create CLW Bundle Config Manually
1. Copy JF_config structure
2. Adjust for CLW template specifics (header rows, columns, etc.)
3. Test with CLW.json data

**Pros**: Quick, can test immediately
**Cons**: Manual work for each new customer

### Option B: Full Rewrite - New Config Generator
1. Analyze Excel template to extract:
   - Sheet names
   - Header positions  
   - Column structure (merged cells, widths)
   - Font/style info
2. Generate bundle config automatically
3. Store in `config_bundled/` directory

**Pros**: Automated for all customers
**Cons**: More development time

### Option C: Hybrid - Template-Based Generator
1. Create base templates for common invoice types
2. Config generator fills in customer-specific values
3. User can customize/override

---

## Recommended Approach

**Start with Option A** to test the pipeline works, then **move to Option C**.

### Immediate Tasks:
1. [ ] Create `CLW_config/CLW_config.json` in bundle format
2. [ ] Test invoice generation with CLW.json + CLW_config
3. [ ] Document the bundle config format
4. [ ] Plan the new config generator architecture

### Future Tasks:
1. [ ] Extract template analysis from Excel
2. [ ] Build config generator with template inheritance
3. [ ] Add validation layer
4. [ ] Create CLI for new config generation

---

## Questions to Discuss

1. **Template variations**: How different are CLW templates from JF? Same sheet structure?

2. **Footer add-ons**: The `footer_data.add_ons.leather_summary_addon` we just added - how should the config reference it?

3. **Aggregation format**: CLW uses which aggregation type for Invoice/Contract sheets?

4. **Static content**: What goes in the "Mark & Nº" column for CLW?

5. **Priority**: Should we just manually create CLW config first to test, or jump into rewriting the generator?
