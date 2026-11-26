"""The one-time code input in a browser: boxes, typing, pasting and the submitted value."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from pydantic_schemaforms import Field, FormModel


class CodeForm(FormModel):
    code: str = Field(..., title='Verification code', ui_element='otp')
    backup: str = Field(
        'AB12', title='Backup code', ui_element='otp', ui_options={'length': 4, 'numeric': False}
    )


def _open(page: Page, framework: str = 'bootstrap', javascript: bool = True) -> None:
    page.set_content(CodeForm.render_form(submit_url='/c', framework=framework))
    if javascript:
        expect(page.locator('.sf-otp')).to_have_count(2)


def _boxes(page: Page):
    return page.locator('.sf-otp').first.locator('input')


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_one_box_per_digit_replaces_the_named_input(page: Page, framework: str):
    _open(page, framework)
    expect(_boxes(page)).to_have_count(6)
    expect(page.locator('input[name="code"]')).to_be_hidden()
    expect(page.locator('label', has_text='Verification code')).to_have_attribute(
        'for', 'code-digit-1'
    )
    expect(_boxes(page).first).to_have_attribute('autocomplete', 'one-time-code')
    expect(_boxes(page).nth(2)).to_have_attribute('aria-label', 'Character 3 of 6')


def test_typing_advances_and_fills_the_named_input(page: Page):
    _open(page)
    _boxes(page).first.click()
    page.keyboard.type('4x2')
    expect(page.locator('input[name="code"]')).to_have_value('42')
    expect(_boxes(page).nth(2)).to_be_focused()


def test_backspace_on_an_empty_box_clears_the_one_before(page: Page):
    _open(page)
    _boxes(page).first.click()
    page.keyboard.type('42')
    page.keyboard.press('Backspace')
    expect(page.locator('input[name="code"]')).to_have_value('4')
    expect(_boxes(page).nth(1)).to_be_focused()


def test_pasting_a_formatted_code_fills_every_box(page: Page):
    _open(page)
    _boxes(page).first.focus()
    page.keyboard.insert_text('123 456')
    expect(page.locator('input[name="code"]')).to_have_value('123456')
    expect(_boxes(page).nth(5)).to_have_value('6')
    expect(_boxes(page).nth(5)).to_be_focused()


def test_letters_code_keeps_its_starting_value(page: Page):
    _open(page)
    letters = page.locator('.sf-otp').nth(1).locator('input')
    expect(letters).to_have_count(4)
    expect(letters.nth(2)).to_have_value('1')
    expect(page.locator('input[name="backup"]')).to_have_value('AB12')


def test_without_javascript_it_is_one_text_box(browser):
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    _open(page, javascript=False)
    expect(page.locator('.sf-otp')).to_have_count(0)
    expect(page.locator('input[name="code"]')).to_be_visible()
    context.close()
