#!/usr/bin/env python3
"""
Logging Control Example
========================

Demonstrates two approaches for controlling library logging:
1. Application-level logging configuration (standard Python approach)
2. Explicit enable_logging parameter (library-specific control)
"""

import logging
import sys

sys.path.insert(0, '..')

from pydantic_schemaforms import render_form_html
from shared_models import MinimalLoginForm


def approach_1_app_level_control():
    """
    Approach 1: Control via application logging configuration
    
    This is the standard Python way. The library respects your app's
    logging level.
    """
    print("=" * 70)
    print("APPROACH 1: Application-Level Logging Control")
    print("=" * 70)
    print()
    
    # INFO level - library logs won't appear (they use DEBUG)
    print("With INFO level (typical production):")
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', force=True)
    html = render_form_html(MinimalLoginForm)
    print("✅ No library logs\n")
    
    # DEBUG level - library logs will appear
    print("With DEBUG level (development/troubleshooting):")
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', force=True)
    html = render_form_html(MinimalLoginForm)
    print("✅ Library logs appear when you set DEBUG\n")


def approach_2_explicit_parameter():
    """
    Approach 2: Explicit enable_logging parameter
    
    Gives you fine-grained control even when DEBUG logging is enabled.
    Useful when you want DEBUG logs from your app but not from libraries.
    """
    print("=" * 70)
    print("APPROACH 2: Explicit Parameter Control")
    print("=" * 70)
    print()
    
    # Set DEBUG level
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', force=True)
    
    print("With enable_logging=True (default):")
    html = render_form_html(MinimalLoginForm, enable_logging=True)
    print("✅ Library logs respect logging config\n")
    
    print("With enable_logging=False (suppress library logs):")
    html = render_form_html(MinimalLoginForm, enable_logging=False)
    print("✅ Library logs suppressed even with DEBUG level\n")


def recommendation():
    """Show recommended usage patterns"""
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()
    
    print("For Production:")
    print("  - Run with INFO level: uvicorn app:app --log-level info")
    print("  - Library logs won't appear")
    print("  - No need to set enable_logging\n")
    
    print("For Development (want all logs):")
    print("  - Run with DEBUG level: uvicorn app:app --log-level debug")
    print("  - All logs appear including library internals")
    print("  - No need to set enable_logging\n")
    
    print("For Development (want app logs only):")
    print("  - Run with DEBUG level: uvicorn app:app --log-level debug")
    print("  - Set enable_logging=False in render_form_html()")
    print("  - Example: render_form_html(MyForm, enable_logging=False)\n")
    
    print("Best Practice:")
    print("  ✅ Use Approach 1 (app-level control) in most cases")
    print("  ✅ Use Approach 2 (explicit parameter) for fine-tuning")
    print("  ✅ Leave enable_logging=True by default")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LIBRARY LOGGING CONTROL DEMONSTRATION")
    print("=" * 70)
    print()
    
    approach_1_app_level_control()
    approach_2_explicit_parameter()
    recommendation()
