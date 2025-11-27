#!/usr/bin/env python3
"""
Bundle Config Generator CLI

This script wraps the BundleConfigGenerator to allow generating bundle configurations
from the command line.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from generate_config.bundle_generator.bundle_generator import BundleConfigGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate invoice configuration in bundle format.")
    parser.add_argument("quantity_data", help="Path to the quantity analysis JSON file")
    parser.add_argument("-o", "--output", help="Output path for the generated config file")
    
    args = parser.parse_args()
    
    quantity_data_path = args.quantity_data
    output_path = args.output
    
    if not output_path:
        # Default output path: same directory as quantity data, with _bundle_config.json suffix
        p = Path(quantity_data_path)
        output_path = str(p.parent / f"{p.stem}_bundle_config.json")
        
    generator = BundleConfigGenerator()
    success = generator.generate_config(quantity_data_path, output_path)
    
    if success:
        print(f"Successfully generated bundle config at: {output_path}")
        sys.exit(0)
    else:
        print("Failed to generate bundle config.")
        sys.exit(1)

if __name__ == "__main__":
    main()
