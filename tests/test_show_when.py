"""Conditional fields: ui_show_when (#237)."""

from enum import Enum

import pytest
from starlette.datastructures import FormData

from pydantic_schemaforms import Field, FormField, FormModel
from pydantic_schemaforms.show_when import check_rule, rule_matches

FRAMEWORKS = ['bootstrap', 'material', 'none']
CHOICES = {'choices': [{'value': 'a', 'label': 'A'}, {'value': 'b', 'label': 'B'}]}


class Kind(Enum):
    A = 'a'
    B = 'b'


class Item(FormModel):
    is_gift: bool = Field(False, title='Gift')
    note: str = Field(
        '', title='Gift note', ui_show_when={'field': 'is_gift', 'truthy': True, 'required': True}
    )


class Address(FormModel):
    country: str = Field('', title='Country')
    state: str = Field('', title='State', ui_show_when={'field': 'country', 'equals': 'US'})


class Form(FormModel):
    kind: str = Field('a', title='Kind', ui_element='select', ui_options=CHOICES)
    detail: str = Field(
        '',
        title='Detail',
        min_length=3,
        ui_show_when={'field': 'kind', 'equals': 'b', 'required': True},
    )
    address: Address = Field(default_factory=Address, title='Address')
    billing: str = Field(
        '', title='Billing', ui_show_when={'field': 'address.country', 'equals': 'US'}
    )
    items: list[Item] = Field(default_factory=list, title='Items')


def _render(data=None, model=Form, framework='bootstrap', **kwargs):
    return str(model.render_form(data, framework=framework, submit_url='/x', **kwargs))


def _wrapper(rendered, name):
    position = rendered.index(f'name="{name}"')
    return rendered[rendered.rindex('<fieldset class="sf-show-when"', 0, position) :].split('>')[0]


@pytest.mark.parametrize(
    ('rule', 'value', 'expected'),
    [
        ({'equals': 'a'}, 'a', True),
        ({'equals': 'a'}, 'b', False),
        ({'equals': 'a'}, None, False),
        ({'equals': 'a'}, ['a', 'b'], True),
        ({'equals': 1}, '1', True),
        ({'equals': True}, 'on', True),
        ({'equals': False}, None, True),
        ({'equals': 'a'}, Kind.A, True),
        ({'in': ['a', 'b']}, 'b', True),
        ({'in': ['a', 'b']}, 'c', False),
        ({'truthy': True}, True, True),
        ({'truthy': True}, 'on', True),
        ({'truthy': True}, 'false', False),
        ({'truthy': True}, None, False),
        ({'truthy': True}, [], False),
        ({'truthy': False}, None, True),
        ({'not_empty': True}, 'x', True),
        ({'not_empty': True}, 0, True),
        ({'not_empty': True}, '', False),
        ({'not_empty': True}, [], False),
        ({'not_empty': False}, '', True),
    ],
)
def test_rule_matches(rule, value, expected):
    assert rule_matches(rule, value) is expected


@pytest.mark.parametrize(
    'rule',
    [
        {},
        'kind',
        {'equals': 'a'},
        {'field': 'kind'},
        {'field': 'kind', 'equals': 'a', 'in': ['a']},
        {'field': 'kind', 'equal': 'a'},
        {'field': 'kind', 'truthy': 'yes'},
        {'field': 'kind', 'in': 'abc'},
        {'field': 'kind', 'equals': None},
    ],
)
def test_bad_rules_are_rejected(rule):
    with pytest.raises(ValueError, match='ui_show_when'):
        check_rule(rule)


def test_enum_values_become_json_safe():
    assert check_rule({'field': 'k', 'equals': Kind.A})['equals'] == 'a'
    assert check_rule({'field': 'k', 'in': [Kind.A, Kind.B]})['in'] == ['a', 'b']


def test_form_field_applies_the_same_checks():
    with pytest.raises(ValueError, match='ui_show_when'):
        FormField('', ui_show_when={'field': 'kind', 'equal': 'a'})
    with pytest.raises(ValueError, match='needs a default'):
        FormField(title='Note', ui_show_when={'field': 'kind', 'equals': 'a'})
    with pytest.raises(ValueError, match='ui_cols'):
        FormField('', ui_cols=99)
    with pytest.raises(ValueError, match='needs ui_group'):
        FormField('', ui_group_show_when={'field': 'kind', 'truthy': True})

    class Form(FormModel):
        kind: Kind = FormField(Kind.A, title='Kind')
        note: str = FormField(
            '', title='Note', ui_show_when={'field': 'kind', 'equals': Kind.B}, ui_cols=6
        )

    assert Form.validate({'kind': 'a', 'note': 'smuggled'}).data['note'] == ''
    assert Form.validate({'kind': 'b', 'note': 'kept'}).data['note'] == 'kept'


