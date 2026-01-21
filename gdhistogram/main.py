"""Main entry point for GDHistogram."""

import sys


def main():
    """Main entry point."""
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Import and run app
    from gdhistogram.ui.app import run_app
    sys.exit(run_app())


if __name__ == "__main__":
    main()
