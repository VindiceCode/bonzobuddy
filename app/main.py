#!/usr/bin/env python3
"""
Bonzo Buddy v2 - Main Application Entry Point

A professional-grade desktop application for testing webhook integrations.
Built with Python, Pydantic, and CustomTkinter.
"""

import sys
import os
from pathlib import Path

# Add the bonzobuddy directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ui.main_window import BonzoBuddyApp


def main():
    """Main application entry point."""
    try:
        # Create and run the application
        app = BonzoBuddyApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()