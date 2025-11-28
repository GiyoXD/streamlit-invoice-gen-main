import logging
from pathlib import Path
from ..auto_bundle_generator.generator import AutoBundleGenerator

logger = logging.getLogger(__name__)

class GenerationService:
    """
    Wraps the AutoBundleGenerator.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        # AutoBundleGenerator handles its own output dir logic, but we can override it
        self.generator = AutoBundleGenerator()

    def generate(self, analysis_path: str, output_path: str, verbose: bool = False) -> bool:
        """
        Generates the bundle config using the analysis file (which acts as the "template" input for the generator
        if we were passing a raw Excel, but here we might need to adapt).
        
        Wait, AutoBundleGenerator expects an Excel file path as 'template_path' in its generate method.
        But our flow is: Analyze -> JSON -> Generate.
        
        The AutoBundleGenerator.generate() method does: Analyze -> Build -> Save.
        It seems AutoBundleGenerator is self-contained.
        
        If we want to use the *intermediate* JSON we just created, we might need to adjust AutoBundleGenerator
        or just pass the original Excel file to it?
        
        Actually, looking at `AutoBundleGenerator.generate`:
        It takes `template_path` (Excel).
        
        If we want to reuse the analysis we just did in step 1, we should check if AutoBundleGenerator
        can accept an analysis object or file.
        
        `AutoBundleGenerator` uses `TemplateAnalyzer`.
        
        If we want to stick to the "Analyze -> Generate" flow where we might have modified the analysis (e.g. headers),
        we need to see if we can pass the analysis JSON.
        
        In the legacy `main.py`, step 2 was `generate_config_ascii.py` which took the JSON.
        
        The new `AutoBundleGenerator` seems to do both.
        
        However, `AutoBundleGenerator` has a `convert_old_config` method, but not a "generate from analysis json" method explicitly exposed?
        
        Let's look at `AutoBundleGenerator.generate`:
        ```python
        analysis = self.analyzer.analyze_template(str(template_path))
        bundle = self.builder.build_bundle(analysis)
        ```
        
        If we want to use the JSON from Step 1, we might need to load it into a `TemplateAnalysisResult` object
        and pass it to `builder.build_bundle`.
        
        For now, to keep it simple and robust, we can just let AutoBundleGenerator re-analyze the Excel file,
        OR we can modify AutoBundleGenerator to accept a pre-analyzed JSON.
        
        Given the user wants to refactor the *Config Creator* (which is the orchestrator),
        and `AutoBundleGenerator` is the new standard.
        
        If we use `AutoBundleGenerator.generate(excel_file)`, it repeats the analysis.
        This might be acceptable overhead.
        
        BUT, if `HeaderMapper` modified mappings in `mapping_config.json`, `AutoBundleGenerator` will pick them up
        during its own analysis phase.
        
        So passing the Excel file to `AutoBundleGenerator` is the safest and cleanest way, 
        even if it means double analysis (once for our explicit logging step, once for generation).
        
        Wait, `main.py` Step 1 was `analyze_excel.py`.
        Step 1.5 was `extract_and_log_headers`.
        Step 2 was `generate_config`.
        
        If we use `AutoBundleGenerator`, it does Analysis + Generation.
        
        So our new flow in `GenerationService` should probably just call `AutoBundleGenerator.generate(original_excel_file)`.
        
        BUT, `ConfigOrchestrator` has already run `AnalysisService`.
        
        If `AnalysisService` is only used for `HeaderMapper` to log headers, that's fine.
        
        Let's implement `generate` to take the *original excel file* and *output path*.
        """
        try:
            logger.info("Step 2: Generating bundle configuration...")
            
            # We need to pass the output directory, not the full file path, 
            # because AutoBundleGenerator constructs the filename itself:
            # config_dir = output_base / f"{analysis.customer_code}_config"
            
            # We want to control the output path to match what WorkspaceManager set up.
            # AutoBundleGenerator.generate takes `output_dir`.
            
            # If we want exact control, we might need to subclass or modify AutoBundleGenerator,
            # but for now let's try to use it as is.
            
            # The `output_path` passed here is likely the *file* path from WorkspaceManager?
            # WorkspaceManager returns `enhanced_output_dir`.
            
            # Let's assume `output_path` passed to this method is the DIRECTORY.
            
            # We need the original excel file. 
            # The `analysis_path` arg is the JSON file. We might not need it if we use AutoBundleGenerator on the Excel.
            # But `ConfigOrchestrator` will pass what it has.
            
            # Let's change the signature to accept `excel_file_path`.
            pass
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return False

    def generate_from_excel(self, excel_path: str, output_dir: Path) -> bool:
        try:
            logger.info("Step 2: Generating bundle configuration...")
            result = self.generator.generate(
                template_path=excel_path,
                output_dir=str(output_dir)
            )
            return result is not None
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return False
