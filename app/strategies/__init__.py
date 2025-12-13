# Strategies package
from .base_strategy import InvoiceGenerationStrategy
from .high_quality_strategy import HighQualityLeatherStrategy
from .second_layer_strategy import SecondLayerLeatherStrategy
from .components.excel_processor import ExcelProcessor
from .components.calculator import Calculator

# Strategy registry factory
def get_strategies():
    """Return a dictionary of fresh strategy instances."""
    return {
        "high_quality": HighQualityLeatherStrategy(),
        "second_layer": SecondLayerLeatherStrategy(),
    }

# Re-export utility functions that were in the original invoice_strategies.py
# These will be moved to utils/ in future phases
def apply_print_settings_to_files(generated_files, invoice_gen_dir):
    """Apply print settings to generated Excel files using PrintAreaConfig."""
    try:
        from ..invoice_generator.print_area_config import PrintAreaConfig
        from openpyxl import load_workbook
        
        files_processed = 0
        sheets_processed = 0
        
        print_config = PrintAreaConfig()
        
        for file_path in generated_files:
            if str(file_path).endswith('.xlsx'):
                try:
                    # Load workbook
                    workbook = load_workbook(file_path)
                    
                    # Apply print settings to each worksheet
                    for worksheet in workbook.worksheets:
                        print_config.configure_print_settings(worksheet)
                        sheets_processed += 1
                    
                    # Save the workbook
                    workbook.save(file_path)
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Warning: Failed to apply print settings to {file_path}: {e}")
                    continue
        
        return files_processed, sheets_processed
        
    except ImportError as e:
        print(f"Warning: PrintAreaConfig not available: {e}")
        return 0, 0

def create_download_zip(files_to_zip):
    """Create a ZIP file from a list of files and return the bytes."""
    import zipfile
    import io
    from pathlib import Path
    
    try:
        # Create a BytesIO buffer to hold the ZIP file
        zip_buffer = io.BytesIO()
        
        # Create ZIP file in memory
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_item in files_to_zip:
                # Handle both Path objects and dictionaries
                if isinstance(file_item, (str, Path)):
                    file_path = Path(file_item)
                    if file_path.exists():
                        # Read file content
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                        file_name = file_path.name
                        zip_file.writestr(file_name, file_data)
                elif isinstance(file_item, dict):
                    # Handle dictionary format (backward compatibility)
                    file_name = file_item.get('name', 'unknown_file')
                    file_data = file_item.get('data', b'')
                    zip_file.writestr(file_name, file_data)
                else:
                    print(f"Warning: Unsupported file item type: {type(file_item)}")
        
        # Get the ZIP file bytes
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        print(f"Error creating ZIP file: {e}")
        return None