import sys
import os

# Add current directory to sys.path (simulating python -m from root)
sys.path.append(os.getcwd())

try:
    print("Attempting to import src.invoice_generator.src.builders.layout_builder...")
    from src.invoice_generator.src.builders import layout_builder
    print("Successfully imported layout_builder!")
except Exception as e:
    print(f"Failed to import layout_builder: {e}")
    import traceback
    traceback.print_exc()
