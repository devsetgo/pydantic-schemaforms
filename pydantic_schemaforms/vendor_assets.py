from __future__ import annotations

import hashlib
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
import tarfile
import zipfile
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
    return project_root() / 'pydantic_schemaforms' / VENDOR_MANIFEST_RELATIVE_PATH


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


def http_get_bytes(url: str, *, user_agent: str = 'pydantic-schemaforms-vendor-script') -> bytes:
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


def npm_package_metadata(package_name: str) -> dict[str, Any]:
    """Fetch package metadata from the npm registry."""
    url = f'https://registry.npmjs.org/{package_name}'
    data = http_get_bytes(url)
    payload = json.loads(data.decode('utf-8'))
    if not isinstance(payload, dict):
        raise ValueError(f'npm registry payload for {package_name} was not an object')
    return payload


def latest_npm_version(package_name: str) -> str:
    payload = npm_package_metadata(package_name)
    dist_tags = payload.get('dist-tags')
    if not isinstance(dist_tags, dict):
        raise ValueError(f'npm registry payload for {package_name} missing dist-tags')
    latest = dist_tags.get('latest')
    if not isinstance(latest, str) or not latest.strip():
        raise ValueError(f'npm registry payload for {package_name} missing latest dist-tag')
    return latest.strip()


def npm_tarball_url(package_name: str, version: str) -> str:
    payload = npm_package_metadata(package_name)
    versions = payload.get('versions')
    if not isinstance(versions, dict) or version not in versions:
        raise ValueError(f'npm registry payload for {package_name} missing version {version}')
    meta = versions.get(version)
    if not isinstance(meta, dict):
        raise ValueError(f'npm registry payload for {package_name}@{version} invalid')
    dist = meta.get('dist')
    if not isinstance(dist, dict):
        raise ValueError(f'npm registry payload for {package_name}@{version} missing dist')
    url = dist.get('tarball')
    if not isinstance(url, str) or not url.strip():
        raise ValueError(f'npm registry payload for {package_name}@{version} missing tarball url')
    return url.strip()


def _safe_member_bytes_from_tgz(tgz_bytes: bytes, member_path: str) -> bytes:
    """Extract a single file from an npm .tgz (tar.gz) blob.

    npm tarballs are typically prefixed with "package/".
    """
    with tarfile.open(fileobj=io.BytesIO(tgz_bytes), mode='r:gz') as tf:
        # Accept both with/without the "package/" prefix.
        candidates = [f'package/{member_path.lstrip("/")}', member_path.lstrip('/')]
        for name in candidates:
            try:
                member = tf.getmember(name)
            except KeyError:
                continue
            if not member.isfile():
                raise ValueError(f'npm tarball member is not a file: {name}')
            f = tf.extractfile(member)
            if f is None:
                raise ValueError(f'failed to extract npm tarball member: {name}')
            return f.read()
    raise FileNotFoundError(f'missing file in npm tarball: {member_path}')


def _write_vendored_file(*, rel_path: Path, data: bytes, source_url: str) -> dict[str, str]:
    abs_path = project_root() / rel_path
    ensure_parent_dir(abs_path)
    abs_path.write_bytes(data)
    return {
        'path': rel_path.as_posix(),
        'sha256': sha256_bytes(data),
        'source_url': source_url,
    }


def vendor_htmx(*, version: str | None = None) -> VendoredFile:
    """Download and vendor HTMX into the package assets folder.

    Returns the recorded vendored file info.
    """
    resolved_version = version or latest_htmx_version()
    download_url = f'https://github.com/bigskysoftware/htmx/releases/download/v{resolved_version}/htmx.min.js'
    license_url = 'https://raw.githubusercontent.com/bigskysoftware/htmx/master/LICENSE'

    js_bytes = http_get_bytes(download_url)
    js_rel_path = Path('pydantic_schemaforms/assets/vendor/htmx/htmx.min.js')
    js_entry = _write_vendored_file(rel_path=js_rel_path, data=js_bytes, source_url=download_url)

    license_bytes = http_get_bytes(license_url)
    license_rel_path = Path('pydantic_schemaforms/assets/vendor/htmx/LICENSE')
    license_entry = _write_vendored_file(rel_path=license_rel_path, data=license_bytes, source_url=license_url)

    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        manifest['schema_version'] = 1

    entry = {
        'name': 'htmx',
        'version': resolved_version,
        'files': [
            js_entry,
            license_entry,
        ],
    }
    upsert_asset_entry(manifest, name='htmx', entry=entry)
    write_manifest(manifest)

    return VendoredFile(path=js_entry['path'], sha256=js_entry['sha256'], source_url=download_url)


