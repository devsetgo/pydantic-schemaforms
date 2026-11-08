"""wizard_options={"review_step": ...}: a read-only last step before Submit (#250)."""

import io
import re
from typing import Literal

import pytest
from werkzeug.datastructures import FileStorage

from pydantic_schemaforms import Field, FormModel, UploadedFile, render_form_html


class About(FormModel):
    name: str = Field(title='Name')
    secret: str = Field('', title='Password', ui_element='password')
    card: str = Field('', title='Card', ui_element='credit_card')
    role: Literal['eng', 'des'] = Field(
        'eng',
        title='Role',
        ui_element='select',
        ui_options={
            'choices': [
                {'value': 'eng', 'label': 'Engineer'},
                {'value': 'des', 'label': 'Designer'},
            ]
        },
    )
    remote: bool = Field(False, title='Remote')
    note: str = Field('', title='Note', ui_show_when={'field': 'remote', 'truthy': True})


class Job(FormModel):
    employer: str = Field(title='Employer')
    starts: str = Field('', title='Starts', ui_element='datetime-local')


class Docs(FormModel):
    resume: UploadedFile | None = Field(None, title='Resume')


class Application(FormModel):
    about: About = Field(title='About you')
    jobs: list[Job] = Field(default_factory=list, title='Experience')
    docs: Docs = Field(title='Documents')


DATA = {
    'about': {
        'name': 'Robin <b>',
        'secret': 'hunter2',
        'card': '4111 1111 1111 1234',
        'role': 'des',
    },
    'jobs': [{'employer': 'Acme', 'starts': '2027-01-04T09:00'}],
}


def _render(**options: object) -> str:
    wizard_options = {'review_step': True, **options}
    return render_form_html(
        Application,
        form_data=DATA,
        submit_url='/apply',
        layout='wizard',
        wizard_options=wizard_options,
    )


def _review(page: str) -> str:
    start = page.index('<div class="sf-display sf-review"')
    return page[
        start : page.index('data-wizard-step="3"', start)
        if 'data-wizard-step="3"' in page[start:]
        else None
    ]


def test_the_review_is_the_last_step_and_holds_the_submit_button() -> None:
    page = _render()
    assert re.findall(r'wizard-progress-title">([^<]+)', page) == [
        'About you',
        'Experience',
        'Documents',
        'Review',
    ]
    assert 'data-wizard-review' in page
    assert re.findall(r'data-wizard-edit="(\d)"', page) == ['0', '1', '2']
    assert 'aria-label="Edit About you"' in page


def test_the_review_adds_no_inputs() -> None:
    plain = render_form_html(Application, form_data=DATA, submit_url='/apply', layout='wizard')
    reviewed = _render()
    names = re.compile(r'<(?:input|select|textarea)[^>]*\bname="([^"]+)"')
    assert sorted(names.findall(plain)) == sorted(names.findall(reviewed))
    assert not names.findall(_review(reviewed))


def test_each_value_has_a_slot_with_its_format() -> None:
    review = _review(_render())
    slots = dict(re.findall(r'data-review-slot="([^"]+)" data-review-format="([^"]+)"', review))
    assert slots == {
        'about.name': 'text',
        'about.secret': 'mask',
        'about.card': 'last4',
        'about.role': 'choice',
        'about.remote': 'yesno',
        'about.note': 'text',
        'employer': 'text',
        'starts': 'datetime',
        'docs.resume': 'file',
    }
    assert 'data-review-list="jobs"' in review
    assert '&quot;des&quot;: &quot;Designer&quot;' in review


def test_the_starting_values_are_formatted_and_escaped() -> None:
    review = _review(_render())
    assert 'Robin &lt;b&gt;' in review
    assert '<b>' not in review
    assert 'hunter2' not in review
    assert '••••••••1234' in review
    assert 'Designer' in review
    assert 'Acme' in review
    assert '2027-01-04 09:00' in review


