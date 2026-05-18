"""Coverage tests for FormTemplates, form_style templates, and layout_base branches.

These tests exercise rendering paths that are not covered by integration-level
tests — primarily the Bootstrap/utility FormTemplates that no renderer currently
calls, the Plain/Material form-style templates, and the callable/BaseLayout
content branches in layout_base.BaseLayout.
"""

from __future__ import annotations

import pytest

from pydantic_schemaforms.layout_base import BaseLayout
from pydantic_schemaforms.rendering.form_style import (
    BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE,
    BOOTSTRAP_ACCORDION_SECTION_TEMPLATE,
    DEFAULT_FIELD_ERROR_TEMPLATE,
    DEFAULT_FIELD_HELP_TEMPLATE,
    MATERIAL_ACCORDION_LAYOUT_TEMPLATE,
    MATERIAL_ACCORDION_SECTION_TEMPLATE,
    MATERIAL_FIELD_ERROR_TEMPLATE,
    MATERIAL_FIELD_HELP_TEMPLATE,
    MATERIAL_LAYOUT_HELP_TEMPLATE,
    MATERIAL_LAYOUT_SECTION_TEMPLATE,
    MATERIAL_MODEL_LIST_ERROR_TEMPLATE,
    MATERIAL_MODEL_LIST_HELP_TEMPLATE,
    MATERIAL_SUBMIT_BUTTON_TEMPLATE,
    PLAIN_ACCORDION_LAYOUT_TEMPLATE,
    PLAIN_FIELD_ERROR_TEMPLATE,
    PLAIN_FIELD_HELP_TEMPLATE,
    PLAIN_LAYOUT_HELP_TEMPLATE,
    PLAIN_LAYOUT_SECTION_TEMPLATE,
    PLAIN_MODEL_LIST_CONTAINER_TEMPLATE,
    PLAIN_MODEL_LIST_ERROR_TEMPLATE,
    PLAIN_MODEL_LIST_HELP_TEMPLATE,
    PLAIN_MODEL_LIST_ITEM_TEMPLATE,
    PLAIN_TAB_LAYOUT_TEMPLATE,
    FormStyle,
    FormStyleTemplates,
    get_form_style,
    register_form_style,
)
from pydantic_schemaforms.templates import FormTemplates
from pydantic_schemaforms.tstring import SafeHTML


# ---------------------------------------------------------------------------
# FormTemplates — Bootstrap / utility input templates
# ---------------------------------------------------------------------------


class TestFormTemplatesInputs:
    """Exercise the bootstrap-style input render functions."""

    def test_text_input(self):
        out = FormTemplates.TEXT_INPUT.render(
            id='username', name='username', value='alice', placeholder='Enter name'
        )
        assert isinstance(out, SafeHTML)
        assert 'type="text"' in out
        assert 'id="username"' in out
        assert 'alice' in out
        assert 'Enter name' in out

    def test_text_input_xss_escaping(self):
        out = FormTemplates.TEXT_INPUT.render(name='f', id='f', value='<script>x</script>')
        assert '&lt;script&gt;' in out
        assert '<script>' not in out

    def test_email_input(self):
        out = FormTemplates.EMAIL_INPUT.render(id='email', name='email', value='a@b.com')
        assert isinstance(out, SafeHTML)
        assert 'type="email"' in out
        assert 'a@b.com' in out

    def test_password_input(self):
        out = FormTemplates.PASSWORD_INPUT.render(id='pw', name='pw')
        assert isinstance(out, SafeHTML)
        assert 'type="password"' in out
        assert 'togglePassword' in out

    def test_number_input(self):
        out = FormTemplates.NUMBER_INPUT.render(
            id='age', name='age', value='25', min_value='0', max_value='120', step='1'
        )
        assert isinstance(out, SafeHTML)
        assert 'type="number"' in out
        assert 'min="0"' in out
        assert 'max="120"' in out

    def test_select_input(self):
        options_html = SafeHTML('<option value="a">A</option><option value="b">B</option>')
        out = FormTemplates.SELECT_INPUT.render(id='pick', name='pick', options=str(options_html))
        assert isinstance(out, SafeHTML)
        assert '<select' in out
        assert '<option value="a">' in out

    def test_textarea_input(self):
        out = FormTemplates.TEXTAREA_INPUT.render(
            id='bio', name='bio', value='Hello', rows='4', cols='40'
        )
        assert isinstance(out, SafeHTML)
        assert '<textarea' in out
        assert 'rows="4"' in out
        assert 'Hello' in out

    def test_checkbox_input(self):
        out = FormTemplates.CHECKBOX_INPUT.render(
            id='agree', name='agree', checkbox_value='1', label_text='I agree'
        )
        assert isinstance(out, SafeHTML)
        assert 'type="checkbox"' in out
        assert 'I agree' in out

    def test_radio_input(self):
        opts = SafeHTML('<label><input type="radio" value="y"> Yes</label>')
        out = FormTemplates.RADIO_INPUT.render(radio_options=str(opts))
        assert isinstance(out, SafeHTML)
        assert 'radio-group' in out


