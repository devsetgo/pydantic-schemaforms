from __future__ import annotations

import base64
import json
import re
from functools import lru_cache
from importlib import resources

from pydantic_schemaforms.tstring import SafeHTML, html


@lru_cache(maxsize=32)
def read_asset_text(relative_path: str) -> str:
    """Read packaged asset text by path relative to the pydantic_schemaforms package.

    Example: "assets/vendor/htmx/htmx.min.js"
    """
    package_root = resources.files('pydantic_schemaforms')
    return (package_root / relative_path).read_text(encoding='utf-8')


@lru_cache(maxsize=8)
def read_asset_bytes(relative_path: str) -> bytes:
    """Read packaged asset bytes by path relative to the pydantic_schemaforms package."""
    package_root = resources.files('pydantic_schemaforms')
    return (package_root / relative_path).read_bytes()


def script_tag_inline(js: str) -> str:
    # js is raw <script> element content, not an HTML context -- html-escaping it
    # here would corrupt the JS (e.g. turn `<` into `&lt;`), so it's passed through
    # via SafeHTML rather than escaped like a normal interpolation.
    _js = SafeHTML(js)
    return html(t'<script>\n{_js}\n</script>')


def script_tag_src(src: str) -> str:
    return html(t'<script src="{src}"></script>')


def style_tag_inline(css: str) -> str:
    _css = SafeHTML(css)
    return html(t'<style>\n{_css}\n</style>')


def style_tag_href(href: str) -> str:
    return html(t'<link rel="stylesheet" href="{href}" />')


@lru_cache(maxsize=8)
def _vendor_manifest() -> dict:
    package_root = resources.files('pydantic_schemaforms')
    text = (package_root / 'assets/vendor/vendor_manifest.json').read_text(encoding='utf-8')
    return json.loads(text)


def vendored_asset_version(name: str) -> str | None:
    manifest = _vendor_manifest()
    assets = manifest.get('assets')
    if not isinstance(assets, list):
        return None
    for asset in assets:
        if isinstance(asset, dict) and asset.get('name') == name:
            v = asset.get('version')
            return v if isinstance(v, str) and v else None
    return None


def _normalized_asset_mode(asset_mode: str | None) -> str:
    return (asset_mode or 'vendored').strip().lower()


def _vendored_text_or_empty(relative_path: str) -> str:
    try:
        return read_asset_text(relative_path)
    except FileNotFoundError:
        return ''


def _pinned_unpkg_url(package: str, asset_name: str, path_suffix: str = '') -> str:
    version = vendored_asset_version(asset_name)
    suffix = f'@{version}' if version else ''
    extra = path_suffix if path_suffix.startswith('/') or not path_suffix else f'/{path_suffix}'
    return f'https://unpkg.com/{package}{suffix}{extra}'


def _pinned_jsdelivr_url(package: str, asset_name: str, path_suffix: str = '') -> str:
    version = vendored_asset_version(asset_name)
    suffix = f'@{version}' if version else ''
    extra = path_suffix if path_suffix.startswith('/') or not path_suffix else f'/{path_suffix}'
    return f'https://cdn.jsdelivr.net/npm/{package}{suffix}{extra}'


def htmx_script_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the HTMX <script> tag based on the requested asset mode.

    Modes:
    - vendored: inline the vendored HTMX JS (offline-by-default)
    - cdn: reference the pinned CDN URL (explicit opt-in)
    - none: return empty string
    """
    mode = _normalized_asset_mode(asset_mode)

    if mode == 'none':
        return ''

    if mode == 'cdn':
        # Explicit opt-in. Keep pinned to the vendored version.
        return script_tag_src(_pinned_unpkg_url('htmx.org', 'htmx'))

    # Default: vendored
    js = read_asset_text('assets/vendor/htmx/htmx.min.js')
    return script_tag_inline(js)


def imask_script_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the IMask <script> tag based on the requested asset mode.

    Modes:
    - vendored: inline the vendored IMask JS
    - cdn: reference the pinned CDN URL (explicit opt-in)
    - none: return empty string
    """
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        return script_tag_src(_pinned_unpkg_url('imask', 'imask', 'dist/imask.min.js'))

    js = read_asset_text('assets/vendor/imask/imask.min.js')
    return script_tag_inline(js)


def framework_css_tag(*, framework: str, asset_mode: str = 'vendored') -> str:
    """Return framework CSS tag for Bootstrap/Materialize.

    For asset_mode='vendored', CSS is inlined.
    For asset_mode='cdn', a pinned jsDelivr URL is emitted.
    """
    mode = _normalized_asset_mode(asset_mode)
    fw = (framework or '').strip().lower()

    if mode == 'none' or fw in {'', 'none'}:
        return ''

    if fw == 'bootstrap':
        if mode == 'cdn':
            return style_tag_href(
                _pinned_jsdelivr_url('bootstrap', 'bootstrap', 'dist/css/bootstrap.min.css')
            )
        css = _vendored_text_or_empty('assets/vendor/bootstrap/bootstrap.min.css')
        return style_tag_inline(css) if css else ''

    if fw == 'material':
        if mode == 'cdn':
            return style_tag_href(
                _pinned_jsdelivr_url(
                    '@materializecss/materialize',
                    'materialize',
                    'dist/css/materialize.min.css',
                )
            )
        css = _vendored_text_or_empty('assets/vendor/materialize/materialize.min.css')
        return style_tag_inline(css) if css else ''

    return ''


