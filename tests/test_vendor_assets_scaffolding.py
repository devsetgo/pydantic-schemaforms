from __future__ import annotations

import json

from pydantic_schemaforms.vendor_assets import manifest_path
from pydantic_schemaforms.vendor_assets import verify_manifest_files


def test_vendor_manifest_exists_and_has_expected_shape() -> None:
    path = manifest_path()
    assert path.exists(), f"Missing vendor manifest at {path}"

    payload = json.loads(path.read_text(encoding='utf-8'))
    assert isinstance(payload.get('schema_version'), int)
    assert 'assets' in payload
    assert isinstance(payload['assets'], list)


def test_vendor_assets_dir_exists() -> None:
    vendor_dir = manifest_path().parent
    assert vendor_dir.exists()
    assert (vendor_dir / 'vendor_manifest.json').exists()


def test_vendor_manifest_checksums_verify() -> None:
    verify_manifest_files(require_nonempty=True)
