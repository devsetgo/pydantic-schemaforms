"""Regenerate the screenshots on the demo site's home page.

Renders the forms with the library itself and photographs them with Playwright,
so the pictures always match the current release. Run after a visual change:

    python scripts/example_screenshots.py      # or: make example-screenshots
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from examples.shared_models import LayoutDemonstrationForm, SignupForm  # noqa: E402
from pydantic_schemaforms import SafeHTML, html  # noqa: E402

OUT = ROOT / 'examples' / 'img' / 'screenshots'

_SIGNUP_MISTAKES = {'name': 'A', 'email': 'ada@example', 'plan': 'Team', 'start_date': ''}


def _page(form: str, *, dark: bool = False) -> str:
    body = SafeHTML(form)
    theme = 'dark' if dark else 'light'
    # Material's tokens live on the form, so the page behind it takes the same surface color.
    page_color = '#141218' if dark else '#ffffff'
    return str(
        html(
            t'<!doctype html><html data-bs-theme="{theme}" data-md-theme="{theme}"><head>'
            t'<meta charset="utf-8"><style>body{{margin:0;padding:28px;background:{page_color}}}'
            t'.md-form{{background:var(--md-sys-color-surface)}}</style>'
            t'</head><body>{body}</body></html>'
        )
    )


def _shots() -> dict[str, str]:
    signup_errors = SignupForm.validate(
        _SIGNUP_MISTAKES, submit_url='/signup', framework='material', self_contained=True
    )
    return {
        'signup-bootstrap': _page(
            SignupForm.render_form(submit_url='/signup', self_contained=True)
        ),
        'signup-material-errors': _page(signup_errors.render_with_errors()),
        'wizard-material-dark': _page(
            LayoutDemonstrationForm.render_form(
                submit_url='/layouts',
                framework='material',
                layout='wizard',
                self_contained=True,
            ),
            dark=True,
        ),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, document in _shots().items():
            page = browser.new_page(viewport={'width': 640, 'height': 400}, device_scale_factor=1.5)
            page.set_content(document)
            page.wait_for_load_state('load')
            page.screenshot(path=OUT / f'{name}.png', full_page=True)
            page.close()
            print(f'Wrote {OUT / name}.png')
        browser.close()


if __name__ == '__main__':
    main()