class TestFormTemplatesLayout:
    """Exercise layout and helper templates."""

    def test_vertical_layout(self):
        out = FormTemplates.VERTICAL_LAYOUT.render(
            sections=str(SafeHTML('<div>field1</div>')), layout_class='my-vl'
        )
        assert isinstance(out, SafeHTML)
        assert 'vertical-layout' in out
        assert 'field1' in out

    def test_horizontal_layout(self):
        out = FormTemplates.HORIZONTAL_LAYOUT.render(
            sections=str(SafeHTML('<div>f</div>')), layout_class='my-hl'
        )
        assert isinstance(out, SafeHTML)
        assert 'horizontal-layout' in out
        assert 'f' in out

    def test_section(self):
        content_html = SafeHTML('<input name="x">')
        title_html = SafeHTML('<h4>Details</h4>')
        out = FormTemplates.SECTION.render(
            section_content=str(content_html), section_title=str(title_html)
        )
        assert isinstance(out, SafeHTML)
        assert 'form-section' in out
        assert '<h4>Details</h4>' in out

    def test_label(self):
        out = FormTemplates.LABEL.render(for_id='field', label_text='My Label')
        assert isinstance(out, SafeHTML)
        assert 'for="field"' in out
        assert 'My Label' in out

    def test_label_xss(self):
        out = FormTemplates.LABEL.render(for_id='f', label_text='<b>bold</b>')
        assert '&lt;b&gt;' in out

    def test_help_text(self):
        out = FormTemplates.HELP_TEXT.render(help_content='Enter your full name')
        assert isinstance(out, SafeHTML)
        assert 'Enter your full name' in out

    def test_error_message(self):
        out = FormTemplates.ERROR_MESSAGE.render(error_content='This field is required')
        assert isinstance(out, SafeHTML)
        assert 'invalid-feedback' in out
        assert 'This field is required' in out

    def test_icon(self):
        out = FormTemplates.ICON.render(icon_name='envelope', icon_class='text-muted')
        assert isinstance(out, SafeHTML)
        assert 'bi-envelope' in out
        assert 'text-muted' in out

    def test_input_group(self):
        prepend = SafeHTML('<span class="input-group-text">@</span>')
        inp = SafeHTML('<input type="text" name="handle">')
        out = FormTemplates.INPUT_GROUP.render(
            prepend=str(prepend), input_element=str(inp), append=''
        )
        assert isinstance(out, SafeHTML)
        assert 'input-group' in out
        assert 'input-group-text' in out

    def test_form_page(self):
        out = FormTemplates.FORM_PAGE.render(
            page_title='My Form',
            form_content=str(SafeHTML('<form action="/submit"></form>')),
        )
        assert isinstance(out, SafeHTML)
        assert '<!DOCTYPE html>' in out
        assert 'My Form' in out
        assert '<form action="/submit">' in out


class TestFormTemplatesMaterial:
    """Exercise the uncovered material-specific FormTemplates."""

    def test_material_icon(self):
        out = FormTemplates.MATERIAL_ICON.render(icon_name='home')
        assert isinstance(out, SafeHTML)
        assert 'material-icons' in out
        assert 'home' in out

    def test_material_submit_button(self):
        out = FormTemplates.MATERIAL_SUBMIT_BUTTON.render(label='Send')
        assert isinstance(out, SafeHTML)
        assert 'md-button' in out
        assert 'Send' in out


# ---------------------------------------------------------------------------
# form_style.py — Plain and Material template functions
# ---------------------------------------------------------------------------


class TestDefaultFormStyleTemplates:
    """DEFAULT_* templates that route through FormStyleTemplates.field_help/error."""

    def test_default_field_help(self):
        out = DEFAULT_FIELD_HELP_TEMPLATE.render(help_text='Helpful hint')
        assert isinstance(out, SafeHTML)
        assert 'field-help' in out
        assert 'Helpful hint' in out

    def test_default_field_help_xss(self):
        out = DEFAULT_FIELD_HELP_TEMPLATE.render(help_text='<script>x</script>')
        assert '&lt;script&gt;' in out

    def test_default_field_error(self):
        out = DEFAULT_FIELD_ERROR_TEMPLATE.render(error_text='Required')
        assert isinstance(out, SafeHTML)
        assert 'field-error' in out
        assert 'Required' in out


