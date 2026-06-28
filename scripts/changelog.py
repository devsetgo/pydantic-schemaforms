"""Update CHANGELOG.md from GitHub releases.

This is used by CI to generate `docs/release-notes.md` before deploying
versioned documentation with mike.

The script preserves everything above the ``## Latest Changes`` sentinel,
then regenerates that section from the GitHub Releases API. Releases whose
tag already appears in the static section are skipped to avoid duplication.
Production and pre-release entries are rendered under separate sub-headings.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def set_date_time(published_at: str) -> str:
    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    published_at = published_at.replace(tzinfo=ZoneInfo("UTC"))
    published_at = published_at.astimezone(ZoneInfo("America/New_York"))
    return published_at.strftime("%Y %B %d, %H:%M")


def get_github_releases(repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/releases?per_page=1000"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pydantic-schemaforms-docs",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected GitHub API response: {data}")
    return data


def _tags_in_static_section(lines: list[str]) -> set[str]:
    """Return all release tag names already documented above ## Latest Changes."""
    tags: set[str] = set()
    for line in lines:
        # Matches markdown links like [26.2.1.beta](...) or plain [26.2.1]
        for match in re.finditer(r'\[([0-9]+\.[0-9]+\.[0-9]+[^\]]*)\]', line):
            tags.add(match.group(1))
    return tags


def main() -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "devsetgo/pydantic-schemaforms")
    try:
        releases = get_github_releases(repo)
    except Exception as exc:
        print(f"Error fetching GitHub releases for {repo}: {exc}")
        raise

    changelog_path = "CHANGELOG.md"
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{changelog_path} not found.") from exc

    try:
        index = lines.index("## Latest Changes\n") + 1
    except ValueError as exc:
        raise ValueError("## Latest Changes not found in CHANGELOG.md.") from exc

    static_lines = lines[:index]
    already_documented = _tags_in_static_section(static_lines)

    stable: list[str] = []
    pre: list[str] = []

    for release in releases:
        if release.get("draft") is True:
            continue

        try:
            name = release.get("name") or release["tag_name"]
            tag_name = release["tag_name"]
            published_at = set_date_time(release["published_at"])
            body = release.get("body") or ""
            release_url = release["html_url"]
        except KeyError as e:
            print(f"Key error processing release: {e}")
            continue

        if tag_name in already_documented:
            continue

        entry = (
            f"### <span style='color:blue'>{name}</span> ([{tag_name}]({release_url}))\n\n"
            f"{body}\n\n"
            f"Published Date: {published_at}\n\n"
        )

        if release.get("prerelease") is True:
            pre.append(entry)
        else:
            stable.append(entry)

    output = list(static_lines)
    if stable:
        output.append("\n#### Production Releases\n\n")
        output.extend(stable)
    if pre:
        output.append("\n#### Pre-releases\n\n")
        output.extend(pre)

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.writelines(output)


if __name__ == "__main__":
    main()
