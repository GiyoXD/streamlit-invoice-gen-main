from abc import ABC, abstractmethod
from pathlib import Path
from ..models import InvoiceData, CompanyConfig

class BaseInvoiceStrategy(ABC):
    """
    Abstract base class for all invoice generation strategies.

    This class defines the Strategy Pattern interface for invoice generation.
    Different types of invoices (standard, hybrid, packing lists) can implement
    different strategies while maintaining the same interface.

    The strategy pattern allows the service to:
    - Support multiple invoice types without changing the core service
    - Add new invoice types by implementing new strategy classes
    - Test strategies independently
    - Switch strategies at runtime

    Each strategy is responsible for the complete invoice generation workflow
    for its specific invoice type, including:
    - Template copying and loading
    - Text replacement operations
    - Table data processing
    - Footer and styling operations
    - Final file saving

    Attributes:
        None (abstract base class)

    Example:
        >>> class CustomStrategy(BaseInvoiceStrategy):
        ...     def generate(self, data, config, template_path, output_path):
        ...         # Custom invoice generation logic
        ...         pass
    """

    @abstractmethod
    def generate(self, data: InvoiceData, config: CompanyConfig, template_path: Path, output_path: Path) -> None:
        """
        Generate an invoice using the provided data and configuration.

        This is the core method that each strategy must implement.
        The method should perform all necessary operations to transform
        the input data into a complete Excel invoice.

        Args:
            data: Validated invoice data from JSON input
            config: Company-specific configuration settings
            template_path: Path to the Excel template file
            output_path: Path where the generated invoice should be saved

        Returns:
            None. The generated invoice is saved to output_path.

        Raises:
            TemplateError: If template processing fails
            DataParserError: If data processing encounters issues

        Example:
            >>> strategy = StandardInvoiceStrategy()
            >>> strategy.generate(data, config, "template.xlsx", "output.xlsx")
        """
        pass
