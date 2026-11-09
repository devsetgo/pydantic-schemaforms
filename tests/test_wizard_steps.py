"""wizard_options={"save_steps": True}: one step per page, saved by the app (#275)."""

import io
import json
import re
from typing import Any

import pytest
from pydantic import model_validator
from werkzeug.datastructures import FileStorage

from pydantic_schemaforms import (
    Field,
    FormModel,
    SavedFile,
    UploadedFile,
    render_form_html,
)


class About(FormModel):
    name: str = Field(title='Name', min_length=2)
    newsletter: bool = Field(False, title='Newsletter')


class Docs(FormModel):
    resume: UploadedFile = Field(title='Resume', ui_max_size=100)


class Item(FormModel):
    label: str = Field(title='Label', min_length=1)


class Dates(FormModel):
    start: int = Field(title='Start')
    end: int = Field(title='End')
    items: list[Item] = Field(default_factory=list, title='Items')


class Application(FormModel):
    about: About = Field(title='About you')
    docs: Docs = Field(title='Documents')
    dates: Dates = Field(title='Dates')

    @model_validator(mode='after')
    def _in_order(self) -> 'Application':
        if self.dates.end <= self.dates.start:
            raise ValueError('End must be after start')
        return self


OPTIONS: dict[str, Any] = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'save_steps': True},
}


def _post(step: int, action: str | None = None, draft: Any = None, **fields: Any):
    form: list[tuple[str, Any]] = [('_sf_wizard_step', str(step))]
    if action:
        form.append(('_sf_wizard', action))
    form += [(name.replace('__', '.'), value) for name, value in fields.items()]
    return Application.validate_step(form, draft=draft, **OPTIONS)


def _upload(name: str = 'cv.pdf', content: bytes = b'12345') -> FileStorage:
    return FileStorage(io.BytesIO(content), filename=name, content_type='application/pdf')


def _step_shown(page: str) -> int:
    match = re.search(r'name="_sf_wizard_step" value="(\d+)"', page)
    assert match
    return int(match.group(1))


def _through_docs() -> dict[str, Any]:
    first = _post(0, 'next', about__name='Ada')
    second = _post(1, 'next', draft=first.draft, docs__resume=_upload())
    second.files[0].ref = 'stored-1'
    return second.draft


def test_a_fresh_form_shows_only_the_first_step() -> None:
    page = render_form_html(Application, **OPTIONS)
    assert _step_shown(page) == 0
    assert 'name="about.name"' in page
    assert 'name="docs.resume"' not in page
    assert 'name="dates.start"' not in page
    assert 'wizard-enhanced wizard-saved' in page
    assert 'schemaformsWizard' not in page
    assert 'value="back"' not in page
    # Only the last step has the form's own submit button.
    assert not re.search(r'<button[^>]*type="submit"(?![^>]*name=)', page)
    assert re.findall(r'value="goto:(\d)"[^>]*disabled', page) == ['1', '2']


def test_a_valid_step_moves_on_and_its_draft_resumes_there() -> None:
    result = _post(0, 'next', about__name='Ada')
    assert (result.is_valid, result.is_complete, result.step) == (True, False, 1)
    assert result.draft['step'] == 1
    assert json.loads(json.dumps(result.draft)) == result.draft
    resumed = render_form_html(Application, draft=result.draft, **OPTIONS)
    assert _step_shown(resumed) == 1
    assert 'name="docs.resume"' in resumed
    assert 'value="back"' in resumed


def test_only_the_current_step_is_checked() -> None:
    result = _post(0, 'next', about__name='A')
    assert not result.is_valid
    assert result.errors == {'about': {'name': 'String should have at least 2 characters'}}
    page = result.render()
    assert _step_shown(page) == 0
    assert 'value="A"' in page
    # Later steps aren't marked as failing before the user gets to them.
    assert len(re.findall(r'class="wizard-progress-item[^"]*has-error"', page)) == 1


def test_no_action_means_next() -> None:
    assert _post(0, None, about__name='Ada').step == 1


def test_back_keeps_a_valid_step_and_drops_an_invalid_one() -> None:
    draft = _post(0, 'next', about__name='Ada').draft
    kept = _post(1, 'back', draft=draft, docs__resume=_upload())
    assert (kept.is_valid, kept.step) == (True, 0)
    assert kept.data['docs']['resume'].filename == 'cv.pdf'

    dropped = _post(1, 'back', draft=draft, docs__resume='')
    assert (dropped.is_valid, dropped.step) == (False, 0)
    assert 'docs' not in dropped.data
    assert _step_shown(dropped.render()) == 0


def test_jumps_only_reach_steps_already_reached() -> None:
    assert _post(0, 'goto:2', about__name='Ada').step == 0
    draft = _through_docs()
    assert _post(2, 'goto:0', draft=draft).step == 0
    back_at_start = _post(0, 'goto:0', draft=draft, about__name='Ada')
    assert back_at_start.step == 0
    assert _post(0, 'goto:2', draft=draft, about__name='Ada').step == 2


