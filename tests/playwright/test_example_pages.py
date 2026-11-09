"""
Every example page must load in a real browser without a JavaScript error,
and pass axe-core with no serious or critical accessibility violation.

Inline scripts are built inside Python strings, where a stray Python-style
`# comment` is a syntax error that silently disables the whole script (this
happened to the Material theme script and to the file-input preview). Only a
browser catches that, so this loads every example GET route under Bootstrap
and Material.

axe-core is vendored for tests only (tests/playwright/vendor/axe.min.js,
MPL-2.0, not shipped in the package). To update it, download axe.min.js from
the axe-core npm tarball and update _AXE_VERSION and _AXE_SHA256 below.

Requires: playwright install chromium
Run:      pytest tests/playwright/test_example_pages.py -v
"""

import hashlib
import socket
import threading
import time
import re
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Page, expect

import examples.main

TIMEOUT = 3_000  # ms — generous for CI latency

_AXE_PATH = Path(__file__).parent / 'vendor' / 'axe.min.js'
_AXE_VERSION = '4.14.0'
_AXE_SHA256 = '20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878'
_BLOCKING_IMPACTS = ('serious', 'critical')
# Named explicitly so docs/reference/accessibility.md's claim can't drift with axe's
# defaults (which leave out WCAG 2.2). axe maps these rules to Section 508
# and EN 301 549 as well.
_AXE_RULE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def examples_server_url():
    """Start the example app (examples/main.py) on a free port."""
    port = _free_port()
    config = uvicorn.Config(examples.main.app, host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError('Test server did not start within 10 seconds')
        time.sleep(0.05)

    yield f'http://127.0.0.1:{port}'

    server.should_exit = True
    thread.join(timeout=5)


def _html_pages() -> list[str]:
    paths = examples.main.app.openapi()['paths']
    return sorted(
        path
        for path, ops in paths.items()
        if 'get' in ops
        and '{' not in path
        and not path.startswith(('/api/', '/vendor/'))
        and not path.endswith(('.csv', '.js', '.css'))
    )


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _html_pages())
def test_example_page_has_no_javascript_errors(
    page: Page, examples_server_url: str, path: str, style: str
) -> None:
    errors: list[str] = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'{examples_server_url}{path}?style={style}', wait_until='domcontentloaded')
    page.wait_for_timeout(200)
    assert errors == [], f'{path} ({style}): {errors}'


def _axe_source() -> str:
    data = _AXE_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == _AXE_SHA256, 'vendored axe.min.js changed'
    assert data.startswith(f'/*! axe v{_AXE_VERSION}'.encode())
    return data.decode()


def _blocking_violations(page: Page) -> list[str]:
    page.add_script_tag(content=_axe_source())
    results = page.evaluate(
        "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}, "
        "resultTypes: ['violations']})",
        _AXE_RULE_TAGS,
    )
    return [
        f'[{violation["impact"]}] {violation["id"]}: {violation["help"]} -> '
        + ', '.join(str(node['target']) for node in violation['nodes'][:5])
        for violation in results['violations']
        if violation['impact'] in _BLOCKING_IMPACTS
    ]


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _html_pages())
def test_example_page_has_no_serious_accessibility_violations(
    page: Page, examples_server_url: str, path: str, style: str
) -> None:
    page.goto(f'{examples_server_url}{path}?style={style}', wait_until='load')
    violations = _blocking_violations(page)
    assert violations == [], f'{path} ({style}):\n' + '\n'.join(violations)


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_validation_errors_have_no_serious_accessibility_violations(
    page: Page, examples_server_url: str, style: str
) -> None:
    # The error state (messages, aria-invalid, the error summary) only exists
    # after a failed submit. form.submit() skips the browser's own constraint
    # checks so the server's errors are what gets rendered.
    page.goto(f'{examples_server_url}/validation?style={style}', wait_until='load')
    with page.expect_navigation(wait_until='load'):
        page.evaluate("document.querySelector('form').submit()")
    expect(page.locator('[aria-invalid="true"]').first).to_be_attached(timeout=TIMEOUT)
    violations = _blocking_violations(page)
    assert violations == [], f'/validation errors ({style}):\n' + '\n'.join(violations)