def framework_js_tag(*, framework: str, asset_mode: str = 'vendored') -> str:
    """Return framework JS tag for Bootstrap/Materialize.

    For asset_mode='vendored', JS is inlined.
    For asset_mode='cdn', a pinned jsDelivr URL is emitted.
    """
    mode = _normalized_asset_mode(asset_mode)
    fw = (framework or '').strip().lower()

    if mode == 'none' or fw in {'', 'none'}:
        return ''

    if fw == 'bootstrap':
        if mode == 'cdn':
            return script_tag_src(
                _pinned_jsdelivr_url('bootstrap', 'bootstrap', 'dist/js/bootstrap.bundle.min.js')
            )
        js = _vendored_text_or_empty('assets/vendor/bootstrap/bootstrap.bundle.min.js')
        return script_tag_inline(js) if js else ''

    if fw == 'material':
        if mode == 'cdn':
            return script_tag_src(
                _pinned_jsdelivr_url(
                    '@materializecss/materialize',
                    'materialize',
                    'dist/js/materialize.min.js',
                )
            )
        js = _vendored_text_or_empty('assets/vendor/materialize/materialize.min.js')
        return script_tag_inline(js) if js else ''

    return ''


@lru_cache(maxsize=4)
def _bootstrap_icons_css_inlined() -> str:
    """Return Bootstrap Icons CSS with the woff2 font inlined as a data URI."""
    css = _vendored_text_or_empty('assets/vendor/bootstrap-icons/bootstrap-icons.min.css')
    if not css:
        return ''
    try:
        font_bytes = read_asset_bytes('assets/vendor/bootstrap-icons/bootstrap-icons.woff2')
        b64 = base64.b64encode(font_bytes).decode('ascii')
        data_uri = f'data:font/woff2;base64,{b64}'
        # Replace both the woff2 url (with or without cache-buster query string) and the
        # woff fallback url so the @font-face block is fully self-contained.
        css = re.sub(
            r'url\("[^"]+"\)\s*format\("woff2"\)',
            f'url("{data_uri}") format("woff2")',
            css,
        )
        css = re.sub(r',\s*url\("[^"]+"\)\s*format\("woff"\)', '', css)
    except FileNotFoundError:
        pass
    return css


def bootstrap_icons_css_content() -> str:
    """Return the Bootstrap Icons CSS with the woff2 font embedded as a data URI.

    Use this when you want to serve the CSS yourself (e.g., from a static endpoint).
    For embedding directly in HTML, use ``bootstrap_icons_css_tag()``.
    """
    return _bootstrap_icons_css_inlined()


def bootstrap_icons_css_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the Bootstrap Icons <style> or <link> tag based on the requested asset mode.

    Modes:
    - vendored: inline the CSS with the woff2 font embedded as a data URI (default)
    - cdn: reference the pinned jsDelivr URL
    - none: return empty string
    """
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        return style_tag_href(
            _pinned_jsdelivr_url(
                'bootstrap-icons', 'bootstrap-icons', 'font/bootstrap-icons.min.css'
            )
        )
    css = _bootstrap_icons_css_inlined()
    return style_tag_inline(css) if css else ''


def datatables_css_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the DataTables <style>/<link> tag based on the requested asset mode."""
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        return style_tag_href(
            _pinned_jsdelivr_url(
                'datatables.net-dt', 'datatables', 'css/dataTables.dataTables.min.css'
            )
        )
    css = _vendored_text_or_empty('assets/vendor/datatables/dataTables.min.css')
    return style_tag_inline(css) if css else ''


def datatables_script_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the DataTables core <script> tag based on the requested asset mode."""
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        return script_tag_src(
            _pinned_jsdelivr_url('datatables.net', 'datatables', 'js/dataTables.min.js')
        )
    js = _vendored_text_or_empty('assets/vendor/datatables/dataTables.min.js')
    return script_tag_inline(js) if js else ''


def datatables_buttons_css_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the DataTables Buttons <style>/<link> tag based on the requested asset mode."""
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        return style_tag_href(
            _pinned_jsdelivr_url(
                'datatables.net-buttons-dt', 'datatables-buttons', 'css/buttons.dataTables.min.css'
            )
        )
    css = _vendored_text_or_empty('assets/vendor/datatables-buttons/buttons.dataTables.min.css')
    return style_tag_inline(css) if css else ''


def datatables_buttons_script_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the DataTables Buttons core + HTML5 export <script> tags (csv/copy only; no Excel/PDF)."""
    mode = _normalized_asset_mode(asset_mode)
    if mode == 'none':
        return ''
    if mode == 'cdn':
        core_url = _pinned_jsdelivr_url(
            'datatables.net-buttons', 'datatables-buttons', 'js/dataTables.buttons.min.js'
        )
        html5_url = _pinned_jsdelivr_url(
            'datatables.net-buttons', 'datatables-buttons', 'js/buttons.html5.min.js'
        )
        return script_tag_src(core_url) + '\n' + script_tag_src(html5_url)
    core_js = _vendored_text_or_empty('assets/vendor/datatables-buttons/dataTables.buttons.min.js')
    html5_js = _vendored_text_or_empty('assets/vendor/datatables-buttons/buttons.html5.min.js')
    parts = [script_tag_inline(js) for js in (core_js, html5_js) if js]
    return '\n'.join(parts)
