"""
Playwright end-to-end tests for HTMX live field validation.

Requires: playwright install chromium
Run:      pytest tests/playwright/ -v
"""

import re

from playwright.sync_api import Page, expect

TIMEOUT = 3_000  # ms — generous for CI latency


# ---------------------------------------------------------------------------
# HTMX attribute contract
# ---------------------------------------------------------------------------


class TestHTMXAttributes:
    """The rendered HTML must carry the HTMX wiring the JS layer depends on."""

    def test_email_field_has_hx_post(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        assert page.locator('#email').get_attribute('hx-post') == '/validate/email'

    def test_email_field_triggers_on_blur(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        assert page.locator('#email').get_attribute('hx-trigger') == 'blur'

    def test_email_field_targets_feedback_div(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        assert page.locator('#email').get_attribute('hx-target') == '#email-feedback'

    def test_feedback_div_exists(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        expect(page.locator('#email-feedback')).to_be_attached()
        expect(page.locator('#name-feedback')).to_be_attached()


# ---------------------------------------------------------------------------
# Validation behaviour — email field
# ---------------------------------------------------------------------------


class TestEmailValidation:
    def test_invalid_email_applies_error_class(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#email').fill('not-an-email')
        page.locator('#email').press('Tab')
        expect(page.locator('#email')).to_have_attribute(
            'class', re.compile(r'is-invalid'), timeout=TIMEOUT
        )

    def test_valid_email_applies_success_class(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#email').fill('user@example.com')
        page.locator('#email').press('Tab')
        expect(page.locator('#email')).to_have_attribute(
            'class', re.compile(r'is-valid'), timeout=TIMEOUT
        )

    def test_invalid_email_shows_feedback_text(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#email').fill('clearly-wrong')
        page.locator('#email').press('Tab')
        expect(page.locator('#email-feedback')).to_contain_text('valid email', timeout=TIMEOUT)

    def test_valid_email_shows_success_feedback(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#email').fill('good@example.com')
        page.locator('#email').press('Tab')
        expect(page.locator('#email-feedback')).to_contain_text('Looks good', timeout=TIMEOUT)

    def test_fixing_invalid_to_valid_updates_class(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        email = page.locator('#email')
        email.fill('bad-email')
        email.press('Tab')
        expect(email).to_have_attribute('class', re.compile(r'is-invalid'), timeout=TIMEOUT)

        email.fill('fixed@example.com')
        email.press('Tab')
        expect(email).to_have_attribute('class', re.compile(r'is-valid'), timeout=TIMEOUT)


# ---------------------------------------------------------------------------
# Validation behaviour — name field
# ---------------------------------------------------------------------------


class TestNameValidation:
    def test_empty_name_applies_error_class(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#name').fill('')
        page.locator('#name').press('Tab')
        expect(page.locator('#name')).to_have_attribute(
            'class', re.compile(r'is-invalid'), timeout=TIMEOUT
        )

    def test_too_short_name_shows_feedback(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#name').fill('A')
        page.locator('#name').press('Tab')
        expect(page.locator('#name-feedback')).to_contain_text('2 characters', timeout=TIMEOUT)

    def test_valid_name_applies_success_class(self, page: Page, live_server_url: str) -> None:
        page.goto(live_server_url)
        page.locator('#name').fill('Alice')
        page.locator('#name').press('Tab')
        expect(page.locator('#name')).to_have_attribute(
            'class', re.compile(r'is-valid'), timeout=TIMEOUT
        )


# ---------------------------------------------------------------------------
# Multi-field independence
# ---------------------------------------------------------------------------


def test_fields_validate_independently(page: Page, live_server_url: str) -> None:
    """Invalid email must not affect the name field and vice versa."""
    page.goto(live_server_url)

    page.locator('#email').fill('bad-email')
    page.locator('#email').press('Tab')
    page.locator('#name').fill('Alice')
    page.locator('#name').press('Tab')

    expect(page.locator('#email')).to_have_attribute(
        'class', re.compile(r'is-invalid'), timeout=TIMEOUT
    )
    expect(page.locator('#name')).to_have_attribute(
        'class', re.compile(r'is-valid'), timeout=TIMEOUT
    )
