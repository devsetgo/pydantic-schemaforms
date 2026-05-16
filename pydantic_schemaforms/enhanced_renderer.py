"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

from __future__ import annotations

import asyncio
import html
import inspect
import json
import logging
import re
import time
from enum import Enum
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .html_markers import wrap_with_schemaforms_markers
from .icon_mapping import map_icon_for_framework
from .rendering.context import RenderContext
from .rendering.field_renderer import FieldRenderer
from .rendering.frameworks import get_framework_config
from .rendering.layout_engine import LayoutEngine, get_nested_form_data
from .rendering.material_icons import render_material_icon
from .rendering.schema_parser import SchemaMetadata, build_schema_metadata, resolve_ui_element
from .rendering.themes import MaterialEmbeddedTheme, RendererTheme, get_theme_for_framework
from .schema_form import FormModel
from .templates import FormTemplates, render_template

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class CSRFMode(str, Enum):
    OFF = 'off'
    FIELD_ONLY = 'field-only'
    REQUIRED_PROVIDER = 'required-provider'


CSRF_MODE_OFF = CSRFMode.OFF.value
CSRF_MODE_FIELD_ONLY = CSRFMode.FIELD_ONLY.value
CSRF_MODE_REQUIRED_PROVIDER = CSRFMode.REQUIRED_PROVIDER.value
CSRF_MODES = {mode.value for mode in CSRFMode}


class SchemaFormValidationError(Exception):
    """Raised when validation errors match the SchemaForm contract."""

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__('Schema form validation error')


