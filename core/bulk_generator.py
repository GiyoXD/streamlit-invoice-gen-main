import pandas as pd
import logging
import zipfile
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from core.invoice_generator.generate_invoice import run_invoice_generation

logger = logging.getLogger(__name__)

class BulkGenerator:
    def __init__(self, template_dir: Path, config_dir: Path, output_dir: Path):
        self.template_dir = template_dir
        self.config_dir = config_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_bulk_file(self, 
                          data_file: Path, 
                          config_path: Path, 
                          template_path: Path) -> Tuple[List[Path], List[str]]:
        """
        Process a bulk data file (CSV/Excel) and generate invoices.
        Returns: (list of generated file paths, list of error messages)
        """
        generated_files = []
        errors = []

        try:
            # 1. Read Data
            if data_file.suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            # Ensure all data is string for consistency with placeholders
            df = df.astype(str)
            
            total_rows = len(df)
            logger.info(f"Starting bulk generation for {total_rows} rows.")

            # 2. Iterate Rows
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = row.to_dict()
                    
                    # Determine Output Filename
                    # Strategy: Use first column as ID, or "Invoice_{index}"
                    file_name = f"Invoice_{index + 1}.xlsx"
                    if not df.empty:
                        first_col = df.columns[0]
                        val = row_data.get(first_col)
                        if val:
                            # Sanitize filename
                            clean_val = "".join(c for c in val if c.isalnum() or c in (' ', '-', '_')).strip()
                            file_name = f"{clean_val}.xlsx"
                    
                    output_path = self.output_dir / file_name
                    
                    # 3. Generate Invoice
                    # We pass the row_data directly as input_data_dict
                    result = run_invoice_generation(
                        input_data_path=Path(f"row_{index}"), # Dummy path
                        output_path=output_path,
                        template_dir=self.template_dir,
                        config_dir=self.config_dir,
                        explicit_config_path=config_path,
                        explicit_template_path=template_path,
                        input_data_dict=row_data # DIRECT INJECTION
                    )
                    
                    if result and result.exists():
                        generated_files.append(result)
                    else:
                        errors.append(f"Row {index+1}: Generation failed without exception.")

                except Exception as e:
                    msg = f"Row {index+1} Error: {str(e)}"
                    logger.error(msg)
                    errors.append(msg)
                    
        except Exception as e:
            errors.append(f"File Read Error: {str(e)}")
            
        return generated_files, errors

    def create_zip_archive(self, file_paths: List[Path], zip_name: str = "Invoices.zip") -> Path:
        """Zip all generated files."""
        zip_path = self.output_dir / zip_name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in file_paths:
                zipf.write(file, arcname=file.name)
        return zip_path
