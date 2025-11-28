import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class HeaderMapper:
    """
    Handles header analysis, logging, and interactive mapping.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.mapping_config_path = base_dir / "mapping_config.json"

    def process_headers(self, analysis_file_path: str, output_base_name: str, 
                       create_log_file: bool = False, interactive: bool = False) -> str:
        """
        Extract headers from the analysis JSON file.
        Optionally creates a header log file and runs interactive mapping.
        """
        try:
            # Load the analysis data
            with open(analysis_file_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Load current mapping configuration
            current_mappings = self._load_mappings()
            
            missing_headers = self._find_missing_headers(analysis_data, current_mappings)
            
            header_log_path = ""
            if create_log_file:
                header_log_path = f"{output_base_name}_headers_found.txt"
                self._write_header_log(header_log_path, analysis_data, current_mappings, missing_headers)
                logger.info(f"Header log created: {header_log_path}")

            if interactive and missing_headers:
                self._run_interactive_mapping(missing_headers, current_mappings)
            elif missing_headers:
                logger.info(f"Found {len(missing_headers)} missing headers.")
                if not create_log_file:
                    logger.info("Use --log-headers to see details or --interactive to fix them.")

            return header_log_path
            
        except Exception as e:
            logger.warning(f"Warning: Could not process headers: {e}")
            return ""

    def _load_mappings(self) -> dict:
        current_mappings = {}
        if self.mapping_config_path.exists():
            try:
                with open(self.mapping_config_path, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                    current_mappings = mapping_data.get('header_text_mappings', {}).get('mappings', {})
            except Exception as e:
                logger.warning(f"Could not load mapping config: {e}")
        return current_mappings

    def _find_missing_headers(self, analysis_data: dict, current_mappings: dict) -> list:
        missing_headers = []
        for sheet in analysis_data.get('sheets', []):
            headers = sheet.get('header_positions', [])
            for header in headers:
                keyword = header.get('keyword', 'Unknown')
                if not self._is_mapped(keyword, current_mappings):
                    missing_headers.append(keyword)
        return list(set(missing_headers)) # Unique

    def _is_mapped(self, keyword: str, current_mappings: dict) -> bool:
        # Check exact
        if keyword in current_mappings: return True
        # Check normalized
        if keyword.replace('\n', '\\n') in current_mappings: return True
        # Check case-insensitive
        keyword_lower = keyword.lower()
        for mapped in current_mappings:
            if mapped.lower() == keyword_lower: return True
        return False

    def _write_header_log(self, log_path: str, analysis_data: dict, current_mappings: dict, missing_headers: list):
        # Implementation of full logging logic (simplified for brevity, but should match original logic)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("HEADERS FOUND IN EXCEL FILE\n")
            f.write("=" * 80 + "\n")
            # ... (Full logging logic would go here, reusing logic from original main.py)
            # For now, just logging missing headers summary
            if missing_headers:
                f.write("\nMISSING HEADERS:\n")
                for h in missing_headers:
                    f.write(f"  - {h}\n")

    def _run_interactive_mapping(self, missing_headers: list, current_mappings: dict):
        print(f"\nFound {len(missing_headers)} missing headers!")
        print("Interactive mapping not fully implemented in this refactor step yet.")
        # In a real scenario, we would move the interactive loop here.
        pass
