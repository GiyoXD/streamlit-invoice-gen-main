
import logging
import time
import datetime
import json
import traceback
from pathlib import Path
from typing import Optional, List, Any, Dict
import argparse

logger = logging.getLogger(__name__)

class GenerationMonitor:
    """
    Context manager to monitor invoice generation, track state, and GUARANTEE 
    metadata file generation upon exit (success or failure).
    """
    def __init__(self, output_path: Path, args: argparse.Namespace = None, input_data: Dict = None):
        self.output_path = Path(output_path)
        self.args = args
        self.input_data = input_data or {}
        
        self.start_time = None
        self.sheets_processed = []
        self.sheets_failed = []
        self.replacements_log = []
        self.header_info = {}
        
        self.status = "pending"
        self.error_message = None
        self.error_traceback = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"=== Generation Process Started ===")
        return self

    def log_success(self, sheet_name: str):
        self.sheets_processed.append(sheet_name)
        logger.info(f"Successfully processed sheet: {sheet_name}")

    def log_failure(self, sheet_name: str, error: Exception = None):
        self.sheets_failed.append(sheet_name)
        msg = f"Failed to process sheet {sheet_name}: {error}"
        logger.error(msg)
        if error:
            logger.debug(traceback.format_exc())

    def update_logs(self, replacements: List = None, header_info: Dict = None):
        if replacements:
            self.replacements_log.extend(replacements)
        if header_info:
            self.header_info.update(header_info)

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Determine status
        if exc_type:
            self.status = "fatal"
            self.error_message = str(exc_val)
            self.error_traceback = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            logger.critical(f"Process crashed: {self.error_message}")
        elif self.sheets_failed:
            self.status = "partial_success" if self.sheets_processed else "error"
            self.error_message = f"Failed sheets: {self.sheets_failed}"
        else:
            self.status = "success"

        # Generate Metadata
        self._write_metadata(duration)
        
        # We generally want to propagate exceptions so the CLI/Orchestrator knows it failed
        return False 

    def _write_metadata(self, duration: float):
        """Write the metadata JSON file."""
        if not self.output_path.parent.exists():
            try:
                self.output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create output directory for metadata: {e}")
        
        meta_path = self.output_path.parent / f"{self.output_path.stem}_metadata.json"
        
        metadata = {
            "status": self.status,
            "timestamp": datetime.datetime.now().isoformat(),
            "duration_seconds": duration,
            "output_file": str(self.output_path.name),
            "sheets_processed": self.sheets_processed,
            "sheets_failed": self.sheets_failed,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "input_metadata": self.input_data.get("metadata", {}),
            "generation_args": vars(self.args) if self.args else {},
        }
        
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            logger.info(f"Metadata written to {meta_path}")
        except Exception as e:
            logger.error(f"FATAL: Failed to write metadata: {e}")