class TestPlainFormStyleTemplates:
    """Plain-framework template functions."""

    def test_plain_layout_section(self):
        body = SafeHTML('<p>Content</p>')
        out = PLAIN_LAYOUT_SECTION_TEMPLATE.render(title='My Section', body_html=str(body))
        assert isinstance(out, SafeHTML)
        assert 'layout-field-section' in out
        assert 'My Section' in out
        assert '<p>Content</p>' in out

    def test_plain_layout_help(self):
        out = PLAIN_LAYOUT_HELP_TEMPLATE.render(help_text='A note')
        assert isinstance(out, SafeHTML)
        assert 'layout-field-help' in out
        assert 'A note' in out

    def test_plain_model_list_container(self):
        items = SafeHTML('<div>item</div>')
        out = PLAIN_MODEL_LIST_CONTAINER_TEMPLATE.render(
            field_name='pets',
            items_html=str(items),
            items_id='pets-items',
            min_items='0',
            max_items='5',
        )
        assert isinstance(out, SafeHTML)
        assert 'model-list-block' in out
        assert 'add-item-btn' in out

    def test_plain_model_list_item(self):
        body = SafeHTML('<input name="pet.name">')
        out = PLAIN_MODEL_LIST_ITEM_TEMPLATE.render(
            index='0',
            field_name='pets',
            model_label='Pet',
            display_index='1',
            remove_button_aria_label='Remove pet 1',
            body_html=str(body),
        )
        assert isinstance(out, SafeHTML)
        assert 'model-list-item' in out
        assert 'remove-item-btn' in out

    def test_plain_model_list_help(self):
        out = PLAIN_MODEL_LIST_HELP_TEMPLATE.render(help_text='Add items')
        assert isinstance(out, SafeHTML)
        assert 'model-list-help' in out
        assert 'Add items' in out

    def test_plain_model_list_error(self):
        out = PLAIN_MODEL_LIST_ERROR_TEMPLATE.render(error_text='Minimum 1 required')
        assert isinstance(out, SafeHTML)
        assert 'model-list-error' in out

    def test_plain_field_help(self):
        out = PLAIN_FIELD_HELP_TEMPLATE.render(help_text='Plain hint')
        assert isinstance(out, SafeHTML)
        assert 'field-help' in out
        assert 'Plain hint' in out

    def test_plain_field_error(self):
        out = PLAIN_FIELD_ERROR_TEMPLATE.render(error_text='Plain error')
        assert isinstance(out, SafeHTML)
        assert 'field-error' in out

    def test_plain_tab_layout(self):
        btns = SafeHTML('<button role="tab">Tab 1</button>')
        panels = SafeHTML('<div role="tabpanel">Panel 1</div>')
        out = PLAIN_TAB_LAYOUT_TEMPLATE.render(tab_buttons=str(btns), tab_panels=str(panels))
        assert isinstance(out, SafeHTML)
        assert 'tab-layout' in out
        assert 'Tab 1' in out

    def test_plain_accordion_layout(self):
        secs = SafeHTML('<details><summary>Q</summary>A</details>')
        out = PLAIN_ACCORDION_LAYOUT_TEMPLATE.render(sections=str(secs))
        assert isinstance(out, SafeHTML)
        assert 'accordion-layout' in out


class TestMaterialFormStyleTemplates:
    """Material-framework template functions."""

    def test_material_layout_section(self):
        body = SafeHTML('<p>Body</p>')
        out = MATERIAL_LAYOUT_SECTION_TEMPLATE.render(title='Card', body_html=str(body))
        assert isinstance(out, SafeHTML)
        assert 'md-layout-card' in out
        assert 'Card' in out

    def test_material_layout_help(self):
        out = MATERIAL_LAYOUT_HELP_TEMPLATE.render(help_text='MD help')
        assert isinstance(out, SafeHTML)
        assert 'md-layout-card__help' in out
        assert 'MD help' in out

    def test_material_model_list_help(self):
        out = MATERIAL_MODEL_LIST_HELP_TEMPLATE.render(help_text='Add rows')
        assert isinstance(out, SafeHTML)
        assert 'md-help-text' in out

    def test_material_model_list_error(self):
        out = MATERIAL_MODEL_LIST_ERROR_TEMPLATE.render(error_text='Too many')
        assert isinstance(out, SafeHTML)
        assert 'md-error-text' in out

    def test_material_field_help(self):
        out = MATERIAL_FIELD_HELP_TEMPLATE.render(help_text='MD field hint')
        assert isinstance(out, SafeHTML)
        assert 'md-field-help-text' in out

    def test_material_field_error(self):
        out = MATERIAL_FIELD_ERROR_TEMPLATE.render(error_text='MD field error')
        assert isinstance(out, SafeHTML)
        assert 'md-field-error-text' in out

    def test_material_submit_button(self):
        out = MATERIAL_SUBMIT_BUTTON_TEMPLATE.render(submit_label='Go')
        assert isinstance(out, SafeHTML)
        assert 'md-button-filled' in out
        assert 'Go' in out


