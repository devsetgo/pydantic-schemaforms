"""Content-Security-Policy nonces for the ``<script>`` and ``<style>`` tags the library emits.

Every such tag is built by ``script_tag``, ``script_src_tag`` or ``style_tag``,
which add ``nonce="..."`` while a ``csp_nonces()`` block is active. The render
entry points open that block from their ``script_nonce=``/``style_nonce=``
arguments. Tags an app writes itself, such as a ``<script>`` inside
``content_html``, are never given the nonce, so a policy still blocks a script
that was injected there.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from .tstring import SafeHTML, html

__all__ = ['csp_nonces', 'script_src_tag', 'script_tag', 'strip_script_tags', 'style_tag']

# The CSP grammar for a nonce: base64 or base64url characters, up to two '=' of padding.
_NONCE_RE = re.compile(r'[A-Za-z0-9+/_-]+={0,2}')
_SCRIPT_RE = re.compile(r'<script\b.*?</script>', re.DOTALL | re.IGNORECASE)

_script_nonce: ContextVar[str | None] = ContextVar('schemaforms_script_nonce', default=None)
_style_nonce: ContextVar[str | None] = ContextVar('schemaforms_style_nonce', default=None)


def check_nonce(value: object, name: str) -> str | None:
    """Return *value* if it is ``None`` or a valid CSP nonce; raise ``ValueError`` otherwise."""

    if value is None:
        return None
    if not isinstance(value, str) or not _NONCE_RE.fullmatch(value):
        raise ValueError(
            f'{name} must be a base64 or base64url token, the form a Content-Security-Policy '
            f'nonce takes (for example secrets.token_urlsafe(16)); got {value!r}'
        )
    return value


@contextmanager
def csp_nonces(script_nonce: str | None = None, style_nonce: str | None = None) -> Iterator[None]:
    """Give every ``<script>``/``<style>`` the library renders inside the block a nonce.

    ``None`` keeps the value of an enclosing block, so a nested render inherits it.
    """

    script = check_nonce(script_nonce, 'script_nonce')
    style = check_nonce(style_nonce, 'style_nonce')
    tokens: list[tuple[ContextVar[str | None], Token[str | None]]] = []
    if script is not None:
        tokens.append((_script_nonce, _script_nonce.set(script)))
    if style is not None:
        tokens.append((_style_nonce, _style_nonce.set(style)))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)


def _open_tag(name: str, attrs: str, nonce: str | None) -> SafeHTML:
    # attrs are library-written attribute text (e.g. 'data-schemaforms-confirm'), never user data.
    _attrs = SafeHTML(f' {attrs}' if attrs else '')
    if nonce is None:
        return html(t'<{SafeHTML(name)}{_attrs}>')
    return html(t'<{SafeHTML(name)}{_attrs} nonce="{nonce}">')


def script_tag(js: str, attrs: str = '') -> SafeHTML:
    """``<script>`` around library JavaScript.

    *js* is element content, not an HTML context, so it is passed through rather
    than escaped (CLAUDE.md rule 4); it must never contain user data.
    """

    return SafeHTML(_open_tag('script', attrs, _script_nonce.get()) + js + '</script>')


def script_src_tag(src: str, attrs: str = '') -> SafeHTML:
    """``<script src="...">`` for a vendored or CDN asset; *src* is escaped."""

    _src = f'src="{html(t"{src}")}"'
    return SafeHTML(
        _open_tag('script', f'{_src} {attrs}' if attrs else _src, _script_nonce.get()) + '</script>'
    )


def style_tag(css: str, attrs: str = '') -> SafeHTML:
    """``<style>`` around library CSS; *css* is passed through like ``script_tag``'s JS."""

    return SafeHTML(_open_tag('style', attrs, _style_nonce.get()) + css + '</style>')


def strip_script_tags(markup: str) -> str:
    """*markup* with every ``<script>...</script>`` element removed, nonce or not."""

    return _SCRIPT_RE.sub('', markup)
