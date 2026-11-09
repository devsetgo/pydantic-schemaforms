"""A wizard skips a step its rule hides (#327)."""

import re
from typing import Literal

from pydantic_schemaforms import Field, FormModel, render_form_html


class Visit(FormModel):
    make: str = Field(title='Make', ui_group='Your car')
    choice: Literal['wait', 'loaner'] = Field('wait', title='While we work', ui_group='Service')
    licence: str = Field(
        '',
        title='Licence',
        ui_group='Loaner car',
        ui_group_show_when={'field': 'choice', 'equals': 'loaner'},
        ui_show_when={'field': 'choice', 'equals': 'loaner', 'required': True},
    )
    name: str = Field(title='Name', ui_group='Contact')


class Loaner(FormModel):
    licence: str = Field(title='Licence')


class Nested(FormModel):
    choice: Literal['wait', 'loaner'] = Field('wait', title='While we work', ui_group='Service')
    loaner: Loaner | None = Field(
        None, title='Loaner car', ui_show_when={'field': 'choice', 'equals': 'loaner'}
    )
    name: str = Field('', title='Name', ui_group='Contact')


SAVE = {'submit_url': '/v', 'layout': 'wizard', 'wizard_options': {'save_steps': True}}


def _header(page: str) -> list[tuple[bool, str, str]]:
    """(shown, number, title) for each header item."""

    items = re.findall(
        r'<li( hidden)?><button[^>]*>\s*<span class="wizard-progress-number">([^<]*)</span>\s*'
        r'<span class="wizard-progress-title">([^<]*)</span>',
        page,
    )
    return [(not hidden, number, title) for hidden, number, title in items]


def _step(step: int, draft: object = None, action: str | None = None, **fields: str):
    form = [('_sf_wizard_step', str(step))]
    if action:
        form.append(('_sf_wizard', action))
    form += list(fields.items())
    return Visit.validate_step(form, draft=draft, **SAVE)


def test_a_hidden_step_leaves_the_header_and_the_numbers_close_up() -> None:
    page = render_form_html(Visit, submit_url='/v', layout='wizard')
    header = _header(page)
    assert [title for visible, _n, title in header if not visible] == ['Loaner car']
    assert [(number, title) for visible, number, title in header if visible] == [
        ('1', 'Your car'),
        ('2', 'Service'),
        ('3', 'Contact'),
    ]
    shown = render_form_html(
        Visit, form_data={'choice': 'loaner'}, submit_url='/v', layout='wizard'
    )
    assert [number for visible, number, _title in _header(shown) if visible] == ['1', '2', '3', '4']


def test_a_sub_form_with_its_own_rule_is_skipped_too() -> None:
    page = render_form_html(Nested, submit_url='/n', layout='wizard')
    assert [title for visible, _n, title in _header(page) if not visible] == ['Loaner car']


def test_save_steps_next_and_back_jump_over_the_hidden_step() -> None:
    first = _step(0, make='Volvo')
    second = _step(1, first.draft, choice='wait')
    assert second.step == 3
    page = second.render()
    assert 'name="name"' in page
    assert _header(page)[2][0] is False
    assert _step(3, second.draft, 'back', name='Robin').step == 1


def test_a_step_that_hides_and_shows_again_before_submit() -> None:
    first = _step(0, make='Volvo')
    loaner = _step(1, first.draft, choice='loaner')
    assert loaner.step == 2
    back = _step(2, loaner.draft, 'back', licence='')
    switched = _step(1, back.draft, choice='wait')
    assert switched.step == 3
    again = _step(3, switched.draft, 'back', name='Robin')
    shown = _step(1, again.draft, choice='loaner')
    assert shown.step == 2
    missing = _step(2, shown.draft, licence='')
    assert not missing.is_valid and 'licence' in missing.errors
    filled = _step(2, shown.draft, licence='D123')
    done = _step(3, filled.draft, name='Robin')
    assert done.is_complete
    assert done.data['licence'] == 'D123'


def test_the_last_step_that_applies_submits() -> None:
    first = _step(0, make='Volvo')
    second = _step(1, first.draft, choice='wait')
    # Contact is the last step either way; it carries the form's own submit button.
    assert re.search(r'<button[^>]*type="submit"(?![^>]*name=)', second.render())
    done = _step(3, second.draft, name='Robin')
    assert done.is_complete
    assert done.data['licence'] == ''


def test_a_jump_to_a_hidden_step_stays_put() -> None:
    first = _step(0, make='Volvo')
    second = _step(1, first.draft, choice='wait')
    assert _step(3, second.draft, 'goto:2', name='Robin').step == 3


def test_the_review_leaves_a_hidden_step_out() -> None:
    options = {**SAVE, 'wizard_options': {'save_steps': True, 'review_step': True}}
    form = [('_sf_wizard_step', '0'), ('make', 'Volvo')]
    first = Visit.validate_step(form, **options)
    second = Visit.validate_step(
        [('_sf_wizard_step', '1'), ('choice', 'wait')], draft=first.draft, **options
    )
    contact = Visit.validate_step(
        [('_sf_wizard_step', '3'), ('name', 'Robin')], draft=second.draft, **options
    )
    assert contact.step == 4
    review = contact.render()
    assert 'Loaner car</' not in review.split('sf-review', 1)[1]
