"""Comprehensive tests for field_renderer.py to increase coverage."""

from __future__ import annotations

import pytest
from pydantic_schemaforms.rendering.field_renderer import FieldRenderer
from pydantic_schemaforms.rendering.context import RenderContext
from unittest.mock import Mock, patch


class TestFieldRendererBasicSetup:
    """Test FieldRenderer initialization and basic properties."""

    def test_field_renderer_init(self):
        """Test FieldRenderer initialization."""
        renderer = Mock()
        renderer.config = {'framework': 'bootstrap'}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        assert field_renderer._renderer == renderer
        assert field_renderer.config == {'framework': 'bootstrap'}
        assert field_renderer.framework == 'bootstrap'

    def test_field_renderer_theme_property(self):
        """Test FieldRenderer theme property."""
        renderer = Mock()
        renderer.theme = {'primary_color': 'blue'}

        field_renderer = FieldRenderer(renderer)
        assert field_renderer.theme == {'primary_color': 'blue'}

    def test_field_renderer_theme_none(self):
        """Test FieldRenderer theme property when not set."""
        renderer = Mock(spec=[])
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        assert field_renderer.theme is None


class TestFieldRendererHiddenFields:
    """Test rendering of hidden fields."""

    def test_render_hidden_field(self):
        """Test rendering of hidden input fields."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='hidden_id',
            field_schema={'ui': {'hidden': True}, 'type': 'string'},
            value='123',
            context=context,
        )

        assert 'hidden' in result.lower()
        assert '123' in result

    def test_render_field_with_hidden_ui_config(self):
        """Test rendering field marked as hidden in UI config."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='secret',
            field_schema={'type': 'string', 'ui': {'hidden': True}},
            value='secret_value',
            context=context,
        )

        assert 'hidden' in result.lower()
        assert 'secret_value' in result


