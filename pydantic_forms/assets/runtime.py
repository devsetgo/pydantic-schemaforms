from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=32)
def read_asset_text(relative_path: str) -> str:
    """Read packaged asset text by path relative to the pydantic_forms package.

    Example: "assets/vendor/htmx/htmx.min.js"
    """
    package_root = resources.files('pydantic_forms')
    return (package_root / relative_path).read_text(encoding='utf-8')


def script_tag_inline(js: str) -> str:
    return f"<script>\n{js}\n</script>"


def script_tag_src(src: str) -> str:
    return f'<script src="{src}"></script>'


@lru_cache(maxsize=8)
def _vendor_manifest() -> dict:
    package_root = resources.files('pydantic_forms')
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


def htmx_script_tag(*, asset_mode: str = 'vendored') -> str:
    """Return the HTMX <script> tag based on the requested asset mode.

    Modes:
    - vendored: inline the vendored HTMX JS (offline-by-default)
    - cdn: reference the pinned CDN URL (explicit opt-in)
    - none: return empty string
    """
    mode = (asset_mode or 'vendored').strip().lower()

    if mode == 'none':
        return ''

    if mode == 'cdn':
        # Explicit opt-in. Keep pinned to the vendored version.
        version = vendored_asset_version('htmx')
        suffix = f'@{version}' if version else ''
        return script_tag_src(f'https://unpkg.com/htmx.org{suffix}')

    # Default: vendored
    js = read_asset_text('assets/vendor/htmx/htmx.min.js')
    return script_tag_inline(js)
