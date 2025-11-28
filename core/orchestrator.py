import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

class Orchestrator:
    """
    Service to orchestrate backend processes, decoupling frontend from backend logic.
    Handles execution of data parsing and invoice generation scripts.
    """

    def __init__(self):
        # Determine project root
        # core/orchestrator.py -> core -> root
        self.project_root = Path(__file__).parent.parent
        
    def _run_subprocess(self, command: List[str], cwd: Path, env_vars: Dict[str, str] = None) -> subprocess.CompletedProcess:
        """Helper to run subprocesses with consistent environment setup"""
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        
        if env_vars:
            env.update(env_vars)

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            return result
        except subprocess.CalledProcessError as e:
            # Re-raise with captured output for better error handling upstream
            raise subprocess.CalledProcessError(
                e.returncode,
                e.cmd,
                output=e.stdout,
                stderr=e.stderr
            ) from e

    def process_excel_to_json(self, excel_path: Path, output_dir: Path) -> Tuple[Path, str]:
        """
        Orchestrate the Excel to JSON conversion process.
        
        Args:
            excel_path: Path to the input Excel file
            output_dir: Directory to save the JSON output
            
        Returns:
            Tuple[Path, str]: (Path to generated JSON file, Identifier/PO number)
        """
        identifier = excel_path.stem
        json_path = output_dir / f"{identifier}.json"
        
        command = [
            sys.executable,
            "-m", "core.data_parser.main",
            "--input-excel", str(excel_path),
            "--output-dir", str(output_dir)
        ]
        
        self._run_subprocess(command, cwd=self.project_root)
        
        if not json_path.exists() or json_path.stat().st_size == 0:
            raise RuntimeError("Processing script completed but JSON file was not created or is empty.")
            
        return json_path, identifier

    def generate_invoice(self, 
                        json_path: Path, 
                        output_path: Path, 
                        template_dir: Path, 
                        config_dir: Path, 
                        flags: List[str] = None) -> Path:
        """
        Orchestrate the Invoice Generation process.
        
        Args:
            json_path: Path to the input JSON data
            output_path: Path where the generated invoice should be saved
            template_dir: Path to templates directory
            config_dir: Path to configuration directory
            flags: Optional list of additional flags (e.g., ['--DAF', '--custom'])
            
        Returns:
            Path: Path to the generated invoice file
        """
        command = [
            sys.executable, 
            "-m", "core.invoice_generator.generate_invoice",
            str(json_path),
            "--templatedir", str(template_dir),
            "--configdir", str(config_dir),
            "--output", str(output_path)
        ]
        
        if flags:
            command.extend(flags)
            
        self._run_subprocess(command, cwd=self.project_root)
        
        if not output_path.exists():
             raise RuntimeError(f"Invoice generation script completed but output file {output_path.name} was not created.")
             
        return output_path