class TestFieldRendererUIElementDetection:
    """Test UI element type detection and configuration."""

    def test_render_field_with_explicit_element(self):
        """Test rendering field with explicit UI element specified."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer._render_layout_field = Mock(return_value='<div>layout</div>')

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='custom',
            field_schema={'type': 'string', 'ui': {'element': 'text'}},
            value='test',
            context=context,
        )

        assert 'name="custom"' in result

    def test_render_field_detects_layout_element(self):
        """Test field renderer detects layout element type."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer._render_layout_field = Mock(return_value='<div>layout content</div>')

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        field_renderer.render_field(
            field_name='layout_field',
            field_schema={'type': 'object', 'ui': {'element': 'layout'}},
            context=context,
        )

        renderer._render_layout_field.assert_called_once()

    def test_render_field_detects_model_list_element(self):
        """Test field renderer detects model_list element type."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer._render_model_list_field = Mock(return_value='<ul>list</ul>')

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        with patch.object(field_renderer, '_render_model_list_field', return_value='<ul>list</ul>'):
            field_renderer.render_field(
                field_name='model_list',
                field_schema={'type': 'array', 'ui': {'element': 'model_list'}},
                context=context,
            )


class TestFieldRendererCheckboxHandling:
    """Test checkbox-specific field rendering."""

    def test_render_checkbox_with_true_value(self):
        """Test rendering checkbox with true value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='agree',
            field_schema={'type': 'boolean'},
            value=True,
            context=context,
            layout='vertical',
        )

        assert 'checkbox' in result.lower() or 'checked' in result.lower()

    def test_render_checkbox_with_string_true_value(self):
        """Test rendering checkbox with string 'true' value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='active',
            field_schema={'type': 'boolean'},
            value='true',
            context=context,
            layout='vertical',
        )

        assert 'checked' in result

    def test_render_checkbox_with_numeric_true_value(self):
        """Test rendering checkbox with numeric true value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='enabled',
            field_schema={'type': 'boolean'},
            value='1',
            context=context,
            layout='vertical',
        )

        assert 'checked' in result

    def test_render_checkbox_with_on_value(self):
        """Test rendering checkbox with 'on' value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='switch',
            field_schema={'type': 'boolean'},
            value='on',
            context=context,
            layout='vertical',
        )

        assert 'checked' in result

    def test_render_toggle_gets_same_checked_value_handling_as_checkbox(self):
        """Regression test: ui_element='toggle' must be treated as checkbox-family.

        Previously only ui_element == 'checkbox' got the True/on/'1' -> checked
        handling; a `toggle` field's raw Python bool `value` fell through to
        `field_attrs['value'] = value` and got mangled by _format_attribute_value
        (which treats any bool as an HTML presence-attribute), producing
        `value="value"` and never setting `checked` at all.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _ToggleModel(FormModel):
            switched: bool = Field(True, title='Switched', ui_element='toggle')

        html = render_form_html(
            _ToggleModel, submit_url='/x', framework='bootstrap', form_data={'switched': True}
        )
        assert 'value="value"' not in html
        assert 'checked="checked"' in html
        assert 'value="1"' in html
        assert 'type="checkbox"' in html

    def test_render_toggle_under_material_framework_uses_switch_template(self):
        """Regression test: Material's separate rendering pipeline (enhanced_renderer
        ._render_material_field) only special-cased input_type == 'checkbox'; a
        'toggle' field fell through to the generic outlined-text-field renderer,
        producing invalid markup like `<input type="toggle" ... value="True">`
        styled as a Material text field. It now renders via a dedicated
        Material switch template (md-toggle-*), not the plain checkbox one.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _ToggleModel(FormModel):
            switched: bool = Field(True, title='Switched', ui_element='toggle')

        html = render_form_html(
            _ToggleModel, submit_url='/x', framework='material', form_data={'switched': True}
        )
        assert 'type="toggle"' not in html
        assert 'md-toggle-wrapper' in html
        assert 'md-toggle-slider' in html
        assert 'type="checkbox"' in html
        assert 'checked="checked"' in html

    def test_radio_and_checkbox_group_get_checkbox_class_not_select_class(self):
        """Regression test: 'radio' and 'checkbox_group' used to be grouped with
        'select'/'multiselect' for CSS class purposes (field_renderer.py's
        _get_input_class and themes.py's RendererTheme.input_class), so their
        individual <input>s got Bootstrap's select_class (form-select, which
        paints a dropdown chevron) instead of checkbox_class (form-check-input)
        -- radio buttons rendered looking like broken dropdown arrows. Fixing
        that also required NOT propagating the (now correct) per-item class
        onto the <fieldset> itself, since form-check-input is sized 1em x 1em
        and collapses a fieldset's box if applied there (see the CheckboxGroup/
        RadioGroup tests in test_inputs.py for that half of the fix).
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _GroupModel(FormModel):
            plan: str = Field(
                'medium',
                title='Plan',
                ui_element='radio',
                ui_options={'choices': ['small', 'medium']},
            )
            channels: list[str] = Field(
                default_factory=list,
                title='Channels',
                ui_element='checkbox_group',
                ui_options={'choices': ['email', 'sms']},
            )

        html = render_form_html(_GroupModel, submit_url='/x', framework='bootstrap')

        radio_start = html.find('<input name="plan"')
        radio_tag = html[radio_start : html.find('/>', radio_start) + 2]
        assert 'form-check-input' in radio_tag
        assert 'form-select' not in radio_tag

        checkbox_start = html.find('<input name="channels"')
        checkbox_tag = html[checkbox_start : html.find('/>', checkbox_start) + 2]
        assert 'form-check-input' in checkbox_tag
        assert 'form-control' not in checkbox_tag

        # Neither fieldset should have the per-item class, or its box collapses.
        assert '<fieldset class="radio-group">' in html
        assert '<fieldset class="checkbox-group">' in html

    def test_material_falls_back_to_shared_registry_for_widgets_it_has_no_template_for(self):
        """Regression test: enhanced_renderer.py's Material dispatch (_render_material_field)
        has no widget-class registry of its own -- only a small hardcoded set of
        native HTML5-ish types plus checkbox/toggle/textarea/select have bespoke
        templates. Everything else (radio, checkbox_group, multiselect, rating,
        star_rating, slider, quantity's stepper, phone's mask, ...) used to fall
        through to _render_material_outlined_field, which just does
        html.escape(str(value)) into a plain text box -- for list-valued fields
        (checkbox_group/multiselect) that showed the raw Python repr
        (e.g. "['email', 'push']") as literal text, and radio/select-like widgets
        lost the ability to pick a different option entirely. These now delegate
        to the same widget-registry rendering Bootstrap uses instead.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _MaterialFallbackModel(FormModel):
            channels: list[str] = Field(
                default_factory=lambda: ['email'],
                title='Channels',
                ui_element='checkbox_group',
                ui_options={'choices': ['email', 'sms']},
            )
            plan: str = Field(
                'small',
                title='Plan',
                ui_element='radio',
                ui_options={'choices': ['small', 'large']},
            )
            quantity: int = Field(1, title='Quantity', ui_element='quantity')

        html = render_form_html(
            _MaterialFallbackModel,
            submit_url='/x',
            framework='material',
            form_data={'channels': ['email', 'sms']},
        )

        # The old bug: raw Python list repr leaking into the page as text.
        assert '&#x27;email&#x27;' not in html
        assert "['email'" not in html

        assert 'checkbox-item' in html
        assert 'type="radio"' in html
        assert 'number-stepper' in html  # quantity's +/- stepper, Material has no template for it

    def test_radio_and_checkbox_group_do_not_duplicate_their_label(self):
        """Regression test: field_renderer.py used to pass the field's title as
        both the fieldset's <legend> AND an outer <label> pointing at the same
        field -- redundant under any framework, and under Material's floating
        -label CSS the duplicate outer label sat absolutely positioned right on
        top of the fieldset, visually overlapping the legend and every option.
        The fieldset's own <legend> is the group's accessible label; no outer
        <label> should be emitted alongside it.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _GroupLabelModel(FormModel):
            plan: str = Field(
                'small',
                title='Pick a plan',
                ui_element='radio',
                ui_options={'choices': ['small', 'large']},
            )
            channels: list[str] = Field(
                default_factory=lambda: ['email'],
                title='Notify via',
                ui_element='checkbox_group',
                ui_options={'choices': ['email', 'sms']},
            )

        for framework in ('bootstrap', 'material'):
            html = render_form_html(_GroupLabelModel, submit_url='/x', framework=framework)
            assert html.count('Pick a plan') == 1, framework
            assert html.count('Notify via') == 1, framework
            assert '<legend>Pick a plan</legend>' in html, framework
            assert '<legend>Notify via</legend>' in html, framework

    def test_checkbox_group_and_radio_collapsible_is_opt_in_across_frameworks(self):
        """ui_options={'collapsible': True} needs no field_renderer.py wiring --
        CheckboxGroup/RadioGroup.render() never call validate_attributes() on
        their whole kwargs blob (unlike SelectInput), so collapsible/collapsed
        simply bind as named render() params with no leak risk. Verified end-to-
        end here across both bootstrap and material, since neither has a
        bespoke Material template for these two ui_elements (see
        enhanced_renderer.py's comment listing radio/checkbox_group as sharing
        the generic FieldRenderer path)."""
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _Burger(FormModel):
            vegetables: list[str] = Field(
                default_factory=list,
                title='Vegetables',
                ui_element='checkbox_group',
                ui_options={
                    'choices': ['Lettuce', 'Pickle'],
                    'collapsible': True,
                    'collapsed': True,
                },
            )
            size: str = Field(
                'medium',
                title='Size',
                ui_element='radio',
                ui_options={'choices': ['small', 'medium', 'large']},
            )

        for framework in ('bootstrap', 'material'):
            html = render_form_html(_Burger, submit_url='/x', framework=framework)
            assert 'toggleCollapsibleGroup' in html, framework
            # vegetables: collapsible + collapsed -- starts closed.
            assert 'aria-expanded="false"' in html, framework
            assert 'style="display:none"' in html, framework
            # size: no collapsible ui_option -- unaffected, plain <legend>.
            assert '<legend>Size</legend>' in html, framework

    def test_material_select_renders_choices_from_ui_options_dict(self):
        """Regression test: _build_material_select_options only handled a raw
        options list (or an enum fallback) -- ui_options={'choices': [...]}
        (the documented way to declare select options) lands in ui_info as a
        dict, and iterating a dict directly yields its key names, not its
        values. That rendered a single bogus '<option value="choices">
        choices</option>' instead of the real choices.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _SelectChoicesModel(FormModel):
            size: str = Field(
                'medium',
                title='Size',
                ui_element='select',
                ui_options={'choices': ['small', 'medium', 'large']},
            )

        html = render_form_html(
            _SelectChoicesModel,
            submit_url='/x',
            framework='material',
            form_data={'size': 'medium'},
        )
        assert '<option value="choices">choices</option>' not in html
        assert '<option value="small">small</option>' in html
        assert '<option value="medium" selected="selected">medium</option>' in html
        assert '<option value="large">large</option>' in html

    def test_bootstrap_select_placeholder_option_is_opt_in(self):
        """Bootstrap/generic-framework counterpart to the Material test below --
        same opt-in ui_options={'placeholder': ...} contract, routed through
        FieldRenderer/SelectInput instead of the Material-specific renderer."""
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _NoPlaceholder(FormModel):
            plan: str = Field(
                ..., title='Plan', ui_element='select', ui_options={'choices': ['free', 'pro']}
            )

        class _WithPlaceholder(FormModel):
            plan: str = Field(
                ...,
                title='Plan',
                ui_element='select',
                ui_options={'choices': ['free', 'pro'], 'placeholder': 'Choose a plan...'},
            )

        # Opt-in only: no `placeholder` configured -> byte-identical to today.
        no_placeholder_html = render_form_html(
            _NoPlaceholder, submit_url='/x', framework='bootstrap'
        )
        assert '<option value="">' not in no_placeholder_html
        assert 'placeholder=' not in no_placeholder_html

        unselected_html = render_form_html(_WithPlaceholder, submit_url='/x', framework='bootstrap')
        assert '<option value="" selected disabled>Choose a plan...</option>' in unselected_html
        # The leaked-attribute trap this feature fixes: no bogus placeholder="..." on <select>.
        assert 'placeholder="Choose a plan' not in unselected_html

        selected_html = render_form_html(
            _WithPlaceholder, submit_url='/x', framework='bootstrap', form_data={'plan': 'pro'}
        )
        assert '<option value="" disabled>Choose a plan...</option>' in selected_html
        assert '<option value="pro" selected>pro</option>' in selected_html

    def test_material_select_placeholder_option_is_opt_in(self):
        """Material's select used to always render an unconditional, empty-
        label, non-disabled blank first option regardless of configuration.
        It's now opt-in via ui_options={'placeholder': ...}, matching the
        generic/bootstrap select path -- see FieldRenderer._build_placeholder_option."""
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _NoPlaceholder(FormModel):
            plan: str = Field(
                ..., title='Plan', ui_element='select', ui_options={'choices': ['free', 'pro']}
            )

        class _WithPlaceholder(FormModel):
            plan: str = Field(
                ...,
                title='Plan',
                ui_element='select',
                ui_options={'choices': ['free', 'pro'], 'placeholder': 'Choose a plan...'},
            )

        no_placeholder_html = render_form_html(
            _NoPlaceholder, submit_url='/x', framework='material'
        )
        assert '<option value="">' not in no_placeholder_html

        unselected_html = render_form_html(_WithPlaceholder, submit_url='/x', framework='material')
        assert (
            '<option value="" selected="selected" disabled="disabled">Choose a plan...</option>'
            in unselected_html
        )

        selected_html = render_form_html(
            _WithPlaceholder, submit_url='/x', framework='material', form_data={'plan': 'pro'}
        )
        assert '<option value="" disabled="disabled">Choose a plan...</option>' in selected_html
        assert 'selected="selected">Choose a plan' not in selected_html
        assert '<option value="pro" selected="selected">pro</option>' in selected_html

    def test_material_text_input_applies_arbitrary_ui_options_attributes(self):
        """Regression test: _build_material_text_input_attributes only read a
        nested ui_options={'attributes': {...}} dict, while every other
        framework (Bootstrap, plain HTML) treats ui_options itself as a flat
        dict of extra HTML attributes (FieldRenderer._apply_ui_option_attributes).
        Live-validation wiring (hx-post/hx-trigger/data-validate-endpoint set
        via ui_options for HTMX) silently disappeared under Material only.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html

        class _HxEmailModel(FormModel):
            email: str = Field(
                '',
                title='Email',
                ui_element='email',
                ui_options={
                    'hx-post': '/validate/email',
                    'hx-trigger': 'blur',
                    'data-validate-endpoint': 'true',
                },
            )

        html = render_form_html(_HxEmailModel, submit_url='/x', framework='material')
        assert 'hx-post="/validate/email"' in html
        assert 'hx-trigger="blur"' in html
        assert 'data-validate-endpoint="true"' in html

    def test_material_multiselect_label_is_static_not_overlapping_floating_label(self):
        """Regression test: SelectInputBase.render_with_label's material branch
        rendered every label as an absolutely-positioned .md-floating-label,
        designed to pair with Material's own .md-select/.md-input classes and
        animate out of the way on focus/non-empty. Widgets Material has no
        bespoke template for (multiselect, combobox) reach this same method
        via the shared registry fallback, but their controls carry none of
        those classes, so the label never animated away -- it sat frozen on
        top of the control. Such labels should use the static .md-field-label
        style instead.
        """
        from pydantic_schemaforms import Field, FormModel, render_form_html
        from typing import List

        class _MultiSelectModel(FormModel):
            tags: List[str] = Field(
                default_factory=lambda: ['python'],
                title='Tags',
                ui_element='multiselect',
                ui_options={'choices': ['python', 'rust']},
            )

        html = render_form_html(_MultiSelectModel, submit_url='/x', framework='material')
        assert 'class="md-floating-label"' not in html
        assert '<label class="md-field-label" for="tags">Tags</label>' in html


