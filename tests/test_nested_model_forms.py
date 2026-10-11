"""Composing complex forms by nesting FormModels as fields.

Covers the whole round trip: render (input names, sections, grouped
layouts), submit (raw request forms and nested JSON in), and validate
(nested data and a nested error tree out, re-rendered next to the inputs).
"""

from __future__ import annotations

import json
import re

import pytest
from pydantic import model_validator
from starlette.datastructures import FormData
from werkzeug.datastructures import MultiDict

from pydantic_schemaforms import Field, FormModel, LiveValidator, render_form_html
from pydantic_schemaforms.error_tree import (
    build_error_tree,
    error_list,
    field_message,
    normalize_error_tree,
)
from pydantic_schemaforms.form_data import decode_submission


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')
    phone: str = Field('', title='Phone')


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(title='Pet name')
    age: int = Field(0, title='Age', ge=0)
    vaccinated: bool = Field(False, title='Vaccinated')


class ProfileForm(FormModel):
    nickname: str = Field(title='Nickname')
    contact: Contact = Field(title='Contact details')
    address: Address = Field(title='Home address', ui_collapsible=True)
    pets: list[Pet] = Field(default_factory=list, title='Pets', min_length=1)


class OnlyGroups(FormModel):
    contact: Contact = Field(title='Contact details')
    address: Address = Field(title='Home address')


VALID_JSON = {
    'nickname': 'mk',
    'contact': {'email': 'a@b.c', 'phone': ''},
    'address': {'street': '1 Main', 'city': 'Xy'},
    'pets': [{'name': 'Rex', 'age': 3, 'vaccinated': True}, {'name': 'Tux', 'age': 1}],
}

VALID_WIRE = [
    ('nickname', 'mk'),
    ('contact.email', 'a@b.c'),
    ('contact.phone', ''),
    ('address.street', '1 Main'),
    ('address.city', 'Xy'),
    ('pets[0].name', 'Rex'),
    ('pets[0].age', '3'),
    ('pets[0].vaccinated', 'on'),
    ('pets[1].name', 'Tux'),
    ('pets[1].age', '1'),
    ('csrf_token', 'ignored'),
]


def _input_names(html: str) -> set[str]:
    return set(re.findall(r'<(?:input|select|textarea)[^>]*\sname="([^"]+)"', html))


def _tab_titles(html: str) -> list[str]:
    return re.findall(r'role="tab"[^>]*>\s*([^<]+?)\s*<', html)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('framework', ['bootstrap', 'material'])
def test_nested_model_fields_render_with_dotted_input_names(framework: str) -> None:
    html = render_form_html(ProfileForm, submit_url='/p', framework=framework)

    names = _input_names(html)
    assert {'nickname', 'contact.email', 'contact.phone', 'address.street', 'address.city'} <= names
    assert {'pets[0].name', 'pets[0].age'} <= names
    assert 'contact' not in names
    assert 'Contact details' in html


def test_sub_model_with_the_same_inner_field_names_stays_distinct() -> None:
    class Home(FormModel):
        city: str = Field(title='City')

    class Work(FormModel):
        city: str = Field(title='City')

    class Commute(FormModel):
        home: Home = Field(title='Home')
        work: Work = Field(title='Work')

    names = _input_names(render_form_html(Commute, submit_url='/c'))
    assert {'home.city', 'work.city'} <= names


def test_optional_sub_model_and_deep_nesting() -> None:
    class Owner(FormModel):
        name: str = Field(title='Owner')
        pets: list[Pet] = Field(default_factory=list, title='Pets')

    class Household(FormModel):
        primary: Owner = Field(title='Primary owner')
        secondary: Owner | None = Field(None, title='Second owner')

    names = _input_names(render_form_html(Household, submit_url='/h'))
    assert {'primary.name', 'primary.pets[0].name', 'secondary.name'} <= names


