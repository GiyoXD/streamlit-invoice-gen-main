
import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

try:
    from core.invoice_generator.resolvers import InvoiceAssetResolver
except ImportError:
    print("Could not import InvoiceAssetResolver. checking path...")
    print(sys.path)
    sys.exit(1)

def run_debug():
    # Define actual paths
    base_dir = Path(r"c:\Users\JPZ031127\Desktop\main_stream_lit_giyo\GENERATE_INVOICE_STREAMLIT_WEB")
    config_dir = base_dir / "database" / "blueprints" / "config" / "bundled"
    template_dir = base_dir / "database" / "blueprints" / "template"
    
    print(f"Config Dir Exists: {config_dir.exists()}")
    print(f"Template Dir Exists: {template_dir.exists()}")
    
    resolver = InvoiceAssetResolver(config_dir, template_dir)
    
    input_file = "CT25048E.json"
    print(f"\nResolving for: {input_file}")
    
    assets = resolver.resolve_assets_for_input_file(input_file)
    
    if assets:
        print("✅ SUCCESS!")
        print(f"Config: {assets.config_path}")
        print(f"Template: {assets.template_path}")
    else:
        print("❌ FAILED to resolve assets.")

if __name__ == "__main__":
    run_debug()
