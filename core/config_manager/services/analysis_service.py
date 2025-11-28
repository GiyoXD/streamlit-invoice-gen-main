import sys
import logging
from pathlib import Path
from ..core.executor import Executor

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Wraps the Excel analysis logic.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.analyze_script_path = base_dir / "config_data_extractor" / "analyze_excel.py"
        self.executor = Executor()

    def analyze(self, excel_file: str, output_path: str, verbose: bool = False) -> bool:
        """
        Runs the analyze_excel.py script.
        """
        if not self.analyze_script_path.exists():
            logger.error(f"Analysis script not found at {self.analyze_script_path}")
            return False

        analyze_command = [
            sys.executable,
            '-X', 'utf8',
            str(self.analyze_script_path),
            excel_file,
            '--json',
            '--quantity-mode',
            '-o',
            output_path
        ]

        logger.info("Step 1: Analyzing Excel file...")
        return self.executor.run_command(analyze_command, verbose)