def test_undeclared_list_of_models_renders_as_a_model_list() -> None:
    class Order(FormModel):
        items: list[Pet] = Field(default_factory=list, title='Items')

    html = render_form_html(Order, submit_url='/o')
    assert 'model-list-container' in html
    assert 'items[0].name' in _input_names(html)


def test_collapsible_sub_model_uses_details_and_opens_when_it_has_errors() -> None:
    closed = render_form_html(
        OnlyGroupsCollapsed, submit_url='/c', form_data={'address': {'city': 'Xy'}}
    )
    assert '<details class="nested-model-section" data-field-name="address">' in closed

    with_error = render_form_html(
        OnlyGroupsCollapsed, submit_url='/c', errors={'address': {'city': 'Too short'}}
    )
    assert '<details class="nested-model-section" data-field-name="address" open>' in with_error


class OnlyGroupsCollapsed(FormModel):
    address: Address = Field(title='Home address', ui_collapsible=True, ui_collapsed=True)


def test_prefilled_nested_values_render_into_the_right_inputs() -> None:
    html = render_form_html(ProfileForm, submit_url='/p', form_data=VALID_JSON)
    assert re.search(
        r'name="address\.city"[^>]*value="Xy"|value="Xy"[^>]*name="address\.city"', html
    )
    assert re.search(
        r'name="pets\[1\]\.name"[^>]*value="Tux"|value="Tux"[^>]*name="pets\[1\]\.name"', html
    )


def test_file_input_inside_a_sub_model_makes_the_form_multipart() -> None:
    class Upload(FormModel):
        document: str = Field('', title='Document', ui_element='file')

    class Application(FormModel):
        attachment: Upload = Field(title='Attachment')

    html = render_form_html(Application, submit_url='/a')
    assert 'enctype="multipart/form-data"' in html


# ---------------------------------------------------------------------------
# Grouped layouts
# ---------------------------------------------------------------------------


def test_tabbed_layout_has_one_tab_per_sub_form_in_declaration_order() -> None:
    html = render_form_html(ProfileForm, layout='tabbed', submit_url='/p')
    assert _tab_titles(html) == ['General', 'Contact details', 'Home address', 'Pets']


def test_general_tab_only_appears_when_the_parent_has_plain_fields() -> None:
    html = render_form_html(OnlyGroups, layout='tabbed', submit_url='/o')
    assert _tab_titles(html) == ['Contact details', 'Home address']


def test_ui_order_reorders_tabs() -> None:
    class Reordered(FormModel):
        contact: Contact = Field(title='Contact details', ui_order=2)
        address: Address = Field(title='Home address', ui_order=1)

    html = render_form_html(Reordered, layout='tabbed', submit_url='/r')
    assert _tab_titles(html) == ['Home address', 'Contact details']


def test_parent_title_names_the_general_group() -> None:
    class Titled(FormModel):
        model_config = {'title': 'About you'}
        nickname: str = Field(title='Nickname')
        contact: Contact = Field(title='Contact details')

    html = render_form_html(Titled, layout='tabbed', submit_url='/t')
    assert _tab_titles(html)[0] == 'About you'


def test_tabs_do_not_draw_a_second_titled_card_inside_the_tab() -> None:
    html = render_form_html(OnlyGroups, layout='tabbed', submit_url='/o')
    assert html.count('Contact details') == 1


def test_side_by_side_renders_one_column_per_group() -> None:
    html = render_form_html(ProfileForm, layout='side-by-side', submit_url='/p')
    assert html.count('class="side-by-side-column"') == 4


def test_accordion_renders_one_panel_per_group_first_open() -> None:
    html = render_form_html(ProfileForm, layout='accordion', submit_url='/p')
    assert 'form-groups-accordion' in html
    panel_buttons = re.findall(r'class="accordion-button[^"]*"', html)
    assert len(panel_buttons) == 4
    assert panel_buttons.count('class="accordion-button expanded"') == 1


