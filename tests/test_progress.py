"""progress=True: how many required fields are filled in (#296)."""

import re

import pytest

from pydantic_schemaforms import Field, FormModel, render_form_html


class Step(FormModel):
    name: str = Field(title='Name')
    note: str = Field('', title='Note')


class Grouped(FormModel):
    first: Step = Field(title='First')
    second: Step = Field(title='Second')
    third: Step = Field(title='Third')


TICKS = re.compile(r'class="form-wizard[^"]*wizard-progress-ticks')


def test_a_plain_form_gets_one_hidden_bar_at_the_top() -> None:
    page = render_form_html(Step, submit_url='/s', progress=True)
    assert page.count('class="sf-progress" data-sf-progress hidden') == 1
    assert page.index('data-sf-progress') < page.index('name="name"')
    assert page.count('<script data-schemaforms-progress>') == 1
    assert 'aria-live="polite"' in page


def test_the_bar_sits_under_the_error_summary() -> None:
    result = Step.validate([('name', '')], submit_url='/s', progress=True)
    page = result.render_with_errors(errors={'name': 'Required'})
    assert page.index('schemaforms-error-summary') < page.index('data-sf-progress')


@pytest.mark.parametrize('layout', ['tabbed', 'accordion', 'side-by-side'])
def test_grouped_layouts_get_the_bar(layout: str) -> None:
    page = render_form_html(Grouped, submit_url='/s', layout=layout, progress=True)
    assert 'data-sf-progress hidden' in page
    assert not TICKS.search(page)


def test_a_wizard_ticks_its_header_instead() -> None:
    page = render_form_html(Grouped, submit_url='/s', layout='wizard', progress=True)
    assert 'class="sf-progress"' not in page
    assert TICKS.search(page)
    assert page.count('data-step-done hidden') == 3
    assert '<script data-schemaforms-progress>' in page


def test_a_wizard_without_a_header_gets_the_bar() -> None:
    page = render_form_html(
        Grouped,
        submit_url='/s',
        layout='wizard',
        wizard_options={'show_progress': False},
        progress=True,
    )
    assert 'data-sf-progress hidden' in page
    assert not TICKS.search(page)


def test_save_steps_ticks_the_steps_already_saved() -> None:
    options = {
        'submit_url': '/s',
        'layout': 'wizard',
        'wizard_options': {'save_steps': True},
        'progress': True,
    }
    draft = Grouped.validate_step([('_sf_wizard_step', '0'), ('first.name', 'a')], **options).draft
    draft = Grouped.validate_step(
        [('_sf_wizard_step', '1'), ('second.name', 'b')], draft=draft, **options
    ).draft
    back = Grouped.validate_step(
        [('_sf_wizard_step', '2'), ('_sf_wizard', 'goto:0'), ('third.name', '')],
        draft=draft,
        **options,
    )
    page = back.render()
    numbers = re.findall(r'wizard-progress-number">([^<]+)', page)
    # On step 1 again: step 2 is saved, step 1 is the one being edited, step 3 isn't saved.
    assert numbers == ['1', '✓', '3']
    assert page.count('data-step-done>') == 1


def test_without_progress_nothing_changes() -> None:
    plain = render_form_html(Grouped, submit_url='/s', layout='wizard')
    assert 'data-step-done' not in plain and not TICKS.search(plain)
    assert 'data-schemaforms-progress' not in render_form_html(Step, submit_url='/s')


def test_progress_takes_true_or_false() -> None:
    with pytest.raises(ValueError, match='progress= takes True or False'):
        render_form_html(Step, submit_url='/s', progress='yes')
