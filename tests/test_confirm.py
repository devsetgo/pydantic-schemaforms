"""confirm=: a native <dialog> asks before the form submits (#295)."""

import re

import pytest

from pydantic_schemaforms import Field, FormModel, html, render_form_html


class CloseAccount(FormModel):
    reason: str = Field('', title='Reason')


class Step(FormModel):
    note: str = Field('', title='Note')


class Wizard(FormModel):
    first: Step = Field(title='First')
    second: Step = Field(title='Second')


TEXTS = {
    'title': 'Close <b>your</b> account?',
    'message': 'This cannot be undone.',
    'confirm_label': 'Close account',
    'cancel_label': 'Keep it',
}


def _dialog(page: str) -> str:
    match = re.search(r'<dialog.*?</dialog>', page, re.DOTALL)
    assert match
    return match.group(0)


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_the_dialog_holds_the_texts_escaped(framework: str) -> None:
    page = render_form_html(CloseAccount, submit_url='/close', framework=framework, confirm=TEXTS)
    dialog = _dialog(page)
    assert 'data-sf-confirm' in dialog
    assert 'aria-label="Close &lt;b&gt;your&lt;/b&gt; account?"' in dialog
    assert '<b>' not in dialog
    assert '<p class="sf-confirm__message">This cannot be undone.</p>' in dialog
    assert re.search(r'data-sf-confirm-cancel autofocus>Keep it</button>', dialog)
    assert re.search(r'data-sf-confirm-ok>Close account</button>', dialog)
    # The dialog sits in the form, after its submit button.
    assert page.index('</dialog>') < page.index('</form>')
    assert page.count('<script data-schemaforms-confirm>') == 1


def test_each_style_gets_its_own_button_classes() -> None:
    bootstrap = _dialog(render_form_html(CloseAccount, submit_url='/close', confirm=True))
    material = _dialog(
        render_form_html(CloseAccount, submit_url='/close', framework='material', confirm=True)
    )
    plain = _dialog(
        render_form_html(CloseAccount, submit_url='/close', framework='none', confirm=True)
    )
    assert 'class="btn btn-primary" data-sf-confirm-ok' in bootstrap
    assert 'class="md-button md-button--filled" data-sf-confirm-ok' in material
    assert 'class="" data-sf-confirm-ok' in plain


def test_true_uses_the_default_texts() -> None:
    dialog = _dialog(render_form_html(CloseAccount, submit_url='/close', confirm=True))
    assert 'Submit this form?' in dialog
    assert 'sf-confirm__message' not in dialog
    assert '>Submit</button>' in dialog and '>Cancel</button>' in dialog


def test_a_message_built_with_html_keeps_its_markup() -> None:
    message = html(t'Type <strong>{"<DELETE>"}</strong> to be sure.')
    dialog = _dialog(
        render_form_html(CloseAccount, submit_url='/close', confirm={'message': message})
    )
    assert 'Type <strong>&lt;DELETE&gt;</strong> to be sure.' in dialog
    plain = _dialog(
        render_form_html(CloseAccount, submit_url='/close', confirm={'message': '<i>x</i>'})
    )
    assert '&lt;i&gt;x&lt;/i&gt;' in plain


def test_without_confirm_there_is_no_dialog() -> None:
    page = render_form_html(CloseAccount, submit_url='/close')
    assert '<dialog' not in page and 'data-schemaforms-confirm' not in page


def test_no_submit_button_means_no_dialog() -> None:
    page = render_form_html(
        CloseAccount, submit_url='/close', confirm=True, include_submit_button=False
    )
    assert '<dialog' not in page


@pytest.mark.parametrize('value', [{'titel': 'x'}, {'title': 3}, 'yes', ['title']])
def test_bad_options_are_rejected(value: object) -> None:
    with pytest.raises(ValueError, match='confirm='):
        render_form_html(CloseAccount, submit_url='/close', confirm=value)


def test_a_review_step_already_asks() -> None:
    with pytest.raises(ValueError, match='use one of them'):
        render_form_html(
            Wizard,
            submit_url='/w',
            layout='wizard',
            wizard_options={'review_step': True},
            confirm=True,
        )


def test_a_failed_submit_keeps_the_dialog() -> None:
    result = CloseAccount.validate([('reason', 3)], submit_url='/close', confirm=TEXTS)
    page = result.render_with_errors()
    assert 'Close account</button>' in _dialog(page)


def test_save_steps_asks_only_on_the_last_step() -> None:
    options = {
        'submit_url': '/w',
        'layout': 'wizard',
        'wizard_options': {'save_steps': True},
        'confirm': True,
    }
    first = render_form_html(Wizard, **options)
    assert '<dialog' not in first
    result = Wizard.validate_step([('_sf_wizard_step', '0'), ('first.note', 'a')], **options)
    assert '<dialog' in result.render()