@pytest.mark.parametrize('layout', ['tabbed', 'side-by-side', 'accordion', 'wizard'])
def test_grouped_layout_on_a_flat_form_explains_how_to_split_it(layout: str) -> None:
    with pytest.raises(ValueError, match='nested FormModel fields'):
        render_form_html(Pet, layout=layout, submit_url='/p')


# ---------------------------------------------------------------------------
# Step wizard
# ---------------------------------------------------------------------------


def _step_titles(html: str) -> list[str]:
    return re.findall(r'class="wizard-progress-title">([^<]+)<', html)


def _active_steps(html: str) -> list[str]:
    return re.findall(r'class="wizard-step[^"]*\bactive\b[^"]*" data-wizard-step="(\d+)"', html)


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'plain'])
def test_wizard_has_one_step_per_group_with_the_first_active(framework: str) -> None:
    html = render_form_html(ProfileForm, layout='wizard', framework=framework, submit_url='/p')

    assert _step_titles(html) == ['General', 'Contact details', 'Home address', 'Pets']
    assert html.count('data-wizard-step=') == 4
    assert _active_steps(html) == ['0']
    assert 'data-wizard-back' in html
    assert 'data-wizard-next' in html
    assert 'window.schemaformsWizard' in html
    # Every step is in the one <form>, so a single POST submits all of them.
    assert {'nickname', 'contact.email', 'address.city'} <= _input_names(html)


def test_wizard_steps_do_not_draw_a_second_titled_card() -> None:
    html = render_form_html(OnlyGroups, layout='wizard', submit_url='/o')
    assert 'layout-field-section' not in html
    assert 'nested-model-section' not in html


def test_wizard_without_javascript_shows_every_step_and_hides_navigation() -> None:
    html = render_form_html(ProfileForm, layout='wizard', submit_url='/p')

    # Only the script adds `wizard-enhanced`; the server never hides a step inline.
    assert 'wizard-enhanced"' not in html
    assert 'style="display: none' not in html.split('<script>')[0]
    assert '.form-wizard:not(.wizard-enhanced) .wizard-footer { display: none; }' in html
    assert '.form-wizard.wizard-enhanced .wizard-step:not(.active) { display: none; }' in html


def test_ui_step_title_overrides_the_step_label_only_in_the_wizard() -> None:
    class Steps(FormModel):
        contact: Contact = Field(title='Contact details', ui_step_title='You', ui_help_text='h')
        address: Address = Field(title='Home address')

    assert _step_titles(render_form_html(Steps, layout='wizard', submit_url='/s')) == [
        'You',
        'Home address',
    ]
    assert _tab_titles(render_form_html(Steps, layout='tabbed', submit_url='/s')) == [
        'Contact details',
        'Home address',
    ]


def test_wizard_options_control_progress_linearity_and_labels() -> None:
    html = render_form_html(
        ProfileForm,
        layout='wizard',
        submit_url='/p',
        wizard_options={
            'linear': False,
            'show_progress': False,
            'back_label': 'Previous',
            'next_label': 'Continue',
        },
    )

    assert 'data-linear="false"' in html
    assert '<ol class="wizard-progress">' not in html
    assert '>Previous</button>' in html
    assert '>Continue</button>' in html


def test_unknown_wizard_option_is_rejected() -> None:
    with pytest.raises(ValueError, match='Unknown wizard_options'):
        render_form_html(
            ProfileForm, layout='wizard', submit_url='/p', wizard_options={'linaer': False}
        )


def test_wizard_re_render_opens_the_first_step_with_an_error_and_marks_the_others() -> None:
    wire = [(k, 'X' if k == 'address.city' else v) for k, v in VALID_WIRE if k != 'contact.email']
    result = ProfileForm.validate(wire, submit_url='/p', layout='wizard')

    html = result.render_with_errors()

    assert _active_steps(html) == ['1']
    assert 'data-active-step="1"' in html
    errored = re.findall(
        r'class="wizard-progress-item[^"]*has-error[^"]*" data-wizard-goto="(\d)"', html
    )
    assert errored == ['1', '2']
    city_input = html.index('name="address.city"')
    assert html.index('String should have at least 2 characters', city_input) - city_input < 1500