def test_custom_title_and_edit_label() -> None:
    page = _render(review_step={'title': 'Check your answers', 'edit_label': 'Change'})
    assert 'Check your answers' in re.findall(r'wizard-progress-title">([^<]+)', page)
    assert 'aria-label="Change About you">Change</button>' in page


@pytest.mark.parametrize(
    'value',
    [{'title': 'x', 'colour': 'red'}, {'title': 3}, 'yes'],
)
def test_bad_review_options_are_rejected(value: object) -> None:
    with pytest.raises(ValueError, match='review_step'):
        _render(review_step=value)


def test_without_the_option_nothing_changes() -> None:
    page = render_form_html(Application, form_data=DATA, submit_url='/apply', layout='wizard')
    assert 'class="sf-display sf-review"' not in page
    assert 'Review</span>' not in page


def test_an_error_never_opens_the_review_step() -> None:
    # Documents is required and was left out, so its step opens, not the review.
    result = Application.validate(
        [('about.name', 'Robin'), ('jobs[0].employer', 'Acme')],
        submit_url='/apply',
        layout='wizard',
        wizard_options={'review_step': True},
    )
    assert result.errors == {'docs': 'Field required'}
    assert 'data-active-step="2"' in result.render_with_errors()


SAVE = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'save_steps': True, 'review_step': {'edit_label': 'Change'}},
}


def _step(step: int, draft: object = None, action: str | None = None, **fields: object):
    form: list[tuple[str, object]] = [('_sf_wizard_step', str(step))]
    if action:
        form.append(('_sf_wizard', action))
    form += [(name.replace('__', '.'), value) for name, value in fields.items()]
    return Application.validate_step(form, draft=draft, **SAVE)


def _through_docs() -> dict:
    first = _step(0, about__name='Robin', about__role='des', about__remote='1', about__note='Hi')
    second = _step(1, first.draft, **{'jobs[0].employer': 'Acme'})
    upload = FileStorage(io.BytesIO(b'cv'), filename='cv.pdf', content_type='application/pdf')
    third = _step(2, second.draft, docs__resume=upload)
    third.files[0].ref = 'r1'
    assert third.step == 3
    return third.draft


def test_save_steps_reaches_the_review_after_the_last_real_step() -> None:
    draft = _through_docs()
    page = render_form_html(Application, draft=draft, **SAVE)
    assert 'data-wizard-review' not in page
    review = _review(page)
    assert 'Designer' in review and 'Acme' in review and 'cv.pdf' in review
    assert re.findall(r'value="goto:(\d)"[^>]*>Change</button>', review) == ['0', '1', '2']
    assert not re.search(r'<input[^>]*name="(?!_sf_)', review)
    assert re.search(r'<button[^>]*type="submit"(?![^>]*name=)', page)


def test_save_steps_review_leaves_out_fields_hidden_by_a_rule() -> None:
    first = _step(0, about__name='Robin', about__note='Hi')
    second = _step(1, first.draft, **{'jobs[0].employer': 'Acme'})
    third = _step(2, second.draft, docs__resume='')
    review = _review(render_form_html(Application, draft=third.draft, **SAVE))
    assert 'Note' not in review


def test_save_steps_submit_on_the_review_validates_everything() -> None:
    result = _step(3, _through_docs())
    assert result.is_complete
    assert result.data['about']['name'] == 'Robin'
    assert result.data['docs']['resume'].ref == 'r1'


def test_save_steps_edit_from_the_review_goes_back() -> None:
    assert _step(3, _through_docs(), 'goto:1').step == 1


def test_uploaded_files_are_named_on_the_review() -> None:
    upload = UploadedFile('cv.pdf', 'application/pdf', io.BytesIO(b''))
    page = render_form_html(
        Application,
        form_data={**DATA, 'docs': {'resume': upload}},
        submit_url='/apply',
        layout='wizard',
        wizard_options={'review_step': True},
    )
    assert 'cv.pdf' in _review(page)
