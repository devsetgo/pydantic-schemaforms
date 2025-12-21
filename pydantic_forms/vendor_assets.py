from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


VENDOR_MANIFEST_RELATIVE_PATH = Path('assets/vendor/vendor_manifest.json')


@dataclass(frozen=True)
class VendoredFile:
    path: str
    sha256: str
    source_url: str


def project_root() -> Path:
    # This works in editable installs and source checkouts.
    return Path(__file__).resolve().parents[1]


def manifest_path() -> Path:
    return project_root() / 'pydantic_forms' / VENDOR_MANIFEST_RELATIVE_PATH


def load_manifest() -> dict[str, Any]:
    path = manifest_path()
    return json.loads(path.read_text(encoding='utf-8'))


def write_manifest(manifest: dict[str, Any]) -> None:
    path = manifest_path()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + '\n', encoding='utf-8')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def http_get_bytes(url: str, *, user_agent: str = 'pydantic-forms-vendor-script') -> bytes:
    req = Request(url, headers={'User-Agent': user_agent})
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def upsert_asset_entry(manifest: dict[str, Any], *, name: str, entry: dict[str, Any]) -> None:
    assets = manifest.setdefault('assets', [])
    for idx, existing in enumerate(assets):
        if isinstance(existing, dict) and existing.get('name') == name:
            assets[idx] = entry
            return
    assets.append(entry)


def latest_htmx_version() -> str:
    """Return latest HTMX version string without leading 'v'.

    Uses the public GitHub API (no auth). If this ever becomes rate-limited,
    callers can pass an explicit version.
    """
    data = http_get_bytes('https://api.github.com/repos/bigskysoftware/htmx/releases/latest')
    payload = json.loads(data.decode('utf-8'))
    tag = str(payload.get('tag_name') or '').strip()
    return tag[1:] if tag.startswith('v') else tag


def vendor_htmx(*, version: str | None = None) -> VendoredFile:
    """Download and vendor HTMX into the package assets folder.

    Returns the recorded vendored file info.
    """
    resolved_version = version or latest_htmx_version()
    download_url = f'https://github.com/bigskysoftware/htmx/releases/download/v{resolved_version}/htmx.min.js'
    license_url = 'https://raw.githubusercontent.com/bigskysoftware/htmx/master/LICENSE'

    js_bytes = http_get_bytes(download_url)
    js_rel_path = Path('pydantic_forms/assets/vendor/htmx/htmx.min.js')
    js_abs_path = project_root() / js_rel_path
    ensure_parent_dir(js_abs_path)
    js_abs_path.write_bytes(js_bytes)
    js_hash = sha256_bytes(js_bytes)

    license_bytes = http_get_bytes(license_url)
    license_rel_path = Path('pydantic_forms/assets/vendor/htmx/LICENSE')
    license_abs_path = project_root() / license_rel_path
    ensure_parent_dir(license_abs_path)
    license_abs_path.write_bytes(license_bytes)
    license_hash = sha256_bytes(license_bytes)

    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        manifest['schema_version'] = 1

    entry = {
        'name': 'htmx',
        'version': resolved_version,
        'files': [
            {
                'path': js_rel_path.as_posix(),
                'sha256': js_hash,
                'source_url': download_url,
            },
            {
                'path': license_rel_path.as_posix(),
                'sha256': license_hash,
                'source_url': license_url,
            },
        ],
    }
    upsert_asset_entry(manifest, name='htmx', entry=entry)
    write_manifest(manifest)

    return VendoredFile(path=js_rel_path.as_posix(), sha256=js_hash, source_url=download_url)


def verify_manifest_files(*, require_nonempty: bool = False) -> None:
    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        raise ValueError('vendor manifest missing integer schema_version')

    assets = manifest.get('assets')
    if not isinstance(assets, list):
        raise ValueError('vendor manifest assets must be a list')

    if require_nonempty and not assets:
        raise ValueError('vendor manifest has no assets')

    root = project_root()
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError('vendor manifest asset entries must be objects')
        files = asset.get('files')
        if not isinstance(files, list):
            raise ValueError(f"asset {asset.get('name')} missing files list")
        for f in files:
            if not isinstance(f, dict):
                raise ValueError('asset file entries must be objects')
            rel = f.get('path')
            expected = f.get('sha256')
            if not isinstance(rel, str) or not rel:
                raise ValueError('asset file missing path')
            if not isinstance(expected, str) or len(expected) != 64:
                raise ValueError(f"asset file {rel} missing sha256")
            abs_path = root / rel
            if not abs_path.exists():
                raise FileNotFoundError(f"vendored file missing: {rel}")
            actual = sha256_file(abs_path)
            if actual != expected:
                raise ValueError(f"sha256 mismatch for {rel}: expected {expected} got {actual}")


def env_truthy(name: str) -> bool:
    v = os.getenv(name)
    return v is not None and v.strip().lower() in {'1', 'true', 'yes', 'on'}