def test_two_wizards_on_one_page_do_not_share_element_ids() -> None:
    html = render_form_html(OnlyGroups, layout='wizard', submit_url='/o')
    wizard = html[html.index('<div class="form-wizard') : html.index('<script>')]
    assert ' id="' not in wizard.replace('id="contact.', '').replace('id="address.', '')


# ---------------------------------------------------------------------------
# JSON in
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'raw',
    [
        pytest.param(FormData(VALID_WIRE), id='starlette-formdata'),
        pytest.param(MultiDict(VALID_WIRE), id='werkzeug-multidict'),
        pytest.param(VALID_WIRE, id='pairs'),
        pytest.param(dict(VALID_WIRE), id='flat-dict'),
        pytest.param(VALID_JSON, id='nested-json'),
    ],
)
def test_every_submission_shape_validates_to_the_same_nested_data(raw) -> None:
    result = ProfileForm.validate(raw, submit_url='/p')

    assert result.is_valid, result.errors
    assert result.data == {
        'nickname': 'mk',
        'contact': {'email': 'a@b.c', 'phone': ''},
        'address': {'street': '1 Main', 'city': 'Xy'},
        'pets': [
            {'name': 'Rex', 'age': 3, 'vaccinated': True},
            {'name': 'Tux', 'age': 1, 'vaccinated': False},
        ],
    }
    assert isinstance(result.instance, ProfileForm)
    assert result.instance.pets[0].vaccinated is True


def test_repeated_keys_collect_into_lists() -> None:
    assert decode_submission([('tags', 'a'), ('tags', 'b')]) == {'tags': ['a', 'b']}


def test_values_are_not_coerced_before_validation_knows_the_type() -> None:
    class Note(FormModel):
        code: str = Field(title='Code')

    result = Note.validate([('code', '1')])
    assert result.data == {'code': '1'}


def test_decode_submission_rejects_unknown_shapes() -> None:
    with pytest.raises(TypeError, match='Cannot decode'):
        decode_submission(42)


# ---------------------------------------------------------------------------
# JSON out: the error tree
# ---------------------------------------------------------------------------


def test_errors_mirror_the_data_and_list_errors_are_keyed_by_index() -> None:
    wire = [pair for pair in VALID_WIRE if pair[0] != 'pets[1].age'] + [('pets[1].age', '-1')]
    wire = [(k, 'X' if k == 'address.city' else v) for k, v in wire]

    result = ProfileForm.validate(wire, submit_url='/p')

    assert not result.is_valid
    assert set(result.errors) == {'address', 'pets'}
    assert 'city' in result.errors['address']
    assert result.errors['pets'] == {1: {'age': 'Must be 0 or greater'}}
    assert {'loc': ['pets', 1, 'age'], 'msg': 'Must be 0 or greater'} in result.error_list()
    assert json.loads(json.dumps(result.errors))['pets']['1']['age'] == 'Must be 0 or greater'


def test_container_errors_are_strings_or_live_under_underscore_errors() -> None:
    result = ProfileForm.validate({**VALID_JSON, 'pets': []})
    assert isinstance(result.errors['pets'], str)

    tree = build_error_tree(
        [
            {'loc': ('pets',), 'msg': 'List problem', 'type': ''},
            {'loc': ('pets', 0, 'name'), 'msg': 'Name problem', 'type': ''},
        ]
    )
    assert tree == {'pets': {'_errors': 'List problem', 0: {'name': 'Name problem'}}}
    assert field_message(tree['pets']) == 'List problem'


