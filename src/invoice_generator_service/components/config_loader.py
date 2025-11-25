import json
from pathlib import Path
from pydantic import ValidationError
from ..models import CompanyConfig
from ..exceptions import ConfigNotFound, InvalidConfig

class ConfigLoader:
    """
    Loads and validates company-specific configuration files.

    This component is responsible for finding, loading, and validating
    company configuration files. It follows the naming convention
    {company_id}_config.json and ensures configurations are valid
    before returning them to the service.

    The ConfigLoader provides a clean separation between configuration
    file handling and the main service logic, making it easy to:
    - Support different configuration formats
    - Add configuration validation rules
    - Cache configurations for performance
    - Handle configuration versioning

    Attributes:
        config_dir (Path): Directory containing configuration files

    Example:
        >>> loader = ConfigLoader("configs/")
        >>> config = loader.load("CLW")  # Loads configs/CLW_config.json
    """

    def __init__(self, config_dir: str = "src/invoice_generator_service/configs"):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Path to directory containing company config files.
                       Defaults to the service's configs directory.
        """
        self.config_dir = Path(config_dir)

    def load(self, company_id: str) -> CompanyConfig:
        """
        Load and validate configuration for a specific company.

        This method performs the complete configuration loading workflow:
        1. Constructs the configuration file path using company_id
        2. Checks if the file exists
        3. Parses the JSON content
        4. Validates the configuration structure
        5. Returns a validated CompanyConfig object

        Args:
            company_id: Company identifier (e.g., "CLW", "JF", "BRO").
                       Used to find the file {company_id}_config.json

        Returns:
            CompanyConfig: Validated configuration object containing
                           all settings for the specified company

        Raises:
            ConfigNotFound: If the configuration file doesn't exist
            InvalidConfig: If the file exists but contains invalid JSON
                          or doesn't match the expected structure

        Example:
            >>> loader = ConfigLoader("configs/")
            >>> config = loader.load("CLW")
            >>> print(config.template_filename)
            CLW_template.xlsx
        """
        config_path = self.config_dir / f"{company_id}_config.json"

        if not config_path.exists():
            raise ConfigNotFound(f"Configuration file not found for company '{company_id}' at {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return CompanyConfig(**data)
        except json.JSONDecodeError as e:
            raise InvalidConfig(f"Invalid JSON in config file {config_path}: {e}") from e
        except ValidationError as e:
            raise InvalidConfig(f"Configuration for '{company_id}' is invalid: {e}") from e
