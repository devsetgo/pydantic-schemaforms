"""Field groups and grid widths in one model (#241)."""

import pytest

from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.rendering.layout_engine import LAYOUTS

FRAMEWORKS = ['bootstrap', 'material', 'none']
XSS = '<script>alert(1)</script>'


class Address(FormModel):
    city: str = Field('', title='City', ui_cols=6)
    zip_code: str = Field('', title='Zip', ui_cols=6)
    note: str = Field('', title='Note', ui_group='Inner group')


class Form(FormModel):
    first: str = Field('', title='First', ui_cols=6)
    last: str = Field('', title='Last', ui_cols=6)
    street: str = Field('', title='Street', ui_group='Location', ui_cols=8)
    plain: str = Field('', title='Plain')
    unit: str = Field('', title='Unit', ui_group='Location', ui_cols=4)
    extra: str = Field('', title='Extra', ui_group='More', ui_group_collapsible=True)
    address: Address = Field(default_factory=Address, title='Sub-form')


def _render(model=Form, framework='bootstrap', **kwargs):
    return str(model.render_form(framework=framework, submit_url='/x', **kwargs))


@pytest.mark.parametrize(
    'kwargs',
    [{'ui_cols': 0}, {'ui_cols': 13}, {'ui_cols': '6'}, {'ui_cols': True}, {'ui_group': ' '}],
)
def test_bad_options_are_rejected(kwargs):
    with pytest.raises(ValueError, match='ui_'):
        Field('', **kwargs)


def test_group_rule_needs_a_group_and_cannot_say_required():
    rule = {'field': 'x', 'truthy': True}
    with pytest.raises(ValueError, match='needs ui_group'):
        Field('', ui_group_show_when=rule)
    with pytest.raises(ValueError, match='required'):
        Field('', ui_group='G', ui_group_show_when={**rule, 'required': True})


def test_forms_using_neither_render_unchanged():
    class Plain(FormModel):
        a: str = Field('', title='A')

    rendered = _render(Plain)

    assert 'sf-grid' not in rendered
    assert 'sf-col' not in rendered


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_widths_share_a_row_under_every_style(framework):
    rendered = _render(framework=framework)

    assert 'data-schemaforms-grid' in rendered
    assert 'class="sf-col sf-col-6"' in rendered
    first_row = rendered.split('class="sf-grid"')[1]
    assert 'name="first"' in first_row
    assert 'name="last"' in first_row


def test_a_row_breaks_past_twelve_and_at_a_full_width_field():
    class Wide(FormModel):
        a: str = Field('', ui_cols=8)
        b: str = Field('', ui_cols=8)
        c: str = Field('', ui_cols=2)
        d: str = Field('')
        e: str = Field('', ui_cols=2)

    rows = _render(Wide).split('class="sf-grid"')[1:]

    assert len(rows) == 3
    assert 'name="a"' in rows[0] and 'name="b"' not in rows[0]
    assert 'name="b"' in rows[1] and 'name="c"' in rows[1]
    assert 'name="e"' in rows[2]


def test_a_hidden_input_does_not_break_a_row():
    class Row(FormModel):
        a: str = Field('', ui_cols=6)
        token: str = Field('t', ui_hidden=True, ui_cols=6)
        b: str = Field('', ui_cols=6)

    rows = _render(Row).split('class="sf-grid"')[1:]

    assert len(rows) == 1
    assert 'name="token"' in rows[0]
    assert rows[0].count('class="sf-col sf-col-6"') == 2


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_a_group_gathers_its_fields_at_its_first_position(framework):
    rendered = _render(framework=framework)

    assert 'Location' in rendered
    assert rendered.index('Location') < rendered.index('name="street"')
    assert rendered.index('name="unit"') < rendered.index('name="plain"')


def test_a_group_works_inside_a_sub_form_and_data_stays_flat():
    rendered = _render()

    assert 'Inner group' in rendered
    assert 'name="address.note"' in rendered
    assert 'data' not in Form.validate({'first': 'a', 'street': 'b'}).data
    assert Form.validate({'street': 'b'}).data['street'] == 'b'


def test_titles_are_escaped():
    class Odd(FormModel):
        a: str = Field('', ui_group=XSS)
        b: str = Field('', ui_group=f'{XSS}2', ui_group_collapsible=True)

    assert XSS not in _render(Odd)


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_collapsible_group_opens_on_an_error(framework):
    class Fold(FormModel):
        a: str = Field('', title='A', min_length=2, ui_group='Fold', ui_group_collapsible=True)
        b: str = Field('', title='B', ui_group='Fold', ui_group_collapsed=True)

    closed = _render(Fold, framework=framework)
    errored = _render(Fold, framework=framework, errors={'a': 'Too short'})

    assert '<details' in closed
    assert ' open' not in closed.split('<details')[1].split('>')[0]
    assert ' open' in errored.split('<details')[1].split('>')[0]


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', sorted(LAYOUTS))
def test_every_layout_shows_every_field(framework, layout):
    rendered = _render(framework=framework, layout=layout)

    for name in ('first', 'street', 'unit', 'extra', 'address.city'):
        assert f'name="{name}"' in rendered
    assert 'sf-col-8' in rendered


