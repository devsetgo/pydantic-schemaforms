"""Read-only display mode: FormModel.render_display (#238)."""

from datetime import date, datetime, time
from enum import Enum
from typing import Literal

import pytest
from pydantic import SecretStr

from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.rendering.layout_engine import LAYOUTS

FRAMEWORKS = ['bootstrap', 'material', 'none']
XSS = '<script>alert(1)</script>'


class Color(Enum):
    RED = 'red'
    BLUE = 'blue'


class Address(FormModel):
    city: str = Field(title='City')
    hidden_note: str = Field('', ui_hidden=True)


class Pet(FormModel):
    name: str = Field(title='Pet name')
    kind: str = Field(
        'cat',
        title='Kind',
        ui_element='select',
        ui_options={'choices': [{'value': 'cat', 'label': 'Feline'}]},
    )
    secret: str = Field('', ui_element='hidden')


class Profile(FormModel):
    intro: None = Field(ui_element='content', ui_content='Please read this intro.')
    name: str = Field(title='Full name')
    bio: str = Field('', title='Bio', ui_element='textarea')
    color: Color = Field(Color.RED, title='Color')
    size: str = Field(
        's',
        title='Size',
        ui_element='radio',
        ui_options={
            'choices': [{'value': 's', 'label': 'Small'}, {'value': 'l', 'label': 'Large'}]
        },
    )
    newsletter: bool = Field(False, title='Newsletter')
    terms: Literal[True] = Field(ui_element='consent', title='I agree', ui_content='Long terms.')
    address: Address = Field(title='Address')
    pets: list[Pet] = Field(default_factory=list, title='Pets')


DATA = {
    'name': 'Ada',
    'bio': '',
    'color': Color.BLUE,
    'size': 'l',
    'newsletter': False,
    'terms': True,
    'address': {'city': 'Paris', 'hidden_note': 'do-not-show'},
    'pets': [{'name': 'Tom', 'kind': 'cat', 'secret': 'do-not-show'}],
}


def _render(model=Profile, data=DATA, **kwargs):
    return str(model.render_display(data, **kwargs))


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_shows_labels_and_values_but_no_inputs(framework):
    rendered = _render(framework=framework)

    for text in ('Full name', 'Ada', 'Paris', 'Tom', 'I agree'):
        assert text in rendered
    for control in ('<input', '<select', '<textarea', '<form', '<button type="submit"'):
        assert control not in rendered


def test_values_use_their_display_form():
    rendered = _render()

    assert '>Large<' in rendered
    assert '>Feline<' in rendered
    assert '>blue<' in rendered
    assert '>No<' in rendered
    assert '>Yes<' in rendered
    assert 'Not provided' in rendered


def test_hidden_fields_and_content_blocks_are_left_out():
    rendered = _render()

    assert 'do-not-show' not in rendered
    assert 'Please read this intro.' not in rendered
    assert 'Long terms.' not in rendered


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_every_value_and_label_is_escaped(framework):
    class Form(FormModel):
        name: str = Field(title=XSS)
        choice: str = Field(
            title='Choice',
            ui_element='select',
            ui_options={'choices': [{'value': 'x', 'label': XSS}]},
        )
        inner: Address = Field(title=XSS)
        pets: list[Pet] = Field(default_factory=list, title='Pets')

    data = {
        'name': XSS,
        'choice': XSS,
        'inner': {'city': XSS},
        'pets': [{'name': XSS, 'kind': XSS}],
    }
    rendered = _render(Form, data, framework=framework)

    assert XSS not in rendered
    assert '&lt;script&gt;' in rendered


def test_a_url_answer_is_shown_as_text_never_as_a_link():
    class Form(FormModel):
        site: str = Field(title='Site', ui_element='url')

    rendered = _render(Form, {'site': 'javascript:alert(1)'})

    assert 'href=' not in rendered
    assert 'javascript:alert(1)' in rendered


def test_secrets_are_masked():
    class Form(FormModel):
        password: str = Field(title='Password', ui_element='password')
        titled_password: str = Field(title='Your password')
        token: SecretStr = Field(title='Token')
        ssn: str = Field(title='SSN', ui_element='ssn')
        card: str = Field(title='Card', ui_element='credit_card')
        captcha: str = Field('', title='Captcha check', ui_element='captcha')

    rendered = _render(
        Form,
        {
            'password': 'hunter2',
            'titled_password': 'hunter3',
            'token': SecretStr('tok-123'),
            'ssn': '123-45-6789',
            'card': '4111 1111 1111 1234',
            'captcha': 'answer-value',
        },
    )

    for secret in (
        'hunter2',
        'hunter3',
        'tok-123',
        '123-45',
        '4111',
        'answer-value',
        'Captcha check',
    ):
        assert secret not in rendered
    assert '••••••••6789' in rendered
    assert '••••••••1234' in rendered