def test_a_linear_jump_forward_checks_the_current_step() -> None:
    draft = _through_docs()
    assert _post(0, 'goto:2', draft=draft, about__name='A').step == 0

    free = Application.validate_step(
        [('_sf_wizard_step', '0'), ('_sf_wizard', 'goto:2'), ('about.name', 'A')],
        draft=draft,
        **{**OPTIONS, 'wizard_options': {'save_steps': True, 'linear': False}},
    )
    assert (free.is_valid, free.step) == (False, 2)
    assert free.data['about']['name'] == 'Ada'


def test_submit_counts_only_on_the_last_step() -> None:
    result = _post(0, 'submit', about__name='Ada')
    assert (result.is_complete, result.step) == (False, 1)


def test_the_final_submit_validates_the_whole_model() -> None:
    draft = _through_docs()
    failed = _post(2, None, draft=draft, dates__start='5', dates__end='3')
    assert not failed.is_complete
    assert failed.errors == {'_errors': 'End must be after start'}
    assert _step_shown(failed.render()) == 2

    done = _post(2, None, draft=draft, dates__start='1', dates__end='3')
    assert done.is_complete
    assert done.data['about'] == {'name': 'Ada', 'newsletter': False}
    resume = done.data['docs']['resume']
    assert isinstance(resume, SavedFile)
    assert (resume.filename, resume.size, resume.ref) == ('cv.pdf', 5, 'stored-1')
    with pytest.raises(ValueError, match='no step left'):
        done.render()


def test_an_error_on_an_earlier_step_reopens_it() -> None:
    draft = _through_docs()
    draft['data']['about']['name'] = 'A'
    failed = _post(2, None, draft=draft, dates__start='1', dates__end='3')
    assert _step_shown(failed.render()) == 0


def test_files_are_handed_over_once_and_kept_by_name() -> None:
    draft = _post(0, 'next', about__name='Ada').draft
    too_big = _post(1, 'next', draft=draft, docs__resume=_upload(content=b'x' * 101))
    assert not too_big.is_valid and too_big.files == []

    accepted = _post(1, 'next', draft=draft, docs__resume=_upload())
    assert [upload.filename for upload in accepted.files] == ['cv.pdf']
    assert accepted.files[0].read() == b'12345'
    saved = accepted.draft['data']['docs']['resume']
    assert saved == {
        '__sf_saved_file__': {
            'filename': 'cv.pdf',
            'content_type': 'application/pdf',
            'size': 5,
            'ref': None,
        }
    }


def test_a_revisited_upload_step_keeps_its_file_when_left_empty() -> None:
    draft = _through_docs()
    again = _post(1, 'next', draft=draft, docs__resume='')
    assert again.is_valid
    assert isinstance(again.data['docs']['resume'], SavedFile)
    with pytest.raises(OSError, match='uploaded on an earlier step'):
        again.data['docs']['resume'].read()


def test_an_unticked_checkbox_on_a_revisited_step_is_unticked() -> None:
    draft = _post(0, 'next', about__name='Ada', about__newsletter='1').draft
    assert draft['data']['about']['newsletter'] == '1'
    again = _post(0, 'next', draft=draft, about__name='Ada')
    assert 'newsletter' not in again.draft['data']['about']


class Grouped(FormModel):
    name: str = Field(title='Name', ui_group='About')
    newsletter: bool = Field(True, title='Newsletter', ui_group='About')
    city: str = Field('', title='City', ui_group='Where')


def test_an_unticked_grouped_checkbox_stays_unticked_on_back() -> None:
    first = Grouped.validate_step([('_sf_wizard_step', '0'), ('name', 'Ada')], **OPTIONS)
    assert first.draft['data']['newsletter'] is False
    back = Grouped.validate_step(
        [('_sf_wizard_step', '1'), ('_sf_wizard', 'back'), ('city', 'Oslo')],
        draft=first.draft,
        **OPTIONS,
    )
    box = re.search(r'<input[^>]*name="newsletter"[^>]*>', back.render())
    assert box and 'checked' not in box.group(0)


def test_form_data_gives_the_starting_values_and_the_draft_goes_on_top() -> None:
    record = {'about': {'name': 'Ada'}, 'dates': {'start': 3, 'end': 9}}
    first = _post(0, 'next', about__name='Grace')
    back = _post(1, 'back', draft=first.draft)
    page = render_form_html(Application, form_data=record, draft=back.draft, **OPTIONS)
    assert _step_shown(page) == 0
    assert 'value="Grace"' in page and 'value="Ada"' not in page
    second = _post(1, 'next', draft=first.draft, docs__resume=_upload())
    assert 'value="9"' in second.render(data=record)


