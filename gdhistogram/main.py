"""Main entry point for GDHistogram."""

import sys
import argparse


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    try:
        import PySide6
    except ImportError as e:
        missing.append(f"PySide6: {e}")
    
    try:
        import plotly
    except ImportError:
        missing.append("plotly")
    
    try:
        import google.oauth2
    except ImportError:
        missing.append("google-auth")
    
    try:
        import googleapiclient
    except ImportError:
        missing.append("google-api-python-client")
    
    try:
        import cryptography
    except ImportError:
        missing.append("cryptography")
    
    return missing


def main():
    """Main entry point."""
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="GDHistogram - Google Docs Revision Analyzer"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if all dependencies are installed"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )
    args = parser.parse_args()
    
    if args.version:
        from gdhistogram.config import APP_NAME, APP_VERSION
        print(f"{APP_NAME} v{APP_VERSION}")
        sys.exit(0)
    
    if args.check_deps:
        missing = check_dependencies()
        if missing:
            print("Missing dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            print("\nInstall with: pip install -r requirements.txt")
            sys.exit(1)
        else:
            print("All dependencies are installed!")
            sys.exit(0)
    
    # Check dependencies before importing UI
    missing = check_dependencies()
    if missing:
        print("Error: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Import and run app
    try:
        from gdhistogram.ui.app import run_app
        sys.exit(run_app())
    except ImportError as e:
        print(f"Error: Failed to import UI components: {e}")
        print("\nThis may be due to missing system libraries for Qt/PySide6.")
        print("On Ubuntu/Debian, try: sudo apt-get install libgl1-mesa-glx libegl1")
        print("On macOS, PySide6 should work out of the box.")
        print("On Windows, ensure Visual C++ Redistributable is installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
