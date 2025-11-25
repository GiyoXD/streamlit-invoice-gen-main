#!/usr/bin/env python3
"""
Helper script to add new mappings to the mapping configuration.

This script allows you to easily add new sheet name mappings and header text mappings
without manually editing the JSON file.
"""

import argparse
import sys
from config_generator.mapping_manager import MappingManager, MappingManagerError


def main():
    """Main entry point for the mapping helper script."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Initialize mapping manager
        mapping_manager = MappingManager(args.config)
        
        if args.add_sheet:
            add_sheet_mapping(mapping_manager, args.add_sheet)
        elif args.add_header:
            add_header_mapping(mapping_manager, args.add_header)
        elif args.list_mappings:
            list_mappings(mapping_manager)
        elif args.generate_report:
            generate_report(mapping_manager, args.generate_report)
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except MappingManagerError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Helper script to manage mapping configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new sheet name mapping
  python add_mapping.py --add-sheet "INVOICE_NEW:Invoice"
  
  # Add a new header text mapping
  python add_mapping.py --add-header "TOTAL AMOUNT:col_amount"
  
  # List all current mappings
  python add_mapping.py --list-mappings
  
  # Generate a mapping report
  python add_mapping.py --generate-report mapping_report.txt
  
  # Use a custom mapping config file
  python add_mapping.py --config custom_mapping.json --list-mappings
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='mapping_config.json',
        help='Path to mapping configuration file (default: mapping_config.json)'
    )
    
    parser.add_argument(
        '--add-sheet',
        metavar='QUANTITY_NAME:TEMPLATE_NAME',
        help='Add a sheet name mapping (format: "quantity_name:template_name")'
    )
    
    parser.add_argument(
        '--add-header',
        metavar='HEADER_TEXT:COLUMN_ID',
        help='Add a header text mapping (format: "header_text:column_id")'
    )
    
    parser.add_argument(
        '--list-mappings', '-l',
        action='store_true',
        help='List all current mappings'
    )
    
    parser.add_argument(
        '--generate-report', '-r',
        metavar='OUTPUT_FILE',
        help='Generate a mapping report to the specified file'
    )
    
    return parser


def add_sheet_mapping(mapping_manager: MappingManager, mapping_spec: str):
    """
    Add a new sheet name mapping.
    
    Args:
        mapping_manager: MappingManager instance
        mapping_spec: Mapping specification in format "quantity_name:template_name"
    """
    try:
        if ':' not in mapping_spec:
            raise ValueError("Sheet mapping must be in format 'quantity_name:template_name'")
        
        quantity_name, template_name = mapping_spec.split(':', 1)
        quantity_name = quantity_name.strip()
        template_name = template_name.strip()
        
        if not quantity_name or not template_name:
            raise ValueError("Both quantity name and template name must be non-empty")
        
        # Add the mapping
        mapping_manager.add_sheet_mapping(quantity_name, template_name)
        mapping_manager.save_mappings()
        
        print(f"✅ Added sheet mapping: '{quantity_name}' -> '{template_name}'")
        
    except ValueError as e:
        print(f"❌ Invalid mapping format: {e}")
        print("   Use format: 'quantity_name:template_name'")
        print("   Example: 'INV_NEW:Invoice'")
    except Exception as e:
        print(f"❌ Error adding sheet mapping: {e}")


def add_header_mapping(mapping_manager: MappingManager, mapping_spec: str):
    """
    Add a new header text mapping.
    
    Args:
        mapping_manager: MappingManager instance
        mapping_spec: Mapping specification in format "header_text:column_id"
    """
    try:
        if ':' not in mapping_spec:
            raise ValueError("Header mapping must be in format 'header_text:column_id'")
        
        header_text, column_id = mapping_spec.split(':', 1)
        header_text = header_text.strip()
        column_id = column_id.strip()
        
        if not header_text or not column_id:
            raise ValueError("Both header text and column ID must be non-empty")
        
        # Validate column ID format
        if not column_id.startswith('col_'):
            print(f"⚠️  Warning: Column ID '{column_id}' doesn't follow 'col_*' convention")
        
        # Add the mapping
        mapping_manager.add_header_mapping(header_text, column_id)
        mapping_manager.save_mappings()
        
        print(f"✅ Added header mapping: '{header_text}' -> '{column_id}'")
        
    except ValueError as e:
        print(f"❌ Invalid mapping format: {e}")
        print("   Use format: 'header_text:column_id'")
        print("   Example: 'TOTAL AMOUNT:col_amount'")
    except Exception as e:
        print(f"❌ Error adding header mapping: {e}")


def list_mappings(mapping_manager: MappingManager):
    """
    List all current mappings.
    
    Args:
        mapping_manager: MappingManager instance
    """
    try:
        print("📋 Current Sheet Name Mappings:")
        print("=" * 50)
        
        if mapping_manager.sheet_mappings:
            for quantity_name, template_name in sorted(mapping_manager.sheet_mappings.items()):
                print(f"  '{quantity_name}' -> '{template_name}'")
        else:
            print("  No sheet mappings configured")
        
        print(f"\n📋 Current Header Text Mappings ({len(mapping_manager.header_mappings)} total):")
        print("=" * 50)
        
        if mapping_manager.header_mappings:
            # Group by column ID for better readability
            by_column = {}
            for header_text, column_id in mapping_manager.header_mappings.items():
                if column_id not in by_column:
                    by_column[column_id] = []
                by_column[column_id].append(header_text)
            
            for column_id in sorted(by_column.keys()):
                print(f"\n  {column_id}:")
                for header_text in sorted(by_column[column_id]):
                    print(f"    '{header_text}'")
        else:
            print("  No header mappings configured")
        
        print(f"\n📊 Summary:")
        print(f"  Sheet mappings: {len(mapping_manager.sheet_mappings)}")
        print(f"  Header mappings: {len(mapping_manager.header_mappings)}")
        
    except Exception as e:
        print(f"❌ Error listing mappings: {e}")


def generate_report(mapping_manager: MappingManager, output_file: str):
    """
    Generate a mapping report.
    
    Args:
        mapping_manager: MappingManager instance
        output_file: Path to output report file
    """
    try:
        mapping_manager.generate_mapping_report(output_file)
        print(f"✅ Mapping report generated: {output_file}")
        
        # Show summary
        unrecognized = mapping_manager.get_unrecognized_items()
        if unrecognized:
            print(f"📊 Found {len(unrecognized)} unrecognized items")
            print("   Review the report file for details and suggestions")
        else:
            print("📊 No unrecognized items found")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")


if __name__ == '__main__':
    sys.exit(main())