"""Python 3.14+ version guard — raises immediately on older runtimes."""

import sys


def check_python_version() -> None:
    if sys.version_info < (3, 14):
        raise RuntimeError(
            f'pydantic-schemaforms requires Python 3.14 or higher. '
            f'Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'
            f'This library uses native Python 3.14 template strings and provides no backward compatibility.\n'
            f'Please upgrade to Python 3.14+ to use pydantic-schemaforms.'
        )


def verify_template_strings() -> None:
    import importlib.util

    try:
        spec = importlib.util.find_spec('string.templatelib')
        if spec is None:
            raise ImportError('string.templatelib module not found')
        __import__('string.templatelib')  # confirm importability; don't keep a module reference
    except ImportError as e:
        raise ImportError(
            f'string.templatelib is not available. '
            f"This suggests you're not using Python 3.14+ or the installation is incomplete.\n"
            f'pydantic-schemaforms requires Python 3.14+ with native template string support.\n'
            f'Original error: {e}'
        ) from e


check_python_version()
verify_template_strings()
