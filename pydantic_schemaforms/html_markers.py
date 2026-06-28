"""Start/end HTML comment markers that frame every SchemaForms-rendered block."""

from __future__ import annotations

# Keep these markers stable and dependency-free.
# Importing from pydantic_schemaforms.__init__ would create circular imports.
START_MARKER = '<!--- Start Pydantic-SchemaForms -->'
END_MARKER = '<!--- End Pydantic-SchemaForms -->'


def wrap_with_schemaforms_markers(html: str, *, enabled: bool = True) -> str:
    """Wrap html with start/end markers; idempotent and strips existing markers first."""
    if not enabled:
        return html

    normalized = (html or '').lstrip().rstrip()
    lines = normalized.splitlines()
    if lines and lines[0].strip() == START_MARKER:
        lines = lines[1:]
    if lines and lines[-1].strip() == END_MARKER:
        lines = lines[:-1]

    inner = '\n'.join(lines).strip()
    if inner:
        return f'{START_MARKER}\n{inner}\n{END_MARKER}'

    return f'{START_MARKER}\n{END_MARKER}'