@pytest.mark.parametrize('layout', ['tabbed', 'accordion', 'wizard'])
def test_a_group_is_its_own_tab_panel_or_step(layout):
    class Flat(FormModel):
        a: str = Field('', title='A', ui_group='One')
        b: str = Field('', title='B', ui_group='Two')

    rendered = _render(Flat, layout=layout)

    assert rendered.index('One') < rendered.index('name="a"') < rendered.index('name="b"')
    assert rendered.index('Two') < rendered.index('name="b"')
    assert 'General' not in rendered


def test_a_group_alone_is_enough_for_a_grouped_layout():
    class Bare(FormModel):
        a: str = Field('')

    with pytest.raises(ValueError, match='ui_group'):
        _render(Bare, layout='tabbed')


def test_a_sub_form_can_join_a_group():
    class Joined(FormModel):
        a: str = Field('', title='A', ui_group='Both')
        address: Address = Field(default_factory=Address, title='Address', ui_group='Both')

    rendered = _render(Joined, layout='tabbed')

    assert 'name="address.city"' in rendered
    assert rendered.index('name="a"') < rendered.index('name="address.city"')


class Hidden(FormModel):
    on: bool = Field(False, title='On')
    a: str = Field(
        'stays-default', title='A', ui_group='G', ui_group_show_when={'field': 'on', 'truthy': True}
    )
    b: str = Field('', title='B', ui_group='G')
    c: str = Field(
        '',
        title='C',
        ui_group='G',
        ui_show_when={'field': 'b', 'not_empty': True, 'required': True},
    )


def test_group_rule_hides_heading_and_fields():
    rendered = _render(Hidden)
    wrapper = rendered[rendered.index('<fieldset class="sf-show-when"') :]

    assert wrapper.split('>')[0].endswith('hidden disabled')
    assert '>G<' in wrapper.split('</fieldset>')[0]


def test_group_rule_drops_every_field_on_the_server():
    result = Hidden.validate({'a': 'smuggled', 'b': 'smuggled'})

    assert result.is_valid, result.errors
    assert result.data['a'] == 'stays-default'
    assert result.data['b'] == ''


def test_a_shown_group_keeps_values_and_its_fields_own_rules():
    shown = Hidden.validate({'on': True, 'a': 'x', 'b': 'y'})

    assert shown.errors == {'c': 'Field required'}
    assert Hidden.validate({'on': True, 'a': 'x', 'b': ''}).data['a'] == 'x'


def test_a_group_rule_can_be_declared_on_any_field():
    class Later(FormModel):
        on: bool = Field(False)
        a: str = Field('', ui_group='G')
        b: str = Field('', ui_group='G', ui_group_show_when={'field': 'on', 'truthy': True})

    assert Later.validate({'a': 'smuggled'}).data['a'] == ''


def test_a_required_field_in_a_ruled_group_is_reported():
    class Bad(FormModel):
        on: bool = Field(False)
        a: str = Field(title='A', ui_group='G', ui_group_show_when={'field': 'on', 'truthy': True})

    with pytest.raises(ValueError, match='need a default'):
        _render(Bad)


def test_conflicting_group_rules_are_reported():
    class Bad(FormModel):
        on: bool = Field(False)
        a: str = Field('', ui_group='G', ui_group_show_when={'field': 'on', 'truthy': True})
        b: str = Field('', ui_group='G', ui_group_show_when={'field': 'on', 'truthy': False})

    with pytest.raises(ValueError, match='more than one'):
        _render(Bad)


@pytest.mark.parametrize('layout', ['tabbed', 'accordion', 'wizard', 'side-by-side'])
def test_group_rule_under_grouped_layouts(layout):
    rendered = _render(Hidden, layout=layout)

    assert 'data-show-when-target="on"' in rendered
    assert 'hidden disabled' in rendered


def test_group_rule_inside_a_sub_form():
    class Parent(FormModel):
        child: Hidden = Field(default_factory=Hidden, title='Child')

    assert 'data-show-when-target="child.on"' in _render(Parent)
    assert Parent.validate({'child': {'a': 'smuggled'}}).data['child']['a'] == 'stays-default'


def test_model_list_items_ignore_groups_and_widths():
    class Item(FormModel):
        a: str = Field('', title='A', ui_group='Ignored', ui_cols=6)

    class Parent(FormModel):
        items: list[Item] = Field(default_factory=list, title='Items')

    rendered = _render(Parent)

    assert 'Ignored' not in rendered
    assert 'sf-col-6' not in rendered


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_display_mode_shows_groups_as_sections_without_widths(framework):
    rendered = str(
        Form.render_display({'first': 'Ada', 'street': 'Main', 'unit': '4'}, framework=framework)
    )

    assert 'Location' in rendered
    assert rendered.index('Location') < rendered.index('Main')
    assert 'sf-col' not in rendered
    assert 'sf-grid' not in rendered


@pytest.mark.parametrize('layout', ['tabbed', 'accordion', 'side-by-side', 'wizard'])
def test_display_mode_under_grouped_layouts(layout):
    rendered = str(Form.render_display({'street': 'Main', 'first': 'Ada'}, layout=layout))

    assert rendered.count('Location') >= 1
    assert 'Main' in rendered
    assert 'Ada' in rendered


def test_display_mode_leaves_a_hidden_group_out():
    data = {'on': False, 'a': 'stale', 'b': 'stale'}

    for layout in ('vertical', 'tabbed'):
        rendered = str(Hidden.render_display(data, layout=layout))
        assert 'stale' not in rendered
        assert '>G<' not in rendered
    assert 'stale' in str(Hidden.render_display({'on': True, 'a': 'stale'}))
