#!/usr/bin/env python3
"""
Command-line interface for Excel Analysis Tool.

This is the main entry point that can be run directly from the project root.
"""

import sys
import argparse
import json
from pathlib import Path

# Add the src directory to the Python path
# Get the absolute path to the directory where this script resides
script_dir = Path(__file__).resolve().parent

# Add the 'src' directory (located in the same folder as this script) to the Python path
sys.path.insert(0, str(script_dir / 'src'))

from analyzers.excel_analyzer import ExcelAnalyzer


def main():
    """Main CLI function that handles argument parsing and analysis execution."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Analyze Excel files to extract font information and start row positions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_excel.py file.xlsx
  python analyze_excel.py file.xlsx -o analysis_results.txt
  python analyze_excel.py file.xlsx --json -o results.json
  python analyze_excel.py file.xlsx -q --json -o results.json
  python analyze_excel.py /path/to/spreadsheet.xlsx --output results.txt
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to the Excel file to analyze'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path to save analysis results (optional, prints to console if not specified)',
        metavar='OUTPUT_FILE'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format instead of text format'
    )
    
    parser.add_argument(
        '-q', '--quantity-mode',
        action='store_true',
        help='Add PCS and SQFT columns after Quantity for packing list sheets'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Basic error handling for file access
    file_path = Path(args.file_path)
    
    # Check if file exists
    if not file_path.exists():
        print(f"Error: File not found: {args.file_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check if file has Excel extension
    if file_path.suffix.lower() not in ['.xlsx', '.xls']:
        print(f"Warning: File does not appear to be an Excel file: {args.file_path}", file=sys.stderr)
    
    # Check if file is readable
    try:
        with open(file_path, 'rb') as f:
            pass
    except PermissionError:
        print(f"Error: Permission denied accessing file: {args.file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot access file {args.file_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Run analysis and output results
    try:
        # Load mapping configuration
        # script_dir is core/config_manager/config_data_extractor
        project_root = script_dir.parent.parent.parent
        mapping_config_path = project_root / "data" / "config_manger_mapper" / "mapping_config.json"
        
        mapping_config = None
        if mapping_config_path.exists():
            try:
                with open(mapping_config_path, 'r', encoding='utf-8') as f:
                    mapping_config = json.load(f)
                print(f"Loaded mapping configuration from: {mapping_config_path}")
            except Exception as e:
                print(f"Warning: Could not load mapping config: {e}")
        
        analyzer = ExcelAnalyzer(quantity_mode=args.quantity_mode, mapping_config=mapping_config)
        
        # Choose output format
        if args.json:
            result_output = analyzer.analyze_and_output_json(str(file_path))
        else:
            result_output = analyzer.analyze_and_output_text(str(file_path))
        
        # Save to file if output path specified, otherwise print to console
        if args.output:
            output_path = Path(args.output)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result_output)
                format_type = "JSON" if args.json else "text"
                print(f"Analysis results saved to: {output_path} ({format_type} format)")
            except Exception as e:
                print(f"Error: Could not save to file {args.output}: {str(e)}", file=sys.stderr)
                sys.exit(1)
        else:
            print(result_output)
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Analysis failed - {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()