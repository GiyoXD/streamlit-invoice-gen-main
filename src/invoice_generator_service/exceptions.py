class InvoiceGeneratorError(Exception):
    """
    Base exception class for all invoice generator service errors.

    This is the root exception that all other service-specific exceptions
    inherit from. It allows for catching all invoice generator errors
    while still providing specific error types for different scenarios.

    Example:
        >>> try:
        ...     service.generate_invoice("CLW", data_path, output_path)
        ... except InvoiceGeneratorError as e:
        ...     print(f"Invoice generation failed: {e}")
    """
    pass

class ConfigNotFound(InvoiceGeneratorError):
    """
    Raised when a company configuration file cannot be found.

    This exception is raised by ConfigLoader when it cannot locate
    the required configuration file for a given company ID.

    Example:
        File structure: configs/CLW_config.json
        Company ID: "CLW"
        If configs/CLW_config.json doesn't exist, ConfigNotFound is raised.
    """
    pass

class InvalidConfig(InvoiceGeneratorError):
    """
    Raised when a configuration file is found but is invalid.

    This exception is raised when:
    - The configuration file contains invalid JSON
    - The configuration data doesn't match the expected structure
    - Required fields are missing or malformed

    Example:
        >>> # This would raise InvalidConfig
        >>> config = {"invalid": "structure"}
        >>> CompanyConfig(**config)  # ValidationError -> InvalidConfig
    """
    pass

class DataParserError(InvoiceGeneratorError):
    """
    Raised when there are issues parsing or validating input data.

    This exception is raised when:
    - Input JSON files are malformed
    - Required data fields are missing
    - Data types don't match expectations

    Example:
        >>> # Missing required fields in data
        >>> data = {"incomplete": "data"}
        >>> InvoiceData(**data)  # May raise DataParserError
    """
    pass

class TemplateError(InvoiceGeneratorError):
    """
    Raised when there are issues with Excel template files.

    This exception is raised when:
    - Template files are corrupted or unreadable
    - Required worksheets are missing from templates
    - Template structure doesn't match configuration expectations

    Example:
        >>> # Template file is missing required worksheet
        >>> # TemplateError would be raised during processing
    """
    pass
