import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'changelog_script', Path(__file__).parent.parent / 'scripts' / 'changelog.py'
)
changelog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(changelog)

PR_URL = 'https://github.com/devsetgo/pydantic-schemaforms/pull'
CHANGELOG = """## [Unreleased]

## [26.4.5] — 2026-11-01

A summary.

### Added

- A thing. (#12)

## [26.4.4] — 2026-10-31

### Fixed

- Older.
"""


def test_decorate_adds_icons_and_links():
    assert changelog.decorate('### Added') == '### ✨ Added'
    assert changelog.decorate('- A thing (#12) by @someone') == (
        f'- A thing ([#12]({PR_URL}/12)) by [@someone](https://github.com/someone)'
    )


def test_decorate_can_be_rerun():
    text = '### Fixed\n\n- A thing (#12) by @someone\n'
    once = changelog.decorate(text)
    assert changelog.decorate(once) == once


def test_decorate_leaves_code_alone():
    text = '- Use `#123456` and `@decorator`\n```css\n### Added\ncolor: #123;\n```'
    assert changelog.decorate(text) == text


def test_decorate_leaves_links_and_addresses_alone():
    text = '- [#12](https://x.test/#34) [@a](https://x.test/@b) me@example.com'
    assert changelog.decorate(text) == text


def test_format_entry_nests_body_under_the_entry():
    entry = changelog.format_entry(
        {
            'tag_name': '26.4.2',
            'name': 'Support for 3.15',
            'html_url': 'https://x.test/26.4.2',
            'published_at': '2026-10-25T01:09:42Z',
            'body': '## Changes\r\n### Fixes\r\n- A fix (#1)',
        }
    )
    assert entry.startswith('### 🚀 [26.4.2 · Support for 3.15](https://x.test/26.4.2)\n')
    assert '#### 🎁 Changes\n##### 🐛 Fixes\n' in entry
    assert '\r' not in entry


def test_changelog_section_stops_at_the_next_version():
    section = changelog.changelog_section(CHANGELOG, '26.4.5')
    assert section.startswith('A summary.')
    assert 'Older' not in section
    assert changelog.changelog_section(CHANGELOG, '1.0.0') == ''


def test_release_body_adds_highlights_and_can_be_rerun():
    draft = '## What changed\n\n[diff](https://x.test/compare/26.4.4...main)\n'
    body = changelog.release_body(draft, CHANGELOG, '26.4.5')
    assert body.index('A summary.') < body.index('## What changed')
    assert '### ✨ Added' in body
    assert 'compare/26.4.4...26.4.5)' in body
    assert changelog.release_body(body, CHANGELOG, '26.4.5') == body


def test_release_body_without_a_section_keeps_the_draft():
    body = changelog.release_body('Just notes', CHANGELOG, '9.9.9')
    assert body == 'Just notes\n'
