#!/usr/bin/env python3
"""Prepare docs for MkDocs.

This project currently maintains documentation as static Markdown under `docs/`.
The workflow references this script for parity with other repos; at the moment it
performs only lightweight validation to keep CI predictable.
"""

from __future__ import annotations

from pathlib import Path


def update_docs() -> None:
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        raise FileNotFoundError("docs/ directory not found")


if __name__ == "__main__":
    update_docs()
