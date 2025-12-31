#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pydantic_schemaforms.vendor_assets import (
    load_manifest,
    vendor_bootstrap,
    vendor_htmx,
    vendor_imask,
    vendor_materialize,
    verify_manifest_files,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description='Vendor and verify third-party assets.')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_update = sub.add_parser('update-htmx', help='Download and vendor the latest (or specified) HTMX.')
    p_update.add_argument('--version', default=None, help='HTMX version (e.g. 2.0.7). Defaults to latest.')

    p_imask = sub.add_parser('update-imask', help='Download and vendor the latest (or specified) IMask (npm).')
    p_imask.add_argument('--version', default=None, help='IMask version. Defaults to npm latest.')

    p_bootstrap = sub.add_parser('update-bootstrap', help='Download and vendor Bootstrap dist assets.')
    p_bootstrap.add_argument('--version', default='5.3.0', help='Bootstrap version (default: 5.3.0).')

    p_materialize = sub.add_parser('update-materialize', help='Download and vendor Materialize CSS (npm).')
    p_materialize.add_argument('--version', default='1.0.0', help='Materialize version (default: 1.0.0).')

    p_verify = sub.add_parser('verify', help='Verify vendored files match manifest checksums.')
    p_verify.add_argument(
        '--require-nonempty',
        action='store_true',
        help='Fail if no assets are listed in the manifest.',
    )

    p_print = sub.add_parser('print', help='Print the current vendor manifest JSON.')

    args = parser.parse_args(argv)

    if args.cmd == 'update-htmx':
        info = vendor_htmx(version=args.version)
        print(f"Vendored HTMX from {info.source_url}")
        print(f"Wrote {info.path} (sha256={info.sha256})")
        return 0

    if args.cmd == 'update-imask':
        info = vendor_imask(version=args.version)
        print(f"Vendored IMask from {info.source_url}")
        print(f"Wrote {info.path} (sha256={info.sha256})")
        return 0

    if args.cmd == 'update-bootstrap':
        info = vendor_bootstrap(version=args.version)
        print(f"Vendored Bootstrap from {info.source_url}")
        print(f"Wrote {info.path} (sha256={info.sha256})")
        return 0

    if args.cmd == 'update-materialize':
        info = vendor_materialize(version=args.version)
        print(f"Vendored Materialize from {info.source_url}")
        print(f"Wrote {info.path} (sha256={info.sha256})")
        return 0

    if args.cmd == 'verify':
        verify_manifest_files(require_nonempty=bool(args.require_nonempty))
        print('Vendored assets verified OK')
        return 0

    if args.cmd == 'print':
        print(json.dumps(load_manifest(), indent=2, sort_keys=False))
        return 0

    return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
