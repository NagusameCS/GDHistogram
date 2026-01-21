#!/usr/bin/env python3
"""
GDHistogram - Google Docs Revision History Analyzer

Run this script to start the application.
"""

import sys
from pathlib import Path

# Add package to path if running directly
if __name__ == "__main__":
    package_dir = Path(__file__).parent
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))

from gdhistogram.main import main

if __name__ == "__main__":
    main()