class TestFieldRendererPasswordFields:
    """Test password field rendering."""

    def test_render_password_field(self):
        """Test rendering of password fields."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='password',
            field_schema={'type': 'string', 'ui': {'input_type': 'password'}},
            value='secret123',
            context=context,
            layout='vertical',
        )

        assert 'password' in result.lower()

    def test_render_password_field_no_value(self):
        """Test rendering of password field without value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='pwd',
            field_schema={'type': 'string', 'ui_element': 'password'},
            value=None,
            context=context,
            layout='vertical',
        )

        assert 'password' in result.lower()


class TestFieldRendererErrorHandling:
    """Test field error rendering."""

    def test_render_field_with_error(self):
        """Test rendering field with error message."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='email',
            field_schema={'type': 'string'},
            value='invalid',
            error='Invalid email format',
            context=context,
            layout='vertical',
        )

        assert 'Invalid email format' in result

    def test_render_field_with_all_errors_dict(self):
        """Test rendering field with all_errors dictionary."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        all_errors = {'field1': 'error1', 'field2': 'error2'}

        result = field_renderer.render_field(
            field_name='field1',
            field_schema={'type': 'string'},
            value='test',
            all_errors=all_errors,
            context=context,
            layout='vertical',
        )

        assert 'name="field1"' in result