def vendor_imask(*, version: str | None = None) -> VendoredFile:
    """Download and vendor IMask (npm) into the package assets folder."""

    package = 'imask'
    resolved_version = version or latest_npm_version(package)
    tarball_url = npm_tarball_url(package, resolved_version)
    tgz = http_get_bytes(tarball_url)

    # Common dist paths for the imask package
    js_bytes = _safe_member_bytes_from_tgz(tgz, 'dist/imask.min.js')
    js_rel_path = Path('pydantic_schemaforms/assets/vendor/imask/imask.min.js')
    js_entry = _write_vendored_file(rel_path=js_rel_path, data=js_bytes, source_url=tarball_url)

    license_bytes: bytes
    try:
        license_bytes = _safe_member_bytes_from_tgz(tgz, 'LICENSE')
    except FileNotFoundError:
        license_bytes = _safe_member_bytes_from_tgz(tgz, 'LICENSE.md')
    license_rel_path = Path('pydantic_schemaforms/assets/vendor/imask/LICENSE')
    license_entry = _write_vendored_file(rel_path=license_rel_path, data=license_bytes, source_url=tarball_url)

    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        manifest['schema_version'] = 1

    entry = {
        'name': 'imask',
        'version': resolved_version,
        'files': [
            js_entry,
            license_entry,
        ],
    }
    upsert_asset_entry(manifest, name='imask', entry=entry)
    write_manifest(manifest)

    return VendoredFile(path=js_entry['path'], sha256=js_entry['sha256'], source_url=tarball_url)


def vendor_materialize(*, version: str = '1.0.0') -> VendoredFile:
    """Download and vendor @materializecss/materialize (npm) assets."""
    package = '@materializecss/materialize'
    resolved_version = version
    tarball_url = npm_tarball_url(package, resolved_version)
    tgz = http_get_bytes(tarball_url)

    css_bytes = _safe_member_bytes_from_tgz(tgz, 'dist/css/materialize.min.css')
    css_rel_path = Path('pydantic_schemaforms/assets/vendor/materialize/materialize.min.css')
    css_entry = _write_vendored_file(rel_path=css_rel_path, data=css_bytes, source_url=tarball_url)

    js_bytes = _safe_member_bytes_from_tgz(tgz, 'dist/js/materialize.min.js')
    js_rel_path = Path('pydantic_schemaforms/assets/vendor/materialize/materialize.min.js')
    js_entry = _write_vendored_file(rel_path=js_rel_path, data=js_bytes, source_url=tarball_url)

    license_bytes: bytes
    try:
        license_bytes = _safe_member_bytes_from_tgz(tgz, 'LICENSE')
    except FileNotFoundError:
        license_bytes = _safe_member_bytes_from_tgz(tgz, 'LICENSE.md')
    license_rel_path = Path('pydantic_schemaforms/assets/vendor/materialize/LICENSE')
    license_entry = _write_vendored_file(rel_path=license_rel_path, data=license_bytes, source_url=tarball_url)

    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        manifest['schema_version'] = 1

    entry = {
        'name': 'materialize',
        'version': resolved_version,
        'files': [
            css_entry,
            js_entry,
            license_entry,
        ],
    }
    upsert_asset_entry(manifest, name='materialize', entry=entry)
    write_manifest(manifest)

    return VendoredFile(path=js_entry['path'], sha256=js_entry['sha256'], source_url=tarball_url)


def vendor_bootstrap(*, version: str = '5.3.0') -> VendoredFile:
    """Download and vendor Bootstrap dist assets from GitHub releases."""
    resolved_version = version
    zip_url = f'https://github.com/twbs/bootstrap/releases/download/v{resolved_version}/bootstrap-{resolved_version}-dist.zip'
    license_url = f'https://raw.githubusercontent.com/twbs/bootstrap/v{resolved_version}/LICENSE'
    zip_bytes = http_get_bytes(zip_url)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        css_candidates = [n for n in names if n.endswith('bootstrap.min.css')]
        js_candidates = [n for n in names if n.endswith('bootstrap.bundle.min.js')]

        if not css_candidates:
            raise FileNotFoundError('missing bootstrap.min.css in bootstrap dist zip')
        if not js_candidates:
            raise FileNotFoundError('missing bootstrap.bundle.min.js in bootstrap dist zip')

        css_bytes = zf.read(css_candidates[0])
        js_bytes = zf.read(js_candidates[0])

    # The dist ZIP does not reliably include the license; fetch from upstream tag.
    license_bytes = http_get_bytes(license_url)

    css_rel_path = Path('pydantic_schemaforms/assets/vendor/bootstrap/bootstrap.min.css')
    css_entry = _write_vendored_file(rel_path=css_rel_path, data=css_bytes, source_url=zip_url)

    js_rel_path = Path('pydantic_schemaforms/assets/vendor/bootstrap/bootstrap.bundle.min.js')
    js_entry = _write_vendored_file(rel_path=js_rel_path, data=js_bytes, source_url=zip_url)

    license_rel_path = Path('pydantic_schemaforms/assets/vendor/bootstrap/LICENSE')
    license_entry = _write_vendored_file(rel_path=license_rel_path, data=license_bytes, source_url=license_url)

    manifest = load_manifest()
    if not isinstance(manifest.get('schema_version'), int):
        manifest['schema_version'] = 1

    entry = {
        'name': 'bootstrap',
        'version': resolved_version,
        'files': [
            css_entry,
            js_entry,
            license_entry,
        ],
    }
    upsert_asset_entry(manifest, name='bootstrap', entry=entry)
    write_manifest(manifest)

    return VendoredFile(path=js_entry['path'], sha256=js_entry['sha256'], source_url=zip_url)


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
