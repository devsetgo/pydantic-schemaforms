"""Content blocks and consent fields (#274)."""

from typing import Literal

import pytest
from starlette.datastructures import FormData

from pydantic_schemaforms import Field, FormModel, html
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine

FRAMEWORKS = ['bootstrap', 'material', 'none']


class Application(FormModel):
    intro: None = Field(ui_element='content', ui_content='Tell us <b>about</b> you.')
    rich: None = Field(ui_element='content', ui_content=html(t'<a href="/x">Terms</a>'))
    name: str = Field(...)
    terms: Literal[True] = Field(
        ui_element='consent',
        title='I agree',
        ui_content='Please read this.',
        unchecked_message='Agree first',
    )


def _render(model=Application, framework='bootstrap', **kwargs):
    return str(model.render_form(framework=framework, submit_url='/x', **kwargs))


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_plain_text_is_escaped_and_html_is_kept(framework):
    rendered = _render(framework=framework)

    assert 'Tell us &lt;b&gt;about&lt;/b&gt; you.' in rendered
    assert '<a href="/x">Terms</a>' in rendered


def test_user_supplied_script_is_escaped():
    payload = '<script>alert(1)</script>'

    class Form(FormModel):
        intro: None = Field(ui_element='content', ui_content=payload)
        terms: bool = Field(False, ui_element='consent', title=payload, ui_content=payload)

    rendered = _render(Form)

    assert payload not in rendered
    assert '&lt;script&gt;' in rendered


def test_plain_string_cannot_claim_to_be_html():
    with pytest.raises(TypeError, match='ui_content'):
        Field(ui_element='content', ui_content_html='<b>x</b>')


def test_generated_title_is_not_a_heading_inside_a_sub_form():
    rendered = _render(_Parent)

    assert '>Note</h3>' not in rendered


def test_required_sub_form_with_other_fields_is_still_required():
    class Inner(FormModel):
        city: str = Field('Paris')

    class Form(FormModel):
        name: str = Field('x')
        inner: Inner = Field(title='Inner')

    result = Form.validate(FormData([('name', 'Ada')]))

    assert not result.is_valid
    assert 'inner' in result.errors


def test_required_consent_in_a_quiet_sub_form_reports_its_own_error():
    class Quiet(FormModel):
        terms: Literal[True] = Field(
            ui_element='consent', ui_content='x', unchecked_message='Agree'
        )

    class Form(FormModel):
        name: str = Field('x')
        quiet: Quiet = Field(title='Quiet')

    result = Form.validate(FormData([('name', 'Ada')]))

    assert result.errors == {'quiet': {'terms': 'Agree'}}


def test_content_block_renders_no_control():
    class Form(FormModel):
        intro: None = Field(ui_element='content', ui_content='Text')

    rendered = _render(Form)

    assert 'name="intro"' not in rendered
    assert 'id="intro-content"' in rendered


def test_title_is_a_heading_only_when_given():
    class Form(FormModel):
        intro: None = Field(ui_element='content', ui_content='Text')
        other: None = Field(ui_element='content', title='A heading', ui_content='Text')

    rendered = _render(Form)

    assert '>A heading</h3>' in rendered
    assert '>Intro</h3>' not in rendered


def test_content_is_left_out_of_validation_and_data():
    result = Application.validate({'name': 'Ada', 'terms': '1', 'intro': 'tampered', 'rich': 'x'})

    assert result.is_valid
    assert result.data == {'name': 'Ada', 'terms': True}


def test_content_is_left_out_of_the_api_model():
    assert set(Application.as_api_model().model_fields) == {'name', 'terms'}


def test_consent_unticked_reports_its_message_and_stays_rendered():
    result = Application.validate({'name': 'Ada'}, submit_url='/x')

    assert not result.is_valid
    assert result.errors == {'terms': 'Agree first'}
    rendered = str(result.render_with_errors())
    assert 'Agree first' in rendered
    assert 'Please read this.' in rendered


def test_consent_checkbox_is_described_by_its_text():
    rendered = _render()

    checkbox = rendered[rendered.index('<input', rendered.index('terms-content')) :]
    checkbox = checkbox[: checkbox.index('>')]
    assert 'type="checkbox"' in checkbox
    assert 'name="terms"' in checkbox
    assert 'aria-describedby="terms-content"' in checkbox
    assert 'scrollable' not in checkbox


def test_consent_error_keeps_the_text_in_the_description():
    result = Application.validate({'name': 'Ada'}, submit_url='/x')

    assert 'aria-describedby="terms-content terms-error"' in str(result.render_with_errors())


@pytest.mark.parametrize('element', ['content', 'consent'])
@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_scrollable_box_can_be_reached_by_keyboard(element, framework):
    class Form(FormModel):
        block: bool = Field(
            False, ui_element=element, ui_content='Long', ui_options={'scrollable': True}
        )

    rendered = _render(Form, framework=framework)

    assert 'tabindex="0"' in rendered
    assert 'overflow-y: auto' in rendered


class _Inner(FormModel):
    note: None = Field(ui_element='content', ui_content='Inner text')
    city: str = Field('Paris')


class _Item(FormModel):
    note: None = Field(ui_element='content', ui_content='Item text')
    pet: str = Field('Rex')


class _Parent(FormModel):
    inner: _Inner = Field(title='Inner')
    items: list[_Item] = Field(default_factory=list, ui_element='model_list', min_length=1)


@pytest.mark.parametrize('layout', ['vertical', 'tabbed', 'side-by-side', 'accordion', 'wizard'])
@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_content_works_in_every_layout_and_sub_form(layout, framework):
    rendered = _render(_Parent, framework=framework, layout=layout)

    assert 'Inner text' in rendered
    assert 'Item text' in rendered


def test_content_in_sub_forms_is_left_out_of_data():
    result = _Parent.validate(
        {
            'inner.city': 'Rome',
            'inner.note': 'tampered',
            'items[0].pet': 'Tom',
            'items[0].note': 'tampered',
        }
    )

    assert result.is_valid, result.errors
    assert result.data == {'inner': {'city': 'Rome'}, 'items': [{'pet': 'Tom'}]}


def test_sub_form_that_submits_nothing_still_validates():
    class Quiet(FormModel):
        note: None = Field(ui_element='content', ui_content='Text')
        subscribe: bool = Field(False, ui_element='consent', ui_content='Text')

    class Form(FormModel):
        name: str = Field('x')
        quiet: Quiet = Field(title='Quiet')

    submission = FormData([('name', 'Ada')])
    result = Form.validate(submission)

    assert result.is_valid, result.errors
    assert result.data == {'name': 'Ada', 'quiet': {'subscribe': False}}


def test_renderers_survive_a_registry_reset():
    LayoutEngine.reset_layout_renderers()

    assert LayoutEngine.get_renderer_for_element('content') is not None
    assert LayoutEngine.get_renderer_for_element('consent') is not None