class TestFieldRendererRequiredFields:
    """Test required field handling."""

    def test_render_required_field(self):
        """Test rendering required field."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        required_fields = ['username', 'email']

        result = field_renderer.render_field(
            field_name='username',
            field_schema={'type': 'string'},
            value='john',
            required_fields=required_fields,
            context=context,
            layout='vertical',
        )

        assert 'required' in result.lower()

    def test_render_optional_field(self):
        """Test rendering optional field."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        required_fields = ['username']

        result = field_renderer.render_field(
            field_name='optional_field',
            field_schema={'type': 'string'},
            value='data',
            required_fields=required_fields,
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)


class TestFieldRendererInputInference:
    """Test input type inference from schema."""

    def test_infer_ui_element_from_schema(self):
        """Test UI element inference from schema."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        # Test with email type
        result = field_renderer.render_field(
            field_name='email',
            field_schema={'type': 'string', 'format': 'email'},
            context=context,
            layout='vertical',
        )

        assert 'email' in result.lower()

    def test_infer_textarea_for_long_string(self):
        """Test textarea inference for long text."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='description',
            field_schema={'type': 'string', 'description': 'A long text field'},
            value='long text content',
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)


class TestFieldRendererContextRequirement:
    """Test that RenderContext is required."""

    def test_render_field_without_context_raises(self):
        """Test that rendering without context raises error."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)

        with pytest.raises(ValueError, match='RenderContext is required'):
            field_renderer.render_field(
                field_name='test', field_schema={'type': 'string'}, value='test', context=None
            )


class TestFieldRendererLayoutOptions:
    """Test field rendering with different layout options."""

    def test_render_field_vertical_layout(self):
        """Test rendering field with vertical layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='field',
            field_schema={'type': 'string'},
            value='test',
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)

    def test_render_field_horizontal_layout(self):
        """Test rendering field with horizontal layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='field',
            field_schema={'type': 'string'},
            value='test',
            context=context,
            layout='horizontal',
        )

        assert isinstance(result, str)

    def test_render_field_inline_layout(self):
        """Test rendering field with inline layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='field',
            field_schema={'type': 'string'},
            value='test',
            context=context,
            layout='inline',
        )

        assert isinstance(result, str)