def test_list_items_on_a_step_are_checked_and_kept() -> None:
    draft = _through_docs()
    failed = _post(
        2, None, draft=draft, dates__start='1', dates__end='3', **{'dates__items[0]__label': ''}
    )
    assert failed.errors['dates']['items'][0]['label']
    done = _post(
        2, None, draft=draft, dates__start='1', dates__end='3', **{'dates__items[0]__label': 'One'}
    )
    assert done.data['dates']['items'] == [{'label': 'One'}]


def test_a_tampered_step_index_cannot_skip_ahead() -> None:
    # Clamped to the last step, so it's a final submit, which fails on the
    # steps never filled in and reopens the first of them.
    result = _post(9, 'next')
    assert (result.is_complete, result.step) == (False, 0)


def test_drafts_must_come_from_validate_step() -> None:
    with pytest.raises(ValueError, match='result.draft'):
        _post(0, 'next', draft={'step': 1}, about__name='Ada')
    with pytest.raises(ValueError, match='result.draft'):
        render_form_html(Application, draft='nope', **OPTIONS)


def test_save_steps_needs_its_options() -> None:
    with pytest.raises(ValueError, match="save_steps': True"):
        Application.validate_step([], submit_url='/apply', layout='wizard')
    with pytest.raises(TypeError, match='draft= needs'):
        render_form_html(Application, submit_url='/apply', layout='wizard', draft=None or {})


def test_without_save_steps_the_wizard_is_unchanged() -> None:
    page = render_form_html(Application, submit_url='/apply', layout='wizard')
    assert 'name="docs.resume"' in page and 'name="dates.start"' in page
    assert '_sf_wizard' not in page
    assert 'schemaformsWizard' in page


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_every_style_posts_back_and_next(framework: str) -> None:
    draft = _post(0, 'next', about__name='Ada').draft
    page = render_form_html(Application, draft=draft, framework=framework, **OPTIONS)
    assert re.search(r'<button type="submit"[^>]*name="_sf_wizard" value="back"', page)
    assert re.search(
        r'<button type="submit"[^>]*name="_sf_wizard" value="next" data-wizard-next', page
    )


def test_a_rule_on_another_step_renders_from_the_draft() -> None:
    class Contact(FormModel):
        method: str = Field('email', title='Method')

    class Detail(FormModel):
        phone: str = Field('', title='Phone', ui_show_when={'field': 'method', 'equals': 'phone'})

    class Ruled(FormModel):
        method: str = Field('email', title='Method', ui_group='How')
        phone: str = Field(
            '',
            title='Phone',
            ui_group='Number',
            ui_show_when={'field': 'method', 'equals': 'phone'},
        )

    draft = Ruled.validate_step([('_sf_wizard_step', '0'), ('method', 'phone')], **OPTIONS).draft
    page = render_form_html(Ruled, draft=draft, **OPTIONS)
    assert 'name="method"' not in page
    wrapper = re.search(r'<fieldset class="sf-show-when"[^>]*>', page)
    assert wrapper and 'hidden' not in wrapper.group(0)


def test_uploaded_file_repr_names_its_class() -> None:
    assert repr(SavedFile('a.pdf', 'application/pdf', 3)).startswith('SavedFile(')
    assert repr(UploadedFile('a.pdf', '', io.BytesIO(b''))).startswith('UploadedFile(')


def test_list_items_survive_a_round_trip_through_the_draft() -> None:
    draft = _through_docs()
    failed = _post(
        2, None, draft=draft, dates__start='5', dates__end='3', **{'dates__items[0]__label': 'One'}
    )
    stored = json.loads(json.dumps(failed.draft))
    assert stored['data']['dates']['items'] == [{'label': 'One'}]
    again = _post(
        2, None, draft=stored, dates__start='1', dates__end='3', **{'dates__items[0]__label': 'One'}
    )
    assert again.is_complete


def test_a_file_part_left_out_entirely_keeps_the_saved_file() -> None:
    draft = _through_docs()
    assert isinstance(_post(1, 'next', draft=draft).data['docs']['resume'], SavedFile)
    other = _post(1, 'next', draft=draft, docs__note='x')
    assert isinstance(other.data['docs']['resume'], SavedFile)


def test_a_non_numeric_step_index_means_the_first_step() -> None:
    assert _post('x', 'next', about__name='Ada').step == 1  # type: ignore[arg-type]


def test_render_needs_a_submit_url_and_has_an_async_twin() -> None:
    import asyncio

    result = Application.validate_step(
        [('_sf_wizard_step', '0'), ('about.name', 'Ada')],
        layout='wizard',
        wizard_options={'save_steps': True},
    )
    with pytest.raises(ValueError, match='submit_url is required'):
        result.render()
    page = asyncio.run(result.render_async(submit_url='/apply'))
    assert _step_shown(page) == 1


def test_saved_files_are_found_inside_list_items() -> None:
    from pydantic_schemaforms.wizard_steps import _contains_saved_file

    assert _contains_saved_file([{'letter': SavedFile('l.pdf', 'application/pdf', 1)}])
    assert not _contains_saved_file([{'letter': None}])