def test_a_rule_field_needs_a_default():
    with pytest.raises(ValueError, match='needs a default'):
        Field(ui_show_when={'field': 'kind', 'equals': 'a'})
    Field(default_factory=list, ui_show_when={'field': 'kind', 'equals': 'a'})


def test_a_typo_in_the_target_field_is_reported():
    class Bad(FormModel):
        kind: str = Field('a')
        other: str = Field('', ui_show_when={'field': 'knid', 'equals': 'a'})

    with pytest.raises(ValueError, match="names 'knid'"):
        Bad.render_form(submit_url='/x')


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_fresh_form_starts_hidden_from_defaults(framework):
    rendered = _render(framework=framework)

    wrapper = _wrapper(rendered, 'detail')
    assert ' hidden disabled' in wrapper
    assert 'data-show-when-target="kind"' in wrapper
    assert 'data-schemaforms-show-when' in rendered


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_field_shows_when_data_matches(framework):
    wrapper = _wrapper(_render({'kind': 'b'}, framework=framework), 'detail')

    assert 'hidden' not in wrapper


def test_forms_without_rules_ship_no_script():
    class Plain(FormModel):
        name: str = Field('')

    assert 'show-when' not in _render(model=Plain)


def test_script_contains_no_python_comment():
    from pydantic_schemaforms.show_when import SHOW_WHEN_SCRIPT

    assert not [line for line in SHOW_WHEN_SCRIPT.splitlines() if line.strip().startswith('#')]


def test_re_render_with_errors_keeps_the_state_without_javascript():
    result = Form.validate(FormData([('kind', 'b'), ('detail', 'x')]), submit_url='/x')

    assert not result.is_valid
    rendered = str(result.render_with_errors())
    assert 'hidden' not in _wrapper(rendered, 'detail')
    assert ' hidden disabled' in _wrapper(rendered, 'billing')
    assert 'at least 3 characters' in rendered


def test_hidden_field_produces_no_error_and_returns_its_default():
    result = Form.validate(FormData([('kind', 'a'), ('detail', 'x')]))

    assert result.is_valid, result.errors
    assert result.data['detail'] == ''


def test_a_tampered_value_for_a_hidden_field_is_dropped():
    result = Form.validate({'kind': 'a', 'detail': 'smuggled value', 'address': {}})

    assert result.is_valid
    assert result.data['detail'] == ''


def test_required_while_shown():
    assert Form.validate(FormData([('kind', 'b')])).errors == {'detail': 'Field required'}
    assert 'detail' in Form.validate(FormData([('kind', 'b'), ('detail', '')])).errors
    assert Form.validate(FormData([('kind', 'a')])).is_valid
    assert Form.validate(FormData([('kind', 'b'), ('detail', 'fine')])).is_valid


def test_required_errors_are_reported_with_other_errors():
    class Both(FormModel):
        kind: str = Field('b', title='Kind')
        age: int = Field(1, ge=1)
        note: str = Field('', ui_show_when={'field': 'kind', 'equals': 'b', 'required': True})

    errors = Both.validate(FormData([('kind', 'b'), ('age', '0')])).errors

    assert set(errors) == {'age', 'note'}


def test_a_required_consent_must_be_ticked_while_shown():
    class Terms(FormModel):
        kind: str = Field('b')
        agree: bool = Field(
            False,
            ui_element='consent',
            ui_content='Terms',
            unchecked_message='Agree first',
            ui_show_when={'field': 'kind', 'equals': 'b', 'required': True},
        )

    assert Terms.validate(FormData([('kind', 'b')])).errors == {'agree': 'Agree first'}
    assert Terms.validate(FormData([('kind', 'a')])).is_valid
    assert _render(model=Terms).count('sf-show-when') == 1


def test_zero_counts_as_a_value_when_required():
    class Count(FormModel):
        kind: str = Field('b')
        amount: int = Field(1, ui_show_when={'field': 'kind', 'equals': 'b', 'required': True})

    assert Count.validate(FormData([('kind', 'b'), ('amount', '0')])).is_valid


def test_nested_path_and_rule_inside_a_sub_form():
    hidden = Form.validate({'address': {'country': 'FR', 'state': 'x'}, 'billing': 'y'})
    shown = Form.validate({'address': {'country': 'US', 'state': 'x'}, 'billing': 'y'})

    assert hidden.data['address']['state'] == ''
    assert hidden.data['billing'] == ''
    assert shown.data['address']['state'] == 'x'
    assert shown.data['billing'] == 'y'
    assert 'data-show-when-target="address.country"' in _render()


