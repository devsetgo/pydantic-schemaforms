"""Library output under a strict Content-Security-Policy: nothing is blocked.

The page is served with ``script-src``/``style-src`` allowing only the nonce, so
any inline handler, ``style`` attribute or tag without the nonce is a violation.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from playwright.sync_api import Page, expect

from examples.job_application_example import JobApplicationForm, _apply_options
from examples.shared_models import LayoutDemonstrationForm, WidgetGalleryForm

NONCE = 'csp0Test1Nonce2'
POLICY = (
    "default-src 'none'; img-src 'self' data:; font-src 'self' data:; "
    f"script-src 'nonce-{NONCE}'; style-src 'nonce-{NONCE}'; form-action 'self'"
)
URL = 'http://csp.test/'
_RECORDER = (
    'window.cspViolations = [];'
    'document.addEventListener("securitypolicyviolation", e => window.cspViolations.push('
    '`${e.violatedDirective}: ${(e.sample || e.blockedURI || "").slice(0, 80)}`));'
)
NONCES = {'script_nonce': NONCE, 'style_nonce': NONCE}


def _serve(page: Page, body: str) -> list[str]:
    document = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<script nonce="{NONCE}">{_RECORDER}</script></head><body>{body}</body></html>'
    )
    page.route(
        URL,
        lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            headers={'Content-Security-Policy': POLICY},
            body=document,
        ),
    )
    page.goto(URL)
    page.wait_for_load_state('load')
    return page.evaluate('window.cspViolations')


_RENDERS: dict[str, Callable[[str], str]] = {
    'gallery': lambda fw: WidgetGalleryForm.render_form(
        framework=fw, submit_url='/x', include_framework_assets=True, **NONCES
    ),
    'display': lambda fw: WidgetGalleryForm.render_display(
        {}, framework=fw, include_framework_assets=True, **NONCES
    ),
    'errors': lambda fw: WidgetGalleryForm.validate(
        {}, submit_url='/x', framework=fw, include_framework_assets=True, **NONCES
    ).render_with_errors(),
    'saved-step wizard': lambda fw: JobApplicationForm.validate_step(
        {}, draft=None, **{**_apply_options(fw, None), 'framework': fw}, **NONCES
    ).render(include_framework_assets=True),
    **{
        f'layout {layout}': (
            lambda fw, layout=layout: LayoutDemonstrationForm.render_form(
                framework=fw,
                submit_url='/x',
                layout=layout,
                include_framework_assets=True,
                **NONCES,
            )
        )
        for layout in ('vertical', 'tabbed', 'side-by-side', 'accordion', 'wizard')
    },
}


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
@pytest.mark.parametrize('name', sorted(_RENDERS))
def test_output_runs_under_a_strict_policy(page: Page, name: str, framework: str) -> None:
    errors: list[str] = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    violations = _serve(page, _RENDERS[name](framework))
    assert violations == []
    assert errors == []


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_tabs_and_accordions_still_switch_under_the_policy(page: Page, framework: str) -> None:
    _serve(
        page,
        LayoutDemonstrationForm.render_form(
            framework=framework, submit_url='/x', layout='tabbed', **NONCES
        ),
    )
    control = page.locator('[role="tab"]').nth(1)
    control.click()
    expect(page.locator(f'[id="{control.get_attribute("aria-controls")}"]')).to_be_visible()
    assert page.evaluate('window.cspViolations') == []


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_an_app_ui_style_still_applies_under_the_policy(page: Page, framework: str) -> None:
    violations = _serve(page, _RENDERS['gallery'](framework))
    field = page.locator('[name="field_options.styled_field"]')
    expect(field).to_have_css('font-weight', '600')
    assert violations == []