def test_model_validator_errors_are_form_wide() -> None:
    class Passwords(FormModel):
        password: str
        confirm: str

        @model_validator(mode='after')
        def _match(self):
            if self.password != self.confirm:
                raise ValueError('Passwords do not match')
            return self

    result = Passwords.validate({'password': 'a', 'confirm': 'b'})
    assert 'Passwords do not match' in result.errors['_errors']
    assert error_list(result.errors)[0]['loc'] == []


def test_normalize_error_tree_accepts_wire_paths_and_the_contract_shape() -> None:
    expected = {'address': {'city': 'bad'}, 'pets': {0: {'name': 'worse'}}}
    assert normalize_error_tree({'address.city': 'bad', 'pets[0].name': 'worse'}) == expected
    assert (
        normalize_error_tree(
            {
                'errors': [
                    {'name': 'address.city', 'message': 'bad'},
                    {'name': 'pets[0].name', 'message': 'worse'},
                ]
            }
        )
        == expected
    )
    assert normalize_error_tree(None) == {}


def test_render_with_errors_puts_each_message_next_to_its_input_in_the_right_tab() -> None:
    wire = [(k, 'X' if k == 'address.city' else v) for k, v in VALID_WIRE]
    result = ProfileForm.validate(wire, submit_url='/p', layout='tabbed')

    html = result.render_with_errors()

    city_input = html.index('name="address.city"')
    message = html.index('String should have at least 2 characters', city_input)
    assert message - city_input < 1500
    active_button = re.search(r'<button[^>]*class="[^"]*active[^"]*"[^>]*>\s*([^<]+?)\s*<', html)
    assert active_button is not None
    assert active_button.group(1) == 'Home address'
    assert 'Address — City' in html


def test_list_item_errors_render_on_the_item() -> None:
    result = ProfileForm.validate({**VALID_JSON, 'pets': [{'name': 'Rex', 'age': -5}]})
    html = result.render_with_errors(submit_url='/p')

    # Skip the hidden add-item <template>, which repeats the item's input names.
    age_input = html.index('name="pets[0].age"', html.index('</template>'))
    assert 0 < html.index('Must be 0 or greater', age_input) - age_input < 300
    assert 'Pet #1 — Age' in html


# ---------------------------------------------------------------------------
# HTMX live validation
# ---------------------------------------------------------------------------


def test_live_validator_registers_nested_fields_under_their_input_names() -> None:
    validator = LiveValidator()
    validator.register_model_validator(ProfileForm)

    assert {'address.city', 'contact.email', 'pets[].name'} <= set(validator.validators)
    assert not validator.validate_field('address.city', 'X').is_valid
    assert validator.validate_field('address.city', 'Xy').is_valid
    assert not validator.validate_field('pets[4].age', -1).is_valid


def test_sub_form_accepts_a_model_instance_as_its_value() -> None:
    html = render_form_html(
        OnlyGroups,
        submit_url='/o',
        form_data={'contact': Contact(email='x@y.z'), 'address': None},
    )
    assert re.search(
        r'name="contact\.email"[^>]*value="x@y\.z"|value="x@y\.z"[^>]*name="contact\.email"', html
    )


def test_sub_form_level_message_renders_above_its_fields() -> None:
    html = render_form_html(
        OnlyGroups,
        submit_url='/o',
        errors={'address': {'_errors': 'Address is incomplete', 'city': 'Too short'}},
    )
    section = html.index('data-field-name="address"') if 'data-field-name="address"' in html else 0
    message = html.index('Address is incomplete')
    assert 'nested-model-error' in html
    assert message < html.index('name="address.city"')
    assert section <= message


def test_unresolvable_sub_model_reference_renders_a_comment_not_a_crash() -> None:
    from pydantic_schemaforms import EnhancedFormRenderer
    from pydantic_schemaforms.rendering.context import RenderContext
    from pydantic_schemaforms.rendering.nested_model_renderer import render_nested_model_field

    renderer = EnhancedFormRenderer()
    html = render_nested_model_field(
        'ghost',
        {'$ref': '#/$defs/Missing'},
        None,
        {},
        RenderContext(form_data={}, schema_defs={}),
        renderer._layout_engine,
    )
    assert 'could not resolve the sub-model' in html


