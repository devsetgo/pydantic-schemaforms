"""PEP 750 t-string HTML processor — structural XSS safety for pydantic-schemaforms.

Every value interpolated into an html() t-string is HTML-escaped automatically,
unless it is already a SafeHTML instance. This makes XSS protection structural:
you cannot accidentally pass unescaped user input into a rendered template.

Composition is safe:
    inner = html(t'<b>{user_name}</b>')   # user_name is escaped; result is SafeHTML
    outer = html(t'<div>{inner}</div>')   # inner passes through unescaped

The substitute() helper handles layout templates whose structure is set by
subclass class attributes (not inline t-string literals). All values passed
to substitute() are treated as already-safe — only use it for developer-
controlled data, never for user input.
"""

from __future__ import annotations

import html as _html
import re
from string.templatelib import Template
from typing import Any

__all__ = ['SafeHTML', 'html', 'substitute']


class SafeHTML(str):
    """Pre-rendered HTML that bypasses auto-escaping in the html() processor.

    Only construct SafeHTML from values you own: rendered library output,
    static HTML literals, or strings that have already been fully escaped.
    Never wrap unvalidated user input in SafeHTML.
    """

    __slots__ = ()


def html(template: Template) -> SafeHTML:
    """Render a t-string, HTML-escaping every interpolation that is not already SafeHTML."""
    parts: list[str] = []
    for chunk in template:
        if isinstance(chunk, str):
            parts.append(chunk)
        else:
            val = chunk.value
            if isinstance(val, SafeHTML):
                parts.append(str(val))
            else:
                parts.append(_html.escape(str(val), quote=True))
    return SafeHTML(''.join(parts))


_PLACEHOLDER: re.Pattern[str] = re.compile(r'\$\{(\w+)\}')


def substitute(template_str: str, **kwargs: Any) -> SafeHTML:
    """Replace ${var} placeholders without escaping — only for developer-controlled layout templates."""

    def _replace(m: re.Match[str]) -> str:
        return str(kwargs.get(m.group(1), m.group(0)))

    return SafeHTML(_PLACEHOLDER.sub(_replace, template_str))
