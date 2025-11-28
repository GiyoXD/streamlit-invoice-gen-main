#!/usr/bin/env python3
"""
Main orchestrator for the Automated Invoice Config Generator.
Refactored to use the Facade Pattern with ConfigOrchestrator.
"""

import argparse
import sys
import logging
from pathlib import Path

# Ensure src is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config_manager.orchestrator import ConfigOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description='Automated Invoice Configuration Generator.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('excel_file', help='Path to the input Excel file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    parser.add_argument('--keep-intermediate', action='store_true', help='Keep intermediate analysis files.')
    parser.add_argument('--log-headers', action='store_true', help='Create a header log file.')
    parser.add_argument('--interactive', action='store_true', help='Enable interactive mapping.')
    
    # Legacy args that might still be passed but ignored or handled differently
    parser.add_argument('--bundle', action='store_true', help='(Deprecated) Always generates bundle.')
    parser.add_argument('-o', '--output', help='(Deprecated) Output path is now auto-managed.')

    args = parser.parse_args()

    # Configure logging
#!/usr/bin/env python3
"""
Main orchestrator for the Automated Invoice Config Generator.
Refactored to use the Facade Pattern with ConfigOrchestrator.
"""

import argparse
import sys
import logging
from pathlib import Path

# Ensure src is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config_manager.orchestrator import ConfigOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description='Automated Invoice Configuration Generator.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('excel_file', help='Path to the input Excel file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    parser.add_argument('--keep-intermediate', action='store_true', help='Keep intermediate analysis files.')
    parser.add_argument('--log-headers', action='store_true', help='Create a header log file.')
    parser.add_argument('--interactive', action='store_true', help='Enable interactive mapping.')
    
    # Legacy args that might still be passed but ignored or handled differently
    parser.add_argument('--bundle', action='store_true', help='(Deprecated) Always generates bundle.')
    parser.add_argument('-o', '--output', help='(Deprecated) Output path is now auto-managed.')

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.resolve()
    orchestrator = ConfigOrchestrator(base_dir)

    options = {
        'verbose': args.verbose,
        'keep_intermediate': args.keep_intermediate,
        'log_headers': args.log_headers,
        'interactive': args.interactive,
        'output_dir': args.output
    }

    success = orchestrator.run(args.excel_file, options)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()