def test_an_unset_password_says_not_provided():
    class Form(FormModel):
        password: str = Field('', title='Password', ui_element='password')

    assert 'Not provided' in _render(Form, {})


def test_dates_honour_custom_formats_and_iso_strings():
    class Form(FormModel):
        plain: date = Field(title='Plain')
        custom: date = Field(title='Custom', ui_options={'date_format': '%d/%m/%Y'})
        from_text: date = Field(title='Text', ui_options={'date_format': '%d/%m/%Y'})
        at: time = Field(title='At', ui_element='time')
        stamp: datetime = Field(title='Stamp')
        not_iso: date = Field(title='Not ISO')

    rendered = _render(
        Form,
        {
            'plain': date(2026, 3, 9),
            'custom': date(2026, 3, 9),
            'from_text': '2026-03-10',
            'at': time(14, 30),
            'stamp': datetime(2026, 3, 9, 14, 30),
            'not_iso': 'someday',
        },
    )

    for text in ('2026-03-09', '09/03/2026', '10/03/2026', '14:30', '2026-03-09 14:30', 'someday'):
        assert f'>{text}<' in rendered


def test_multiple_choices_and_files():
    class Upload:
        filename = 'cv.pdf'

    class Form(FormModel):
        tags: list[str] = Field(
            title='Tags',
            ui_element='checkbox_group',
            ui_options={
                'choices': [{'value': 'a', 'label': 'Alpha'}, {'value': 'b', 'label': 'Beta'}]
            },
        )
        doc: str = Field('', title='Doc', ui_element='file')

    rendered = _render(Form, {'tags': ['a', 'b'], 'doc': Upload()})

    assert 'Alpha, Beta' in rendered
    assert 'cv.pdf' in rendered


def test_multi_line_answers_keep_their_line_breaks():
    class Form(FormModel):
        bio: str = Field(title='Bio', ui_element='textarea')

    assert 'white-space: pre-wrap' in _render(Form, {'bio': 'one\n  two'})


def test_accepts_a_model_instance():
    class Form(FormModel):
        name: str = Field(title='Name')
        color: Color = Field(Color.RED, title='Color')

    rendered = str(Form.render_display(Form(name='Ada')))

    assert 'Ada' in rendered
    assert '>red<' in rendered


def test_values_are_not_coerced_like_a_raw_submission():
    class Form(FormModel):
        answer: str = Field(title='Answer')

    assert '>yes<' in _render(Form, {'answer': 'yes'})


def test_model_list_is_a_table_with_real_headers():
    rendered = _render()

    assert '<table' in rendered
    assert '<th scope="col">Pet name</th>' in rendered
    assert '<td>Tom</td>' in rendered
    assert 'hidden' not in rendered.split('<table')[1].split('</table>')[0]


def test_empty_list_and_empty_optional_sub_form_say_not_provided():
    class Form(FormModel):
        address: Address | None = Field(None, title='Address')
        pets: list[Pet] = Field(default_factory=list, title='Pets')

    rendered = _render(Form, {'address': None, 'pets': []})

    assert rendered.count('Not provided') == 2
    assert '<table' not in rendered


def test_sub_forms_nest_and_recurse():
    class Owner(FormModel):
        address: Address = Field(title='Home')
        pets: list[Pet] = Field(default_factory=list, title='Pets')

    class Form(FormModel):
        owner: Owner = Field(title='Owner')
        owners: list[Owner] = Field(default_factory=list, title='Owners')

    inner = {'address': {'city': 'Rome'}, 'pets': [{'name': 'Rex'}]}
    rendered = _render(Form, {'owner': inner, 'owners': [inner]})

    assert rendered.count('Rome') == 2
    assert rendered.count('Rex') == 2


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', sorted(LAYOUTS))
def test_every_layout_renders_every_value(framework, layout):
    rendered = _render(framework=framework, layout=layout)

    assert 'Ada' in rendered
    assert 'Paris' in rendered
    assert 'Tom' in rendered


def test_wizard_is_flat():
    rendered = _render(layout='wizard')

    assert 'wizard' not in rendered.lower()
    assert 'Next' not in rendered


def test_tabs_come_from_the_shared_layout():
    assert 'form-groups-tabbed' in _render(layout='tabbed')
    assert 'form-groups-accordion' in _render(layout='accordion')
    assert 'form-groups-side-by-side' in _render(layout='side-by-side')


