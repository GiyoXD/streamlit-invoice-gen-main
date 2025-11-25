"""
Main ConfigGenerator orchestrator for the Config Generator system.

This module provides the main ConfigGenerator class that coordinates all components
to implement the template-based update workflow: load template → load quantity data 
→ update specific fields → write output.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .template_loader import TemplateLoader, TemplateLoaderError
from .quantity_data_loader import QuantityDataLoader, QuantityDataLoaderError
from .header_text_updater import HeaderTextUpdater
from .header_layout_updater import HeaderLayoutUpdater
from .font_updater import FontUpdater
from .row_data_updater import RowDataUpdater
from .position_updater import PositionUpdater
from .style_updater import StyleUpdater
from .merge_rules_updater import MergeRulesUpdater
from .number_format_updater import NumberFormatUpdater
from .fallback_updater import FallbackUpdater
from .summary_updater import SummaryUpdater
from .weight_summary_updater import WeightSummaryUpdater
from .config_writer import ConfigWriter, ConfigWriterError
from .models import QuantityAnalysisData


class ConfigGeneratorError(Exception):
    """Custom exception for ConfigGenerator errors."""
    pass


class ConfigGenerator:
    """
    Main orchestrator class that coordinates all components for config generation.
    
    This class implements the template-based update workflow by loading the template
    configuration, extracting data from quantity analysis, updating specific fields
    while preserving business logic, and writing the output configuration.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the ConfigGenerator with all required components.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger or self._setup_default_logger()
        
        # Initialize all components
        # Find the mapping config path relative to this script
        script_dir = Path(__file__).resolve().parent
        # Go up one level: config_generator -> generate_config -> config_template_cli
        base_dir = script_dir.parent.parent
        mapping_config_path = str(base_dir / "mapping_config.json")
        
        self.template_loader = TemplateLoader()
        self.quantity_data_loader = QuantityDataLoader()
        self.header_text_updater = HeaderTextUpdater(mapping_config_path)
        print("🔍 [CONFIG_GENERATOR] Initializing HeaderLayoutUpdater...")
        self.header_layout_updater = HeaderLayoutUpdater()
        print("✅ [CONFIG_GENERATOR] HeaderLayoutUpdater initialized")
        self.font_updater = FontUpdater()
        self.position_updater = RowDataUpdater()
        self.footer_updater = PositionUpdater()  # For footer configurations with merge rules
        self.style_updater = StyleUpdater(mapping_config_path)
        self.merge_rules_updater = MergeRulesUpdater()
        self.number_format_updater = NumberFormatUpdater()
        self.fallback_updater = FallbackUpdater()
        self.summary_updater = SummaryUpdater()
        self.weight_summary_updater = WeightSummaryUpdater()
        self.config_writer = ConfigWriter()
        
        # Initialize mapping manager for reporting
        try:
            from .mapping_manager import MappingManager
            self.mapping_manager = MappingManager()
        except Exception as e:
            self.logger.warning(f"Could not initialize mapping manager: {e}")
            self.mapping_manager = None
        
        self.logger.info("ConfigGenerator initialized with all components")
    
    def generate_config(self, template_path: str, quantity_data_path: str, output_path: str, interactive_mode: bool = False) -> None:
        """
        Generate configuration by implementing the complete template-based update workflow.
        
        This method orchestrates the entire process:
        1. Load template configuration from sample_config.json
        2. Load quantity analysis data
        3. Update specific fields (headers, fonts, positions) while preserving template structure
        4. Write the updated configuration to output file
        
        Args:
            template_path: Path to the template configuration file (sample_config.json)
            quantity_data_path: Path to the quantity analysis JSON file
            output_path: Path where the generated configuration should be written
            interactive_mode: If True, enable interactive fallbacks for header mapping with user validation
            
        Raises:
            ConfigGeneratorError: If any step in the workflow fails
        """
        try:
            self.logger.info(f"Starting config generation workflow")
            self.logger.info(f"Template: {template_path}")
            self.logger.info(f"Quantity data: {quantity_data_path}")
            self.logger.info(f"Output: {output_path}")
            
            
            # Step 1: Load template configuration
            self.logger.info("Step 1: Loading template configuration")
            template_config = self._load_template(template_path)
            
            # Step 2: Load quantity analysis data
            self.logger.info("Step 2: Loading quantity analysis data")
            quantity_data = self._load_quantity_data(quantity_data_path)
            
            # Step 3: Update specific fields while preserving template structure
            self.logger.info("Step 3: Updating configuration fields")
            updated_config = self._update_configuration(template_config, quantity_data, interactive_mode)
            
            # Step 4: Write the updated configuration
            self.logger.info("Step 4: Writing updated configuration")
            self._write_configuration(updated_config, output_path)
            
            # Step 5: Generate mapping report if mapping manager is available
            if self.mapping_manager:
                self.logger.info("Step 5: Generating mapping report")
                self._generate_mapping_report(output_path)
            
            self.logger.info("Config generation completed successfully")
            
        except Exception as e:
            error_msg = f"Config generation failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e
    
    def _load_template(self, template_path: str) -> Dict[str, Any]:
        """
        Load and validate the template configuration.
        
        Args:
            template_path: Path to the template file
            
        Returns:
            Loaded template configuration dictionary
            
        Raises:
            ConfigGeneratorError: If template loading fails
        """
        try:
            self.logger.debug(f"Loading template from: {template_path}")
            template_config = self.template_loader.load_template(template_path)
            self.logger.debug("Template loaded and validated successfully")
            return template_config
            
        except TemplateLoaderError as e:
            error_msg = f"Template loading failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e
    
    def _load_quantity_data(self, quantity_data_path: str) -> QuantityAnalysisData:
        """
        Load and validate quantity analysis data.
        
        Args:
            quantity_data_path: Path to the quantity data file
            
        Returns:
            Loaded and parsed quantity analysis data
            
        Raises:
            ConfigGeneratorError: If quantity data loading fails
        """
        try:
            self.logger.debug(f"Loading quantity data from: {quantity_data_path}")
            quantity_data = self.quantity_data_loader.load_quantity_data(quantity_data_path)
            self.logger.debug(f"Quantity data loaded successfully with {len(quantity_data.sheets)} sheets")
            return quantity_data
            
        except QuantityDataLoaderError as e:
            error_msg = f"Quantity data loading failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e
    
    def _update_configuration(self, template_config: Dict[str, Any], quantity_data: QuantityAnalysisData, interactive_mode: bool = False) -> Dict[str, Any]:
        """
        Update configuration by applying all field updates while preserving template structure.
        
        This method coordinates the selective update process:
        1. Update header texts in header_to_write sections
        2. Update header spans (colspan/rowspan) in header_to_write sections
        3. Update font information in styling sections
        4. Update start_row and column positions (includes row heights)
        5. Update number formats in styling sections
        6. Update data cell merging rules
        7. Update data_cell_merging_rule with colspan from headers
        
        Args:
            template_config: Base template configuration
            quantity_data: Quantity analysis data for updates
            interactive_mode: If True, enable interactive fallbacks for header mapping
            
        Returns:
            Updated configuration with selective field replacements
            
        Raises:
            ConfigGeneratorError: If any update step fails
        """
        try:
            self.logger.debug("Starting configuration updates")
            
            # Start with the template as base
            updated_config = template_config.copy()
            
            # Step 3a: Update header texts
            self.logger.debug("Updating header texts")
            updated_config = self.header_text_updater.update_header_texts(updated_config, quantity_data, interactive_mode)
            
            # Step 3a.1: Update fallback values
            self.logger.debug("Updating fallback values")
            updated_config = self.fallback_updater.update_fallbacks(updated_config, quantity_data)
            
            # Step 3b: Update header layout (spans + positions)
            self.logger.debug("Updating header layout (spans + positions)")
            print("🔍 [CONFIG_GENERATOR] About to call HeaderLayoutUpdater...")
            # Re-initialize HeaderLayoutUpdater with Excel analysis data
            excel_analysis_data = {
                'file_path': quantity_data.file_path,
                'timestamp': quantity_data.timestamp,
                'sheets': [
                    {
                        'sheet_name': sheet.sheet_name,
                        'header_font': {'name': sheet.header_font.name, 'size': sheet.header_font.size},
                        'data_font': {'name': sheet.data_font.name, 'size': sheet.data_font.size},
                        'start_row': sheet.start_row,
                        'header_positions': [
                            {'keyword': pos.keyword, 'row': pos.row, 'column': pos.column}
                            for pos in sheet.header_positions
                        ]
                    }
                    for sheet in quantity_data.sheets
                ]
            }
            self.header_layout_updater = HeaderLayoutUpdater(excel_analysis_data)
            updated_config = self.header_layout_updater.update_header_layout(updated_config)
            print("✅ [CONFIG_GENERATOR] HeaderLayoutUpdater completed")
            
            # Step 3c: Update font information
            self.logger.debug("Updating font information")
            updated_config = self.font_updater.update_fonts(updated_config, quantity_data)
            
            # Step 3d: Update start_row and row heights (column positions handled in Step 3b)
            self.logger.debug("Updating start_row and row heights")
            updated_config = self.position_updater.update_positions(updated_config, quantity_data)
            
            # Step 3d2: Update footer configurations with merge rules (raw index format)
            self.logger.debug("Updating footer configurations with merge rules")
            self.footer_updater.update_footer_configurations(updated_config, quantity_data)
            
            # Step 3e: Update number formats
            self.logger.debug("Updating number formats")
            # Set Excel file path for format extraction
            self.style_updater.set_excel_file_path(quantity_data.file_path)
            # Pass template config for column ID mapping
            self.style_updater.set_template_config(updated_config)
            updated_config = self.style_updater.update_number_formats(updated_config, quantity_data)
            
            # Step 3e.1: Update alignments
            self.logger.debug("Updating alignments")
            updated_config = self.style_updater.update_alignments(updated_config, quantity_data)
            
            # Step 3e.2: Update number formats in mappings and footer configurations
            self.logger.debug("Updating number formats in mappings and footer configurations")
            for sheet_data in quantity_data.sheets:
                updated_config = self.number_format_updater.update_config_with_number_formats(updated_config, sheet_data)
            
            # Step 3f: Update data cell merging rules
            self.logger.debug("Updating data cell merging rules")
            updated_config = self.merge_rules_updater.update_data_cell_merging_rules(updated_config, quantity_data)
            
            # Step 3g: Update data_cell_merging_rule with colspan from headers
            self.logger.debug("Updating data_cell_merging_rule with colspan from headers")
            updated_config = self.merge_rules_updater.update_data_cell_merging_col(updated_config)
            
            # Step 3h: Update summary field based on FOB summary detection
            self.logger.debug("Updating summary field based on FOB summary detection")
            updated_config = self.summary_updater.update_summary(updated_config, quantity_data)
            
            # Step 3i: Update weight summary config based on NW(KGS) detection
            self.logger.debug("Updating weight summary config based on NW(KGS) detection")
            updated_config = self.weight_summary_updater.update_weight_summary(updated_config, quantity_data)
            
            self.logger.debug("All configuration updates completed")
            return updated_config
            
        except Exception as e:
            error_msg = f"Configuration update failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e
    
    def _write_configuration(self, config: Dict[str, Any], output_path: str) -> None:
        """
        Write the updated configuration to output file with validation.
        
        Args:
            config: Updated configuration to write
            output_path: Path where configuration should be written
            
        Raises:
            ConfigGeneratorError: If writing or validation fails
        """
        try:
            self.logger.debug(f"Writing configuration to: {output_path}")
            self.config_writer.write_config(config, output_path)
            self.logger.debug("Configuration written and validated successfully")
            
        except ConfigWriterError as e:
            error_msg = f"Configuration writing failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e
    
    def _generate_mapping_report(self, output_path: str) -> None:
        """
        Generate a mapping report for unrecognized items.
        
        Args:
            output_path: Path of the generated config file (used to determine report path)
        """
        try:
            if not self.mapping_manager:
                return
            
            # Generate report path based on output path
            import os
            base_name = os.path.splitext(output_path)[0]
            report_path = f"{base_name}_mapping_report.txt"
            
            # Collect unrecognized items from all updaters
            all_unrecognized = []
            
            # Get unrecognized items from mapping manager
            if hasattr(self.mapping_manager, 'get_unrecognized_items'):
                all_unrecognized.extend(self.mapping_manager.get_unrecognized_items())
            
            # Generate the report
            self.mapping_manager.generate_mapping_report(report_path)
            
            if all_unrecognized:
                self.logger.info(f"Mapping report generated: {report_path}")
                self.logger.info(f"Found {len(all_unrecognized)} items that may need manual mapping")
            
        except Exception as e:
            self.logger.warning(f"Could not generate mapping report: {e}")
    
    def _setup_default_logger(self) -> logging.Logger:
        """
        Set up a default logger for the ConfigGenerator.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('ConfigGenerator')
        
        # Only add handler if logger doesn't already have handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def validate_inputs(self, template_path: str, quantity_data_path: str, output_path: str) -> bool:
        """
        Validate input parameters before starting the generation process.
        
        Args:
            template_path: Path to template file
            quantity_data_path: Path to quantity data file
            output_path: Path for output file
            
        Returns:
            True if all inputs are valid
            
        Raises:
            ConfigGeneratorError: If any input validation fails
        """
        try:
            # Validate input parameters
            if not template_path or not isinstance(template_path, str):
                raise ConfigGeneratorError("Template path must be a non-empty string")
            
            if not quantity_data_path or not isinstance(quantity_data_path, str):
                raise ConfigGeneratorError("Quantity data path must be a non-empty string")
            
            if not output_path or not isinstance(output_path, str):
                raise ConfigGeneratorError("Output path must be a non-empty string")
            
            self.logger.debug("Input validation passed")
            return True
            
        except Exception as e:
            error_msg = f"Input validation failed: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigGeneratorError(error_msg) from e