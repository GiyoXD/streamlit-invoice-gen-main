import logging
import sys
from pathlib import Path
from typing import Dict, Any

from .core.workspace import WorkspaceManager
from .services.analysis_service import AnalysisService
from .services.header_mapper import HeaderMapper
from .services.generation_service import GenerationService
from .services.template_preprocessor import TemplatePreprocessor

logger = logging.getLogger(__name__)

class ConfigOrchestrator:
    """
    Facade for the configuration generation process.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.workspace = WorkspaceManager(base_dir / "result")
        self.analyzer = AnalysisService(base_dir)
        self.mapper = HeaderMapper(base_dir)
        self.generator = GenerationService(base_dir)
        self.preprocessor = TemplatePreprocessor()

    def run(self, excel_file: str, options: Dict[str, Any] = None) -> bool:
        """
        Executes the full configuration generation workflow.
        """
        if options is None:
            options = {}
            
        excel_path = Path(excel_file).resolve()
        if not excel_path.exists():
            logger.error(f"Input file not found: {excel_file}")
            return False

        logger.info(f"Starting configuration workflow for: {excel_path.name}")

        # --- Step 0: Pre-process Template (Text Replacement & Row Removal) ---
        # This modifies the template in-place (or the copy if it was copied)
        # to insert placeholders (JFINV) and clear dummy data.
        if not self.preprocessor.process(excel_path):
            logger.error("Template pre-processing failed. Aborting.")
            return False

        # 1. Setup Workspace
        # If output_dir is specified in options, use it. Otherwise, use WorkspaceManager default.
        custom_output = options.get('output_dir')
        if custom_output:
            output_dir = Path(custom_output)
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using custom output directory: {output_dir}")
        else:
            output_dir, metadata = self.workspace.setup_output_directory(excel_path)
            logger.info(f"Output directory: {output_dir}")

        success = False
        try:
            # 2. Analyze (Intermediate step for header logging)
            # We create a temp file for analysis JSON
            # If using custom output, we might want to put temp files there or in a temp dir
            # For simplicity, let's put it in the output dir (or a temp subdir if custom)
            
            if custom_output:
                # Use a temp dir for intermediate files to avoid cluttering the target config dir
                import tempfile
                temp_dir = Path(tempfile.mkdtemp())
                analysis_json_path = str(temp_dir / f"analysis_{excel_path.stem}.json")
            else:
                analysis_json_path = self.workspace.get_temp_file(
                    suffix=".json", prefix="analysis_", dir=output_dir
                )
            
            if not self.analyzer.analyze(str(excel_path), analysis_json_path, verbose=options.get('verbose')):
                logger.error("Analysis failed.")
                return False

            # 3. Header Mapping (Optional Logging)
            log_headers = options.get('log_headers', False)
            interactive = options.get('interactive', False)
            
            # We always process headers to check for missing ones, but only log if requested
            self.mapper.process_headers(
                analysis_json_path, 
                str(output_dir / excel_path.stem),
                create_log_file=log_headers,
                interactive=interactive
            )

            # 4. Generate Config
            # We use the new AutoBundleGenerator which re-processes the Excel
            # This is slightly redundant but cleaner than depending on the intermediate JSON
            # which might be tied to the legacy format.
            if not self.generator.generate_from_excel(str(excel_path), output_dir):
                logger.error("Generation failed.")
                return False

            success = True
            logger.info("Configuration generated successfully!")

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 5. Cleanup
            if not options.get('keep_intermediate'):
                self.workspace.cleanup()

        return success
