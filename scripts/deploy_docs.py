#!/usr/bin/env python3
"""Deploy versioned documentation using mike.

Designed to work both locally and in GitHub Actions.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def _read_first_match(file_path: Path, pattern: str) -> str | None:
    if not file_path.exists():
        return None
    content = file_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(pattern, content)
    if not match:
        return None
    return match.group(1)


def get_current_version() -> str | None:
    """Infer version from project files or GitHub tag."""
    version_sources: list[tuple[str, str]] = [
        ("pyproject.toml", r"^version\s*=\s*[\"']([^\"']+)[\"']\s*$"),
        ("makefile", r"^APP_VERSION\s*=\s*([^\s]+)\s*$"),
        ("pydantic_schemaforms/__init__.py", r"^__version__\s*=\s*[\"']([^\"']+)[\"']\s*$"),
    ]

    project_root = Path(__file__).resolve().parent.parent

    for rel_path, pattern in version_sources:
        try:
            value = _read_first_match(project_root / rel_path, pattern)
            if value:
                print(f"Found version {value} in {rel_path}")
                return value
        except Exception as exc:
            print(f"Could not read version from {rel_path}: {exc}")

    github_ref = os.environ.get("GITHUB_REF", "")
    if github_ref.startswith("refs/tags/"):
        tag = github_ref.removeprefix("refs/tags/")
        version = tag.lstrip("v")
        if version:
            print(f"Found version {version} from GitHub tag")
            return version

    tag_name = os.environ.get("GITHUB_RELEASE_TAG", "").strip()
    if tag_name:
        version = tag_name.lstrip("v")
        print(f"Found version {version} from GITHUB_RELEASE_TAG")
        return version

    return None


def run_command(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, check=True)


def deploy_documentation(
    version: str,
    *,
    aliases: list[str] | None = None,
    push: bool = False,
    title: str | None = None,
    dev: bool = False,
    ignore_remote_status: bool = False,
) -> None:
    if not version.strip():
        raise ValueError("Version cannot be empty")

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    cmd: list[str] = ["mike", "deploy", version]

    if aliases:
        cmd.extend(aliases)

    if title:
        cmd.extend(["--title", title])

    if not dev:
        cmd.append("--update-aliases")

    if ignore_remote_status:
        cmd.append("--ignore-remote-status")

    if push:
        cmd.append("--push")

    run_command(cmd)


def list_versions() -> None:
    run_command(["mike", "list"])


def serve_docs() -> None:
    run_command(["mike", "serve"])


def delete_version(version: str, *, push: bool = False) -> None:
    cmd = ["mike", "delete", version]
    if push:
        cmd.append("--push")
    run_command(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy versioned documentation with mike")
    parser.add_argument("action", choices=["deploy", "list", "serve", "delete"])
    parser.add_argument("--version", help="Version to deploy (auto-detected if not specified)")
    parser.add_argument("--aliases", nargs="*", default=[], help="Aliases for the version")
    parser.add_argument("--push", action="store_true", help="Push to remote repository")
    parser.add_argument("--title", help="Custom title for the version")
    parser.add_argument("--dev", action="store_true", help="Deploy as development version")
    parser.add_argument(
        "--ignore-remote-status",
        action="store_true",
        help="Ignore remote git status conflicts",
    )

    args = parser.parse_args()

    try:
        if args.action == "deploy":
            version = args.version or get_current_version()
            if not version:
                print("Could not determine version automatically. Please specify --version")
                sys.exit(1)

            aliases = list(args.aliases)
            deploy_documentation(
                version,
                aliases=aliases,
                push=args.push,
                title=args.title,
                dev=args.dev,
                ignore_remote_status=args.ignore_remote_status,
            )
        elif args.action == "list":
            list_versions()
        elif args.action == "serve":
            serve_docs()
        elif args.action == "delete":
            if not args.version:
                print("Version is required for delete action")
                sys.exit(1)
            delete_version(args.version, push=args.push)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    main()