def test_field_keeps_unlisted_ui_keys_alongside_listed_ones() -> None:
    class Keeps(FormModel):
        address: Address = Field(title='Home address', ui_help_text='h', ui_collapsible=True)

    schema = Keeps.model_json_schema()['properties']['address']
    assert schema['ui_help_text'] == 'h'
    assert schema['ui_collapsible'] is True


def test_field_keeps_non_pydantic_keywords_alongside_ui_options() -> None:
    class Iconic(FormModel):
        email: str = Field('', title='Email', icon='envelope', ui_help_text='h')
        tags: list[str] = Field(default_factory=list, validation_alias='labels')

    properties = Iconic.model_json_schema()['properties']
    assert properties['email']['icon'] == 'envelope'
    assert 'bi-envelope' in render_form_html(Iconic, submit_url='/i')
    assert Iconic.model_validate({'labels': ['a']}).tags == ['a']


def test_decoder_compacts_list_indices_instead_of_padding() -> None:
    # One field must not be able to make the server allocate a huge padded list,
    # and an item removed without re-indexing the rest must still decode.
    assert decode_submission([('pets[50000000].name', 'x'), ('nickname', 'mk')]) == {
        'pets': [{'name': 'x'}],
        'nickname': 'mk',
    }
    assert decode_submission([('pets[2].name', 'b'), ('pets[0].name', 'a')]) == {
        'pets': [{'name': 'a'}, {'name': 'b'}]
    }


@pytest.mark.parametrize('layout', ['tabbed', 'accordion', 'wizard'])
def test_grouped_material_forms_skip_native_validation_of_hidden_groups(layout: str) -> None:
    form_tag = re.search(
        r'<form[^>]*>',
        render_form_html(ProfileForm, layout=layout, framework='material', submit_url='/p'),
    )
    assert form_tag is not None
    assert 'novalidate' in form_tag.group(0)

    vertical = render_form_html(ProfileForm, framework='material', submit_url='/p')
    assert 'novalidate' not in re.search(r'<form[^>]*>', vertical).group(0)


def test_removing_every_item_of_a_repeating_sub_form_still_checks_min_length() -> None:
    without_pets = [(k, v) for k, v in VALID_WIRE if not k.startswith('pets')]
    result = ProfileForm.validate(without_pets, submit_url='/p')
    assert result.errors == {'pets': 'List should have at least 1 item after validation, not 0'}

    # Nested JSON that omits the key keeps the field's default, as Pydantic does.
    assert ProfileForm.validate({k: v for k, v in VALID_JSON.items() if k != 'pets'}).is_valid


def test_layout_field_without_a_handler_explains_what_to_do() -> None:
    from typing import Any

    class Orphan(FormModel):
        table: Any = Field(None, title='Rows', input_type='layout')

    html = render_form_html(Orphan, submit_url='/o')
    assert 'Layout field "Rows" has no registered layout_handler' in html
    assert 'docs/complex_forms.md' in html


def test_container_message_and_child_errors_share_one_node_in_either_order() -> None:
    whole_list = {'loc': ('pets',), 'msg': 'too few', 'type': ''}
    one_item = {'loc': ('pets', 0, 'name'), 'msg': 'required', 'type': ''}
    expected = {'pets': {'_errors': 'too few', 0: {'name': 'required'}}}

    assert build_error_tree([whole_list, one_item]) == expected
    assert build_error_tree([one_item, whole_list]) == expected


def test_normalize_error_tree_treats_a_bare_message_as_form_wide() -> None:
    assert normalize_error_tree('Server unavailable') == {'_errors': 'Server unavailable'}


