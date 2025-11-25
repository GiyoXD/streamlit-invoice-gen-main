from pathlib import Path
import json
from .components.config_loader import ConfigLoader
from .strategies.base_strategy import BaseInvoiceStrategy
from .strategies.standard_invoice_strategy import StandardInvoiceStrategy
from .models import InvoiceData

class InvoiceService:
    """
    Main service for generating invoices. It orchestrates the loading of
    configurations, data, and the execution of the appropriate strategy.
    """
    def __init__(self, config_dir: str, template_dir: str):
        self.config_loader = ConfigLoader(config_dir)
        self.template_dir = Path(template_dir)
        self.strategies = {
            "standard": StandardInvoiceStrategy(),
            # "hybrid": HybridInvoiceStrategy() will be added here
        }

    def generate_invoice(self, company_id: str, data_path: Path, output_path: Path, strategy_name: str = "standard"):
        """
        Generates an invoice for a given company using a specified strategy.

        Args:
            company_id: The identifier for the company (e.g., "JF", "CLW").
            data_path: Path to the input JSON data file.
            output_path: Path where the generated invoice will be saved.
            strategy_name: The name of the strategy to use.
        """
        # 1. Load Configuration
        config = self.config_loader.load(company_id)
        
        # 2. Load Data
        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        invoice_data = InvoiceData(**raw_data)

        # 3. Select and Execute Strategy
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        template_name = config.dict().get('template_filename', f"{company_id}_template.xlsx")
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found at {template_path}")

        strategy.generate(invoice_data, config, template_path, output_path)
        
        print(f"Invoice generation complete for {company_id}.")
