"""Field rendering helpers shared across renderers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from pydantic_schemaforms.icon_mapping import map_icon_for_framework
from pydantic_schemaforms.inputs import HiddenInput
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.frameworks import get_input_component
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine
from pydantic_schemaforms.rendering.schema_parser import extract_ui_info
from pydantic_schemaforms.tstring import SafeHTML, html

# Importing this registers the 'model_list' ui_element renderer (LayoutEngine
# .register_layout_renderer, builtin=True) as a side effect at import time --
# model_list is a core, always-available feature (unlike DataTableLayout,
# which only registers itself if an app imports it), so this needs to be a
# real, unconditional import here rather than the lazy per-call imports the
# thin delegator methods below use for everything else in that module.
from . import model_list_renderer as _model_list_renderer  # noqa: F401

# ui_element values that render as an HTML checkbox under the hood and so
# need the same boolean checked/value handling ('toggle' is CheckboxInput's
# styled-as-a-switch subclass -- functionally a checkbox, see ToggleSwitch's
# docstring).
_CHECKBOX_LIKE_ELEMENTS = {'checkbox', 'toggle', 'toggle_switch', 'checkbox_toggle'}

# ui_element values whose individual <input> elements are checkboxes/radios
# under the hood, regardless of whether the widget is a single boolean
# (checkbox/toggle) or a group of options (radio/checkbox_group). This is
# broader than _CHECKBOX_LIKE_ELEMENTS above (which is only for the
# single-boolean checked/value coercion) -- radio/checkbox_group don't have a
# single boolean value, but their per-item <input>s still need the
# checkbox-family CSS class, not the dropdown-styled select_class (applying
# select_class -- e.g. Bootstrap's .form-select, which paints a dropdown
# chevron -- directly onto a radio/checkbox <input> makes it look like a
# broken dropdown arrow instead of a radio button).
_CHECKBOX_FAMILY_ELEMENTS = _CHECKBOX_LIKE_ELEMENTS | {'radio', 'checkbox_group'}


class FieldRenderer:
    """Encapsulates the heavy lifting of turning schema fields into HTML."""

    def __init__(self, renderer: Any) -> None:
        self._renderer = renderer

    @property
    def config(self) -> dict[str, Any]:
        return self._renderer.config

    @property
    def framework(self) -> str:
        return self._renderer.framework

    @property
    def theme(self):
        return getattr(self._renderer, 'theme', None)

    def render_field(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any = None,
        error: str | None = None,
        required_fields: list[str] | None = None,
        context: RenderContext | None = None,
        layout: str = 'vertical',
        all_errors: dict[str, str] | None = None,
    ) -> str:
        if context is None:
            raise ValueError('RenderContext is required for field rendering')

        ui_info = extract_ui_info(field_schema)

        if ui_info.get('hidden'):
            return self._render_hidden_field(field_name, value)

        ui_element = (
            ui_info.get('element')
            or ui_info.get('ui_element')
            or ui_info.get('widget')
            or ui_info.get('input_type')
            or self._infer_ui_element(field_schema)
        )

        if ui_element == 'layout':
            return self._renderer._render_layout_field(  # noqa: SLF001
                field_name,
                field_schema,
                value,
                ui_info,
                context,
            )

        # Second, independent dispatch keyspace from the 'layout_handler'
        # lookup above -- looked up directly by ui_element (model_list,
        # datatable, or any future registered composite), regardless of
        # whether input_type is 'layout'. See LayoutEngine.get_renderer_for_element.
        custom_renderer = LayoutEngine.get_renderer_for_element(ui_element)
        if custom_renderer is not None:
            enriched_context = replace(
                context,
                error=error,
                required_fields=tuple(required_fields or ()),
                all_errors=dict(all_errors or {}),
            )
            return custom_renderer(
                field_name,
                field_schema,
                value,
                ui_info,
                enriched_context,
                self._renderer._layout_engine,  # noqa: SLF001
            )

        input_component = get_input_component(ui_element)()  # type: ignore[misc]

        field_attrs: dict[str, Any] = {
            'name': field_name,
            'id': field_name,
            'class': self._get_input_class(ui_element),
        }

        if value is not None and ui_element != 'password':
            if ui_element in _CHECKBOX_LIKE_ELEMENTS:
                if value is True or value == 'true' or value == '1' or value == 'on':
                    field_attrs['checked'] = True
                field_attrs['value'] = '1'
            else:
                field_attrs['value'] = value
        elif value is not None and ui_element == 'password':
            field_attrs['value'] = value

        resolved_required = required_fields or []
        if field_name in resolved_required:
            field_attrs['required'] = True

        if 'minLength' in field_schema:
            field_attrs['minlength'] = field_schema['minLength']
        if 'maxLength' in field_schema:
            field_attrs['maxlength'] = field_schema['maxLength']
        if 'minimum' in field_schema:
            field_attrs['min'] = field_schema['minimum']
        if 'maximum' in field_schema:
            field_attrs['max'] = field_schema['maximum']
        if 'pattern' in field_schema:
            field_attrs['pattern'] = field_schema['pattern']

        if ui_info.get('autofocus'):
            field_attrs['autofocus'] = True
        if ui_info.get('disabled'):
            field_attrs['disabled'] = True
        if ui_info.get('readonly'):
            field_attrs['readonly'] = True
        if ui_info.get('placeholder'):
            field_attrs['placeholder'] = ui_info['placeholder']
        if ui_info.get('class'):
            field_attrs['class'] += f' {ui_info["class"]}'
        if ui_info.get('style'):
            field_attrs['style'] = ui_info['style']

        ui_options_dict, ui_options_list = self._extract_ui_options(ui_info, field_schema)
        if ui_options_dict:
            field_attrs = self._apply_ui_option_attributes(field_attrs, ui_options_dict, ui_element)

        label_text = field_schema.get('title', field_name.replace('_', ' ').title())
        help_text = ui_info.get('help_text') or field_schema.get('description')
        icon = ui_info.get('icon')
        if icon:
            icon = map_icon_for_framework(icon, self.framework)

        try:
            if ui_element in ('select', 'radio', 'multiselect', 'combobox', 'checkbox_group'):
                selection_options = ui_options_list or []
                if not selection_options and 'enum' in field_schema:
                    selection_options = field_schema['enum']
                if (
                    not selection_options
                    and isinstance(field_schema.get('items'), dict)
                    and 'enum' in field_schema.get('items', {})
                ):
                    selection_options = field_schema['items']['enum']

                formatted_options = self._normalize_options(selection_options, value)

                if not formatted_options:
                    input_html = html(
                        t'<!-- Warning: No options provided for {ui_element} field '
                        t"'{field_name}' -->"
                    )
                else:
                    if ui_element == 'select':
                        placeholder_option = self._build_placeholder_option(ui_options_dict, value)
                        if placeholder_option is not None:
                            formatted_options = [placeholder_option, *formatted_options]

                    field_attrs.pop('value', None)
                    # radio/checkbox_group already show their title as the
                    # <fieldset><legend>; passing the same text as an outer
                    # label too duplicates it (and under Material's floating
                    # -label CSS the duplicate sits absolutely positioned on
                    # top of the fieldset, visually overlapping it).
                    outer_label = label_text
                    if ui_element in ('radio', 'checkbox_group'):
                        field_attrs.setdefault('group_name', field_name)
                        field_attrs.setdefault('legend', label_text)
                        outer_label = None
                    if ui_element == 'multiselect':
                        field_attrs['multiple'] = True

                    input_html = input_component.render_with_label(  # type: ignore[union-attr]
                        label=outer_label,
                        help_text=help_text,
                        error=error,
                        icon=icon,
                        framework=self.framework,
                        options=formatted_options,
                        **field_attrs,
                    )
            else:
                input_html = input_component.render_with_label(  # type: ignore[union-attr]
                    label=label_text,
                    help_text=help_text,
                    error=error,
                    icon=icon,
                    framework=self.framework,
                    **field_attrs,
                )

            if input_html is None:
                input_html = html(t'<!-- Error: {ui_element} input returned None -->')
        except Exception as exc:  # pragma: no cover - defensive fallback
            error_message = str(exc)
            input_html = html(t'<!-- Error rendering {ui_element}: {error_message} -->')

        wrapper_class = ''
        if self.theme:
            wrapper_class = self.theme.field_wrapper_class() or ''
        if not wrapper_class:
            wrapper_class = self.config.get('field_wrapper_class', '')
        if wrapper_class:
            _input_html = SafeHTML(str(input_html))
            return html(t'<div class="{wrapper_class}">{_input_html}</div>')
        return input_html

    def _render_model_list_field(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any,
        error: str | None,
        required_fields: list[str] | None,
        ui_info: dict[str, Any],
        context: RenderContext,
        all_errors: dict[str, str] | None,
    ) -> str:
        from .model_list_renderer import render_model_list_field

        return render_model_list_field(
            self,
            field_name,
            field_schema,
            value,
            error,
            required_fields,
            ui_info,
            context,
            all_errors,
        )

    def _extract_ui_options(
        self, ui_info: dict[str, Any], field_schema: dict[str, Any]
    ) -> tuple[dict[str, Any], list[Any]]:
        raw_options = (
            ui_info.get('options')
            or ui_info.get('ui_options')
            or field_schema.get('ui_options')
            or {}
        )

        options_dict: dict[str, Any] = raw_options if isinstance(raw_options, dict) else {}
        options_list: list[Any] = []

        if isinstance(raw_options, list):
            options_list = raw_options
        elif isinstance(options_dict, dict):
            if isinstance(options_dict.get('choices'), list):
                options_list = options_dict.get('choices', [])
            elif isinstance(options_dict.get('options'), list):
                options_list = options_dict.get('options', [])

        return options_dict, options_list

    def _apply_ui_option_attributes(
        self,
        field_attrs: dict[str, Any],
        ui_options: dict[str, Any],
        ui_element: str | None = None,
    ) -> dict[str, Any]:
        if not ui_options:
            return field_attrs

        option_keys_to_skip = {'choices', 'options', 'async_options', 'fetch_url'}
        if ui_element == 'select':
            # 'placeholder' drives the forced-selection blank option built by
            # _build_placeholder_option -- for `select` specifically (unlike
            # `text`/`tags`, where it's a real HTML placeholder attribute) it
            # must not also leak through as a meaningless placeholder="..."
            # attribute on the <select> tag itself (browsers ignore it there).
            option_keys_to_skip = option_keys_to_skip | {'placeholder'}

        # checkbox_group/radio's collapsible/collapsed ui_options need no
        # entry here, unlike 'placeholder' above -- CheckboxGroup.render()/
        # RadioGroup.render() (selection_inputs.py) never call
        # validate_attributes() on their whole kwargs blob the way
        # SelectInput does, so an unconsumed kwarg is just dropped, never
        # written into HTML as a stray attribute. Same reason 'legend'/
        # 'variant' already work with no skip-list entry.

        for key, option_value in ui_options.items():
            if key in option_keys_to_skip:
                continue
            if isinstance(option_value, (list, dict)):
                continue

            if key == 'class' and field_attrs.get('class'):
                field_attrs['class'] = f'{field_attrs["class"]} {option_value}'.strip()
            elif key == 'style' and field_attrs.get('style'):
                separator = '; ' if not str(field_attrs['style']).strip().endswith(';') else ' '
                field_attrs['style'] = f'{field_attrs["style"]}{separator}{option_value}'
            else:
                field_attrs[key] = option_value

        return field_attrs

    def _normalize_options(self, options: list[Any], current_value: Any) -> list[dict[str, Any]]:
        if not options:
            return []

        normalized: list[dict[str, Any]] = []

        for option in options:
            if isinstance(option, dict):
                formatted = option.copy()
                if 'value' not in formatted:
                    fallback_value = None
                    for fallback_key in ('id', 'key', 'label'):
                        if fallback_key in formatted:
                            fallback_value = formatted[fallback_key]
                            break
                    formatted['value'] = fallback_value

                if not formatted.get('label'):
                    formatted['label'] = str(formatted.get('value', ''))

                formatted.setdefault(
                    'selected',
                    self._is_option_selected(formatted.get('value'), current_value),
                )
                normalized.append(formatted)
            elif isinstance(option, (list, tuple)) and option:
                value = option[0]  # type: ignore[index]
                label = option[1] if len(option) > 1 else option[0]  # type: ignore[index]
                normalized.append(
                    {
                        'value': value,
                        'label': label,
                        'selected': self._is_option_selected(value, current_value),
                    }
                )
            else:
                normalized.append(
                    {
                        'value': option,
                        'label': option,
                        'selected': self._is_option_selected(option, current_value),
                    }
                )

        return normalized

    def _build_placeholder_option(
        self, ui_options: dict[str, Any], current_value: Any
    ) -> dict[str, Any] | None:
        """A disabled, empty-value first option forcing a genuine choice --
        opt-in via ui_options={'placeholder': '...'} on `select` fields.
        Stays disabled (unselectable once a real option is chosen) whether
        or not it's the one currently marked `selected`."""
        placeholder_text = ui_options.get('placeholder')
        if not placeholder_text:
            return None
        return {
            'value': '',
            'label': placeholder_text,
            'disabled': True,
            'selected': current_value is None or self._is_option_selected('', current_value),
        }

    def _is_option_selected(self, option_value: Any, current_value: Any) -> bool:
        if option_value is None or current_value is None:
            return False

        option_str = str(option_value)

        if isinstance(current_value, (list, tuple, set)):
            return option_str in {str(val) for val in current_value}

        return option_str == str(current_value)

    def _render_hidden_field(self, field_name: str, value: Any) -> str:
        hidden_input = HiddenInput()
        return hidden_input.render(name=field_name, id=field_name, value=value or '')

    def _infer_ui_element(self, field_schema: dict[str, Any]) -> str:
        field_type = field_schema.get('type', 'string')

        if field_type == 'string':
            max_length = field_schema.get('maxLength', 0)
            if max_length > 200:
                return 'textarea'
            if 'email' in field_schema.get('title', '').lower():
                return 'email'
            if 'password' in field_schema.get('title', '').lower():
                return 'password'
            return 'text'
        if field_type in ('integer', 'number'):
            return 'number'
        if field_type == 'boolean':
            return 'checkbox'
        return 'text'

    def _get_input_class(self, ui_element: str) -> str:
        themed_class = ''
        if self.theme:
            themed_class = self.theme.input_class(ui_element)
        if themed_class:
            return themed_class
        if ui_element in _CHECKBOX_FAMILY_ELEMENTS:
            return self.config.get('checkbox_class', '')
        if ui_element in ('select', 'multiselect'):
            return self.config.get('select_class', '')
        return self.config.get('input_class', '')

    def render_model_list_from_schema(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        schema_def: dict[str, Any],
        values: list[dict[str, Any]],
        error: str | None,
        ui_info: dict[str, Any],
        required_fields: list[str],
        context: RenderContext,
        all_errors: dict[str, str] | None = None,
    ) -> str:
        from .model_list_renderer import render_model_list_from_schema

        return render_model_list_from_schema(
            self,
            field_name,
            field_schema,
            schema_def,
            values,
            error,
            ui_info,
            required_fields,
            context,
            all_errors,
        )

    def extract_nested_errors_for_field(
        self, field_name: str, all_errors: dict[str, Any]
    ) -> dict[str, str]:
        from .model_list_renderer import extract_nested_errors_for_field

        return extract_nested_errors_for_field(self, field_name, all_errors)

    def _render_schema_list_item(
        self,
        field_name: str,
        schema_def: dict[str, Any],
        index: int,
        item_data: dict[str, Any],
        context: RenderContext,
        ui_info: dict[str, Any] | None = None,
        nested_errors: dict[str, str] | None = None,
    ) -> str:
        from .model_list_renderer import render_schema_list_item

        return render_schema_list_item(
            self, field_name, schema_def, index, item_data, context, ui_info, nested_errors
        )