def test_a_failing_layout_default_factory_is_not_swallowed() -> None:
    from typing import Any

    def broken() -> Any:
        raise RuntimeError('bad default')

    class Broken(FormModel):
        table: Any = Field(default_factory=broken, title='Rows', input_type='layout')

    with pytest.raises(RuntimeError, match='bad default'):
        render_form_html(Broken, submit_url='/b')


@pytest.mark.parametrize('framework', ['bootstrap', 'material'])
def test_choice_widgets_show_the_current_value(framework: str) -> None:
    class Choices(FormModel):
        size: str = Field('small', ui_element='radio', ui_options={'choices': ['small', 'large']})
        channels: list[str] = Field(
            default_factory=list, ui_element='checkbox_group', ui_options={'choices': ['a', 'b']}
        )
        city: str = Field('', ui_element='combobox', ui_options={'choices': ['Oslo', 'Rome']})

    html = render_form_html(
        Choices,
        form_data={'size': 'large', 'channels': ['b'], 'city': 'Rome'},
        submit_url='/c',
        framework=framework,
    )
    checked = re.findall(r'<input[^>]*\bchecked\b[^>]*>', html)
    assert sorted(re.search(r'value="([^"]*)"', tag).group(1) for tag in checked) == ['b', 'large']
    assert re.search(r'<input[^>]*name="city"[^>]*value="Rome"', html)


def test_custom_date_formats_apply_to_iso_string_values() -> None:
    from datetime import date, datetime, time

    class Formatted(FormModel):
        day: date = Field(
            date(2024, 1, 1), ui_element='date', ui_options={'date_format': '%m/%d/%Y'}
        )
        at: time = Field(time(9, 0), ui_element='time', ui_options={'time_format': '%I:%M %p'})
        when: datetime = Field(
            datetime(2024, 1, 1),
            ui_element='datetime',
            ui_options={'datetime_format': '%d.%m.%Y %H:%M'},
        )

    for data in (
        {'day': '2024-06-15', 'at': '14:30:00', 'when': '2024-06-15T18:00:00'},  # JSON / ISO
        {'day': '06/15/2024', 'at': '02:30 PM', 'when': '15.06.2024 18:00'},  # typed, re-rendered
    ):
        html = render_form_html(Formatted, form_data=data, submit_url='/f')
        assert re.findall(r'name="(?:day|at|when)"[^>]*?value="([^"]*)"', html) == [
            '06/15/2024',
            '02:30 PM',
            '15.06.2024 18:00',
        ]


@pytest.mark.parametrize('framework', ['bootstrap', 'material'])
def test_hidden_element_renders_a_bare_input_and_color_shows_its_value(framework: str) -> None:
    class Widgets(FormModel):
        token: str = Field('', title='Secret Label', ui_element='hidden')
        shade: str = Field('#123456', title='Shade', ui_element='color')
        plain: str = Field(
            '#abcdef', title='Plain', ui_element='color', ui_options={'show_value': False}
        )

    html = render_form_html(
        Widgets,
        form_data={'token': 'abc', 'shade': '#123456', 'plain': '#abcdef'},
        submit_url='/w',
        framework=framework,
    )
    assert 'Secret Label' not in html
    token_input = re.search(r'<input[^>]*name="token"[^>]*>', html).group(0)
    assert 'type="hidden"' in token_input
    assert 'value="abc"' in token_input
    assert html.count('color-value-display') == 1


def test_render_with_errors_accepts_a_merged_error_tree() -> None:
    wire = [(k, 'X' if k == 'address.city' else v) for k, v in VALID_WIRE]
    result = ProfileForm.validate(wire, submit_url='/p')
    rule_errors = {'nickname': ['Nickname is taken']}

    html = result.render_with_errors(errors={**rule_errors, **result.errors})

    assert 'Nickname is taken' in html
    assert 'String should have at least 2 characters' in html