class TestFieldRendererInputClassing:
    """Test input CSS class generation."""

    def test_get_input_class_for_text(self):
        """Test input class generation for text input."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value='form-control')

        field_renderer = FieldRenderer(renderer)

        css_class = field_renderer._get_input_class('text')
        assert 'form-control' in css_class

    def test_get_input_class_for_email(self):
        """Test input class generation for email input."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value='form-control')

        field_renderer = FieldRenderer(renderer)

        css_class = field_renderer._get_input_class('email')
        assert 'form-control' in css_class

    def test_get_input_class_for_checkbox(self):
        """Test input class generation for checkbox."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value='form-check-input')

        field_renderer = FieldRenderer(renderer)

        css_class = field_renderer._get_input_class('checkbox')
        assert 'form-check-input' in css_class


class TestFieldRendererFrameworkSpecific:
    """Test framework-specific rendering."""

    def test_render_field_bootstrap_framework(self):
        """Test rendering field for bootstrap framework."""
        renderer = Mock()
        renderer.config = {'theme': 'bootstrap'}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='test',
            field_schema={'type': 'string'},
            value='test',
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)

    def test_render_field_material_framework(self):
        """Test rendering field for material framework."""
        renderer = Mock()
        renderer.config = {'theme': 'material'}
        renderer.framework = 'material'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='test',
            field_schema={'type': 'string'},
            value='test',
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)


class TestFieldRendererNullValues:
    """Test handling of null/None values."""

    def test_render_field_with_none_value(self):
        """Test rendering field with None value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='optional',
            field_schema={'type': 'string'},
            value=None,
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)

    def test_render_checkbox_with_none_value(self):
        """Test rendering checkbox with None value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = 'bootstrap'

        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = field_renderer.render_field(
            field_name='checkbox',
            field_schema={'type': 'boolean'},
            value=None,
            context=context,
            layout='vertical',
        )

        assert isinstance(result, str)


class _DummyRenderer:
    def __init__(self, config=None, framework='bootstrap', theme=None):
        self.config = config or {}
        self.framework = framework
        self.theme = theme

    def _render_layout_field(self, *args, **kwargs):
        return '<div>layout</div>'


class _CaptureInput:
    last_kwargs = None

    def render_with_label(self, **kwargs):
        _CaptureInput.last_kwargs = kwargs
        return "<input data-captured='true' />"


class _NoneInput:
    def render_with_label(self, **kwargs):
        return None


def _context(schema_defs=None):
    return RenderContext(form_data={}, schema_defs=schema_defs or {})


def test_render_field_uses_schema_and_ui_option_attributes_with_config_wrapper(monkeypatch):
    renderer = _DummyRenderer(
        config={
            'input_class': 'base-input',
            'field_wrapper_class': 'field-wrap',
        }
    )
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name='username',
        field_schema={
            'type': 'string',
            'title': 'User Name',
            'description': 'desc',
            'minLength': 2,
            'maxLength': 20,
            'minimum': 1,
            'maximum': 99,
            'pattern': '^[a-z]+$',
            'ui': {
                'autofocus': True,
                'disabled': True,
                'readonly': True,
                'placeholder': 'Your name',
                'class': 'ui-class',
                'style': 'color: red',
                'icon': 'user',
                'options': {
                    'class': 'opt-class',
                    'style': 'font-weight: bold',
                    'data-x': '1',
                    'choices': ['ignored'],
                    'obj': {'a': 1},
                    'list': [1, 2],
                },
            },
        },
        value='alice',
        required_fields=['username'],
        context=_context(),
    )

    assert 'field-wrap' in html
    captured = _CaptureInput.last_kwargs
    assert captured is not None
    assert captured['name'] == 'username'
    assert captured['required'] is True
    assert captured['minlength'] == 2
    assert captured['maxlength'] == 20
    assert captured['min'] == 1
    assert captured['max'] == 99
    assert captured['pattern'] == '^[a-z]+$'
    assert captured['placeholder'] == 'Your name'
    assert captured['autofocus'] is True
    assert captured['disabled'] is True
    assert captured['readonly'] is True
    assert 'base-input' in captured['class']
    assert 'ui-class' in captured['class']
    assert 'opt-class' in captured['class']
    assert 'color: red' in captured['style']
    assert 'font-weight: bold' in captured['style']
    assert captured['data-x'] == '1'


def test_render_field_uses_theme_wrapper_class(monkeypatch):
    class _Theme:
        @staticmethod
        def input_class(_ui):
            return 'theme-input'

        @staticmethod
        def field_wrapper_class():
            return 'theme-field-wrap'

    renderer = _DummyRenderer(config={'field_wrapper_class': 'config-wrap'}, theme=_Theme())
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name='title',
        field_schema={'type': 'string'},
        value='x',
        context=_context(),
    )

    assert 'theme-field-wrap' in html
    assert 'config-wrap' not in html


def test_render_field_selection_paths_multiselect_and_no_options(monkeypatch):
    renderer = _DummyRenderer(config={'select_class': 'sel-class'})
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name='tags',
        field_schema={
            'type': 'array',
            'items': {'enum': ['a', 'b', 'c']},
            'ui': {'element': 'multiselect'},
        },
        value=['b'],
        context=_context(),
    )

    assert 'captured' in html
    captured = _CaptureInput.last_kwargs
    assert captured['multiple'] is True
    assert 'value' not in captured
    assert len(captured['options']) == 3
    assert any(opt['value'] == 'b' and opt['selected'] for opt in captured['options'])

    no_options_html = field_renderer.render_field(
        field_name='empty_select',
        field_schema={'type': 'string', 'ui': {'element': 'select'}},
        value=None,
        context=_context(),
    )
    assert 'Warning: No options provided' in no_options_html


def test_render_field_selection_paths_combobox_and_checkbox_group(monkeypatch):
    """Regression test: combobox/checkbox_group must receive options like select/radio do.

    Previously these two ui_element values were missing from the options-dispatch
    tuple, so their render() never received `options=` and silently fell back to
    a bare empty <select></select> via SelectInputBase.render_with_label.
    """
    renderer = _DummyRenderer()
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name='fav_color',
        field_schema={
            'type': 'string',
            'enum': ['red', 'green', 'blue'],
            'ui': {'element': 'combobox'},
        },
        value='green',
        context=_context(),
    )
    assert 'captured' in html
    captured = _CaptureInput.last_kwargs
    assert len(captured['options']) == 3
    assert any(opt['value'] == 'green' and opt['selected'] for opt in captured['options'])

    html = field_renderer.render_field(
        field_name='prefs',
        field_schema={
            'type': 'array',
            'items': {'enum': ['a', 'b']},
            'ui': {'element': 'checkbox_group'},
        },
        value=['a'],
        context=_context(),
    )
    assert 'captured' in html
    captured = _CaptureInput.last_kwargs
    assert captured['group_name'] == 'prefs'
    assert captured['legend'] == 'Prefs'
    assert len(captured['options']) == 2


def test_render_field_handles_none_from_component(monkeypatch):
    renderer = _DummyRenderer()
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _NoneInput,
    )

    html = field_renderer.render_field(
        field_name='nickname',
        field_schema={'type': 'string'},
        value='nick',
        context=_context(),
    )

    assert 'input returned None' in html


def test_extract_apply_and_normalize_option_helpers():
    field_renderer = FieldRenderer(_DummyRenderer())

    options_dict, options_list = field_renderer._extract_ui_options(
        {'options': [{'value': 1}]},
        {},
    )
    assert options_dict == {}
    assert options_list == [{'value': 1}]

    options_dict, options_list = field_renderer._extract_ui_options(
        {'ui_options': {'choices': ['x', 'y']}},
        {},
    )
    assert options_dict == {'choices': ['x', 'y']}
    assert options_list == ['x', 'y']

    options_dict, options_list = field_renderer._extract_ui_options(
        {},
        {'ui_options': {'options': ['m', 'n']}},
    )
    assert options_dict == {'options': ['m', 'n']}
    assert options_list == ['m', 'n']

    attrs = field_renderer._apply_ui_option_attributes(
        {'class': 'base', 'style': 'color: red'},
        {
            'class': 'extra',
            'style': 'font-size: 12px',
            'size': 5,
            'choices': [1],
            'obj': {'a': 1},
        },
    )
    assert attrs['class'] == 'base extra'
    assert 'color: red' in attrs['style'] and 'font-size: 12px' in attrs['style']
    assert attrs['size'] == 5

    normalized = field_renderer._normalize_options(
        [
            {'id': 'a', 'label': 'Alpha'},
            ('b', 'Beta'),
            'c',
        ],
        current_value=['b', 'c'],
    )
    assert normalized[0]['value'] == 'a'
    assert normalized[0]['label'] == 'Alpha'
    assert normalized[1]['selected'] is True
    assert normalized[2]['selected'] is True

    assert field_renderer._is_option_selected(None, 'x') is False
    assert field_renderer._is_option_selected('x', None) is False
    assert field_renderer._is_option_selected('2', {1, 2}) is True
    assert field_renderer._is_option_selected('2', '2') is True


def test_build_placeholder_option():
    field_renderer = FieldRenderer(_DummyRenderer())

    # No current value -- placeholder is the effective selection.
    placeholder = field_renderer._build_placeholder_option(
        {'placeholder': 'Choose a plan...'}, current_value=None
    )
    assert placeholder == {
        'value': '',
        'label': 'Choose a plan...',
        'disabled': True,
        'selected': True,
    }

    # A real value is already chosen -- placeholder stays present and
    # disabled (unselectable again) but is no longer the selected one.
    placeholder = field_renderer._build_placeholder_option(
        {'placeholder': 'Choose a plan...'}, current_value='pro'
    )
    assert placeholder['selected'] is False
    assert placeholder['disabled'] is True

    # Not configured at all, or configured with a falsy value -- opt-in only.
    assert field_renderer._build_placeholder_option({}, current_value=None) is None
    assert field_renderer._build_placeholder_option({'placeholder': ''}, current_value=None) is None


def test_apply_ui_option_attributes_skips_placeholder_for_select_only():
    """placeholder is a real, documented ui_options key for other widgets
    (text/tags) -- the leak-suppression for `select` (see
    _build_placeholder_option) must not affect them."""
    field_renderer = FieldRenderer(_DummyRenderer())

    select_attrs = field_renderer._apply_ui_option_attributes(
        {}, {'placeholder': 'Choose a plan...'}, 'select'
    )
    assert 'placeholder' not in select_attrs

    text_attrs = field_renderer._apply_ui_option_attributes(
        {}, {'placeholder': 'Full name'}, 'text'
    )
    assert text_attrs['placeholder'] == 'Full name'

    # No ui_element passed at all (existing callers/tests) -- unaffected.
    default_attrs = field_renderer._apply_ui_option_attributes({}, {'placeholder': 'Full name'})
    assert default_attrs['placeholder'] == 'Full name'


def test_render_field_select_placeholder_option_opt_in(monkeypatch):
    renderer = _DummyRenderer()
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    schema = {
        'type': 'string',
        'enum': ['free', 'pro'],
        'ui': {'element': 'select', 'options': {'placeholder': 'Choose a plan...'}},
    }

    field_renderer.render_field(
        field_name='plan', field_schema=schema, value=None, context=_context()
    )
    options = _CaptureInput.last_kwargs['options']
    assert options[0] == {
        'value': '',
        'label': 'Choose a plan...',
        'disabled': True,
        'selected': True,
    }
    assert len(options) == 3

    field_renderer.render_field(
        field_name='plan', field_schema=schema, value='pro', context=_context()
    )
    options = _CaptureInput.last_kwargs['options']
    assert options[0]['selected'] is False
    assert options[0]['disabled'] is True
    assert any(opt['value'] == 'pro' and opt['selected'] for opt in options[1:])

    # No placeholder configured at all -- output is unaffected (opt-in only).
    no_placeholder_schema = {
        'type': 'string',
        'enum': ['free', 'pro'],
        'ui': {'element': 'select'},
    }
    field_renderer.render_field(
        field_name='plan', field_schema=no_placeholder_schema, value=None, context=_context()
    )
    options = _CaptureInput.last_kwargs['options']
    assert len(options) == 2
    assert all(opt['value'] != '' for opt in options)


def test_render_model_list_field_errors_and_ref_resolution():
    field_renderer = FieldRenderer(_DummyRenderer())

    no_ref = field_renderer._render_model_list_field(
        field_name='items',
        field_schema={'type': 'array', 'items': {}},
        value=None,
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(),
        all_errors={},
    )
    assert 'must be typed as list[ItemModel]' in no_ref

    unresolved_ref = field_renderer._render_model_list_field(
        field_name='items',
        field_schema={'type': 'array', 'items': {'$ref': '#/defs/Missing'}},
        value=None,
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(schema_defs={}),
        all_errors={},
    )
    assert 'Could not resolve model reference' in unresolved_ref

    class _FakeItem:
        def __init__(self, payload):
            self.payload = payload

        def model_dump(self):
            return self.payload

    schema_defs = {'Item': {'properties': {'name': {'type': 'string'}}}}

    html = field_renderer._render_model_list_field(
        field_name='items',
        field_schema={
            'type': 'array',
            'title': 'Items',
            'items': {'$ref': '#/$defs/Item'},
        },
        value=[_FakeItem({'name': 'a'}), {'name': 'b'}, _FakeItem({'name': 'c'})],
        error='E',
        required_fields=['items'],
        ui_info={'help_text': 'help'},
        context=_context(schema_defs=schema_defs),
        all_errors={'items[0].name': 'required', 'other': 'x'},
    )
    assert 'model-list-item' in html
    assert 'required' in html
    assert 'value="a"' in html
    assert 'value="b"' in html
    assert 'value="c"' in html


def test_render_model_list_field_single_model_dump_value_path():
    field_renderer = FieldRenderer(_DummyRenderer())

    class _SingleItem:
        @staticmethod
        def model_dump():
            return {'name': 'single'}

    schema_defs = {'Item': {'properties': {'name': {'type': 'string'}}}}

    html = field_renderer._render_model_list_field(
        field_name='items',
        field_schema={'type': 'array', 'items': {'$ref': '#/$defs/Item'}},
        value=_SingleItem(),
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(schema_defs=schema_defs),
        all_errors={},
    )

    assert 'value="single"' in html


def test_render_model_list_field_schema_fallback_and_container_theming(monkeypatch):
    class _Theme:
        @staticmethod
        def render_model_list_container(**kwargs):
            return f"<section data-field='{kwargs['field_name']}'>theme</section>"

    field_renderer = FieldRenderer(_DummyRenderer(theme=_Theme()))

    calls = []

    def _fake_item(field_name, schema_def, index, item_data, context, ui_info, nested_errors=None):
        calls.append((field_name, index, dict(item_data)))
        return f"<article data-index='{index}'>item</article>"

    monkeypatch.setattr(field_renderer, '_render_schema_list_item', _fake_item)

    themed = field_renderer.render_model_list_from_schema(
        field_name='items',
        field_schema={'title': 'Items', 'minItems': 2, 'maxItems': 5},
        schema_def={'properties': {'name': {'type': 'string'}}},
        values=[],
        error=None,
        ui_info={'help_text': 'help', 'add_button_label': 'Add'},
        required_fields=['items'],
        context=_context(),
    )
    assert "data-field='items'" in themed
    assert calls == [('items', 0, {}), ('items', 1, {}), ('items', 0, {})]

    class _ThemeEmpty:
        @staticmethod
        def render_model_list_container(**kwargs):
            return ''

    field_renderer_empty = FieldRenderer(_DummyRenderer(theme=_ThemeEmpty()))
    monkeypatch.setattr(field_renderer_empty, '_render_schema_list_item', _fake_item)

    fallback = field_renderer_empty.render_model_list_from_schema(
        field_name='things',
        field_schema={'title': 'Things', 'minItems': 0, 'description': 'desc'},
        schema_def={'properties': {}},
        values=[],
        error='oops',
        ui_info={},
        required_fields=[],
        context=_context(),
    )
    assert 'model-list-container' in fallback


def test_extract_nested_errors_and_schema_list_item_rendering(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())

    extracted = field_renderer.extract_nested_errors_for_field(
        'addresses',
        {
            'addresses[0].street': 'required',
            'addresses[0]': 'ignored',
            'other[0].x': 'not used',
        },
    )
    assert extracted == {'0.street': 'required'}

    monkeypatch.setattr(
        field_renderer, 'render_field', lambda name, *_args, **_kwargs: f"<input name='{name}' />"
    )

    html_collapsible = field_renderer._render_schema_list_item(
        field_name='addresses[]',
        schema_def={
            'properties': {
                '_internal': {'type': 'string'},
                'street': {'type': 'string'},
                'phones': {'type': 'array', 'input_type': 'model_list'},
                'zip': {'type': 'string'},
                'city': {'type': 'string'},
                'country': {'type': 'string'},
            }
        },
        index=1,
        item_data={'street': 'Main'},
        context=_context(),
        ui_info={'collapsible_items': True, 'items_expanded': False},
    )
    assert '_item_1_content' in html_collapsible
    assert 'bi-chevron-right' in html_collapsible
    assert 'col-lg-4 col-md-6' in html_collapsible
    assert 'col-12' in html_collapsible

    html_non_collapsible = field_renderer._render_schema_list_item(
        field_name='tasks',
        schema_def={'properties': {'name': {'type': 'string'}, 'due': {'type': 'string'}}},
        index=0,
        item_data={'name': 'A'},
        context=_context(),
        ui_info={'collapsible_items': False, 'item_title_template': 'Task #{index}'},
    )
    assert 'bi-card-list' in html_non_collapsible
    assert 'data-bs-toggle="collapse"' not in html_non_collapsible
    assert 'col-12' in html_non_collapsible

    html_medium_columns = field_renderer._render_schema_list_item(
        field_name='contacts',
        schema_def={
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'phone': {'type': 'string'},
            }
        },
        index=0,
        item_data={'name': 'A'},
        context=_context(),
        ui_info={'collapsible_items': False},
    )
    assert 'col-md-6' in html_medium_columns


def test_render_field_radio_enum_branch_and_helpers(monkeypatch):
    renderer = _DummyRenderer(config={'select_class': 'select-base'})
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.field_renderer.get_input_component',
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name='status',
        field_schema={
            'type': 'string',
            'enum': ['open', 'closed'],
            'ui': {'element': 'radio'},
        },
        value='closed',
        context=_context(),
    )

    assert 'captured' in html
    captured = _CaptureInput.last_kwargs
    assert captured['group_name'] == 'status'
    assert captured['legend'] == 'Status'
    assert any(opt['value'] == 'closed' and opt['selected'] for opt in captured['options'])

    attrs = {'x': 1}
    assert field_renderer._apply_ui_option_attributes(attrs, {}) == {'x': 1}

    normalized = field_renderer._normalize_options([{'id': 'abc'}], current_value='abc')
    assert normalized[0]['value'] == 'abc'
    assert normalized[0]['label'] == 'abc'
    assert normalized[0]['selected'] is True

    assert field_renderer._infer_ui_element({'type': 'string', 'maxLength': 500}) == 'textarea'
    assert field_renderer._infer_ui_element({'type': 'string', 'title': 'Email Address'}) == 'email'
    assert field_renderer._infer_ui_element({'type': 'string', 'title': 'Password'}) == 'password'
    assert field_renderer._infer_ui_element({'type': 'number'}) == 'number'
    assert field_renderer._infer_ui_element({'type': 'boolean'}) == 'checkbox'
    assert field_renderer._infer_ui_element({'type': 'object'}) == 'text'
    assert field_renderer._get_input_class('checkbox') == ''


def test_render_model_list_field_single_dict_value_through_schema_path(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())

    schema_defs = {'Thing': {'properties': {'name': {'type': 'string'}}}}

    monkeypatch.setattr(
        field_renderer,
        'render_model_list_from_schema',
        lambda **kwargs: f'schema-list:{kwargs["field_name"]}:{len(kwargs["values"])}',
    )

    schema_result = field_renderer._render_model_list_field(
        field_name='things',
        field_schema={'type': 'array', 'items': {'$ref': '#/defs/Thing'}},
        value={'name': 'single'},
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(schema_defs=schema_defs),
        all_errors={},
    )
    assert schema_result == 'schema-list:things:1'


def test_render_model_list_from_schema_values_path(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())
    call_indexes = []

    def _fake_item(field_name, schema_def, index, item_data, context, ui_info, nested_errors=None):
        call_indexes.append(index)
        return f"<item idx='{index}' />"

    monkeypatch.setattr(field_renderer, '_render_schema_list_item', _fake_item)

    html = field_renderer.render_model_list_from_schema(
        field_name='rows',
        field_schema={'title': 'Rows', 'maxItems': 7},
        schema_def={'properties': {'name': {'type': 'string'}}},
        values=[{'name': 'a'}, {'name': 'b'}],
        error=None,
        ui_info={},
        required_fields=[],
        context=_context(),
    )

    assert 'model-list-container' in html
    assert call_indexes == [0, 1, 0]
