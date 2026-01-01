# Vendored assets

This directory is reserved for third-party assets that are shipped with `pydantic-schemaforms`.

## Policy (summary)

- Default rendering must be offline-capable (no external CDNs by default).
- Vendored assets must be pinned and recorded in `vendor_manifest.json`.
- Each asset entry must include a version, a source URL, and a SHA256 checksum.
- License text and notices must be included or referenced as required by the upstream license.

## Update workflow (planned)

Use `python scripts/vendor_assets.py` (and Make targets) to download/update assets and
regenerate the manifest checksums. Manual copy/paste updates are discouraged.
