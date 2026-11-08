"""autosave=True and warn_unsaved=True: keep what's typed, warn before leaving (#243)."""

import re

import pytest

from pydantic_schemaforms import Field, FormModel, render_form_html


class Profile(FormModel):
    name: str = Field(title='Name')
    secret_note: str = Field('', title='Secret note', ui_autosave=False)


def _form_tag(page: str) -> str:
    match = re.search(r'<form[^>]*>', page)
    assert match
    return match.group(0)


def test_autosave_marks_the_form_and_adds_a_hidden_notice() -> None:
    page = render_form_html(Profile, submit_url='/p', autosave=True)
    assert 'data-sf-autosave="Profile"' in _form_tag(page)
    notice = re.search(r'<div[^>]*data-sf-draft-notice[^>]*>.*?</div>', page, re.DOTALL)
    assert notice and 'hidden' in notice.group(0) and 'role="status"' in notice.group(0)
    assert 'data-sf-draft-discard' in notice.group(0)
    assert page.count('<script data-schemaforms-autosave>') == 1


def test_the_autosave_script_comes_after_the_others() -> None:
    page = render_form_html(Profile, submit_url='/p', autosave=True, progress=True, confirm=True)
    script = page.index('<script data-schemaforms-autosave>')
    assert script > page.index('<script data-schemaforms-progress>')
    assert script > page.index('<script data-schemaforms-confirm>')


def test_warn_unsaved_alone_needs_no_notice() -> None:
    page = render_form_html(Profile, submit_url='/p', warn_unsaved=True)
    form = _form_tag(page)
    assert 'data-sf-warn-unsaved="true"' in form and 'data-sf-autosave' not in form
    assert not re.search(r'<div[^>]*data-sf-draft-notice', page)
    assert '<script data-schemaforms-autosave>' in page


def test_without_the_options_nothing_is_added() -> None:
    page = render_form_html(Profile, submit_url='/p')
    assert 'data-sf-autosave' not in page and 'data-sf-warn-unsaved' not in page
    assert 'data-schemaforms-autosave' not in page


@pytest.mark.parametrize(
    ('framework', 'alert', 'button'),
    [
        ('bootstrap', 'alert alert-info', 'btn btn-link btn-sm p-0 align-baseline alert-link'),
        ('material', 'md-banner md-banner--info', 'md-button md-button--text'),
        ('none', 'alert alert-info', ''),
    ],
)
def test_the_notice_uses_each_styles_alert(framework: str, alert: str, button: str) -> None:
    page = render_form_html(Profile, submit_url='/p', framework=framework, autosave=True)
    assert f'class="{alert} sf-draft-notice"' in page
    assert f'class="{button}" data-sf-draft-discard' in page


def test_ui_autosave_false_marks_the_field() -> None:
    page = render_form_html(Profile, submit_url='/p', autosave=True)
    secret = re.search(r'<[^>]*name="secret_note"[^>]*>', page)
    assert secret and 'data-sf-no-autosave' in secret.group(0)
    name = re.search(r'<input[^>]*name="name"[^>]*>', page)
    assert name and 'data-sf-no-autosave' not in name.group(0)


def test_the_captcha_answer_is_never_saved() -> None:
    class Guarded(FormModel):
        answer: str = Field(
            '', title='Answer', ui_element='captcha', ui_options={'secret_key': 'test-key'}
        )

    page = render_form_html(Guarded, submit_url='/g', autosave=True)
    answer = re.search(r'<input[^>]*name="answer"[^>]*>', page)
    assert answer and 'data-sf-no-autosave' in answer.group(0)


def test_a_failed_submit_keeps_both_options() -> None:
    result = Profile.validate([('name', '')], submit_url='/p', autosave=True, warn_unsaved=True)
    form = _form_tag(result.render_with_errors(errors={'name': 'Required'}))
    assert 'data-sf-autosave="Profile"' in form and 'data-sf-warn-unsaved' in form


@pytest.mark.parametrize('option', ['autosave', 'warn_unsaved'])
def test_the_options_take_true_or_false(option: str) -> None:
    with pytest.raises(ValueError, match=f'{option}= takes True or False'):
        render_form_html(Profile, submit_url='/p', **{option: 'yes'})
