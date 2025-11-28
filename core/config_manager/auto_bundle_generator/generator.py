"""
Auto Bundle Generator - Main orchestrator for automatic config generation.

This is the main entry point that:
1. Takes an Excel template file OR old config file
2. Analyzes its structure
3. Generates a complete bundle config
4. Saves it to the config_bundled directory
"""

import logging
import json
import sys
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

from .template_analyzer import TemplateAnalyzer, TemplateAnalysisResult
from .bundle_builder import BundleBuilder
from .config_converter import ConfigConverter

logger = logging.getLogger(__name__)


class AutoBundleGenerator:
    """
    Main class for automatic bundle config generation.
    
    Usage:
        generator = AutoBundleGenerator()
        config_path = generator.generate("path/to/template.xlsx")
        # OR convert old config
        config_path = generator.convert_old_config("path/to/old_config.json")
    """
    
    def __init__(self, output_base_dir: Optional[Path] = None):
        """
        Initialize the generator.
        
        Args:
            output_base_dir: Base directory for config output. 
                           Defaults to invoice_generator/src/config_bundled/
        """
        self.analyzer = TemplateAnalyzer()
        self.builder = BundleBuilder()
        self.converter = ConfigConverter()
        
        # Set default output directory
        if output_base_dir:
            self.output_base_dir = Path(output_base_dir)
        else:
            # Find the config_bundled directory relative to this file
            current_dir = Path(__file__).parent
            # Go up to src/config_manager, then to invoice_generator/src/config_bundled
            project_root = current_dir.parent.parent
            self.output_base_dir = project_root / "invoice_generator" / "src" / "config_bundled"
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def convert_old_config(self, config_path: str, output_dir: Optional[str] = None,
                           dry_run: bool = False) -> Optional[Path]:
        """
        Convert old-format config to bundle format.
        
        Args:
            config_path: Path to old config JSON file
            output_dir: Optional custom output directory
            dry_run: If True, print config but don't save
            
        Returns:
            Path to generated config file, or None if dry_run
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"Config Converter")
        self.logger.info(f"=" * 60)
        self.logger.info(f"Source: {config_path}")
        
        # Convert
        bundle = self.converter.convert(str(config_path))
        customer_code = bundle["_meta"]["customer"]
        
        self.logger.info(f"Customer: {customer_code}")
        self.logger.info(f"Sheets: {bundle['processing']['sheets']}")
        
        if dry_run:
            self.logger.info("\n[Dry Run] Generated config:")
            print(json.dumps(bundle, indent=2, ensure_ascii=False))
            return None
        
        # Determine output path
        if output_dir:
            output_base = Path(output_dir)
        else:
            output_base = self.output_base_dir
        
        config_dir = output_base / f"{customer_code}_config"
        config_file = config_dir / f"{customer_code}_config.json"
        
        self.logger.info(f"\nSaving to: {config_file}")
        
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Config saved successfully!")
        
        return config_file
    
    def generate(self, template_path: str, output_dir: Optional[str] = None,
                 dry_run: bool = False) -> Optional[Path]:
        """
        Generate bundle config from template.
        
        Args:
            template_path: Path to Excel template file
            output_dir: Optional custom output directory
            dry_run: If True, print config but don't save
            
        Returns:
            Path to generated config file, or None if dry_run
        """
        template_path = Path(template_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"Auto Bundle Generator")
        self.logger.info(f"=" * 60)
        self.logger.info(f"Template: {template_path}")
        
        
        # Step 1: Analyze template
        self.logger.info("\n[Step 1] Analyzing template structure...")
        analysis = self.analyzer.analyze_template(str(template_path))
        
        self._print_analysis_summary(analysis)
        
        # Step 2: Build bundle config
        self.logger.info("\n[Step 2] Building bundle config...")
        bundle = self.builder.build_bundle(analysis)
        
        # Step 3: Save or print
        if dry_run:
            self.logger.info("\n[Dry Run] Generated config:")
            print(json.dumps(bundle, indent=2, ensure_ascii=False))
            return None
        
        # Determine output path
        if output_dir:
            output_base = Path(output_dir)
        else:
            output_base = self.output_base_dir
        
        config_dir = output_base / f"{analysis.customer_code}_config"
        config_file = config_dir / f"{analysis.customer_code}_config.json"
        
        self.logger.info(f"\n[Step 3] Saving config to: {config_file}")
        
        # Create directory
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Config saved successfully!")
        self.logger.info(f"   Directory: {config_dir}")
        self.logger.info(f"   File: {config_file.name}")
        
        return config_file
    
    def _print_analysis_summary(self, analysis: TemplateAnalysisResult):
        """Print summary of template analysis."""
        self.logger.info(f"\n   Customer Code: {analysis.customer_code}")
        self.logger.info(f"   Sheets found: {len(analysis.sheets)}")
        
        for sheet in analysis.sheets:
            self.logger.info(f"\n   [{sheet.name}]")
            self.logger.info(f"      Header row: {sheet.header_row}")
            self.logger.info(f"      Data source: {sheet.data_source}")
            self.logger.info(f"      Columns: {len(sheet.columns)}")
            
            for col in sheet.columns:
                children_info = f" ({len(col.children)} children)" if col.children else ""
                self.logger.info(f"         - {col.id}: '{col.header}'{children_info}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-generate invoice bundle configs from Excel templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate config from CLW template
  python -m src.config_manager.auto_bundle_generator.generator CLW.xlsx
  
  # Dry run - just print the config without saving
  python -m src.config_manager.auto_bundle_generator.generator CLW.xlsx --dry-run
  
  # Custom output directory
  python -m src.config_manager.auto_bundle_generator.generator CLW.xlsx -o ./my_configs
  
  # Verbose mode
  python -m src.config_manager.auto_bundle_generator.generator CLW.xlsx -v

The tool will:
  1. Analyze the Excel template structure
  2. Detect sheet types (Invoice, Contract, Packing list)
  3. Extract column layouts, fonts, widths
  4. Generate a complete bundle config
  5. Save to config_bundled/{CUSTOMER}_config/
        """
    )
    
    parser.add_argument(
        'template',
        help='Path to Excel template file (e.g., CLW.xlsx)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: invoice_generator/src/config_bundled/)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print generated config without saving'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output'
    )
    
    parser.add_argument(
        '--convert',
        action='store_true',
        help='Convert old config format instead of analyzing template'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )
    
    try:
        generator = AutoBundleGenerator()
        
        # Check file extension to auto-detect mode
        input_path = Path(args.template)
        is_json = input_path.suffix.lower() == '.json'
        
        if args.convert or is_json:
            # Convert old config
            result = generator.convert_old_config(
                args.template,
                output_dir=args.output,
                dry_run=args.dry_run
            )
        else:
            # Analyze template
            result = generator.generate(
                args.template,
                output_dir=args.output,
                dry_run=args.dry_run
            )
        
        if result:
            print(f"\n✅ SUCCESS: Config generated at {result}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
