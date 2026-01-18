"""Utilities for wrapping rendered HTML with identifiable markers.

These markers can be useful when embedding SchemaForms output inside larger HTML
responses, debugging, or post-processing HTML.

The goal is for the start marker to be the first line and the end marker to be
the last line of the returned HTML string.
"""

from __future__ import annotations

# Keep these markers stable and dependency-free.
# Importing from pydantic_schemaforms.__init__ would create circular imports.
START_MARKER = "<!--- Start Pydantic-SchemaForms -->"
END_MARKER = "<!--- End Pydantic-SchemaForms -->"


def wrap_with_schemaforms_markers(html: str, *, enabled: bool = True) -> str:
    """Wrap HTML with SchemaForms start/end markers.

    - Ensures the start marker is the first line (no leading whitespace).
    - Ensures the end marker is the last line (no trailing whitespace).
    - Avoids duplicating markers if already present.

    Args:
        html: HTML string to wrap.
        enabled: If False, returns html unchanged.

    Returns:
        Wrapped HTML string.
    """

    if not enabled:
        return html

    # Normalize whitespace so our markers become true first/last lines.
    normalized = (html or "").lstrip().rstrip()

    # Strip existing markers if present (so we can reliably enforce first/last).
    lines = normalized.splitlines()
    if lines and lines[0].strip() == START_MARKER:
        lines = lines[1:]
    if lines and lines[-1].strip() == END_MARKER:
        lines = lines[:-1]

    inner = "\n".join(lines).strip()
    if inner:
        return f"{START_MARKER}\n{inner}\n{END_MARKER}"

    return f"{START_MARKER}\n{END_MARKER}"
