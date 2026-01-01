"""
Python version validation for pydantic-schemaforms.

This library requires Python 3.14+ for native template string support.
No backward compatibility is provided for older Python versions.
"""

import sys


def check_python_version() -> None:
    """
    Check that Python 3.14+ is being used.

    Raises:
        RuntimeError: If Python version is less than 3.14
    """
    if sys.version_info < (3, 14):
        raise RuntimeError(
            f"pydantic-schemaforms requires Python 3.14 or higher. "
            f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            f"This library uses native Python 3.14 template strings and provides no backward compatibility.\n"
            f"Please upgrade to Python 3.14+ to use pydantic-schemaforms."
        )


def verify_template_strings() -> None:
    """
    Verify that template strings are available.

    Raises:
        ImportError: If string.templatelib is not available
    """
    import importlib.util

    try:
        spec = importlib.util.find_spec("string.templatelib")
        if spec is None:
            raise ImportError("string.templatelib module not found")
        # Test that we can actually import it (don't keep the import)
        __import__("string.templatelib")
    except ImportError as e:
        raise ImportError(
            f"string.templatelib is not available. "
            f"This suggests you're not using Python 3.14+ or the installation is incomplete.\n"
            f"pydantic-schemaforms requires Python 3.14+ with native template string support.\n"
            f"Original error: {e}"
        ) from e


# Run version checks on import
check_python_version()
verify_template_strings()
