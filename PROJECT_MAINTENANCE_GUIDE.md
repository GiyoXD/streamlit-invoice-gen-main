# Project Maintenance Guide

This document summarizes the key components of the **Invoice Generation System**. We have simplified the structure to use a single "source of truth".

## 1. Core Structure
**Everything** is now stored in `database/blueprints`. There is no separate "new vs old" folder anymore.

| Type | Path | Description |
| :--- | :--- | :--- |
| **Configs** | `database/blueprints/config/bundled` | Folder for each company (e.g., `CT_config`, `JF_config`). |
| **Templates** | `database/blueprints/template` | Excel template files. |
| **Mappings** | `database/blueprints/config/mapper` | Global column mapping rules. |

## 2. Workflows

### A. Adding a New Company (`2_Add_New_Company.py`)
1.  You upload a file.
2.  The system saves the new config to `database/blueprints/config/bundled/{Prefix}_config`.
3.  The system saves the template to `database/blueprints/template/{Prefix}.xlsx`.

### B. Generating an Invoice (`0_Generate_Invoice.py`)
1.  You upload a shipping list.
2.  The system looks in `database/blueprints/config/bundled` to find the matching config.
3.  If it guesses wrong, you can use the **Dropdown** to pick the right one.

## 3. Troubleshooting

*   **"Command Failed (ImportError)":** We fixed `core/config_manager/main.py` to run correctly.
*   **"Path Not Found":** Use the Dropdown menu in the UI. It will show you exactly what is available in the `blueprints` folder.
