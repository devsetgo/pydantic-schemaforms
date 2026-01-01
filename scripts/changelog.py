"""Update CHANGELOG.md from GitHub releases.

This is used by CI to generate `docs/release-notes.md` before deploying
versioned documentation with mike.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def set_date_time(published_at: str) -> str:
    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    published_at = published_at.replace(tzinfo=ZoneInfo("UTC"))  # Make it aware in UTC
    published_at = published_at.astimezone(
        ZoneInfo("America/New_York")
    )  # Convert to US Eastern Time
    return published_at.strftime("%Y %B %d, %H:%M")  # Format it to a more human-readable format


def get_github_releases(repo: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
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

    lines = lines[:index]

    for release in releases:
        # Skip drafts and prereleases from the changelog unless you explicitly want them.
        if release.get("draft") is True:
            continue

        try:
            name = release.get("name") or release["tag_name"]
            tag_name = release["tag_name"]
            published_at = set_date_time(release["published_at"])
            body = release.get("body") or ""
            release_url = release["html_url"]
        except KeyError as e:
            print(f"Key error: {e}")
            continue

        markdown = (
            f"### <span style='color:blue'>{name}</span> ([{tag_name}]({release_url}))\n\n"
            f"{body}\n\n"
            f"Published Date: {published_at}\n\n"
        )
        lines.append(markdown)

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main()
