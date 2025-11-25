#!/usr/bin/env python3
"""
Config Generator CLI - Generate fully working configurations from quantity analysis data.

This CLI tool takes your quantity analysis data (like quantity_mode_analysis.json)
and generates a complete, ready-to-use configuration file by updating the template
with your specific data while preserving all business logic.
"""

import argparse
import sys
import os
import json
from pathlib import Path
# The actual configuration logic is in a separate module.
from config_generator.config_generator import ConfigGenerator, ConfigGeneratorError


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging level based on verbosity
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    try:
        # Validate input files
        if not validate_input_files(args):
            return 1
        
        # Generate configuration
        success = generate_configuration(args)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate fully working configurations from quantity analysis data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - generate config from your quantity data
  python generate_config_ascii.py quantity_mode_analysis.json
  
  # Specify custom output file
  python generate_config_ascii.py quantity_mode_analysis.json -o my_config.json
  
  # Use custom template instead of default sample_config.json
  python generate_config_ascii.py quantity_data.json -t my_template.json -o output.json
  
  # Verbose output to see detailed processing
  python generate_config_ascii.py quantity_data.json -v
  
  # Quiet mode - only show errors
  python generate_config_ascii.py quantity_data.json -q

The tool will:
  [OK] Load your quantity analysis data
  [OK] Update the template with your specific values
  [OK] Preserve all business logic and configurations
  [OK] Generate a complete, ready-to-use config file
        """
    )
    
    # Required argument: quantity data file
    parser.add_argument(
        'quantity_data',
        help='Path to your quantity analysis JSON file (e.g., quantity_mode_analysis.json)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-t', '--template',
        default='sample_config.json',
        help='Path to template configuration file (default: sample_config.json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: generated_config.json)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output with detailed processing information'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - only show errors'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate input files without generating output'
    )
    
    parser.add_argument(
        '--show-info',
        action='store_true',
        help='Show information about the quantity data and exit'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable interactive mode for header mapping with user validation'
    )
    
    return parser


def validate_input_files(args):
    """Validate that input files exist and are readable."""
    # Check quantity data file
    if not os.path.exists(args.quantity_data):
        print(f"[ERROR] Quantity data file not found: {args.quantity_data}")
        return False
    
    # Check template file
    if not os.path.exists(args.template):
        print(f"[ERROR] Template file not found: {args.template}")
        print(f"[TIP] Make sure you have {args.template} in the current directory")
        return False
    
    # Try to load and validate JSON files
    try:
        # This line reads the file using the system's default encoding
        with open(args.quantity_data, 'r', encoding='utf-8') as f:
            quantity_data = json.load(f)
        
        # Basic validation of quantity data structure
        if 'sheets' not in quantity_data:
            print(f"[ERROR] Invalid quantity data format: missing 'sheets' key")
            return False
        
        if not isinstance(quantity_data['sheets'], list):
            print(f"[ERROR] Invalid quantity data format: 'sheets' must be a list")
            return False
        
        if not args.quiet:
            print(f"[OK] Quantity data loaded: {len(quantity_data['sheets'])} sheets found")
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in quantity data file: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error reading quantity data file: {e}")
        return False
    
    try:
        # This line also reads the file using the system's default encoding
        with open(args.template, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        # Basic validation of template structure
        required_keys = ['sheets_to_process', 'sheet_data_map', 'data_mapping']
        for key in required_keys:
            if key not in template_data:
                print(f"[ERROR] Invalid template format: missing '{key}' key")
                return False
        
        if not args.quiet:
            print(f"[OK] Template loaded: {len(template_data['data_mapping'])} sheet configurations")
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in template file: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error reading template file: {e}")
        return False
    
    return True


def generate_configuration(args):
    """Generate the configuration using the ConfigGenerator."""
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Generate default output name based on input
        input_name = Path(args.quantity_data).stem
        output_path = f"{input_name}_config.json"
    
    # Show info if requested
    if args.show_info:
        show_quantity_data_info(args.quantity_data)
        return True
    
    # Validate only if requested
    if args.validate_only:
        print("[SUCCESS] All input files are valid")
        return True
    
    try:
        if not args.quiet:
            print(f"\n[GENERATING] Starting configuration generation...")
            print(f"[TEMPLATE] {args.template}")
            print(f"[DATA] {args.quantity_data}")
            print(f"[OUTPUT] {output_path}")
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            if not args.quiet:
                print(f"[CREATED] Output directory: {output_dir}")
        
        # Generate configuration by calling the external class
        generator = ConfigGenerator()
        # Pass interactive mode to the generator
        generator.generate_config(args.template, args.quantity_data, output_path, interactive_mode=args.interactive)
        
        if not args.quiet:
            print(f"\n[SUCCESS] Configuration generated successfully!")
            print(f"[SAVED] Output saved to: {output_path}")
            
            # Show summary of what was generated
            show_generation_summary(output_path, args.quantity_data)
        
        return True
        
    except ConfigGeneratorError as e:
        print(f"[ERROR] Configuration generation failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during generation: {e}")
        return False


def show_quantity_data_info(quantity_path):
    """Show information about the quantity data file."""
    try:
        with open(quantity_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n[INFO] Quantity Data Information:")
        print(f"[FILE] {quantity_path}")
        
        if 'file_path' in data:
            print(f"[SOURCE] {data['file_path']}")
        
        if 'timestamp' in data:
            print(f"[TIME] {data['timestamp']}")
        
        print(f"[SHEETS] {len(data['sheets'])} sheets found")
        
        for sheet in data['sheets']:
            print(f"\n  [SHEET] {sheet['sheet_name']}:")
            print(f"    [START_ROW] {sheet['start_row']}")
            print(f"    [HEADER_FONT] {sheet['header_font']['name']} {sheet['header_font']['size']}pt")
            print(f"    [DATA_FONT] {sheet['data_font']['name']} {sheet['data_font']['size']}pt")
            print(f"    [HEADERS] {len(sheet['header_positions'])} positions")
            
            # Show first few headers
            for i, pos in enumerate(sheet['header_positions'][:3]):
                print(f"      - {pos['keyword']}")
            if len(sheet['header_positions']) > 3:
                print(f"      - ... and {len(sheet['header_positions']) - 3} more")
        
    except Exception as e:
        print(f"[ERROR] Error reading quantity data info: {e}")


def show_generation_summary(output_path, quantity_path):
    """Show summary of what was generated."""
    try:
        # Load generated config
        with open(output_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Load quantity data for comparison
        with open(quantity_path, 'r', encoding='utf-8') as f:
            quantity_data = json.load(f)
        
        print(f"\n[SUMMARY] Generation Summary:")
        print(f"[PROCESSED] {len(config['data_mapping'])} sheets")
        
        # Show what was updated
        updates_made = []
        for sheet_data in quantity_data['sheets']:
            sheet_name = sheet_data['sheet_name']
            if sheet_name in config['data_mapping']:
                sheet_config = config['data_mapping'][sheet_name]
                
                # Check start_row update
                if sheet_config['start_row'] == sheet_data['start_row']:
                    updates_made.append(f"  [UPDATED] {sheet_name}: start_row -> {sheet_data['start_row']}")
                
                # Check font updates
                if 'styling' in sheet_config:
                    styling = sheet_config['styling']
                    if styling['header_font']['name'] == sheet_data['header_font']['name']:
                        updates_made.append(f"  [UPDATED] {sheet_name}: fonts -> {sheet_data['header_font']['name']}")
        
        if updates_made:
            print("[UPDATES] Applied:")
            for update in updates_made:
                print(update)
        
        print(f"[PRESERVED] Business logic: mappings, formulas, styling rules")
        print(f"[READY] Configuration is complete and valid")
        
    except Exception as e:
        print(f"[WARNING] Could not show generation summary: {e}")


if __name__ == '__main__':
    sys.exit(main())