def test_model_list_items_follow_their_own_values():
    result = Form.validate(
        FormData(
            [
                ('items[0].note', 'dropped'),
                ('items[1].is_gift', 'on'),
                ('items[1].note', 'kept'),
                ('items[2].is_gift', 'on'),
            ]
        )
    )

    assert result.errors == {'items': {2: {'note': 'Field required'}}}
    rendered = _render({'items': [{'is_gift': False}, {'is_gift': True}]})
    assert 'data-show-when-target="items[1].is_gift"' in rendered
    assert ' hidden disabled' in _wrapper(rendered, 'items[0].note')
    assert 'hidden' not in _wrapper(rendered, 'items[1].note')


def test_a_rule_on_a_whole_sub_form():
    class Parent(FormModel):
        separate: bool = Field(False, title='Separate')
        shipping: Address | None = Field(
            None, title='Shipping', ui_show_when={'field': 'separate', 'truthy': True}
        )

    assert Parent.validate({'shipping': {'country': 'US'}}).data['shipping'] is None
    assert ' hidden disabled' in _wrapper(_render(model=Parent), 'shipping.country')


def test_chains_hide_in_any_declaration_order():
    class Chain(FormModel):
        last: str = Field('', ui_show_when={'field': 'middle', 'equals': 'x'})
        middle: str = Field('', ui_show_when={'field': 'first', 'truthy': True})
        first: bool = Field(False)

    result = Chain.validate({'middle': 'x', 'last': 'y'})

    assert result.data == {'last': '', 'middle': '', 'first': False}
    assert ' hidden disabled' in _wrapper(_render({'middle': 'x'}, model=Chain), 'last')


def test_a_hidden_section_hides_the_errors_inside_it():
    class Parent(FormModel):
        on: bool = Field(False)
        item: Item | None = Field(None, ui_show_when={'field': 'on', 'truthy': True})

    assert Parent.validate({'item': {'is_gift': True}}).is_valid


@pytest.mark.parametrize('layout', ['vertical', 'tabbed', 'side-by-side', 'accordion', 'wizard'])
@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_every_layout_keeps_the_state(layout, framework):
    assert ' hidden disabled' in _wrapper(_render(framework=framework, layout=layout), 'detail')


def test_a_fields_own_disabled_state_is_left_alone():
    class Both(FormModel):
        kind: str = Field('b')
        note: str = Field('', ui_disabled=True, ui_show_when={'field': 'kind', 'equals': 'b'})

    assert 'disabled' not in _wrapper(_render({'kind': 'b'}, model=Both), 'note')
    assert ' disabled' in _render({'kind': 'b'}, model=Both).split('name="note"')[1].split('>')[0]


def test_rule_values_are_escaped_in_the_attribute():
    class Odd(FormModel):
        kind: str = Field('')
        note: str = Field('', ui_show_when={'field': 'kind', 'equals': '"><script>x</script>'})

    assert '<script>x</script>' not in _render(model=Odd)


@pytest.mark.parametrize('layout', ['vertical', 'tabbed'])
def test_display_mode_leaves_hidden_fields_out(layout):
    data = {
        'kind': 'a',
        'detail': 'stale-detail',
        'address': {'country': 'US', 'state': 'CA'},
        'billing': 'shown-billing',
        'items': [{'is_gift': False, 'note': 'stale-note'}, {'is_gift': True, 'note': 'kept-note'}],
    }
    rendered = str(Form.render_display(data, layout=layout))

    assert 'stale-detail' not in rendered
    assert '>Detail<' not in rendered
    assert 'CA' in rendered
    assert 'shown-billing' in rendered
    assert 'stale-note' not in rendered
    assert 'kept-note' in rendered


def test_display_mode_drops_a_column_hidden_in_every_row_and_a_hidden_section():
    class Parent(FormModel):
        on: bool = Field(False, title='On')
        extra: Address | None = Field(
            None, title='Extra', ui_show_when={'field': 'on', 'truthy': True}
        )
        items: list[Item] = Field(default_factory=list, title='Items')

    data = {'on': False, 'extra': {'country': 'FR'}, 'items': [{'is_gift': False}]}

    for layout in ('vertical', 'tabbed'):
        rendered = str(Parent.render_display(data, layout=layout, edit_urls={'extra': '/e'}))
        assert 'Gift note' not in rendered
        assert 'Extra' not in rendered
        assert 'FR' not in rendered
