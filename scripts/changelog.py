"""Update CHANGELOG.md from GitHub releases.

This is used by CI to generate `docs/release-notes.md` before deploying
versioned documentation with mike.

The script preserves everything above the ``## Latest Changes`` sentinel,
then regenerates that section from the GitHub Releases API. Releases whose
tag already appears in the static section are skipped to avoid duplication.
Production and pre-release entries are rendered under separate sub-headings.
Section headings get an icon and PR/issue/author references become links, so
the changelog can be written in plain Keep a Changelog form.

``--release-body TAG BODY_FILE`` prints a release body with that version's
CHANGELOG section added on top. The publish workflow uses it, so highlights are
written once and shown in both places.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


REPO_URL = "https://github.com/devsetgo/pydantic-schemaforms"
HIGHLIGHTS_START = "<!-- changelog-highlights -->"
HIGHLIGHTS_END = "<!-- /changelog-highlights -->"

SECTION_ICONS = {
    "added": "✨",
    "breaking": "💥",
    "breaking changes": "💥",
    "bug fixes": "🐛",
    "changed": "🔄",
    "changes": "🎁",
    "code improvements": "♻️",
    "contributors": "🙌",
    "dependencies": "⬆️",
    "deprecated": "⚠️",
    "documentation": "📝",
    "features": "✨",
    "fixed": "🐛",
    "fixes": "🐛",
    "github actions": "👷",
    "maintenance": "🔧",
    "removed": "🗑️",
    "security": "🔒",
}


def set_date_time(published_at: str) -> str:
    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    published_at = published_at.replace(tzinfo=ZoneInfo("UTC"))
    published_at = published_at.astimezone(ZoneInfo("America/New_York"))
    return published_at.strftime("%Y %B %d, %H:%M")


def _add_section_icon(line: str) -> str:
    match = re.fullmatch(r"(#{2,6}) (.+?)\s*", line)
    if match is None:
        return line
    icon = SECTION_ICONS.get(match.group(2).lower())
    return f"{match.group(1)} {icon} {match.group(2)}" if icon else line


def _link_references(line: str) -> str:
    # Odd-numbered parts are inside backticks, where `#123` may be a color and
    # `@name` a decorator or package.
    parts = line.split("`")
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(
            r"(?<![\w\[/&#])(?<!\]\()#(\d+)\b",
            rf"[#\1]({REPO_URL}/pull/\1)",
            parts[i],
        )
        parts[i] = re.sub(
            r"(?<![\w\[/.@])@([A-Za-z0-9][A-Za-z0-9-]*)\b(?!\])",
            r"[@\1](https://github.com/\1)",
            parts[i],
        )
    return "`".join(parts)


def decorate(text: str) -> str:
    """Add section icons and reference links, outside code fences. Safe to rerun."""
    output: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        output.append(line if in_fence else _link_references(_add_section_icon(line)))
    return "\n".join(output)


def _demote_headings(body: str) -> str:
    """Keep a release body's headings below the h3 of its changelog entry."""
    return re.sub(
        r"^(#{1,4}) ", lambda m: "#" * (len(m.group(1)) + 2) + " ", body, flags=re.MULTILINE
    )


def format_entry(release: dict) -> str:
    tag_name = release["tag_name"]
    name = release.get("name") or tag_name
    title = tag_name if name == tag_name else f"{tag_name} · {name}"
    icon = "🧪" if release.get("prerelease") else "🚀"
    body = (release.get("body") or "").replace("\r\n", "\n").strip()
    published_at = set_date_time(release["published_at"])
    return (
        f"### {icon} [{title}]({release['html_url']})\n\n"
        f"📅 Published {published_at}\n\n"
        f"{decorate(_demote_headings(body))}\n\n"
    )


def changelog_section(changelog: str, tag: str) -> str:
    """Return the text of a version's section in the changelog, or an empty string."""
    match = re.search(
        rf"^## \[{re.escape(tag)}\][^\n]*\n(.*?)(?=^## |\Z)",
        changelog,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def release_body(body: str, changelog: str, tag: str) -> str:
    """Put a version's changelog section on top of its body. Safe to rerun."""
    body = body.replace("\r\n", "\n")
    body = re.sub(
        rf"{re.escape(HIGHLIGHTS_START)}.*?{re.escape(HIGHLIGHTS_END)}\s*",
        "",
        body,
        flags=re.DOTALL,
    ).strip()
    # The draft can only compare against main, which moves on after the release.
    body = re.sub(r"(/compare/[^)\s]+\.\.\.)main\)", rf"\g<1>{tag})", body)
    section = changelog_section(changelog, tag)
    if not section:
        return body + "\n"
    return f"{HIGHLIGHTS_START}\n{decorate(section)}\n{HIGHLIGHTS_END}\n\n{body}\n"


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
            tag_name = release["tag_name"]
            entry = format_entry(release)
        except KeyError as e:
            print(f"Key error processing release: {e}")
            continue

        if tag_name in already_documented:
            continue

        if release.get("prerelease") is True:
            pre.append(entry)
        else:
            stable.append(entry)

    output = [decorate("".join(static_lines))]
    if stable:
        output.append("\n## 🚀 Production Releases\n\n")
        output.extend(stable)
    if pre:
        output.append("\n## 🧪 Pre-releases\n\n")
        output.extend(pre)

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.writelines(output)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--release-body":
        with open(sys.argv[3], encoding="utf-8") as f:
            current_body = f.read()
        with open("CHANGELOG.md", encoding="utf-8") as f:
            print(release_body(current_body, f.read(), sys.argv[2]), end="")
    else:
        main()
