#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _request_json(url: str, token: Optional[str]) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pydantic-schemaforms-docs-generator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        payload = resp.read().decode(charset)
        return json.loads(payload)


def _normalize_repo(repo: str) -> str:
    repo = repo.strip()
    if repo.startswith("https://github.com/"):
        repo = repo.removeprefix("https://github.com/")
    return repo.strip("/")


def fetch_releases(*, repo: str, limit: int, token: Optional[str]) -> List[Dict[str, Any]]:
    repo = _normalize_repo(repo)

    releases: List[Dict[str, Any]] = []
    per_page = 100
    max_pages = (limit + per_page - 1) // per_page

    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/releases?per_page={per_page}&page={page}"
        batch = _request_json(url, token)
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected GitHub API response for {url}: {type(batch)}")

        if not batch:
            break

        for item in batch:
            if isinstance(item, dict):
                releases.append(item)
                if len(releases) >= limit:
                    return releases

    return releases


def render_markdown(*, repo: str, releases: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = []
    lines.append("# Release notes")
    lines.append("")
    lines.append(f"Generated from GitHub releases for `{_normalize_repo(repo)}` on {now}.")
    lines.append("")

    if not releases:
        lines.append("No releases found.")
        return "\n".join(lines) + "\n"

    for rel in releases:
        tag = rel.get("tag_name") or "(no tag)"
        name = rel.get("name") or ""
        published_at = rel.get("published_at") or ""
        prerelease = bool(rel.get("prerelease"))
        draft = bool(rel.get("draft"))
        html_url = rel.get("html_url") or ""

        title_bits = [str(tag)]
        if name and name != tag:
            title_bits.append(str(name))
        title = " — ".join(title_bits)

        flags: List[str] = []
        if draft:
            flags.append("draft")
        if prerelease:
            flags.append("pre-release")

        lines.append(f"## {title}")
        lines.append("")

        meta_bits: List[str] = []
        if published_at:
            meta_bits.append(f"Published: `{published_at}`")
        if flags:
            meta_bits.append("Status: " + ", ".join(f"`{f}`" for f in flags))
        if html_url:
            meta_bits.append(f"Link: {html_url}")

        if meta_bits:
            for bit in meta_bits:
                lines.append(f"- {bit}")
            lines.append("")

        body = rel.get("body") or ""
        body = body.strip()
        if body:
            lines.append(body)
            lines.append("")
        else:
            lines.append("*(No release notes provided.)*")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/release-notes.md from GitHub Releases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python scripts/generate_release_notes.py --repo devsetgo/pydantic-schemaforms --max 1000

            If you hit GitHub API rate limits:
              export GITHUB_TOKEN=...  # fine-grained token with public repo read access
              python scripts/generate_release_notes.py --repo devsetgo/pydantic-schemaforms --max 1000
            """.strip()
        ),
    )
    parser.add_argument("--repo", required=True, help="GitHub repo in the form owner/name")
    parser.add_argument("--max", type=int, default=1000, help="Max number of releases to fetch")
    parser.add_argument(
        "--out",
        default="docs/release-notes.md",
        help="Output markdown path (default: docs/release-notes.md)",
    )

    args = parser.parse_args(argv)

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    try:
        releases = fetch_releases(repo=args.repo, limit=max(1, args.max), token=token)
        md = render_markdown(repo=args.repo, releases=releases)

        out_path = args.out
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"Wrote {out_path} ({len(releases)} releases)")
        return 0
    except HTTPError as e:
        print(f"GitHub API error: HTTP {e.code} {e.reason}", file=sys.stderr)
        try:
            details = e.read().decode("utf-8", errors="replace")
            print(details, file=sys.stderr)
        except Exception:
            pass
        return 2
    except URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