def test_a_group_with_nothing_to_show_gets_no_tab():
    class Form(FormModel):
        intro: None = Field(ui_element='content', ui_content='Hello')
        address: Address = Field(title='Address')

    assert 'General' not in _render(Form, {'address': {'city': 'Oslo'}}, layout='tabbed')


def test_a_grouped_layout_needs_groups():
    class Form(FormModel):
        name: str = Field(title='Name')

    with pytest.raises(ValueError, match='needs groups'):
        _render(Form, {'name': 'x'}, layout='tabbed')


def test_unknown_layout_is_rejected():
    with pytest.raises(ValueError, match='Unknown layout'):
        _render(layout='nope')


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', ['vertical', 'tabbed', 'side-by-side', 'accordion', 'wizard'])
def test_edit_links(framework, layout):
    rendered = _render(framework=framework, layout=layout, edit_urls={'address': '/edit?a=1&b=2'})

    assert 'href="/edit?a=1&amp;b=2"' in rendered
    assert 'aria-label="Edit Address"' in rendered
    assert rendered.index('aria-label="Edit Address"') < rendered.index('Paris')


def test_edit_url_for_an_unknown_section_is_rejected():
    with pytest.raises(ValueError, match='not sub-form fields'):
        _render(edit_urls={'adress': '/edit'})


@pytest.mark.parametrize(
    'url', ['javascript:alert(1)', 'java\tscript:alert(1)', 'data:text/html,x']
)
def test_edit_url_with_an_unsafe_scheme_is_rejected(url):
    with pytest.raises(ValueError, match='relative or http'):
        _render(edit_urls={'address': url})


def test_material_uses_its_own_classes_and_variant():
    rendered = _render(framework='material', material_variant='filled')

    assert 'md-display' in rendered
    assert 'md-form--filled' in rendered
    assert 'md-table' in rendered


def test_plain_style_adds_no_framework_classes():
    rendered = _render(framework='none')

    assert 'col-sm-4' not in rendered
    assert 'md-display' not in rendered


def test_datatable_layout_value_shows_its_rows():
    from pydantic_schemaforms import DataTableLayout

    class Row(DataTableLayout):
        name: str = Field(title='Row name')

    class Form(FormModel):
        table: dict = Field(
            title='Table', input_type='layout', layout_handler='datatable', default_factory=dict
        )

    rendered = _render(Form, {'table': Row.as_layout_value(rows=[{'name': 'Grace'}])})

    assert '<th scope="col">Row name</th>' in rendered
    assert 'Grace' in rendered
    assert 'model_cls' not in rendered


def test_a_custom_composite_falls_back_to_the_value_shape():
    from pydantic_schemaforms import LayoutEngine

    LayoutEngine.register_layout_renderer('my_widget', lambda *args: '')
    try:

        class Form(FormModel):
            rows: list[dict] = Field(title='Rows', ui_element='my_widget')
            detail: dict = Field(title='Detail', ui_element='my_widget')

        rendered = _render(Form, {'rows': [{'first_name': XSS}], 'detail': {'first_name': 'Ada'}})
    finally:
        LayoutEngine.reset_layout_renderers()

    assert '<th scope="col">First Name</th>' in rendered
    assert XSS not in rendered
    assert 'Ada' in rendered


def test_example_confirmation_page_after_a_valid_submit():
    from fastapi.testclient import TestClient

    import examples.main

    client = TestClient(examples.main.app)
    form = {
        'personal_info.first_name': 'Alex',
        'personal_info.last_name': 'Johnson',
        'personal_info.email': 'alex@example.com',
        'contact_info.phone': '+1 555 987 6543',
        'contact_info.address': '456 Demo Street',
        'contact_info.city': 'Oslo',
        'contact_info.postal_code': '94102',
        'preferences.digest_frequency': 'daily',
        'task_list.project_name': 'Demo',
        'task_list.tasks[0].task_name': 'Ship it',
        'task_list.tasks[0].priority': 'high',
    }
    response = client.post('/layouts?layout=vertical&style=material', data=form)

    assert 'sf-display' in response.text, response.text[:2000]
    assert 'md-display' in response.text
    assert 'Ship it' in response.text


def test_assets_are_opt_in():
    assert 'bootstrap' not in _render(framework='bootstrap').lower().split('<dl')[0]
    assert '<style' in _render(framework='bootstrap', self_contained=True)


def test_markers_can_be_turned_off():
    assert 'Pydantic-SchemaForms' in _render()
    assert 'Pydantic-SchemaForms' not in _render(include_html_markers=False)
