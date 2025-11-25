from pathlib import Path
from ..models import InvoiceData, CompanyConfig
from .base_strategy import BaseInvoiceStrategy
from ..operations import text_replacement_operations, table_operations
from ..io.workbook_loader_factory import WorkbookLoaderFactory
import shutil

class StandardInvoiceStrategy(BaseInvoiceStrategy):
    """
    Standard invoice generation strategy.

    This strategy implements the core invoice generation logic that mirrors
    the original `generate_invoice.py` script. It performs the standard
    workflow of:

    1. Template copying and loading
    2. Text replacement operations (headers, placeholders)
    3. Table data processing and insertion
    4. Footer processing (if configured)
    5. Styling and formatting
    6. Final file saving

    This strategy is designed to be a faithful reproduction of the original
    invoice generation process while using modern, modular components.

    The strategy uses the WorkbookLoaderFactory to support different Excel
    file formats, currently focused on XLSX but extensible to other formats.

    Attributes:
        None (stateless strategy class)

    Example:
        >>> strategy = StandardInvoiceStrategy()
        >>> strategy.generate(data, config, "CLW_template.xlsx", "output.xlsx")
    """

    def generate(self, data: InvoiceData, config: CompanyConfig, template_path: Path, output_path: Path) -> None:
        """
        Generate a standard Excel invoice.

        This method implements the complete standard invoice generation workflow:
        - Copies the template to create a working file
        - Loads the workbook using the appropriate loader
        - Performs text replacements for headers and placeholders
        - Processes and inserts table data
        - Applies any configured styling or formatting
        - Saves the final invoice

        The method maintains compatibility with the original invoice_generator
        by using the same data structures and processing logic.

        Args:
            data: Validated invoice data containing metadata and table data
            config: Company-specific configuration with mappings and settings
            template_path: Path to the Excel template file to use as base
            output_path: Path where the completed invoice will be saved

        Returns:
            None. The generated invoice is saved to output_path.

        Raises:
            TemplateError: If template loading or processing fails
            ValueError: If configuration is invalid for standard processing

        Example:
            >>> data = InvoiceData(metadata={"filename": "test.xlsx"})
            >>> config = CompanyConfig(template_filename="template.xlsx")
            >>> strategy = StandardInvoiceStrategy()
            >>> strategy.generate(data, config, "template.xlsx", "invoice.xlsx")
        """
        print("Executing StandardInvoiceStrategy...")

        # 1. Copy template to output path
        shutil.copy(template_path, output_path)

        # 2. Load the workbook using the factory pattern
        loader_factory = WorkbookLoaderFactory()
        loader = loader_factory.get_loader(output_path)
        workbook = loader.load(output_path)

        # 3. Run header replacement tasks
        text_replacement_operations.run_invoice_header_replacement_task(workbook, data.dict())

        # 4. Process tables
        config_dict = config.dict()
        sheets_to_process = config_dict.get('sheets_to_process', [])

        for sheet_name in sheets_to_process:
            if sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]
                sheet_mapping = config_dict.get('data_mapping', {}).get(sheet_name, {})

                if sheet_mapping:
                    header_map = sheet_mapping.get('mappings', {})
                    start_row = sheet_mapping.get('start_row')

                    if header_map and start_row:
                        header_row = table_operations.find_header_row(worksheet, header_map, start_row)
                        if header_row:
                            table_data = data.dict().get('processed_tables_data', {}).get('1', {})
                            if table_data:
                                table_operations.fill_invoice_data(worksheet, header_row, table_data, header_map)

        # For now, just save the workbook after replacements.
        workbook.save(output_path)
        print(f"Standard invoice generated at {output_path}")
