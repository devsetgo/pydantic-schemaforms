#!/usr/bin/env python3
"""
Logging Configuration Example
==============================

This example shows how to configure logging for pydantic-schemaforms.

By default, the library uses DEBUG level logging which won't appear
unless you explicitly configure your application to show DEBUG logs.
"""

import logging
import sys

# Add parent directory to path
sys.path.insert(0, '..')

from pydantic_schemaforms import render_form_html
from shared_models import MinimalLoginForm, UserRegistrationForm


def example_1_no_logging():
    """
    Example 1: Default behavior - no library logs appear
    
    When you use the library without configuring logging,
    the library's internal logs won't appear in your output.
    """
    print("=" * 70)
    print("Example 1: Default (No Logging)")
    print("=" * 70)
    print()
    
    html = render_form_html(MinimalLoginForm, show_timing=True)
    
    print("✅ Form rendered successfully")
    print("✅ No library logs appeared")
    print("✅ Timing still works in the HTML output:", "Rendered in" in html)
    print()


def example_2_with_info_logging():
    """
    Example 2: Application with INFO level logging
    
    Most applications use INFO level logging. The library logs
    won't appear because they use DEBUG level.
    """
    print("=" * 70)
    print("Example 2: Application with INFO Level Logging")
    print("=" * 70)
    print()
    
    # Configure your application's logging (typical setup)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        force=True  # Reconfigure if already configured
    )
    
    print("Application logging configured at INFO level\n")
    
    html = render_form_html(UserRegistrationForm, show_timing=True)
    
    print("\n✅ Form rendered successfully")
    print("✅ Library logs didn't appear (they use DEBUG level)")
    print()


def example_3_with_debug_logging():
    """
    Example 3: Enable library logging for debugging
    
    If you want to see the library's internal logs for debugging,
    configure your logging to DEBUG level.
    """
    print("=" * 70)
    print("Example 3: Enable Library Logging (DEBUG Level)")
    print("=" * 70)
    print()
    
    # Configure logging to DEBUG to see library internals
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        force=True  # Reconfigure if already configured
    )
    
    print("Application logging configured at DEBUG level\n")
    
    html = render_form_html(MinimalLoginForm, show_timing=True)
    
    print("\n✅ Form rendered successfully")
    print("✅ Library DEBUG logs appeared above (if logging was configured before import)")
    print()


def example_4_selective_logging():
    """
    Example 4: Enable logging only for pydantic-schemaforms
    
    You can enable DEBUG logging just for the library without
    affecting your application's logging level.
    """
    print("=" * 70)
    print("Example 4: Selective Library Logging")
    print("=" * 70)
    print()
    
    # Configure root logger at INFO
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s',
        force=True
    )
    
    # Enable DEBUG only for pydantic_schemaforms
    pydantic_logger = logging.getLogger('pydantic_schemaforms')
    pydantic_logger.setLevel(logging.DEBUG)
    
    print("Enabled DEBUG logging only for pydantic_schemaforms\n")
    
    html = render_form_html(UserRegistrationForm, show_timing=True)
    
    print("\n✅ Form rendered successfully")
    print("✅ Library logs visible, but application stays at INFO level")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PYDANTIC-SCHEMAFORMS LOGGING CONFIGURATION EXAMPLES")
    print("=" * 70)
    print()
    
    # Run examples
    example_1_no_logging()
    example_2_with_info_logging()
    # example_3_with_debug_logging()  # Uncomment to see DEBUG logs
    # example_4_selective_logging()    # Uncomment to see selective logging
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("✅ Library logs use DEBUG level - won't appear by default")
    print("✅ Application controls logging - library doesn't interfere")
    print("✅ Enable DEBUG level to see library internals when needed")
    print("✅ show_timing parameter still works in HTML regardless of logging")
    print()