class TestBootstrapAccordionTemplates:
    """Bootstrap accordion templates not covered by layout engine tests."""

    def test_bootstrap_accordion_layout(self):
        sections = SafeHTML('<div class="accordion-item">item</div>')
        out = BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE.render(
            layout_id='acc1', sections=str(sections)
        )
        assert isinstance(out, SafeHTML)
        assert 'accordion' in out
        assert 'accordion-item' in out

    def test_bootstrap_accordion_section(self):
        content = SafeHTML('<p>Answer</p>')
        out = BOOTSTRAP_ACCORDION_SECTION_TEMPLATE.render(
            section_id='q1',
            title='Question',
            content=str(content),
            aria_expanded='false',
        )
        assert isinstance(out, SafeHTML)
        assert 'accordion-item' in out
        assert 'Question' in out
        assert '<p>Answer</p>' in out

    def test_material_accordion_layout(self):
        secs = SafeHTML('<div class="md-accordion-section">s</div>')
        out = MATERIAL_ACCORDION_LAYOUT_TEMPLATE.render(sections=str(secs))
        assert isinstance(out, SafeHTML)
        assert 'md-accordion-layout' in out

    def test_material_accordion_section(self):
        content = SafeHTML('<p>MD Answer</p>')
        out = MATERIAL_ACCORDION_SECTION_TEMPLATE.render(
            section_id='mq1',
            title='MD Question',
            content=str(content),
        )
        assert isinstance(out, SafeHTML)
        assert 'md-accordion' in out
        assert 'MD Question' in out


class TestGetFormStyleBranches:
    """Exercise the fallback branches in get_form_style."""

    def test_explicit_variant_passed(self):
        # Hits _parse_framework_variant line: return framework, variant
        style = get_form_style('bootstrap', variant='default')
        assert style.framework == 'bootstrap'

    def test_colon_descriptor_syntax(self):
        # Hits _parse_framework_variant line: return base, version
        style = get_form_style('bootstrap:5')
        assert style.framework == 'bootstrap'

    def test_no_variant_no_colon(self):
        # Hits _parse_framework_variant line: return framework, 'default'
        style = get_form_style('plain')
        assert style is not None

    def test_base_framework_fallback(self):
        # Register only 'default' variant, request a specific variant that isn't
        # registered — hits: return _FORM_STYLE_REGISTRY[base_key]
        register_form_style(FormStyle(framework='test-fw-fallback', variant='default',
                                      templates=FormStyleTemplates()))
        style = get_form_style('test-fw-fallback:99')
        assert style.framework == 'test-fw-fallback'

    def test_global_default_fallback(self):
        # Unknown framework falls through to ('default', 'default') built-in.
        # Hits: return _FORM_STYLE_REGISTRY[fallback]
        style = get_form_style('completely-unknown-framework-xyz')
        assert style is not None


# ---------------------------------------------------------------------------
# layout_base.BaseLayout — uncovered content-type branches
# ---------------------------------------------------------------------------


class TestBaseLayoutContentBranches:
    """Cover the content=None, callable, and BaseLayout branches."""

    def test_none_content_renders_empty(self):
        layout = BaseLayout(content=None)
        result = layout.render()
        assert isinstance(result, str)
        assert result == '' or '<div' in result  # template wraps with div but content empty

    def test_callable_content(self):
        def _make_content(data, errors, renderer, framework):
            return f'<p>{framework}</p>'

        layout = BaseLayout(_make_content)
        result = layout.render(framework='bootstrap')
        assert '<p>bootstrap</p>' in result

    def test_baselayout_content(self):
        inner = BaseLayout('inner text')
        outer = BaseLayout(inner)
        result = outer.render()
        assert 'inner text' in result

    def test_list_with_baselayout_items(self):
        a = BaseLayout('item-a')
        b = BaseLayout('item-b')
        layout = BaseLayout([a, b])
        result = layout.render()
        assert 'item-a' in result
        assert 'item-b' in result
