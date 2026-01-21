"""Main entry point for GDHistogram."""

import sys
import argparse


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
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


def check_ui_dependencies():
    """Check if UI dependencies are available."""
    try:
        import PySide6
        return True, None
    except ImportError as e:
        return False, str(e)


def check_web_dependencies():
    """Check if web dependencies are available."""
    try:
        import flask
        return True, None
    except ImportError as e:
        return False, str(e)


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
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run web-based interface (works in Codespaces)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for web interface (default: 5000)"
    )
    args = parser.parse_args()
    
    if args.version:
        from gdhistogram.config import APP_NAME, APP_VERSION
        print(f"{APP_NAME} v{APP_VERSION}")
        sys.exit(0)
    
    if args.check_deps:
        missing = check_dependencies()
        if missing:
            print("Missing core dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            print("\nInstall with: pip install -r requirements.txt")
            sys.exit(1)
        
        ui_ok, ui_err = check_ui_dependencies()
        web_ok, web_err = check_web_dependencies()
        
        print("Core dependencies: ✓ All installed")
        print(f"Desktop UI (PySide6): {'✓' if ui_ok else '✗ ' + ui_err}")
        print(f"Web UI (Flask): {'✓' if web_ok else '✗ ' + web_err}")
        sys.exit(0)
    
    # Check core dependencies
    missing = check_dependencies()
    if missing:
        print("Error: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run web interface if requested or if desktop UI not available
    if args.web:
        web_ok, web_err = check_web_dependencies()
        if not web_ok:
            print(f"Error: Flask not installed: {web_err}")
            print("Install with: pip install flask")
            sys.exit(1)
        
        from gdhistogram.web_app import run_web_app
        run_web_app(port=args.port)
        return
    
    # Try desktop UI first
    ui_ok, ui_err = check_ui_dependencies()
    if ui_ok:
        try:
            from gdhistogram.ui.app import run_app
            sys.exit(run_app())
        except ImportError as e:
            print(f"Error: Failed to import UI components: {e}")
            print("\nFalling back to web interface...")
            args.web = True
    
    # Fall back to web interface
    if not ui_ok or args.web:
        web_ok, web_err = check_web_dependencies()
        if web_ok:
            print("Desktop UI not available, starting web interface...")
            print("This works great in GitHub Codespaces!\n")
            from gdhistogram.web_app import run_web_app
            run_web_app(port=args.port)
        else:
            print("Error: Neither desktop UI nor web UI available.")
            print("\nFor desktop UI (PySide6):")
            print("  - On Ubuntu/Debian: sudo apt-get install libgl1-mesa-glx libegl1")
            print("  - Then: pip install PySide6")
            print("\nFor web UI (Flask):")
            print("  pip install flask")
            sys.exit(1)


if __name__ == "__main__":
    main()