def test_file_input_preview_lists_the_chosen_file(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/gallery')
    page.get_by_role('tab', name='Files & Specialized').click()
    page.set_input_files(
        '[name="files_specialized.file_input"]',
        files=[{'name': '<b>report</b>.txt', 'mimeType': 'text/plain', 'buffer': b'hello'}],
    )
    preview = page.locator('[id="files_specialized.file_input_preview"]')
    # The name is shown as text, never parsed as markup.
    expect(preview).to_contain_text('<b>report</b>.txt', timeout=TIMEOUT)
    expect(preview.locator('b')).to_have_count(0)


def test_material_placeholder_select_keeps_its_label_floated(
    page: Page, examples_server_url: str
) -> None:
    page.goto(f'{examples_server_url}/gallery?style=material')
    page.locator('.tab-button', has_text='Selection Inputs').click()
    label = page.locator('label[for="selection_inputs.select_placeholder"]')
    # A floated label is body-small, sitting in the outline's notch.
    expect(label).to_have_css('font-size', '12px', timeout=TIMEOUT)


_GROUP_CONTROLS = {
    'tabbed': '[role="tab"][aria-controls^="tab-"]',
    'accordion': 'button[aria-controls^="accordion-"]',
}


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('layout', ['tabbed', 'accordion'])
def test_grouped_forms_on_one_page_switch_independently(
    page: Page, examples_server_url: str, layout: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/layouts/two-forms?style={style}&layout={layout}')
    first, second = page.locator('form').nth(0), page.locator('form').nth(1)

    def panel(form, index: int):
        control = form.locator(_GROUP_CONTROLS[layout]).nth(index)
        return page.locator(f'[id="{control.get_attribute("aria-controls")}"]')

    second.locator(_GROUP_CONTROLS[layout]).nth(1).click()

    expect(panel(second, 1)).to_be_visible(timeout=TIMEOUT)
    expect(panel(first, 0)).to_be_visible(timeout=TIMEOUT)
    expect(panel(first, 1)).to_be_hidden(timeout=TIMEOUT)


def test_material_pages_load_no_bootstrap(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/gallery?style=material')
    expect(page.locator('form.md-form')).to_be_visible(timeout=TIMEOUT)
    expect(page.locator('link[href*="bootstrap"]')).to_have_count(0)
    expect(page.locator('script[src*="bootstrap"]')).to_have_count(0)


@pytest.mark.parametrize('variant', ['outlined', 'filled'])
@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_material_variants_and_schemes_pass_axe(
    page: Page, examples_server_url: str, variant: str, theme: str
) -> None:
    page.add_init_script(f"localStorage.setItem('sf-theme', '{theme}')")
    page.goto(f'{examples_server_url}/gallery?style=material&variant={variant}')
    expect(page.locator('form.md-form')).to_be_visible(timeout=TIMEOUT)
    assert _blocking_violations(page) == []


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_model_list_add_remove_and_title(page: Page, examples_server_url: str, style: str) -> None:
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(f'{examples_server_url}/pets?style={style}&demo=true')
    items = page.locator('.model-list-item')
    expect(items.first).to_be_visible(timeout=TIMEOUT)
    before = items.count()
    # The demo list starts at its max_items, so remove before adding.
    items.first.locator('.remove-item-btn').click()
    expect(items).to_have_count(before - 1, timeout=TIMEOUT)
    page.locator('.add-item-btn').first.click()
    expect(items).to_have_count(before, timeout=TIMEOUT)
    expect(items.last.locator('input:visible').first).to_be_visible(timeout=TIMEOUT)


def test_material_model_list_item_collapses(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/pets?style=material&demo=true')
    item = page.locator('.model-list-item').first
    body = item.locator('.md-model-item__body')
    summary = item.locator('summary')
    was_open = body.is_visible()
    summary.click()
    if was_open:
        expect(body).to_be_hidden(timeout=TIMEOUT)
    else:
        expect(body).to_be_visible(timeout=TIMEOUT)


def test_star_rating_works_from_the_keyboard(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/gallery?style=material')
    page.locator('.tab-button', has_text='Numeric').click()
    star = page.locator('.star-rating-input [role="radio"][tabindex="0"]').first
    star.focus()
    value = star.get_attribute('data-rating')
    star.press('ArrowRight')
    expected = str(min(int(value) + 1, 5))
    expect(
        page.locator(f'.star-rating-input [role="radio"][data-rating="{expected}"]').first
    ).to_have_attribute('aria-checked', 'true', timeout=TIMEOUT)


@pytest.mark.parametrize('variant', ['outlined', 'filled'])
def test_material_floated_label_clears_the_leading_icon(
    page: Page, examples_server_url: str, variant: str
) -> None:
    page.goto(f'{examples_server_url}/layouts?style=material&layout=vertical&variant={variant}')
    field = page.locator('.md-field--leading-icon', has=page.locator('input:not([value=""])')).first
    expect(field).to_be_visible(timeout=TIMEOUT)
    label = field.locator('.md-floating-label').bounding_box()
    icon = field.locator('.md-field__leading').bounding_box()
    overlaps_x = label['x'] < icon['x'] + icon['width'] and icon['x'] < label['x'] + label['width']
    overlaps_y = (
        label['y'] < icon['y'] + icon['height'] and icon['y'] < label['y'] + label['height']
    )
    assert not (overlaps_x and overlaps_y), (label, icon)


def test_material_success_page_shows_json_left_aligned(
    page: Page, examples_server_url: str
) -> None:
    page.goto(f'{examples_server_url}/login?style=material&demo=true')
    page.locator('form.md-form [type="submit"]').first.click()
    code = page.locator('pre code').first
    expect(code).to_be_visible(timeout=TIMEOUT)
    expect(code).to_have_css('text-align', 'start')


def test_material_layout_switcher_has_gaps_and_no_page_overflow(
    page: Page, examples_server_url: str
) -> None:
    page.set_viewport_size({'width': 1072, 'height': 800})
    page.goto(f'{examples_server_url}/layouts?style=material&layout=tabbed')
    links = page.locator('.layout-switcher a')
    expect(links.first).to_be_visible(timeout=TIMEOUT)
    first, second = links.nth(0).bounding_box(), links.nth(1).bounding_box()
    assert second['x'] - (first['x'] + first['width']) >= 8
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')


def test_material_csv_import_stays_material_after_load(
    page: Page, examples_server_url: str, tmp_path
) -> None:
    csv_file = tmp_path / 'employees.csv'
    csv_file.write_text(
        'name,email,department,project_team_name,project_description\n'
        'Ada,not-an-email,engineering,Platform,Core\n'
    )
    page.goto(f'{examples_server_url}/employees/import?style=material')
    page.locator('input[type="file"]').set_input_files(csv_file)
    page.get_by_role('button', name='Load CSV').click()
    expect(page.locator('form.md-form')).to_be_visible(timeout=TIMEOUT)
    expect(page.locator('.datatable-row-error').first).to_be_visible(timeout=TIMEOUT)
    expect(page.locator('link[href*="bootstrap"]')).to_have_count(0)
    screenshots = Path(__file__).parent / 'screenshots'
    screenshots.mkdir(exist_ok=True)
    page.screenshot(path=screenshots / 'data-table-errors.png', full_page=True)


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _html_pages())
def test_example_page_passes_axe_in_dark(
    page: Page, examples_server_url: str, path: str, style: str
) -> None:
    page.add_init_script("localStorage.setItem('sf-theme', 'dark')")
    page.goto(f'{examples_server_url}{path}?style={style}', wait_until='load')
    violations = _blocking_violations(page)
    assert violations == [], f'{path} ({style}, dark):\n' + '\n'.join(violations)


@pytest.mark.parametrize(
    ('style', 'attribute'), [('bootstrap', 'data-bs-theme'), ('material', 'data-md-theme')]
)
def test_dark_toggle_switches_and_persists(
    page: Page, examples_server_url: str, style: str, attribute: str
) -> None:
    page.goto(f'{examples_server_url}/login?style={style}', wait_until='load')
    toggle = page.locator('#sf-theme-toggle')
    expect(toggle).to_have_text('Dark', timeout=TIMEOUT)
    toggle.click()
    expect(page.locator('html')).to_have_attribute(attribute, 'dark')
    expect(toggle).to_have_text('Light')
    page.reload(wait_until='load')
    expect(page.locator('html')).to_have_attribute(attribute, 'dark')
    toggle.click()
    expect(page.locator('html')).to_have_attribute(attribute, 'light')


def test_material_tokens_can_be_overridden_for_a_custom_scheme(
    page: Page, examples_server_url: str
) -> None:
    page.goto(f'{examples_server_url}/login?style=material', wait_until='load')
    page.add_style_tag(content='form.md-form { --md-sys-color-primary: rgb(0, 99, 155); }')
    expect(page.locator('form.md-form [type="submit"]').first).to_have_css(
        'background-color', 'rgb(0, 99, 155)', timeout=TIMEOUT
    )


def test_validation_reports_the_same_errors_in_both_styles(
    page: Page, examples_server_url: str
) -> None:
    summaries = {}
    for style, selector in (
        ('bootstrap', '.alert-danger li'),
        ('material', '.md-error-summary li'),
    ):
        page.goto(f'{examples_server_url}/validation?style={style}', wait_until='load')
        page.locator('form [type="submit"]').first.click()
        items = page.locator(selector)
        expect(items.first).to_be_visible(timeout=TIMEOUT)
        summaries[style] = items.all_inner_texts()
    assert summaries['material'] == summaries['bootstrap']
    expect(page.locator('.md-error-text').first).to_be_visible()
    screenshots = Path(__file__).parent / 'screenshots'
    screenshots.mkdir(exist_ok=True)
    page.screenshot(path=screenshots / 'validation-errors.png', full_page=True)


def test_site_header_style_and_variant_apply_across_pages(
    page: Page, examples_server_url: str
) -> None:
    page.goto(f'{examples_server_url}/login', wait_until='load')
    expect(page.locator('[data-sf-variant]')).to_have_count(0)
    page.locator('[data-sf-style="material"]').click()
    expect(page.locator('form.md-form')).to_be_visible(timeout=TIMEOUT)

    page.locator('[data-sf-variant="filled"]').click()
    expect(page.locator('form.md-form')).to_have_class(re.compile('md-form--filled'))

    page.goto(f'{examples_server_url}/contact', wait_until='load')
    expect(page.locator('form.md-form--filled')).to_be_visible(timeout=TIMEOUT)
    expect(page.locator('[data-sf-variant="filled"]')).to_have_attribute('aria-current', 'true')

    page.locator('[data-sf-style="bootstrap"]').click()
    expect(page.locator('form:not(.md-form)').first).to_be_visible(timeout=TIMEOUT)
    page.goto(f'{examples_server_url}/feedback', wait_until='load')
    expect(page.locator('form:not(.md-form)').first).to_be_visible(timeout=TIMEOUT)


def test_material_pages_show_the_site_header(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/login?style=material', wait_until='load')
    expect(page.locator('.top-resource-bar')).to_contain_text('Documentation', timeout=TIMEOUT)
    expect(page.locator('.site-brand-shell')).to_be_visible()


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_show_when_follows_the_controlling_field(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/gallery?style={style}')
    page.get_by_role('tab', name='Field Options').click()
    method = page.locator('[name="field_options.contact_method"]')
    phone = page.locator('[name="field_options.contact_phone"]')

    expect(phone).to_be_visible()
    method.select_option('email')
    expect(phone).to_be_hidden()
    expect(phone).to_be_disabled()
    method.select_option('phone')
    expect(phone).to_be_visible()
    expect(phone).to_be_enabled()
    expect(phone).to_have_value('555-0100')

    page.locator('[name="field_options.wants_updates"]').uncheck()
    expect(page.locator('[name="field_options.update_topics"]')).to_be_hidden()
    # Depends on the field just hidden, so it follows it.
    expect(page.locator('[name="field_options.update_note"]')).to_be_hidden()


def test_show_when_inside_a_new_model_list_item(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/validation')
    block = page.locator('[data-field-name="items"]').first
    block.locator('.add-item-btn').click()
    items = block.locator('[name$=".is_gift"]')
    last = items.count() - 1
    name = items.nth(last).get_attribute('name')
    note = block.locator(f'[name="{name.replace("is_gift", "gift_note")}"]')

    expect(note).to_be_hidden()
    items.nth(last).check()
    expect(note).to_be_visible()
    if last > 0:
        expect(block.locator('[name$=".gift_note"]').first).to_be_hidden()


@pytest.mark.parametrize('style', ['bootstrap', 'material', 'none'])
def test_ui_cols_share_a_row_and_stack_when_narrow(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.set_viewport_size({'width': 1100, 'height': 800})
    page.goto(f'{examples_server_url}/layouts/field-groups?style={style}')
    first = page.locator('[name="first_name"]')
    last = page.locator('[name="last_name"]')

    assert first.bounding_box()['y'] == last.bounding_box()['y']
    assert first.bounding_box()['x'] < last.bounding_box()['x']

    page.set_viewport_size({'width': 500, 'height': 800})
    assert first.bounding_box()['y'] < last.bounding_box()['y']


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_group_show_when_hides_the_whole_group(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/layouts/field-groups?style={style}')
    company = page.locator('[name="company"]')

    expect(company).to_be_visible()
    expect(page.get_by_text('Invoice', exact=True)).to_be_visible()
    page.locator('[name="wants_invoice"]').uncheck()
    expect(company).to_be_hidden()
    expect(company).to_be_disabled()
    expect(page.get_by_text('Invoice', exact=True)).to_be_hidden()


@pytest.mark.parametrize('javascript', [True, False])
@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_save_steps_wizard_walks_through(
    browser, examples_server_url: str, style: str, javascript: bool
) -> None:
    context = browser.new_context(java_script_enabled=javascript)
    page = context.new_page()
    try:
        page.goto(f'{examples_server_url}/layouts/save-steps?style={style}', wait_until='load')
        page.fill('[name="applicant.full_name"]', 'Robin Example')
        page.fill('[name="applicant.postcode"]', 'SW9 9ZZ')
        with page.expect_navigation(wait_until='load'):
            if javascript:
                page.click('[data-wizard-next]')
            else:
                # The theme's script stops Enter submitting a form. Without it, Enter
                # uses the first submit button, the hidden Next, not a header jump.
                page.press('[name="applicant.postcode"]', 'Enter')
        expect(page.locator('[name="documents.resume"]')).to_be_attached(timeout=TIMEOUT)
        if javascript:
            assert _blocking_violations(page) == []

        page.set_input_files(
            '[name="documents.resume"]',
            files=[{'name': 'cv.txt', 'mimeType': 'text/plain', 'buffer': b'hello'}],
        )
        with page.expect_navigation(wait_until='load'):
            page.click('[data-wizard-next]')
        expect(page.locator('[name="availability.city"]')).to_have_value('London', timeout=TIMEOUT)

        with page.expect_navigation(wait_until='load'):
            page.click('[data-wizard-back]')
        expect(page.locator('[name="documents.resume"]')).to_be_attached(timeout=TIMEOUT)
        with page.expect_navigation(wait_until='load'):
            page.click('[data-wizard-next]')

        page.fill('[name="availability.start_date"]', '2027-03-01')
        page.fill('[name="availability.end_date"]', '2027-02-01')
        with page.expect_navigation(wait_until='load'):
            page.click('[data-wizard-next]')
        # The review step shows the saved answers, the file by its name.
        review = page.locator('.sf-review')
        expect(review).to_contain_text('cv.txt', timeout=TIMEOUT)
        expect(review).to_contain_text('London')
        with page.expect_navigation(wait_until='load'):
            page.click('form [type="submit"]:not([name])')
        expect(page.get_by_text('must be after the earliest start date')).to_be_visible(
            timeout=TIMEOUT
        )
        if javascript:
            assert _blocking_violations(page) == []

        with page.expect_navigation(wait_until='load'):
            page.click('.sf-review [value="goto:2"]')
        page.fill('[name="availability.end_date"]', '2027-09-01')
        with page.expect_navigation(wait_until='load'):
            page.click('[data-wizard-next]')
        with page.expect_navigation(wait_until='load'):
            page.click('form [type="submit"]:not([name])')
        expect(page.get_by_text('Application Saved and Submitted')).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text('cv.txt', exact=True)).to_be_visible(timeout=TIMEOUT)
    finally:
        context.close()


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_review_step_shows_the_live_answers(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(
        f'{examples_server_url}/layouts?layout=wizard&review=true&linear=false&style={style}',
        wait_until='load',
    )
    review = page.locator('[data-wizard-review]')
    page.locator('.wizard-progress-item', has_text='Review').click()
    expect(review).to_be_visible(timeout=TIMEOUT)
    expect(review.locator('[data-review-slot="personal_info.first_name"]')).to_have_text('Alex')
    rows = review.locator('[data-review-list="task_list.tasks"] > tr:not([hidden])')
    expect(rows).to_have_count(2, timeout=TIMEOUT)
    expect(rows.first).to_contain_text('Complete project setup')
    assert _blocking_violations(page) == []

    # Edit goes back to the step. The change shows as old -> new, as text, never markup.
    review.locator('[data-wizard-edit="0"]').click()
    page.fill('[name="personal_info.first_name"]', '<b>Robin</b>')
    page.locator('.wizard-progress-item', has_text='Review').click()
    slot = review.locator('[data-review-slot="personal_info.first_name"]')
    expect(slot.locator('[aria-hidden="true"]')).to_have_text(
        'Alex → <b>Robin</b>', timeout=TIMEOUT
    )
    expect(slot.locator('strong')).to_have_count(2)
    expect(slot.locator('.sf-sr-only')).to_have_text('Changed from Alex to <b>Robin</b>')
    expect(review.locator('b')).to_have_count(0)
    unchanged = review.locator('[data-review-slot="personal_info.last_name"]')
    expect(unchanged).to_have_text('Johnson')
    assert _blocking_violations(page) == []

    # A list item added in the browser is tagged Added; one removed is shown as Removed.
    review.locator('[data-wizard-edit="3"]').click()
    page.locator('.add-item-btn').first.click()
    page.fill('[name="task_list.tasks[2].task_name"]', 'Third task')
    page.locator('.wizard-progress-item', has_text='Review').click()
    expect(rows).to_have_count(3, timeout=TIMEOUT)
    expect(rows.nth(2)).to_contain_text('Added: Third task')

    review.locator('[data-wizard-edit="3"]').click()
    page.locator('.model-list-item .remove-item-btn').last.click()
    page.locator('.model-list-item .remove-item-btn').last.click()
    page.locator('.wizard-progress-item', has_text='Review').click()
    expect(rows).to_have_count(2, timeout=TIMEOUT)
    expect(rows.nth(1)).to_contain_text('Removed: Write documentation')


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_confirm_dialog_asks_before_submitting(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/confirm?style={style}', wait_until='load')
    dialog = page.locator('dialog[data-sf-confirm]')
    submit = page.locator('form [type="submit"]:not([name])')

    submit.click()
    expect(dialog).to_be_visible(timeout=TIMEOUT)
    expect(dialog.get_by_role('heading')).to_have_text('Close your account?')
    expect(dialog.locator('[data-sf-confirm-cancel]')).to_be_focused()
    assert _blocking_violations(page) == []

    dialog.locator('[data-sf-confirm-cancel]').click()
    expect(dialog).to_be_hidden(timeout=TIMEOUT)
    submit.click()
    expect(dialog).to_be_visible(timeout=TIMEOUT)
    page.keyboard.press('Escape')
    expect(dialog).to_be_hidden(timeout=TIMEOUT)
    assert '/confirm' in page.url

    # Confirm submits; the unticked box comes back as the server's error.
    submit.click()
    with page.expect_navigation(wait_until='load'):
        dialog.locator('[data-sf-confirm-ok]').click()
    expect(page.get_by_text('Tick the box to confirm you understand', exact=True)).to_be_visible(
        timeout=TIMEOUT
    )

    page.check('[name="understood"]')
    page.locator('form [type="submit"]:not([name])').click()
    with page.expect_navigation(wait_until='load'):
        page.locator('dialog[data-sf-confirm] [data-sf-confirm-ok]').click()
    expect(page.get_by_text('Account Closed')).to_be_visible(timeout=TIMEOUT)


def test_confirm_without_javascript_submits_directly(browser, examples_server_url: str) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(f'{examples_server_url}/confirm', wait_until='load')
        page.check('[name="understood"]')
        with page.expect_navigation(wait_until='load'):
            page.click('form [type="submit"]:not([name])')
        expect(page.get_by_text('Account Closed')).to_be_visible(timeout=TIMEOUT)
    finally:
        context.close()


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_progress_counts_required_fields_as_they_fill(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/layouts?layout=tabbed&count=true&style={style}')
    count = page.locator('.sf-progress__count')
    expect(count).to_have_text('6 of 6 complete', timeout=TIMEOUT)
    page.fill('[name="personal_info.first_name"]', '')
    expect(count).to_have_text('5 of 6 complete', timeout=TIMEOUT)
    assert _blocking_violations(page) == []

    # A wizard ticks its step header instead; a step with nothing required ticks once passed.
    page.goto(f'{examples_server_url}/layouts?layout=wizard&count=true&linear=false&style={style}')
    numbers = page.locator('.wizard-progress-number')
    expect(numbers).to_have_text(['✓', '✓', '3', '✓'], timeout=TIMEOUT)
    page.fill('[name="personal_info.first_name"]', '')
    expect(numbers.first).to_have_text('1', timeout=TIMEOUT)
    page.fill('[name="personal_info.first_name"]', 'Robin')
    for _ in range(3):
        page.click('[data-wizard-next]')
    expect(numbers).to_have_text(['✓', '✓', '✓', '✓'], timeout=TIMEOUT)
    expect(page.locator('[data-step-done]:not([hidden])')).to_have_count(4)
    assert _blocking_violations(page) == []


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_autosave_restores_a_draft_after_a_reload(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(f'{examples_server_url}/layouts?layout=tabbed&autosave=true&style={style}')
    page.evaluate('localStorage.clear()')
    notice = page.locator('[data-sf-draft-notice]')
    expect(notice).to_be_hidden()
    page.fill('[name="personal_info.first_name"]', 'Robin')
    page.get_by_role('tab', name='Task List').click()
    page.locator('.add-item-btn').first.click()
    page.fill('[name="task_list.tasks[2].task_name"]', 'Third task')
    page.wait_for_function('Object.keys(localStorage).length === 1')

    page.reload(wait_until='load')
    expect(notice).to_be_visible(timeout=TIMEOUT)
    expect(page.locator('[name="personal_info.first_name"]')).to_have_value('Robin')
    expect(page.locator('[name="task_list.tasks[2].task_name"]')).to_have_value('Third task')
    assert _blocking_violations(page) == []

    # Discard goes back to the server's values.
    with page.expect_navigation(wait_until='load'):
        notice.locator('[data-sf-draft-discard]').click()
    expect(page.locator('[name="personal_info.first_name"]')).to_have_value('Alex')
    expect(notice).to_be_hidden()

    # A submit that goes ahead clears the draft.
    page.fill('[name="personal_info.first_name"]', 'Sam')
    page.wait_for_function('Object.keys(localStorage).length === 1')
    with page.expect_navigation(wait_until='load'):
        page.locator('form [type="submit"]:not([name])').first.click()
    assert page.evaluate('Object.keys(localStorage).length') == 0


def test_warn_unsaved_asks_only_when_something_changed(
    page: Page, examples_server_url: str
) -> None:
    asked: list[str] = []
    page.on('dialog', lambda dialog: (asked.append(dialog.type), dialog.accept()))
    url = f'{examples_server_url}/layouts?layout=tabbed&warn=true'
    page.goto(url)
    page.click('[name="personal_info.first_name"]')
    page.goto(f'{examples_server_url}/')
    assert asked == []

    page.goto(url)
    page.click('[name="personal_info.first_name"]')
    page.keyboard.type('X')
    page.goto(f'{examples_server_url}/')
    assert asked == ['beforeunload']


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_a_wizard_skips_a_step_that_does_not_apply(
    page: Page, examples_server_url: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/wizards/car-care?style={style}', wait_until='load')
    titles = page.locator('.wizard-progress li:not([hidden]) .wizard-progress-title')
    active = page.locator('.wizard-step.active .wizard-step-title')
    expect(titles).to_have_text(
        ['Your car', 'Services', 'Date and time', 'Contact', 'Review'], timeout=TIMEOUT
    )

    page.fill('[name="make"]', 'Volvo V60')
    page.fill('[name="plate"]', 'AB 123')
    for _ in range(3):
        page.click('[data-wizard-next]')
    expect(active).to_have_text('Contact')

    page.click('[data-wizard-back]')
    page.check('input[name="while_we_work"][value="loaner"]')
    expect(titles).to_have_text(
        ['Your car', 'Services', 'Date and time', 'Loaner car', 'Contact', 'Review'],
        timeout=TIMEOUT,
    )
    page.click('[data-wizard-next]')
    expect(active).to_have_text('Loaner car')
    assert _blocking_violations(page) == []

    page.click('[data-wizard-back]')
    page.check('input[name="while_we_work"][value="drop_off"]')
    expect(titles).to_have_text(
        ['Your car', 'Services', 'Date and time', 'Contact', 'Review'], timeout=TIMEOUT
    )


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_an_added_list_item_starts_with_its_defaults(
    page: Page, examples_server_url: str, style: str
) -> None:
    # A new item used to be a blanked clone of an existing one, leaving a
    # select with no option chosen.
    page.goto(f'{examples_server_url}/wizards/team-onboarding?style={style}')
    page.fill('[name="workspace.name"]', 'Acme')
    page.fill('[name="workspace.address"]', 'acme-co')
    page.click('[data-wizard-next]')
    page.fill('[name="invites[0].email"]', 'sam@example.com')
    page.select_option('[name="invites[0].role"]', 'admin')
    page.locator('.add-item-btn:visible').first.click()
    expect(page.locator('[name="invites[1].role"]')).to_have_value('member', timeout=TIMEOUT)
    expect(page.locator('[name="invites[1].email"]')).to_have_value('')
    expect(page.locator('[name="invites[0].role"]')).to_have_value('admin')
