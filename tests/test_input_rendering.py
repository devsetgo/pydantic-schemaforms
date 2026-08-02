"""
Coverage-boost tests targeting all files below 90%.

Each class targets a specific module. Tests exercise uncovered branches
identified from the --cov-report=term-missing output.
"""

from __future__ import annotations

import asyncio
import sys
import warnings
from datetime import date, datetime, time
from typing import Annotated, Optional
from unittest import mock

import pytest
from pydantic import AnyUrl, BaseModel
from pydantic.fields import FieldInfo

from pydantic_schemaforms import FormModel


# ---------------------------------------------------------------------------
# layouts.py  (0% → import triggers module-level deprecation warn)
# ---------------------------------------------------------------------------


class TestLayoutsDeprecationShim:
    def test_import_emits_deprecation_warning(self):
        # Force fresh import so module-level warn() runs.
        mod_name = 'pydantic_schemaforms.layouts'
        sys.modules.pop(mod_name, None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            import pydantic_schemaforms.layouts as layouts_mod  # noqa: F401

            sys.modules.pop(mod_name, None)  # clean up for other test runs

        dep_warns = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert dep_warns, 'Expected at least one DeprecationWarning'
        assert 'layouts is deprecated' in str(dep_warns[0].message)


# ---------------------------------------------------------------------------
# icon_mapping.py  (61%)
# ---------------------------------------------------------------------------


class TestIconMappingUncovered:
    def test_get_bootstrap_icon(self):
        from pydantic_schemaforms.icon_mapping import get_bootstrap_icon

        result = get_bootstrap_icon('envelope')
        assert result == 'bi bi-envelope'

    def test_get_material_icon(self):
        from pydantic_schemaforms.icon_mapping import get_material_icon

        result = get_material_icon('envelope')
        assert result == 'email'

    def test_get_icon_unknown_returns_none(self):
        from pydantic_schemaforms.icon_mapping import get_bootstrap_icon

        assert get_bootstrap_icon('nonexistent-icon-xyz') is None

    def test_update_field_icons_for_framework_with_icon(self):
        from pydantic_schemaforms.icon_mapping import update_field_icons_for_framework

        fields = {
            'email_field': {'icon': 'envelope', 'placeholder': 'test'},
            'no_icon_field': {'placeholder': 'test'},
        }
        result = update_field_icons_for_framework(fields, 'bootstrap')
        assert result['email_field']['icon'] == 'bi bi-envelope'
        assert 'icon' not in result['no_icon_field']
        assert result['no_icon_field']['placeholder'] == 'test'

    def test_update_field_icons_for_framework_material(self):
        from pydantic_schemaforms.icon_mapping import update_field_icons_for_framework

        fields = {'field': {'icon': 'lock'}}
        result = update_field_icons_for_framework(fields, 'material')
        assert result['field']['icon'] == 'lock'


# ---------------------------------------------------------------------------
# version_check.py  (68%)
# ---------------------------------------------------------------------------


class TestVersionCheckUncovered:
    def test_check_python_version_raises_on_old_python(self):
        from pydantic_schemaforms.version_check import check_python_version

        import collections

        VersionInfo = collections.namedtuple(
            'version_info', ['major', 'minor', 'micro', 'releaselevel', 'serial']
        )
        fake = VersionInfo(3, 13, 0, 'final', 0)
        with mock.patch('pydantic_schemaforms.version_check.sys') as mock_sys:
            mock_sys.version_info = fake
            with pytest.raises(RuntimeError, match='Python 3.14'):
                check_python_version()

    def test_verify_template_strings_spec_none_raises(self):
        from pydantic_schemaforms.version_check import verify_template_strings

        with mock.patch('importlib.util.find_spec', return_value=None):
            with pytest.raises(ImportError, match='not available'):
                verify_template_strings()


# ---------------------------------------------------------------------------
# input_types.py  (78%)
# ---------------------------------------------------------------------------


class TestInputTypesUncovered:
    def test_get_valid_input_types_known_type(self):
        from pydantic_schemaforms.input_types import get_valid_input_types

        result = get_valid_input_types(str)
        assert isinstance(result, set)
        assert len(result) > 0

    def test_get_valid_input_types_unknown_returns_empty(self):
        from pydantic_schemaforms.input_types import get_valid_input_types

        result = get_valid_input_types(object)
        assert result == set()

    def test_is_input_type_valid_raises_with_field_name(self):
        from pydantic_schemaforms.input_types import is_input_type_valid

        with pytest.raises(ValueError, match="field 'my_field'"):
            is_input_type_valid(bool, 'text', 'my_field')

    def test_is_input_type_valid_raises_without_field_name(self):
        from pydantic_schemaforms.input_types import is_input_type_valid

        with pytest.raises(ValueError):
            is_input_type_valid(bool, 'text')

    def test_format_icon_class_empty_string(self):
        from pydantic_schemaforms.input_types import format_icon_class

        assert format_icon_class('') == ''

    def test_format_icon_class_already_prefixed(self):
        from pydantic_schemaforms.input_types import format_icon_class

        result = format_icon_class('bi bi-person', 'bootstrap')
        assert result == 'bi bi-person'

    def test_format_icon_class_adds_prefix(self):
        from pydantic_schemaforms.input_types import format_icon_class

        result = format_icon_class('person', 'bootstrap')
        assert result == 'bi bi-person'

    def test_format_icon_class_unknown_framework_uses_bootstrap(self):
        from pydantic_schemaforms.input_types import format_icon_class

        result = format_icon_class('person', 'unknown-fw')
        assert 'person' in result


# ---------------------------------------------------------------------------
# integration/sync.py  (76%)
# ---------------------------------------------------------------------------


class TestSyncUncovered:
    def test_normalize_form_data_single_item_list(self):
        from pydantic_schemaforms.integration.sync import normalize_form_data

        result = normalize_form_data({'field': ['value']})
        assert result['field'] == 'value'

    def test_normalize_form_data_multi_item_list_kept(self):
        from pydantic_schemaforms.integration.sync import normalize_form_data

        result = normalize_form_data({'field': ['a', 'b']})
        assert result['field'] == ['a', 'b']

    def test_normalize_form_data_on_becomes_true(self):
        from pydantic_schemaforms.integration.sync import normalize_form_data

        result = normalize_form_data({'active': 'on'})
        assert result['active'] is True

    def test_normalize_form_data_off_becomes_false(self):
        from pydantic_schemaforms.integration.sync import normalize_form_data

        result = normalize_form_data({'active': 'off'})
        assert result['active'] is False

    def test_handle_sync_form_validation_error_renders(self):
        from pydantic_schemaforms.integration.builder import FormBuilder
        from pydantic_schemaforms.integration.sync import handle_sync_form

        builder = FormBuilder().email_input('email').required('email')
        result = handle_sync_form(
            builder,
            submitted_data={'email': ''},
            render_on_error=True,
        )
        assert result['success'] is False
        assert 'form_html' in result

    def test_handle_sync_form_validation_error_no_render(self):
        from pydantic_schemaforms.integration.builder import FormBuilder
        from pydantic_schemaforms.integration.sync import handle_sync_form

        builder = FormBuilder().email_input('email').required('email')
        result = handle_sync_form(
            builder,
            submitted_data={'email': ''},
            render_on_error=False,
        )
        assert result['success'] is False
        assert 'form_html' not in result


# ---------------------------------------------------------------------------
# integration/react.py  (79%)
# ---------------------------------------------------------------------------


class TestReactIntegrationUncovered:
    def _make(self):
        from pydantic_schemaforms.integration.json_schema_form_adapter import (
            ReactJSONSchemaFormAdapter,
        )

        return ReactJSONSchemaFormAdapter()

    def test_datetime_field_gets_datetime_widget(self):
        class M(BaseModel):
            created_at: datetime

        ui = self._make().generate_ui_schema(M)
        assert ui.get('created_at', {}).get('ui:widget') == 'datetime'

    def test_date_field_gets_date_widget(self):
        class M(BaseModel):
            birthday: date

        ui = self._make().generate_ui_schema(M)
        assert ui.get('birthday', {}).get('ui:widget') == 'date'

    def test_password_field_name_gets_password_widget(self):
        class M(BaseModel):
            password: str

        ui = self._make().generate_ui_schema(M)
        assert ui.get('password', {}).get('ui:widget') == 'password'

    def test_bio_field_gets_textarea_widget(self):
        class M(BaseModel):
            bio: str

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:widget') == 'textarea'

    def test_description_field_gets_textarea_widget(self):
        class M(BaseModel):
            description: str

        ui = self._make().generate_ui_schema(M)
        assert ui.get('description', {}).get('ui:widget') == 'textarea'

    def test_ui_autofocus(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_autofocus': True})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:autofocus') is True

    def test_ui_placeholder(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_placeholder': 'Write here'})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:placeholder') == 'Write here'

    def test_ui_help_text(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_help_text': 'Short bio'})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:help') == 'Short bio'

    def test_ui_disabled(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_disabled': True})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:disabled') is True

    def test_ui_readonly(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_readonly': True})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:readonly') is True

    def test_ui_options_dict(self):
        class M(BaseModel):
            bio: str = FieldInfo(default='', json_schema_extra={'ui_options': {'rows': 6}})

        ui = self._make().generate_ui_schema(M)
        assert ui.get('bio', {}).get('ui:options') == {'rows': 6}

    def test_no_widget_returns_none_entry(self):
        class M(BaseModel):
            plain: str

        ui = self._make().generate_ui_schema(M)
        assert 'plain' not in ui

    def test_generate_complete_config(self):
        class M(BaseModel):
            bio: str

        config = self._make().generate_complete_config(M, initial_data={'bio': 'hello'})
        assert 'schema' in config
        assert 'uiSchema' in config
        assert config['formData'] == {'bio': 'hello'}


# ---------------------------------------------------------------------------
# integration/vue.py  (86%)
# ---------------------------------------------------------------------------


class TestVueIntegrationUncovered:
    def _make(self):
        from pydantic_schemaforms.integration.vue_formulate_adapter import VueFormulateAdapter

        return VueFormulateAdapter()

    def test_optional_field_unwrapped(self):
        class M(BaseModel):
            nickname: Optional[str] = None

        config = self._make().generate_form_config(M)
        field = next(f for f in config if f['name'] == 'nickname')
        assert field['type'] == 'text'

    def test_password_field(self):
        class M(BaseModel):
            password: str

        config = self._make().generate_form_config(M)
        field = next(f for f in config if f['name'] == 'password')
        assert field['type'] == 'password'

    def test_bool_field(self):
        class M(BaseModel):
            active: bool

        config = self._make().generate_form_config(M)
        field = next(f for f in config if f['name'] == 'active')
        assert field['type'] == 'checkbox'

    def test_number_field(self):
        class M(BaseModel):
            score: float

        config = self._make().generate_form_config(M)
        field = next(f for f in config if f['name'] == 'score')
        assert field['type'] == 'number'

    def test_validation_rules_with_email(self):
        class M(BaseModel):
            email: str

        rules = self._make().generate_validation_rules(M)
        assert 'email' in rules['email']


# ---------------------------------------------------------------------------
# inputs/registry.py  (86%)
# ---------------------------------------------------------------------------


class TestRegistryUncovered:
    def test_register_inputs_plural(self):
        from pydantic_schemaforms.inputs.base import FormInput
        from pydantic_schemaforms.inputs.registry import register_inputs, reset_input_registry

        class RI1(FormInput):
            ui_element = '_ri_test_1'

            def get_input_type(self):
                return 'text'

            def render(self, **kwargs):
                return '<input />'

        class RI2(FormInput):
            ui_element = '_ri_test_2'

            def get_input_type(self):
                return 'text'

            def render(self, **kwargs):
                return '<input />'

        register_inputs([RI1, RI2])
        reset_input_registry()

    def test_register_input_no_aliases_raises(self):
        from pydantic_schemaforms.inputs.base import FormInput
        from pydantic_schemaforms.inputs.registry import register_input_class, reset_input_registry

        class BadInput(FormInput):
            ui_element = None
            ui_element_aliases = None

            def get_input_type(self):
                return 'text'

            def render(self, **kwargs):
                return '<input />'

        with pytest.raises(ValueError, match='At least one alias'):
            register_input_class(BadInput, aliases=[])

        reset_input_registry()

    def test_register_input_empty_alias_skipped(self):
        from pydantic_schemaforms.inputs.base import FormInput
        from pydantic_schemaforms.inputs.registry import (
            get_input_component_map,
            register_input_class,
            reset_input_registry,
        )

        class GoodInput(FormInput):
            ui_element = '_ri_good_test'

            def get_input_type(self):
                return 'text'

            def render(self, **kwargs):
                return '<input />'

        register_input_class(GoodInput, aliases=['', '_ri_good_test'])
        mapping = get_input_component_map()
        assert '_ri_good_test' in mapping
        assert '' not in mapping
        reset_input_registry()


# ---------------------------------------------------------------------------
# integration/schema.py  (88%)
# ---------------------------------------------------------------------------


class TestJSONSchemaGeneratorUncovered:
    def _gen(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator

        return JSONSchemaGenerator()

    def test_issubclass_safe_non_type(self):
        from pydantic_schemaforms.integration.schema import _issubclass_safe

        assert _issubclass_safe('not_a_type', str) is False
        assert _issubclass_safe(42, int) is False

    def test_ensure_model_class_accepts_instance(self):
        class M(BaseModel):
            x: str

        instance = M(x='hello')
        cls = self._gen().ensure_model_class(instance)
        assert cls is M

    def test_ensure_model_class_raises_on_none(self):
        with pytest.raises(TypeError, match='cannot be None'):
            self._gen().ensure_model_class(None)

    def test_ensure_model_class_raises_on_non_model(self):
        with pytest.raises(TypeError):
            self._gen().ensure_model_class('not_a_model')

    def test_normalize_annotation_annotated(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator

        ann = Annotated[int, 'some_metadata']
        result = JSONSchemaGenerator.normalize_annotation(ann)
        assert result is int

    def test_datetime_field_maps_to_date_time_format(self):
        class M(BaseModel):
            ts: datetime

        schema = self._gen().generate_schema(M)
        assert schema['properties']['ts']['format'] == 'date-time'

    def test_anyurl_field_maps_to_uri_format(self):
        class M(BaseModel):
            site: AnyUrl

        schema = self._gen().generate_schema(M)
        assert schema['properties']['site']['format'] == 'uri'

    def test_apply_field_metadata_min_max_len(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
        from pydantic import Field as PydanticField

        class M(BaseModel):
            name: str = PydanticField(min_length=2, max_length=50)

        schema = JSONSchemaGenerator().generate_schema(M)
        assert schema['properties']['name'].get('minLength') == 2
        assert schema['properties']['name'].get('maxLength') == 50

    def test_apply_field_metadata_numeric_constraints(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
        from pydantic import Field as PydanticField

        class M(BaseModel):
            score: int = PydanticField(ge=0, le=100)

        schema = JSONSchemaGenerator().generate_schema(M)
        props = schema['properties']['score']
        assert props.get('minimum') == 0
        assert props.get('maximum') == 100

    def test_apply_field_metadata_exclusive_constraints(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
        from pydantic import Field as PydanticField

        class M(BaseModel):
            val: float = PydanticField(gt=0.0, lt=1.0)

        schema = JSONSchemaGenerator().generate_schema(M)
        props = schema['properties']['val']
        assert props.get('exclusiveMinimum') == 0.0
        assert props.get('exclusiveMaximum') == 1.0

    def test_apply_field_metadata_multiple_of(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
        from pydantic import Field as PydanticField

        class M(BaseModel):
            qty: int = PydanticField(multiple_of=5)

        schema = JSONSchemaGenerator().generate_schema(M)
        assert schema['properties']['qty'].get('multipleOf') == 5

    def test_apply_field_metadata_bool_default(self):
        from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
        from pydantic import Field as PydanticField

        class M(BaseModel):
            active: bool = PydanticField(default=True)

        schema = JSONSchemaGenerator().generate_schema(M)
        assert schema['properties']['active'].get('default') is True

    def test_openapi_schema_generator(self):
        from pydantic_schemaforms.integration.schema import OpenAPISchemaGenerator

        class M(BaseModel):
            name: str

        gen = OpenAPISchemaGenerator()
        req = gen.generate_request_schema(M)
        assert 'content' in req
        resp = gen.generate_response_schema(M)
        assert '200' in resp


# ---------------------------------------------------------------------------
# inputs/text_inputs.py  (86%) — exercise "already supplied" branches
# ---------------------------------------------------------------------------


class TestTextInputsUncovered:
    def test_password_explicit_autocomplete(self):
        from pydantic_schemaforms.inputs.text_inputs import PasswordInput

        inp = PasswordInput()
        html = inp.render(name='pw', autocomplete='current-password')
        assert 'autocomplete="current-password"' in html

    def test_email_explicit_inputmode(self):
        from pydantic_schemaforms.inputs.text_inputs import EmailInput

        inp = EmailInput()
        html = inp.render(name='em', inputmode='numeric')
        assert 'inputmode="numeric"' in html

    def test_search_explicit_inputmode(self):
        from pydantic_schemaforms.inputs.text_inputs import SearchInput

        inp = SearchInput()
        html = inp.render(name='q', inputmode='text')
        assert 'inputmode="text"' in html

    def test_url_explicit_inputmode(self):
        from pydantic_schemaforms.inputs.text_inputs import URLInput

        inp = URLInput()
        html = inp.render(name='site', inputmode='text')
        assert 'inputmode="text"' in html

    def test_url_explicit_pattern(self):
        from pydantic_schemaforms.inputs.text_inputs import URLInput

        inp = URLInput()
        html = inp.render(name='site', pattern=r'https://.+')
        assert 'pattern' in html

    def test_tel_explicit_inputmode(self):
        from pydantic_schemaforms.inputs.text_inputs import TelInput

        inp = TelInput()
        html = inp.render(name='ph', inputmode='numeric')
        assert 'inputmode="numeric"' in html

    def test_tel_explicit_autocomplete(self):
        from pydantic_schemaforms.inputs.text_inputs import TelInput

        inp = TelInput()
        html = inp.render(name='ph', autocomplete='off')
        assert 'autocomplete="off"' in html

    def test_phone_with_country_code_on_value(self):
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', country_code='+1', value='5551234')
        assert '+1' in html

    def test_phone_with_country_code_on_placeholder(self):
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', country_code='+44', placeholder='7911123456')
        assert '+44' in html

    def test_phone_already_prefixed_value(self):
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', country_code='+1', value='+1 5551234')
        assert '+1' in html

    def test_phone_default_output_unchanged_without_phone_format(self):
        """No phone_format kwarg -> byte-identical to the pre-mask-feature output."""
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', id='ph', country_code='+1', value='5551234')
        assert '<script>' not in html

    def test_phone_with_format_mask_adds_pattern_and_script(self):
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', id='ph', phone_format='(###) ###-####')
        assert 'maxlength="14"' in html
        assert '<script>' in html
        assert '(###) ###-####' in html

    def test_phone_format_mask_without_live_format_has_no_script(self):
        from pydantic_schemaforms.inputs.text_inputs import PhoneInput

        inp = PhoneInput()
        html = inp.render(name='ph', id='ph', phone_format='###-####', live_format=False)
        assert '<script>' not in html
        assert 'maxlength="8"' in html

    def test_textarea_none_value(self):
        from pydantic_schemaforms.inputs.text_inputs import TextArea

        inp = TextArea()
        html = inp.render(name='msg', value=None)
        assert '<textarea' in html
        assert html.count('<textarea') == 1


# ---------------------------------------------------------------------------
# inputs/datetime_inputs.py -- custom date/time/datetime display formats
# ---------------------------------------------------------------------------


class TestDatetimeInputsCustomFormat:
    def test_date_input_with_format_renders_text_type_and_pattern(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(
            name='d', id='d', date_format='%d/%m/%Y', value=date(2026, 3, 5), live_format=False
        )
        assert 'type="text"' in html
        assert 'type="date"' not in html
        assert 'value="05/03/2026"' in html
        assert r'pattern="\d{2}/\d{2}/\d{4}"' in html
        assert 'inputmode="numeric"' in html

    def test_date_input_with_format_and_live_format_adds_script(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(name='d', id='d', date_format='%d/%m/%Y')
        assert '<script>' in html
        assert '"##/##/####"' in html

    def test_date_input_format_without_live_format_has_no_script(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(name='d', id='d', date_format='%d/%m/%Y', live_format=False)
        assert '<script>' not in html
        assert 'schemaforms-picker-toggle' not in html

    def test_date_input_with_format_includes_single_visible_box_and_toggle(self):
        """A custom-format date field stays a single visible input -- the
        browser's calendar picker is reachable via a small toggle button
        (backed by a visually-hidden native <input type="date">, opened via
        showPicker()), not a second visible box."""
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(name='d', id='d', date_format='%d/%m/%Y')
        # Exactly one visible text input carrying the field's name/value.
        assert html.count('name="d"') == 1
        assert 'schemaforms-picker-toggle' in html
        assert 'aria-label="Open date picker"' in html
        # The hidden native picker is excluded from tab order / AT and never submits.
        assert 'type="date" id="d__picker" tabindex="-1" aria-hidden="true"' in html
        assert 'opacity: 0' in html
        assert 'showPicker' in html
        # The picker's onchange handler must build the SAME %d/%m/%Y order.
        assert 'getDate()).padStart(2, \'0\') + "/"' in html
        assert 'getMonth() + 1).padStart(2, \'0\') + "/"' in html
        assert 'getFullYear()' in html

    def test_date_input_with_month_name_format_includes_toggle(self):
        """%B (full month name) has no fixed digit width, so the live-typing
        mask is unavailable, but the picker toggle IS available -- it builds
        the whole value from a Date at once via a hardcoded month-name array,
        not by live-typing character by character."""
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(name='d', id='d', date_format='%Y %B %d')
        assert 'schemaforms-picker-toggle' in html
        assert 'aria-label="Open date picker"' in html
        assert '"January"' in html
        assert '"December"' in html
        assert 'replace(/\\D/g' not in html

    def test_time_input_with_format_includes_toggle(self):
        from pydantic_schemaforms.inputs.datetime_inputs import TimeInput

        inp = TimeInput()
        html = inp.render(name='t', id='t', time_format='%H:%M')
        assert html.count('name="t"') == 1
        assert 'type="time" id="t__picker" tabindex="-1"' in html
        assert 'aria-label="Open time picker"' in html
        assert "new Date('1970-01-01T' + this.value)" in html

    def test_datetime_input_with_format_includes_toggle(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(name='dt', id='dt', datetime_format='%Y%m%d%H%M%S')
        assert html.count('name="dt"') == 1
        assert 'type="datetime-local" id="dt__picker" tabindex="-1"' in html
        assert 'aria-label="Open date and time picker"' in html
        assert 'new Date(this.value)' in html

    def test_datetime_input_with_ampm_format_includes_toggle(self):
        """%I:%M %p is a common USA datetime format -- confirms it gets a
        working picker toggle despite %p being unsupported by the live mask."""
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(name='dt', id='dt', datetime_format='%m/%d/%Y %I:%M %p')
        assert 'schemaforms-picker-toggle' in html
        assert 'aria-label="Open date and time picker"' in html
        assert 'replace(/\\D/g' not in html

    def test_picker_toggle_omitted_for_unsupported_format(self):
        """%f (microseconds) has no JS Date equivalent, so it's excluded from
        the directive set the picker toggle's JS can build from -- the toggle
        should be silently omitted, not emit broken JS."""
        from pydantic_schemaforms.inputs.datetime_inputs import TimeInput

        inp = TimeInput()
        html = inp.render(name='t', id='t', time_format='%H:%M:%f')
        assert 'schemaforms-picker-toggle' not in html

    def test_picker_toggle_included_for_ampm_format(self):
        """%p (AM/PM) IS derivable from a JS Date (fixed 2-char output), so
        unlike the live-typing mask (still disabled, see
        test_time_input_with_12h_format_includes_ampm_pattern_and_toggle_but_no_mask_script),
        the picker toggle is available for this format."""
        from pydantic_schemaforms.inputs.datetime_inputs import TimeInput

        inp = TimeInput()
        html = inp.render(name='t', id='t', time_format='%I:%M %p')
        assert 'schemaforms-picker-toggle' in html

    def test_picker_toggle_omitted_without_live_format(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DateInput

        inp = DateInput()
        html = inp.render(name='d', id='d', date_format='%d/%m/%Y', live_format=False)
        assert 'schemaforms-picker-toggle' not in html

    def test_time_input_with_military_format_no_ampm(self):
        from pydantic_schemaforms.inputs.datetime_inputs import TimeInput

        inp = TimeInput()
        html = inp.render(name='t', id='t', time_format='%H:%M', value=time(23, 30))
        assert 'type="text"' in html
        assert 'value="23:30"' in html
        assert 'AM' not in html
        assert 'PM' not in html
        assert 'step=' not in html

    def test_time_input_with_12h_format_includes_ampm_pattern_and_toggle_but_no_mask_script(self):
        from pydantic_schemaforms.inputs.datetime_inputs import TimeInput

        inp = TimeInput()
        html = inp.render(name='t', id='t', time_format='%I:%M %p', value=time(23, 30))
        assert 'value="11:30 PM"' in html
        assert 'AM|PM' in html
        # The picker toggle works (whole value built at once from a Date)...
        assert 'schemaforms-picker-toggle' in html
        # ...but %p has no fixed digit width, so live per-character-typing
        # masking is still disabled for this format.
        assert 'replace(/\\D/g' not in html

    def test_datetime_input_with_custom_format_renders_and_masks(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(
            name='dt',
            id='dt',
            datetime_format='%d-%m-%Y %H:%M:%S',
            value=datetime(2026, 3, 5, 23, 30, 15),
        )
        assert 'type="text"' in html
        assert 'value="05-03-2026 23:30:15"' in html
        assert '<script>' in html

    def test_datetime_input_set_now_button_with_supported_format(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(
            name='dt', id='dt', datetime_format='%Y%m%d%H%M%S', with_set_now_button=True
        )
        assert 'Set Now' in html
        assert 'setCurrentDatetime_dt(' in html
        # Must not collide with the default (unformatted) global function name.
        assert 'function setCurrentDatetime(' not in html

    def test_datetime_input_set_now_button_omitted_for_unsupported_format(self):
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(
            name='dt',
            id='dt',
            datetime_format='%Y-%m-%d %H:%M:%S.%f',
            with_set_now_button=True,
        )
        assert 'Set Now' not in html
        assert 'datetime-input-group' not in html

    def test_datetime_input_set_now_button_with_ampm_and_month_name_format(self):
        """%B/%p are both JS-derivable (see _JS_DATE_PART_EXPR), so the Set
        Now button works for this format even though the live-typing mask
        does not."""
        from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput

        inp = DatetimeInput()
        html = inp.render(
            name='dt',
            id='dt',
            datetime_format='%B %d, %Y %I:%M %p',
            with_set_now_button=True,
        )
        assert 'Set Now' in html
        assert 'datetime-input-group' in html

    def test_material_date_field_with_custom_format_uses_widget_registry(self):
        from pydantic_schemaforms.schema_form import Field, FormModel
        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        class _MaterialDateForm(FormModel):
            start_date: date = Field(..., ui_element='date', ui_options={'date_format': '%d/%m/%Y'})

        renderer = EnhancedFormRenderer(framework='material')
        html = renderer.render_form_from_model(
            _MaterialDateForm, data={'start_date': date(2026, 3, 5)}, submit_url='/x'
        )
        assert 'value="05/03/2026"' in html
        assert r'pattern="\d{2}/\d{2}/\d{4}"' in html

    def test_material_date_field_default_rendering_unchanged(self):
        from pydantic_schemaforms.schema_form import Field, FormModel
        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        class _MaterialDateForm(FormModel):
            plain_date: date = Field(..., ui_element='date')

        renderer = EnhancedFormRenderer(framework='material')
        html = renderer.render_form_from_model(
            _MaterialDateForm, data={'plain_date': date(2026, 3, 5)}, submit_url='/x'
        )
        assert 'type="date"' in html
        assert 'value="2026-03-05"' in html
        assert 'pattern=' not in html


# ---------------------------------------------------------------------------
# inputs/numeric_inputs.py  (88%)
# ---------------------------------------------------------------------------


class TestNumericInputsUncovered:
    def test_percentage_with_percent_in_placeholder(self):
        from pydantic_schemaforms.inputs.numeric_inputs import PercentageInput

        inp = PercentageInput()
        html = inp.render(name='pct', placeholder='75%')
        assert 'placeholder="75%"' in html

    def test_slider_no_labels(self):
        from pydantic_schemaforms.inputs.numeric_inputs import SliderInput

        inp = SliderInput()
        html = inp.render(name='sl', show_labels=False)
        assert 'slider-labels' not in html

    def test_temperature_fahrenheit(self):
        from pydantic_schemaforms.inputs.numeric_inputs import TemperatureInput

        inp = TemperatureInput()
        html = inp.render(name='temp', unit='fahrenheit')
        assert '°F' in html or '-459.67' in html

    def test_temperature_kelvin(self):
        from pydantic_schemaforms.inputs.numeric_inputs import TemperatureInput

        inp = TemperatureInput()
        html = inp.render(name='temp', unit='kelvin')
        assert 'K' in html or '293K' in html


# ---------------------------------------------------------------------------
# inputs/base.py  (88%)
# ---------------------------------------------------------------------------


class TestBaseInputUncovered:
    def test_build_error_message(self):
        from pydantic_schemaforms.inputs.base import build_error_message

        html = build_error_message('email', 'Invalid email')
        assert 'email-error' in html
        assert 'Invalid email' in html

    def test_build_help_text(self):
        from pydantic_schemaforms.inputs.base import build_help_text

        html = build_help_text('email', 'Enter your email')
        assert 'email-help' in html
        assert 'Enter your email' in html

    def test_format_attribute_value_none(self):
        from pydantic_schemaforms.inputs.text_inputs import TextInput

        inp = TextInput()
        result = inp._format_attribute_value('placeholder', None)
        assert result == ''

    def test_format_attribute_value_list(self):
        from pydantic_schemaforms.inputs.text_inputs import TextInput

        inp = TextInput()
        result = inp._format_attribute_value('class', ['form-control', 'is-valid'])
        assert result == 'form-control is-valid'

    def test_validate_attributes_none_value_skipped(self):
        from pydantic_schemaforms.inputs.text_inputs import TextInput

        inp = TextInput()
        # Passing a valid attr with None value — should be skipped (continue)
        result = inp.validate_attributes(name='test', value=None)
        assert 'name' in result

    def test_render_with_label_material_framework(self):
        from pydantic_schemaforms.inputs.text_inputs import TextInput

        inp = TextInput()
        html = inp.render_with_label(
            label='Name',
            help_text='Your name',
            error='Required',
            framework='material',
            name='name',
        )
        assert 'md-field' in html or 'Name' in html

    def test_render_with_label_no_framework(self):
        from pydantic_schemaforms.inputs.text_inputs import TextInput

        inp = TextInput()
        html = inp.render_with_label(
            label='Name',
            help_text='Your name',
            error='Required',
            framework='none',
            name='name',
        )
        assert 'Name' in html

    def test_select_input_base_fallback_no_options(self):
        from pydantic_schemaforms.inputs.selection_inputs import SelectInput

        inp = SelectInput()
        html = inp.render_with_label(
            label='Choose',
            framework='bootstrap',
            name='choice',
            options=None,
        )
        assert 'Choose' in html

    def test_select_input_base_material_with_icon(self):
        from pydantic_schemaforms.inputs.selection_inputs import SelectInput

        inp = SelectInput()
        html = inp.render_with_label(
            label='Choose',
            framework='material',
            name='choice',
            icon='list',
            options=[{'value': 'a', 'label': 'A'}],
        )
        assert 'md-field' in html or 'Choose' in html

    def test_select_input_base_none_framework_with_icon(self):
        from pydantic_schemaforms.inputs.selection_inputs import SelectInput

        inp = SelectInput()
        html = inp.render_with_label(
            label='Pick',
            framework='none',
            name='pick',
            icon='list',
            options=[{'value': 'x', 'label': 'X'}],
        )
        assert 'Pick' in html


# ---------------------------------------------------------------------------
# rendering/schema_parser.py  (86%)
# ---------------------------------------------------------------------------


class TestSchemaParserUncovered:
    def test_build_schema_metadata_with_dynamic_fields(self):
        from pydantic_schemaforms.rendering.schema_parser import (
            build_schema_metadata,
            reset_schema_metadata_cache,
        )

        class DynModel(FormModel):
            name: str

            @classmethod
            def ensure_dynamic_fields(cls):
                return True

        reset_schema_metadata_cache()
        meta = build_schema_metadata(DynModel)
        assert meta is not None
        reset_schema_metadata_cache()

    def test_infer_field_type_int(self):
        from pydantic_schemaforms.rendering.schema_parser import _infer_field_type

        fi = FieldInfo(annotation=int)
        assert _infer_field_type(fi) == 'integer'

    def test_infer_field_type_float(self):
        from pydantic_schemaforms.rendering.schema_parser import _infer_field_type

        fi = FieldInfo(annotation=float)
        assert _infer_field_type(fi) == 'number'

    def test_infer_field_type_bool(self):
        from pydantic_schemaforms.rendering.schema_parser import _infer_field_type

        fi = FieldInfo(annotation=bool)
        assert _infer_field_type(fi) == 'boolean'

    def test_field_info_to_schema_with_description_and_ui(self):
        from pydantic_schemaforms.rendering.schema_parser import _field_info_to_schema

        fi = FieldInfo(
            annotation=str,
            description='A field',
            json_schema_extra={'ui_placeholder': 'Enter here'},
        )
        schema = _field_info_to_schema('my_field', fi)
        assert schema.get('description') == 'A field'
        assert 'ui' in schema
        assert schema['ui'].get('placeholder') == 'Enter here'

    def test_inject_dynamic_fields_with_fieldinfo_in_dict(self):
        from pydantic_schemaforms.rendering.schema_parser import _inject_dynamic_fields

        class DynModel2(FormModel):
            name: str

        # Inject a FieldInfo directly into the class dict (simulated dynamic field)
        extra_fi = FieldInfo(annotation=str, default='hello')
        DynModel2.extra_dynamic = extra_fi  # type: ignore[attr-defined]

        props: dict = {}
        required: list = []
        _inject_dynamic_fields(DynModel2, props, required)
        # Cleanup
        del DynModel2.extra_dynamic


# ---------------------------------------------------------------------------
# render_form.py  (81%)
# ---------------------------------------------------------------------------


class TestRenderFormUncovered:
    def test_render_form_html_asset_mode_none_skips_htmx(self):
        from pydantic_schemaforms import render_form_html

        class M(FormModel):
            name: str

        html = render_form_html(M, submit_url='/submit', asset_mode='none')
        assert 'name' in html

    def test_render_form_html_include_imask(self):
        import pytest
        from pydantic_schemaforms.render_form import render_form_html as legacy_render

        class M(FormModel):
            name: str

        with pytest.warns(DeprecationWarning, match='render_form.render_form_html is deprecated'):
            html = legacy_render(M, submit_url='/submit', include_imask=True)
        assert 'name' in html

    def test_render_form_html_async_no_running_loop(self):
        import pytest
        from pydantic_schemaforms.render_form import render_form_html_async as legacy_async

        class M(FormModel):
            name: str

        # Run without an event loop — hits the except RuntimeError branch
        with pytest.warns(DeprecationWarning):
            html = asyncio.run(legacy_async(M, submit_url='/submit'))
        assert 'name' in html


# ---------------------------------------------------------------------------
# html_markers.py  (92%)
# ---------------------------------------------------------------------------


class TestHtmlMarkersUncovered:
    def test_wrap_disabled(self):
        from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

        out = wrap_with_schemaforms_markers('<form/>', enabled=False)
        assert out == '<form/>'
        assert 'pydantic-schemaforms' not in out

    def test_wrap_empty_html(self):
        from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

        out = wrap_with_schemaforms_markers('')
        # Empty inner content → single-line marker block
        assert 'Start Pydantic-SchemaForms' in out
        assert 'End Pydantic-SchemaForms' in out


# ---------------------------------------------------------------------------
# integration/utils.py  (90%)
# ---------------------------------------------------------------------------


class TestIntegrationUtilsUncovered:
    def test_map_pydantic_to_json_schema_type_fallback(self):
        from pydantic_schemaforms.integration.utils import map_pydantic_to_json_schema_type

        assert map_pydantic_to_json_schema_type(bytes) == 'string'

    def test_check_framework_availability_unknown(self):
        from pydantic_schemaforms.integration.utils import check_framework_availability

        assert check_framework_availability('django') is False

    def test_check_framework_availability_known(self):
        from pydantic_schemaforms.integration.utils import check_framework_availability

        # fastapi may or may not be installed; just check it returns a bool
        result = check_framework_availability('fastapi')
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# render_form.py  (remaining: imask with no tag, async loop)
# ---------------------------------------------------------------------------


class TestRenderFormRemainder:
    def test_include_imask_no_tag_emitted(self):
        import pytest
        from pydantic_schemaforms.render_form import render_form_html as legacy_render

        class M(FormModel):
            name: str

        # asset_mode='none' → imask_script_tag returns '' → inner if imask_tag is False
        with pytest.warns(DeprecationWarning, match='render_form.render_form_html is deprecated'):
            html = legacy_render(M, submit_url='/submit', include_imask=True, asset_mode='none')
        assert 'name' in html


# ---------------------------------------------------------------------------
# rendering/schema_parser.py  (remaining)
# ---------------------------------------------------------------------------


class TestSchemaParserRemainder:
    def test_inject_dynamic_fields_with_runtime_fields(self):
        from pydantic_schemaforms.rendering.schema_parser import _inject_dynamic_fields

        class ModelWithRuntime(FormModel):
            name: str

        # Simulate __runtime_fields__ populated by register_field
        extra_fi = FieldInfo(annotation=str, default='x')
        ModelWithRuntime.__runtime_fields__ = {'runtime_col': (str, extra_fi)}

        props: dict = {}
        required: list = []
        _inject_dynamic_fields(ModelWithRuntime, props, required)
        assert 'runtime_col' in props
        del ModelWithRuntime.__runtime_fields__

    def test_inject_dynamic_fields_required_runtime_field(self):
        from pydantic_schemaforms.rendering.schema_parser import _inject_dynamic_fields

        class ModelReq(FormModel):
            name: str

        # Required FieldInfo (no default)
        req_fi = FieldInfo(annotation=str)
        ModelReq.__runtime_fields__ = {'req_col': (str, req_fi)}

        props: dict = {}
        required: list = []
        _inject_dynamic_fields(ModelReq, props, required)
        assert 'req_col' in required
        del ModelReq.__runtime_fields__