class EnhancedFormRenderer:
    """Render Pydantic FormModels into HTML using UI metadata."""

    def __init__(
        self,
        framework: str = 'bootstrap',
        theme: Optional[RendererTheme] = None,
        *,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
    ):
        self.framework = framework
        self.include_framework_assets = include_framework_assets
        if theme is None and framework == 'material':
            theme = MaterialEmbeddedTheme()
        resolved_theme = theme or get_theme_for_framework(
            framework,
            include_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
        self._theme: RendererTheme = resolved_theme
        self.asset_mode = asset_mode
        if hasattr(self._theme, 'config'):
            self.config = self._theme.config  # type: ignore[union-attr]
        elif isinstance(self._theme, MaterialEmbeddedTheme):
            self.config = {}
        else:
            self.config = get_framework_config(framework)
        self._layout_engine = LayoutEngine(self)
        self._field_renderer = FieldRenderer(self)

    @property
    def theme(self) -> RendererTheme:
        return self._theme

    def render_form_from_model(
        self,
        model_cls: Type[FormModel],
        data: Dict[str, Any] | None = None,
        errors: Dict[str, Any] | None = None,
        *,
        submit_url: str = '/submit',
        method: str = 'POST',
        csrf_mode: CSRFMode | str = CSRF_MODE_OFF,
        csrf_token_provider: str | Callable[[], str] | None = None,
        include_submit_button: bool = True,
        layout: str = 'vertical',
        debug: bool = False,
        show_timing: bool = False,
        enable_logging: bool = False,
        **kwargs,
    ) -> str:
        """Render a complete HTML form from a FormModel definition."""

        # Start timing
        start_time = time.perf_counter()

        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        data = dict(data or {})
        errors = errors or {}

        # Keep backward compatibility for callers still passing these via kwargs.
        include_csrf = bool(kwargs.pop('include_csrf', False))
        csrf_field_name = kwargs.pop('csrf_field_name', 'csrf_token') or 'csrf_token'

        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        if isinstance(errors, dict) and 'errors' in errors:
            errors = {err.get('name', ''): err.get('message', '') for err in errors['errors']}

        error_summary_markup = self._render_error_summary(errors)

        default_form_class = self._theme.form_class() or self.config.get('form_class', '')
        form_attrs = {
            'method': method,
            'action': submit_url,
            'class': default_form_class,
            'novalidate': True,
        }
        form_attrs.update(kwargs)
        form_attrs['action'] = submit_url  # kwargs must not override action
        form_attrs = self._theme.transform_form_attributes(form_attrs)

        resolved_csrf_mode = self._resolve_csrf_mode(
            include_csrf=include_csrf,
            csrf_mode=csrf_mode,
            debug=debug,
        )
        csrf_markup = self._render_csrf_field(
            mode=resolved_csrf_mode,
            csrf_token_provider=csrf_token_provider,
            csrf_field_name=csrf_field_name,
        )
        form_body_parts: List[str] = []

        fields = metadata.fields
        required_fields = metadata.required_fields
        layout_fields = metadata.layout_fields
        non_layout_fields = metadata.non_layout_fields

        if layout_fields:
            model_fields = getattr(model_cls, 'model_fields', {}) or {}
            for field_name, _field_schema in layout_fields:
                if field_name in data:
                    continue
                field_info = model_fields.get(field_name)
                if not field_info:
                    continue
                default_factory = getattr(field_info, 'default_factory', None)
                if default_factory is not None:
                    try:
                        data[field_name] = default_factory()
                    except Exception:  # pragma: no cover - defensive
                        continue
                elif not field_info.is_required():
                    default_value = getattr(field_info, 'default', None)
                    if default_value is not None:
                        data[field_name] = default_value

        if len(layout_fields) > 1 and len(non_layout_fields) == 0:
            form_body_parts.extend(
                self._render_layout_fields_as_tabs(
                    layout_fields,
                    data,
                    errors,
                    required_fields,
                    context,
                )
            )
        elif layout == 'tabbed':
            form_body_parts.extend(
                self._render_tabbed_layout(fields, data, errors, required_fields, context)
            )
        elif layout == 'side-by-side':
            form_body_parts.extend(
                self._render_side_by_side_layout(fields, data, errors, required_fields, context)
            )
        else:
            for field_name, field_schema in fields:
                form_body_parts.append(
                    self._render_field(
                        field_name,
                        field_schema,
                        data.get(field_name),
                        errors.get(field_name),
                        required_fields,
                        context,
                        layout,
                        errors,
                    )
                )

        if error_summary_markup:
            form_body_parts.insert(0, error_summary_markup)

        submit_markup = self._render_submit_button() if include_submit_button else ''

        # Calculate render time before form_wrapper (we'll add timing display inside form)
        render_time = time.perf_counter() - start_time

        form_markup = self._theme.render_form_wrapper(
            form_attrs=form_attrs,
            csrf_token=csrf_markup,
            form_content='\n'.join(form_body_parts),
            submit_markup=submit_markup,
            render_time=render_time if show_timing else None,
        )

        output_parts = [self._render_layout_support_styles(), form_markup]

        has_model_list_fields = any(
            resolve_ui_element(field_schema) == 'model_list' for _name, field_schema in fields
        )
        if has_model_list_fields:
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self._model_list_framework())
            output_parts.append(list_renderer.get_model_list_javascript())

        combined_output = '\n'.join(output_parts)

        if enable_logging:
            logger.debug(
                f'Form rendered in {render_time:.3f} seconds (model: {model_cls.__name__})'
            )

        if not debug:
            return combined_output

        return combined_output + self._build_debug_panel(
            form_html=combined_output,
            model_cls=model_cls,
            data=data,
            errors=errors,
            metadata=metadata,
            render_time=render_time,
        )

    def render_form_fields_only(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        layout: str = 'vertical',
        **kwargs,
    ) -> str:
        """Render only the field markup for nested usage."""

        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        if isinstance(errors, dict) and 'errors' in errors:
            errors = {err.get('name', ''): err.get('message', '') for err in errors['errors']}

        fields = metadata.fields
        required_fields = metadata.required_fields

        form_parts: List[str] = []
        for field_name, field_schema in fields:
            form_parts.append(
                self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    context,
                    layout,
                    errors,
                )
            )

        return '\n'.join(form_parts)

    async def render_form_from_model_async(
        self,
        model_cls: Type[FormModel],
        data: Dict[str, Any] | None = None,
        errors: Dict[str, Any] | None = None,
        *,
        submit_url: str = '/submit',
        method: str = 'POST',
        include_csrf: bool = False,
        csrf_mode: CSRFMode | str = CSRF_MODE_OFF,
        csrf_token_provider: str | Callable[[], str] | None = None,
        csrf_field_name: str = 'csrf_token',
        include_submit_button: bool = True,
        layout: str = 'vertical',
        **kwargs,
    ) -> str:
        """Async wrapper for render_form_from_model."""

        render_callable = partial(
            self.render_form_from_model,
            model_cls,
            data=data,
            errors=errors,
            submit_url=submit_url,
            method=method,
            include_csrf=include_csrf,
            csrf_mode=csrf_mode,
            csrf_token_provider=csrf_token_provider,
            csrf_field_name=csrf_field_name,
            include_submit_button=include_submit_button,
            layout=layout,
            **kwargs,
        )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, render_callable)

    def _render_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        layout: str = 'vertical',
        all_errors: Optional[Dict[str, str]] = None,
    ) -> str:
        if self.framework == 'material':
            return self._render_material_field(
                field_name,
                field_schema,
                value,
                error,
                required_fields,
                context,
                layout,
                all_errors,
            )
        return self._field_renderer.render_field(
            field_name,
            field_schema,
            value,
            error,
            required_fields,
            context,
            layout,
            all_errors,
        )

    def _render_tabbed_layout(
        self,
        fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        return self._layout_engine.render_tabbed_layout(
            fields, data, errors, required_fields, context
        )

    def _render_layout_fields_as_tabs(
        self,
        layout_fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        return self._layout_engine.render_layout_fields_as_tabs(
            layout_fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_layout_field_content(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        return self._layout_engine.render_layout_field_content(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _get_nested_form_data(
        self,
        field_name: str,
        main_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return get_nested_form_data(field_name, main_data or {})

    def _render_side_by_side_layout(
        self,
        fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        return self._layout_engine.render_side_by_side_layout(
            fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _extract_nested_errors_for_field(
        self, field_name: str, all_errors: Dict[str, Any]
    ) -> Dict[str, str]:
        nested_errors: Dict[str, str] = {}
        field_prefix = f'{field_name}['

        for error_path, error_message in (all_errors or {}).items():
            if error_path.startswith(field_prefix):
                nested_part = error_path[len(field_prefix) :]
                if '].' in nested_part:
                    nested_errors[nested_part.replace('].', '.')] = error_message

        return nested_errors

    def _render_layout_support_styles(self) -> str:
        """Return shared form layout CSS so templates don't need framework-specific fixes."""

        return """
<style data-schemaforms-layout-support>
.pydantic-form,
.md-form {
    width: 100%;
    max-width: none;
}

.pydantic-form > div,
.pydantic-form > fieldset,
.pydantic-form > [class*="row"],
.md-form > div,
.md-form > fieldset,
.md-form > [class*="row"] {
    width: 100% !important;
    max-width: none !important;
}

.pydantic-form [class*="col-"],
.md-form [class*="col-"] {
    min-width: 0;
    flex: 1 1 auto !important;
}

.pydantic-form [class*="section"],
.pydantic-form [data-schemaforms-section],
.pydantic-form fieldset,
.md-form [class*="section"],
.md-form [data-schemaforms-section],
.md-form fieldset {
    width: 100% !important;
    max-width: none !important;
    box-sizing: border-box;
}
</style>
"""

    def _flatten_error_messages(self, errors: Any, prefix: str = '') -> List[Tuple[str, str]]:
        """Flatten mixed error payloads into (field_path, message) tuples."""

        flattened: List[Tuple[str, str]] = []

        if isinstance(errors, dict):
            for key, value in errors.items():
                path = f'{prefix}.{key}' if prefix and key else str(key or prefix)
                flattened.extend(self._flatten_error_messages(value, path))
            return flattened

        if isinstance(errors, list):
            for item in errors:
                flattened.extend(self._flatten_error_messages(item, prefix))
            return flattened

        field_path = prefix or 'form'
        message = '' if errors is None else str(errors)
        if message:
            flattened.append((field_path, message))
        return flattened

    def _singularize_label(self, label: str) -> str:
        """Best-effort singularization for indexed collection labels."""

        if label.endswith('ies') and len(label) > 3:
            return f'{label[:-3]}y'
        if label.endswith('s') and len(label) > 1:
            return label[:-1]
        return label

    def _humanize_error_field(self, field_path: str) -> str:
        """Convert internal field paths into user-friendly labels."""

        if not field_path or field_path == 'form':
            return 'Form'

        tokens: List[str | int] = []
        for name_token, index_token in re.findall(r'([^.\[\]]+)|\[(\d+)\]', field_path):
            if name_token:
                tokens.append(name_token)
            elif index_token:
                tokens.append(int(index_token))

        if not tokens:
            return field_path

        parts: List[str] = []
        for token in tokens:
            if isinstance(token, str):
                pretty = token.replace('_', ' ').strip().title()
                parts.append(pretty)
                continue

            if parts:
                collection_label = self._singularize_label(parts[-1])
                parts[-1] = f'{collection_label} #{token + 1}'
            else:
                parts.append(f'Item #{token + 1}')

        return ' — '.join(parts)

    def _render_error_summary(self, errors: Dict[str, Any]) -> str:
        """Render a framework-aware top-level summary for validation errors."""

        if not isinstance(errors, dict) or not errors:
            return ''

        flattened = self._flatten_error_messages(errors)
        if not flattened:
            return ''

        items_html = '\n'.join(
            f'<li><strong>{html.escape(self._humanize_error_field(field))}:</strong> {html.escape(message)}</li>'
            for field, message in flattened
        )

        if self.framework == 'material':
            return (
                '<section class="md-field">'
                '<div class="md-error-summary" role="alert" aria-live="polite">'
                '<div class="md-error-summary__title">Submission failed. Please correct the following:</div>'
                f'<ul class="md-error-summary__list">{items_html}</ul>'
                '</div>'
                '</section>'
            )

        return (
            '<div class="alert alert-danger schemaforms-error-summary" role="alert" aria-live="polite">'
            '<strong>Submission failed.</strong> Please correct the following:'
            f'<ul class="mb-0 mt-2">{items_html}</ul>'
            '</div>'
        )

    def _resolve_csrf_mode(
        self, *, include_csrf: bool, csrf_mode: CSRFMode | str, debug: bool
    ) -> str:
        explicit_field_only = csrf_mode in {CSRFMode.FIELD_ONLY, CSRF_MODE_FIELD_ONLY}
        if isinstance(csrf_mode, CSRFMode):
            normalized = csrf_mode.value
        else:
            normalized = str(csrf_mode or CSRF_MODE_OFF).strip().lower().replace('_', '-')

        # Backwards compatibility: include_csrf=True means at least field rendering.
        if include_csrf and normalized == CSRF_MODE_OFF:
            normalized = CSRF_MODE_FIELD_ONLY

        if normalized not in CSRF_MODES:
            raise ValueError(
                'Invalid csrf_mode. Expected one of: off, field-only, required-provider'
            )

        # Guard explicit field-only usage in non-debug contexts, while preserving
        # include_csrf backwards-compatibility flows that map off -> field-only.
        if explicit_field_only and normalized == CSRF_MODE_FIELD_ONLY and not debug:
            raise ValueError(
                "CSRF mode 'field-only' is only allowed when debug=True. "
                "Use 'required-provider' for production use."
            )

        return normalized

    def _resolve_csrf_token(
        self,
        csrf_token_provider: str | Callable[[], str] | None,
    ) -> str | None:
        if csrf_token_provider is None:
            return None

        token_value: Any
        if callable(csrf_token_provider):
            token_value = csrf_token_provider()
        else:
            token_value = csrf_token_provider

        if token_value is None:
            return None

        token = str(token_value)
        return token if token else None

    def _render_csrf_field(
        self,
        *,
        mode: str,
        csrf_token_provider: str | Callable[[], str] | None,
        csrf_field_name: str,
    ) -> str:
        if mode == CSRF_MODE_OFF:
            return ''

        token = self._resolve_csrf_token(csrf_token_provider)
        if mode == CSRF_MODE_REQUIRED_PROVIDER and token is None:
            raise ValueError(
                "CSRF mode 'required-provider' requires a csrf_token_provider that returns a token"
            )

        from .inputs.specialized_inputs import CSRFInput

        csrf_input = CSRFInput()
        safe_token = html.escape(token, quote=True) if token else ''
        return csrf_input.render(token=safe_token, name=csrf_field_name)

    def _render_layout_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        return self._layout_engine.render_layout_field(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _render_submit_button(self) -> str:
        button_class = self._theme.button_class() or self.config.get('button_class', '')
        return self._theme.render_submit_button(button_class)

    def _model_list_framework(self) -> str:
        """Allow subclasses to control which framework powers model list assets."""
        if self.framework == 'material':
            return 'bootstrap'
        return self.framework

    # ------------------------------------------------------------------ #
    #  Material Design field rendering                                     #
    #  Called by _render_field when self.framework == "material".          #
    #  These methods mirror the field-level logic that was previously      #
    #  maintained in SimpleMaterialRenderer as method overrides.           #
    # ------------------------------------------------------------------ #

    _MATERIAL_REQUIRED = 'required="required" aria-required="true"'

    @staticmethod
    def _attr(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ''

    def _render_material_help_block(self, help_text: Optional[str]) -> str:
        if not help_text:
            return ''
        return render_template(
            FormTemplates.MATERIAL_HELP_TEXT, help_content=html.escape(str(help_text))
        )

    def _render_material_error_block(self, error: Optional[str]) -> str:
        if not error:
            return ''
        return render_template(
            FormTemplates.MATERIAL_ERROR_TEXT, error_content=html.escape(str(error))
        )

    def _wrap_material_field_body(
        self, *, field_body: str, help_text: Optional[str], error: Optional[str]
    ) -> str:
        return render_template(
            FormTemplates.MATERIAL_FIELD_CONTAINER,
            field_body=field_body,
            help_text=self._render_material_help_block(help_text),
            error_text=self._render_material_error_block(error),
        )

    def _wrap_material_with_icon(self, icon: Optional[str], input_wrapper: str) -> str:
        if not icon:
            return input_wrapper
        icon_markup = render_material_icon(icon, classes='md-icon')
        return render_template(
            FormTemplates.MATERIAL_FIELD_WITH_ICON,
            icon_markup=icon_markup,
            input_wrapper=input_wrapper,
        )

    def _build_material_text_input_attributes(self, ui_info: Dict[str, Any]) -> str:
        attrs = []
        for source, attr_name in (
            ('min_value', 'min'),
            ('max_value', 'max'),
            ('min_length', 'minlength'),
            ('max_length', 'maxlength'),
            ('step', 'step'),
        ):
            if ui_info.get(source) is not None:
                attrs.append(f'{attr_name}="{html.escape(str(ui_info[source]))}"')
        extra = ui_info.get('attributes')
        if isinstance(extra, dict):
            for attr_name, attr_value in extra.items():
                if attr_value is not None:
                    attrs.append(f'{attr_name}="{html.escape(str(attr_value))}"')
        return ' '.join(attrs)

    def _build_material_select_options(
        self, ui_info: Dict[str, Any], field_schema: Dict[str, Any]
    ) -> List[List[str]]:
        options = ui_info.get('options', [])
        if not options and 'enum' in field_schema:
            options = [{'value': v, 'label': v} for v in field_schema['enum']]
        normalized: List[List[str]] = []
        for option in options:
            if isinstance(option, dict):
                opt_value = option.get('value', '')
                opt_label = option.get('label', opt_value)
            else:
                opt_value = opt_label = str(option)
            normalized.append([opt_value, opt_label])
        return normalized

    def _infer_material_input_type(self, field_schema: Dict[str, Any]) -> str:
        field_type = field_schema.get('type', 'string')
        field_format = field_schema.get('format', '')
        if field_format == 'email':
            return 'email'
        if field_format == 'date':
            return 'date'
        if field_type in ('integer', 'number'):
            return 'number'
        if field_type == 'boolean':
            return 'checkbox'
        if field_schema.get('enum'):
            return 'select'
        return 'text'

    def _render_material_text_input(
        self,
        field_name: str,
        input_type: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        is_required: bool,
    ) -> str:
        error_class = ' error' if error else ''
        attrs = self._build_material_text_input_attributes(ui_info)
        if is_required:
            attrs = f'{attrs} {self._MATERIAL_REQUIRED}'.strip()
        value_attr = self._attr(value) if value is not None else ''
        return render_template(
            FormTemplates.MATERIAL_TEXT_INPUT,
            input_type=input_type,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            value=value_attr,
            attributes=attrs,
        )

    def _render_material_textarea_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        is_required: bool,
    ) -> str:
        error_class = ' error' if error else ''
        attrs = self._MATERIAL_REQUIRED if is_required else ''
        value_content = html.escape(str(value)) if value is not None else ''
        return render_template(
            FormTemplates.MATERIAL_TEXTAREA,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            value=value_content,
            attributes=attrs,
        )

    def _render_material_select_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
        is_required: bool,
    ) -> str:
        error_class = ' error' if error else ''
        attrs = self._MATERIAL_REQUIRED if is_required else ''
        options = self._build_material_select_options(ui_info, field_schema)
        rendered_options = [
            render_template(FormTemplates.MATERIAL_SELECT_OPTION, value='', selected='', label='')
        ]
        for opt_value, opt_label in options:
            is_selected = str(value) == str(opt_value)
            rendered_options.append(
                render_template(
                    FormTemplates.MATERIAL_SELECT_OPTION,
                    value=self._attr(opt_value),
                    selected=' selected="selected"' if is_selected else '',
                    label=html.escape(str(opt_label)),
                )
            )
        return render_template(
            FormTemplates.MATERIAL_SELECT,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            options=''.join(rendered_options),
            attributes=attrs,
        )

    def _render_material_checkbox_field(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        required_text = ' *' if is_required else ''
        checked_attr = (
            'checked="checked"'
            if value is True or str(value).lower() in {'true', '1', 'on'}
            else ''
        )
        required_attr = self._MATERIAL_REQUIRED if is_required else ''
        return render_template(
            FormTemplates.MATERIAL_CHECKBOX_FIELD,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            label=html.escape(label),
            required_indicator=required_text,
            checked=checked_attr,
            required=required_attr,
            help_text=self._render_material_help_block(help_text),
            error_text=self._render_material_error_block(error),
        )

    def _render_material_outlined_field(
        self,
        field_name: str,
        input_type: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        required_text = ' *' if is_required else ''
        icon = ui_info.get('icon')
        if icon:
            icon = map_icon_for_framework(icon, 'material')

        if input_type == 'textarea':
            control_html = self._render_material_textarea_input(
                field_name, value, error, ui_info, is_required
            )
        elif input_type == 'select':
            control_html = self._render_material_select_input(
                field_name, value, error, ui_info, field_schema, is_required
            )
        else:
            control_html = self._render_material_text_input(
                field_name, input_type, value, error, ui_info, is_required
            )

        input_wrapper = render_template(
            FormTemplates.MATERIAL_FIELD_INPUT_WRAPPER,
            input_control=control_html,
            field_id=self._attr(field_name),
            label=html.escape(label),
            required_indicator=required_text,
        )
        field_body = self._wrap_material_with_icon(icon, input_wrapper)
        return self._wrap_material_field_body(
            field_body=field_body, help_text=help_text, error=error
        )

    def _render_material_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        _layout: str = 'vertical',
        all_errors: Optional[Dict[str, Any]] = None,
    ) -> str:
        context = context or RenderContext(form_data={}, schema_defs={})
        ui_info = field_schema.get('ui', {}) or field_schema

        if ui_info.get('hidden'):
            return (
                f'<input type="hidden" name="{field_name}" value="{html.escape(str(value or ""))}">'
            )

        input_type = (
            ui_info.get('input_type')
            or ui_info.get('element')
            or self._infer_material_input_type(field_schema)
        )

        if input_type == 'layout':
            return self._render_layout_field(
                field_name, field_schema, value, error, ui_info, context
            )

        if input_type == 'model_list':
            return self._render_material_model_list_field(
                field_name, field_schema, value, error, required_fields, context, all_errors
            )

        label = field_schema.get('title', field_name.replace('_', ' ').title())
        help_text = ui_info.get('help_text') or field_schema.get('description')
        is_required = field_name in (required_fields or [])

        if input_type == 'checkbox':
            return self._render_material_checkbox_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )

        return self._render_material_outlined_field(
            field_name,
            input_type,
            label,
            value,
            error,
            help_text,
            is_required,
            ui_info,
            field_schema,
        )

    def _render_material_model_list_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        all_errors: Optional[Dict[str, Any]] = None,
    ) -> str:
        context = context or RenderContext(form_data={}, schema_defs={})
        field_html = self._field_renderer.render_field(
            field_name,
            field_schema,
            value,
            error,
            required_fields or [],
            context,
            'vertical',
            all_errors or {},
        )
        return render_template(FormTemplates.MATERIAL_MODEL_LIST_WRAPPER, content=field_html)

    def _build_debug_panel(
        self,
        *,
        form_html: str,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]],
        errors: Optional[Dict[str, Any]],
        metadata: SchemaMetadata,
        render_time: float = 0.0,
    ) -> str:
        """Return a collapsed debug panel with tabs for rendered output, source, schema, and errors."""

        safe_data = data or {}
        safe_errors = errors or {}

        try:
            model_source = inspect.getsource(model_cls)
        except Exception as exc:  # pragma: no cover - defensive
            model_source = f'Source not available for {model_cls.__name__}: {exc}'

        try:
            schema_json = json.dumps(model_cls.model_json_schema(), indent=2, default=str)
        except Exception as exc:  # pragma: no cover - defensive
            schema_json = f'Schema generation failed: {exc}'

        try:
            schema = model_cls.model_json_schema()
            required = set(schema.get('required', []) or [])
            properties = schema.get('properties', {}) or {}
            validation_rules: Dict[str, Any] = {}
            for name, prop in properties.items():
                rule: Dict[str, Any] = {'required': name in required}
                for key in (
                    'type',
                    'format',
                    'pattern',
                    'minimum',
                    'maximum',
                    'minLength',
                    'maxLength',
                    'enum',
                ):
                    if key in prop:
                        rule[key] = prop[key]
                validation_rules[name] = rule
        except Exception as exc:  # pragma: no cover - defensive
            validation_rules = {'__error__': f'Could not derive constraints: {exc}'}

        rendered_tab = html.escape(form_html)
        source_tab = html.escape(model_source)
        schema_tab = html.escape(schema_json)
        validation_tab = html.escape(json.dumps(validation_rules, indent=2, default=str))
        live_tab = html.escape(
            json.dumps({'errors': safe_errors, 'data': safe_data}, indent=2, default=str)
        )

        # Format render time for display
        time_display = f' — {render_time:.3f}s render' if render_time > 0 else ''

        panel = f"""
<div class="pf-debug-panel">
    <details>
        <summary class="pf-debug-summary">Debug panel (development only){time_display}</summary>
        <div class="pf-debug-tabs">
            <div class="pf-debug-tablist" role="tablist">
                <button type="button" class="pf-debug-tab-btn pf-active" data-pf-tab="rendered">Rendered HTML</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="source">Form/model source</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="schema">Schema / validation</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="live">Live payload</button>
            </div>
            <div class="pf-debug-tab pf-active" data-pf-pane="rendered"><pre>{rendered_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="source"><pre>{source_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="schema"><pre>{schema_tab}</pre><pre>{validation_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="live"><pre class="pf-debug-live-output">{live_tab}</pre></div>
        </div>
    </details>
</div>
<style>
.pf-debug-panel {{ margin-top: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; }}
.pf-debug-summary {{ cursor: pointer; padding: 0.6rem 0.85rem; font-weight: 600; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }}
.pf-debug-tabs {{ padding: 0.35rem 0.85rem 0.75rem; }}
.pf-debug-tablist {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }}
.pf-debug-tab-btn {{ border: 1px solid #d0d7de; background: #ffffff; padding: 0.25rem 0.65rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }}
.pf-debug-tab-btn.pf-active {{ background: #0d6efd; color: #ffffff; border-color: #0d6efd; }}
.pf-debug-tab {{ display: none; }}
.pf-debug-tab.pf-active {{ display: block; }}
.pf-debug-tab pre {{ white-space: pre-wrap; word-break: break-word; font-size: 0.85rem; background: #ffffff; border: 1px dashed #d0d7de; padding: 0.65rem; border-radius: 6px; margin: 0.35rem 0; overflow: auto; }}
</style>
<script>
(function() {{
    document.querySelectorAll('.pf-debug-panel').forEach(function(panel) {{
        var buttons = panel.querySelectorAll('[data-pf-tab]');
        var panes = panel.querySelectorAll('[data-pf-pane]');
        buttons.forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                var target = btn.getAttribute('data-pf-tab');
                buttons.forEach(function(b) {{ b.classList.remove('pf-active'); }});
                panes.forEach(function(p) {{ p.classList.remove('pf-active'); }});
                btn.classList.add('pf-active');
                var pane = panel.querySelector('[data-pf-pane="' + target + '"]');
                if (pane) {{ pane.classList.add('pf-active'); }}
            }});
        }});

        // Live payload updater
        var form = document.querySelector('form');
        var liveOutput = panel.querySelector('.pf-debug-live-output');
        if (form && liveOutput) {{
            function updateLivePayload() {{
                var formData = new FormData(form);
                var data = {{}};
                var seen = {{}};

                // Parse form data including arrays (pets[0].name, etc.)
                for (var pair of formData.entries()) {{
                    var key = pair[0];
                    var value = pair[1];

                    // Handle array notation like pets[0].name
                    var arrayMatch = key.match(/^(\\w+)\\[(\\d+)\\]\\.(\\w+)$/);
                    if (arrayMatch) {{
                        var arrayName = arrayMatch[1];
                        var index = parseInt(arrayMatch[2]);
                        var fieldName = arrayMatch[3];

                        if (!data[arrayName]) {{
                            data[arrayName] = [];
                        }}
                        if (!data[arrayName][index]) {{
                            data[arrayName][index] = {{}};
                        }}
                        data[arrayName][index][fieldName] = value;
                        seen[key] = true;
                    }} else if (key in seen) {{
                        // Multiple values for same key - convert to array
                        if (!Array.isArray(data[key])) {{
                            data[key] = [data[key]];
                        }}
                        data[key].push(value);
                    }} else {{
                        data[key] = value;
                        seen[key] = true;
                    }}
                }}

                // Handle checkboxes (unchecked = not in FormData)
                var checkboxes = form.querySelectorAll('input[type=\"checkbox\"]');
                checkboxes.forEach(function(cb) {{
                    if (!cb.name) return;
                    if (!(cb.name in data)) {{
                        data[cb.name] = false;
                    }} else if (data[cb.name] === 'on') {{
                        data[cb.name] = true;
                    }}
                }});

                var payload = {{ data: data, errors: {{}} }};
                liveOutput.textContent = JSON.stringify(payload, null, 2);
            }}

            // Update on any input change
            form.addEventListener('input', updateLivePayload);
            form.addEventListener('change', updateLivePayload);

            // Initial update after a brief delay to catch dynamic content
            setTimeout(updateLivePayload, 100);
        }}
    }});
}})();
</script>
"""

        return panel


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Dict[str, str] | SchemaFormValidationError | None = None,
    framework: str = 'bootstrap',
    layout: str = 'vertical',
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    *,
    include_html_markers: bool = True,
    **kwargs,
) -> str:
    """Convenience wrapper mirroring the legacy helper."""

    # Backwards-compatible knobs (historically accepted via kwargs).
    # - self_contained: inline framework assets (CSS/JS) for the selected framework.
    # - include_framework_assets: explicit opt-in for framework assets.
    # - asset_mode: 'vendored' (inline) or 'cdn' (external).
    self_contained = bool(kwargs.pop('self_contained', False))
    include_framework_assets = bool(kwargs.pop('include_framework_assets', False))
    asset_mode = str(kwargs.pop('asset_mode', 'vendored'))
    submit_url_raw = kwargs.pop('submit_url', None)
    if submit_url_raw is None:
        raise ValueError('submit_url is required; the library does not choose submission targets')
    submit_url = str(submit_url_raw).strip()
    if not submit_url:
        raise ValueError('submit_url cannot be empty')
    if self_contained:
        include_framework_assets = True

    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get('name', ''): err.get('message', '') for err in errors.errors}
        errors = error_dict

    renderer = EnhancedFormRenderer(
        framework=framework,
        include_framework_assets=include_framework_assets,
        asset_mode=asset_mode,
    )
    html = renderer.render_form_from_model(
        form_model_cls,
        data=form_data,
        errors=errors,
        submit_url=submit_url,
        layout=layout,
        debug=debug,
        show_timing=show_timing,
        enable_logging=enable_logging,
        **kwargs,
    )
    return wrap_with_schemaforms_markers(html, enabled=include_html_markers)


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Dict[str, str] | SchemaFormValidationError | None = None,
    framework: str = 'bootstrap',
    layout: str = 'vertical',
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    *,
    include_html_markers: bool = True,
    **kwargs,
) -> str:
    """Async counterpart to render_form_html."""

    # Ensure these knobs work consistently in async mode too.
    self_contained = bool(kwargs.pop('self_contained', False))
    include_framework_assets = bool(kwargs.pop('include_framework_assets', False))
    asset_mode = str(kwargs.pop('asset_mode', 'vendored'))
    if self_contained:
        include_framework_assets = True

    render_callable = partial(
        render_form_html,
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        layout=layout,
        debug=debug,
        show_timing=show_timing,
        enable_logging=enable_logging,
        include_framework_assets=include_framework_assets,
        asset_mode=asset_mode,
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    html = await loop.run_in_executor(None, render_callable)
    return wrap_with_schemaforms_markers(html, enabled=include_html_markers)
