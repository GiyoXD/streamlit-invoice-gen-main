#!/usr/bin/env python3
"""
Height Analysis Utility - Standalone tool for analyzing Excel row heights.

This utility allows you to analyze row heights in Excel files without
generating a full configuration. Useful for verification and troubleshooting.
"""

import sys
import json
import argparse
from pathlib import Path

# Add the generate_config directory to the path
sys.path.append(str(Path(__file__).parent))

from config_generator.excel_height_analyzer import ExcelHeightAnalyzer
from config_generator.quantity_data_loader import QuantityDataLoader


def analyze_heights(quantity_data_path: str, show_detailed: bool = False) -> None:
    """
    Analyze heights in the Excel file from quantity analysis data.
    
    Args:
        quantity_data_path: Path to quantity analysis JSON file
        show_detailed: Whether to show detailed analysis
    """
    
    print("📏 Height Analysis Utility")
    print("=" * 50)
    
    try:
        # Load quantity analysis data
        print(f"📂 Loading quantity data: {quantity_data_path}")
        loader = QuantityDataLoader()
        quantity_data = loader.load_quantity_data(quantity_data_path)
        print(f"✅ Loaded {len(quantity_data.sheets)} sheets from {Path(quantity_data.file_path).name}")
        
        # Initialize height analyzer
        analyzer = ExcelHeightAnalyzer()
        
        # Analyze each sheet
        for i, sheet_data in enumerate(quantity_data.sheets, 1):
            print(f"\n📋 Sheet {i}/{len(quantity_data.sheets)}: {sheet_data.sheet_name}")
            print("-" * 40)
            
            try:
                # Extract actual heights
                actual_heights = analyzer.extract_actual_row_heights(
                    quantity_data.file_path, sheet_data
                )
                
                # Display basic height information
                print(f"📏 Row Heights (in points):")
                if 'header_actual' in actual_heights:
                    print(f"  Header: {actual_heights['header_actual']:.1f}")
                if 'data_actual' in actual_heights:
                    print(f"  Data:   {actual_heights['data_actual']:.1f}")
                if 'footer_actual' in actual_heights:
                    print(f"  Footer: {actual_heights['footer_actual']:.1f}")
                
                # Show data consistency
                if 'data_consistency' in actual_heights:
                    consistency = actual_heights['data_consistency']
                    status = "✅ Consistent" if consistency['consistent'] else "⚠️ Inconsistent"
                    print(f"📊 Data Consistency: {status}")
                    print(f"  {consistency['message']}")
                    
                    if show_detailed and 'heights' in consistency:
                        print(f"  Rows analyzed: {consistency['total_rows_checked']}")
                        if not consistency['consistent']:
                            print(f"  Height range: {consistency['min_height']:.1f} - {consistency['max_height']:.1f}")
                
                # Validate structure
                structure = analyzer.validate_invoice_structure(
                    quantity_data.file_path, sheet_data
                )
                
                structure_status = "✅ Valid" if structure['structure_valid'] else "⚠️ Issues Found"
                print(f"🏗️ Structure: {structure_status}")
                
                if structure['issues']:
                    print(f"  Issues ({len(structure['issues'])}):")
                    for issue in structure['issues'][:3]:  # Show first 3
                        print(f"    - {issue}")
                    if len(structure['issues']) > 3:
                        print(f"    ... and {len(structure['issues']) - 3} more")
                
                if structure['recommendations']:
                    print(f"  Recommendations ({len(structure['recommendations'])}):")
                    for rec in structure['recommendations'][:2]:  # Show first 2
                        print(f"    - {rec}")
                    if len(structure['recommendations']) > 2:
                        print(f"    ... and {len(structure['recommendations']) - 2} more")
                
                # Show detailed analysis if requested
                if show_detailed:
                    print(f"\n📊 Detailed Analysis:")
                    for section, data in structure.get('analysis', {}).items():
                        print(f"  {section.title()}:")
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if key != 'heights':  # Skip detailed height lists
                                    print(f"    {key}: {value}")
                
            except Exception as e:
                print(f"❌ Error analyzing {sheet_data.sheet_name}: {e}")
        
        print(f"\n📋 Analysis Summary:")
        print(f"  Total sheets analyzed: {len(quantity_data.sheets)}")
        print(f"  Source file: {Path(quantity_data.file_path).name}")
        print(f"  Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        if show_detailed:
            traceback.print_exc()


def compare_with_config(quantity_data_path: str, config_path: str) -> None:
    """
    Compare actual Excel heights with configuration heights.
    
    Args:
        quantity_data_path: Path to quantity analysis JSON file
        config_path: Path to configuration JSON file
    """
    
    print("🔍 Height Comparison Utility")
    print("=" * 50)
    
    try:
        # Load data
        loader = QuantityDataLoader()
        quantity_data = loader.load_quantity_data(quantity_data_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📂 Loaded quantity data: {Path(quantity_data.file_path).name}")
        print(f"📂 Loaded config: {Path(config_path).name}")
        
        analyzer = ExcelHeightAnalyzer()
        
        # Compare each sheet
        for sheet_data in quantity_data.sheets:
            # Map sheet name
            sheet_name = sheet_data.sheet_name
            config_sheet_name = None
            
            # Find corresponding config sheet
            data_mapping = config.get('data_mapping', {})
            for config_name in data_mapping.keys():
                if config_name.lower() in sheet_name.lower() or sheet_name.lower() in config_name.lower():
                    config_sheet_name = config_name
                    break
            
            if not config_sheet_name:
                print(f"⚠️ No config found for sheet: {sheet_name}")
                continue
            
            print(f"\n📋 Comparing: {sheet_name} ↔ {config_sheet_name}")
            print("-" * 40)
            
            try:
                # Get actual heights
                actual_heights = analyzer.extract_actual_row_heights(
                    quantity_data.file_path, sheet_data
                )
                
                # Get config heights
                sheet_config = data_mapping[config_sheet_name]
                config_heights = sheet_config.get('styling', {}).get('row_heights', {})
                
                if not config_heights:
                    print(f"⚠️ No row heights in config for {config_sheet_name}")
                    continue
                
                # Compare
                comparison = analyzer.compare_with_config_heights(actual_heights, config_heights)
                
                print(f"🎯 Overall Match: {'✅ Yes' if comparison['overall_match'] else '❌ No'}")
                
                # Show detailed comparison
                for section in ['header', 'data', 'footer']:
                    if section in comparison['differences']:
                        diff_data = comparison['differences'][section]
                        actual = diff_data['actual']
                        config = diff_data['config']
                        matches = diff_data['matches']
                        difference = diff_data['difference']
                        
                        status = "✅" if matches else "❌"
                        print(f"  {section.title()}: {status} Actual: {actual:.1f} | Config: {config:.1f} | Diff: {difference:.1f}")
                
                # Show recommendations
                if comparison['recommendations']:
                    print(f"💡 Recommendations:")
                    for rec in comparison['recommendations']:
                        print(f"  - {rec}")
                
            except Exception as e:
                print(f"❌ Error comparing {sheet_name}: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Analyze Excel row heights from quantity analysis data")
    parser.add_argument("quantity_data", help="Path to quantity analysis JSON file")
    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis")
    parser.add_argument("--compare", help="Path to config file for comparison")
    
    args = parser.parse_args()
    
    if not Path(args.quantity_data).exists():
        print(f"❌ Error: Quantity data file not found: {args.quantity_data}")
        return 1
    
    if args.compare:
        if not Path(args.compare).exists():
            print(f"❌ Error: Config file not found: {args.compare}")
            return 1
        compare_with_config(args.quantity_data, args.compare)
    else:
        analyze_heights(args.quantity_data, args.detailed)
    
    return 0


if __name__ == "__main__":
    exit(main())
