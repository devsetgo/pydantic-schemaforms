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
import time
from enum import Enum
from functools import partial
from typing import Any
from collections.abc import Callable

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticSerializationError, PydanticUndefined, to_jsonable_python

from .html_markers import wrap_with_schemaforms_markers
from .rendering.context import RenderContext
from .rendering.field_renderer import FieldRenderer
from .error_tree import iter_errors, normalize_error_tree
from .form_data import decode_submission
from .rendering.layout_engine import (
    GROUPED_LAYOUTS,
    LayoutEngine,
    check_layout,
    check_wizard_options,
)
from .rendering.schema_parser import (
    SchemaMetadata,
    build_schema_metadata,
    extract_ui_info,
    resolve_nested_model_ref,
    resolve_list_item_ref,
    resolve_ui_element,
)
from .rendering.themes import (
    MaterialTheme,
    RendererTheme,
    class_defaults_for_theme,
    get_theme_for_framework,
)
from .schema_form import FormModel
from .tstring import SafeHTML
from .tstring import html as render_html

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class CSRFMode(str, Enum):
    """How `render_form_html()`/`render_form_from_model()` handle CSRF.

    - `OFF`: no CSRF field rendered (default).
    - `FIELD_ONLY`: renders the field with an empty token if no
      `csrf_token_provider` is given -- not a real protection, so it's
      only accepted when `debug=True` (see `_resolve_csrf_mode`); use it
      for local prototyping only.
    - `REQUIRED_PROVIDER`: renders the field and raises `ValueError` unless
      `csrf_token_provider` supplies a non-empty token -- the mode meant
      for production use.
    """

    OFF = 'off'
    FIELD_ONLY = 'field-only'
    REQUIRED_PROVIDER = 'required-provider'


CSRF_MODE_OFF = CSRFMode.OFF.value
CSRF_MODE_FIELD_ONLY = CSRFMode.FIELD_ONLY.value
CSRF_MODE_REQUIRED_PROVIDER = CSRFMode.REQUIRED_PROVIDER.value
CSRF_MODES = {mode.value for mode in CSRFMode}


class SchemaFormValidationError(Exception):
    """Raised when validation errors match the SchemaForm contract."""

    def __init__(self, errors: list[dict[str, Any]]):
        self.errors = errors
        super().__init__('Schema form validation error')


def _general_group_title(model_cls: type[FormModel], metadata: SchemaMetadata) -> str:
    """Heading of the group holding a parent's own plain fields under a
    grouped layout: the model's explicit title, else "General"."""
    title = metadata.schema.get('title')
    return title if title and title != model_cls.__name__ else 'General'


def _field_default(info: FieldInfo) -> Any:
    """A field's starting value, or None when it has none to show."""
    if info.default_factory is not None:
        if info.default_factory_takes_validated_data:
            return None
        return info.default_factory()  # type: ignore[call-arg]
    if info.default is not PydanticUndefined:
        return info.default
    if isinstance(info.annotation, type) and issubclass(info.annotation, BaseModel):
        return EnhancedFormRenderer._model_defaults(info.annotation)
    return None


def _render_values(raw: Any) -> dict[str, Any]:
    """Submitted or app-supplied data, decoded into the nested shape the
    renderer reads."""
    return _enum_values(decode_submission(raw))


def _enum_values(value: Any) -> Any:
    # Data from a database row or a model_dump() holds Enum members, while
    # every option, radio and checkbox carries the member's value.
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _enum_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_enum_values(item) for item in value]
    return value


def _schema_has_file_input(
    schema: dict[str, Any], schema_defs: dict[str, Any], seen: frozenset[str] = frozenset()
) -> bool:
    for _name, field_schema in (schema.get('properties') or {}).items():
        if resolve_ui_element(field_schema) == 'file':
            return True
        ref = resolve_nested_model_ref(field_schema) or resolve_list_item_ref(field_schema)
        if ref and ref not in seen and ref in schema_defs:
            if _schema_has_file_input(schema_defs[ref], schema_defs, seen | {ref}):
                return True
    return False


def _has_file_field(
    fields: list[tuple[str, dict[str, Any]]],
    data: dict[str, Any],
    schema_defs: dict[str, Any] | None = None,
) -> bool:
    """Whether this form needs `enctype="multipart/form-data"`: either a
    top-level `input_type='file'` field, or a `layout_handler`-dispatched
    field whose *current value* will render its own nested file input (see
    `LayoutEngine.layout_field_needs_multipart` -- a layout field's own
    schema only ever says `ui_element == 'layout'`, never revealing what it
    actually renders, so that has to be checked separately, using the
    field's value, not its static schema)."""
    for field_name, field_schema in fields:
        ui_element = resolve_ui_element(field_schema)
        if ui_element == 'file':
            return True
        if ui_element in ('nested_model', 'model_list') and _schema_has_file_input(
            {'properties': {field_name: field_schema}}, schema_defs or {}
        ):
            return True
        if ui_element == 'layout':
            ui_info = extract_ui_info(field_schema)
            handler_name = ui_info.get('layout_handler') or ui_info.get('layout_renderer')
            if LayoutEngine.layout_field_needs_multipart(handler_name, data.get(field_name)):
                return True
    return False


class EnhancedFormRenderer:
    """Render Pydantic FormModels into HTML using UI metadata."""

    config: dict[str, str]

    def __init__(
        self,
        framework: str = 'bootstrap',
        theme: RendererTheme | None = None,
        *,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
        material_variant: str | None = None,
    ):
        self.framework = framework
        self.include_framework_assets = include_framework_assets
        if material_variant is not None and material_variant not in MaterialTheme.VARIANTS:
            raise ValueError(
                f"material_variant must be 'outlined' or 'filled', not {material_variant!r}"
            )
        resolved_theme = theme or get_theme_for_framework(
            framework,
            include_assets=include_framework_assets,
            asset_mode=asset_mode,
            material_variant=material_variant,
        )
        self._theme: RendererTheme = resolved_theme
        self.asset_mode = asset_mode
        self.class_defaults = class_defaults_for_theme(self._theme, framework)
        self._layout_engine = LayoutEngine(self)
        self._field_renderer = FieldRenderer(self)

    @property
    def theme(self) -> RendererTheme:
        return self._theme

    def render_form_from_model(
        self,
        model_cls: type[FormModel],
        data: dict[str, Any] | None = None,
        errors: dict[Any, Any] | None = None,
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
        inject_layout_styles: bool = True,
        **kwargs: Any,
    ) -> str:
        """Render a complete HTML form from a FormModel definition."""

        # Start timing
        start_time = time.perf_counter()

        check_layout(layout)
        wizard_options = check_wizard_options(kwargs.pop('wizard_options', None))
        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        # A fresh form (no data passed) starts from the model's defaults. Data
        # that was passed, such as a submission being re-rendered, is used as
        # is: an unticked checkbox is simply absent from a submission, so
        # filling in its default would tick it again.
        if data is None:
            data = self._model_defaults(model_cls)
        data = _render_values(data)

        # Keep backward compatibility for callers still passing these via kwargs.
        include_csrf = bool(kwargs.pop('include_csrf', False))
        csrf_field_name = kwargs.pop('csrf_field_name', 'csrf_token') or 'csrf_token'

        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        errors = normalize_error_tree(errors)
        error_summary_markup = self._render_error_summary(errors)

        default_form_class = self._theme.form_class() or self.class_defaults.form_class()
        form_attrs: dict[str, Any] = {
            'method': method,
            'action': submit_url,
            'class': default_form_class,
            'novalidate': True,
        }
        # A <form> with a file input still submits under the default
        # application/x-www-form-urlencoded encoding unless told otherwise --
        # which silently sends only the filename, never the file's contents.
        # Auto-set multipart/form-data whenever the model has a file field,
        # unless the caller already chose an enctype explicitly.
        if 'enctype' not in kwargs and _has_file_field(metadata.fields, data, metadata.schema_defs):
            form_attrs['enctype'] = 'multipart/form-data'
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
        form_body_parts: list[str] = []
        self._prefill_layout_field_defaults(model_cls, metadata, data)

        if layout in GROUPED_LAYOUTS:
            form_body_parts.extend(
                self._layout_engine.render_groups(
                    metadata,
                    data,
                    errors,
                    context,
                    mode=layout,
                    general_title=_general_group_title(model_cls, metadata),
                    wizard_options=wizard_options,
                )
            )
        else:
            for field_name, field_schema in metadata.fields:
                form_body_parts.append(
                    self._render_field(
                        field_name,
                        field_schema,
                        data.get(field_name),
                        errors.get(field_name),
                        metadata.required_fields,
                        context,
                        'vertical',
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

        styles = self._render_layout_support_styles() if inject_layout_styles else ''
        output_parts = [styles, form_markup] if styles else [form_markup]

        # Direct top-level fields cover the common case, but a form composed
        # entirely of layout/tab fields (e.g. a tabbed wrapper) never lists
        # 'model_list' among its own fields even when a nested sub-form
        # rendered inside one of its tabs does -- so also check the actual
        # rendered markup for the add-item button that model_list fields
        # always emit, regardless of nesting depth or framework.
        has_model_list_fields = (
            any(
                resolve_ui_element(field_schema) == 'model_list'
                for _name, field_schema in metadata.fields
            )
            or 'add-item-btn' in form_markup
        )
        if has_model_list_fields:
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer()
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
            render_time=render_time,
        )

    def render_form_fields_only(
        self,
        model_cls: type[FormModel],
        data: dict[str, Any] | None = None,
        errors: dict[Any, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render only the field markup for nested usage."""

        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        data = _render_values(data)
        errors = normalize_error_tree(errors)
        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        form_parts: list[str] = []
        for field_name, field_schema in metadata.fields:
            form_parts.append(
                self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    metadata.required_fields,
                    context,
                    'vertical',
                )
            )

        return '\n'.join(form_parts)

    async def render_form_from_model_async(
        self,
        model_cls: type[FormModel],
        data: dict[str, Any] | None = None,
        errors: dict[Any, Any] | None = None,
        *,
        submit_url: str = '/submit',
        method: str = 'POST',
        include_csrf: bool = False,
        csrf_mode: CSRFMode | str = CSRF_MODE_OFF,
        csrf_token_provider: str | Callable[[], str] | None = None,
        csrf_field_name: str = 'csrf_token',
        include_submit_button: bool = True,
        layout: str = 'vertical',
        inject_layout_styles: bool = True,
        **kwargs: Any,
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
            inject_layout_styles=inject_layout_styles,
            **kwargs,
        )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, render_callable)

    @staticmethod
    def _model_defaults(model_cls: type[BaseModel]) -> dict[str, Any]:
        """The values a fresh form starts with: each field's default, in the
        same JSON-ish shape a submission has (an Enum as its value, a date as
        ISO text). A required sub-form starts with its own defaults."""
        defaults: dict[str, Any] = {}
        if not (isinstance(model_cls, type) and issubclass(model_cls, BaseModel)):
            return defaults
        for name, info in model_cls.model_fields.items():
            value = _field_default(info)
            if value is None:
                continue
            try:
                defaults[info.alias or name] = to_jsonable_python(value)
            except PydanticSerializationError:
                defaults[info.alias or name] = value  # e.g. a layout value holding a model class
        return defaults

    @staticmethod
    def _prefill_layout_field_defaults(
        model_cls: type[FormModel], metadata: SchemaMetadata, data: dict[str, Any]
    ) -> None:
        """A layout_handler field (e.g. DataTableLayout) renders from its value,
        so seed a missing value from the field's default/default_factory."""
        model_fields = getattr(model_cls, 'model_fields', {}) or {}
        for field_name, _field_schema in metadata.layout_fields:
            if field_name in data:
                continue
            field_info = model_fields.get(field_name)
            if not field_info:
                continue
            default_factory = getattr(field_info, 'default_factory', None)
            if default_factory is not None:
                # A factory taking validated data can't run before validation.
                if not getattr(field_info, 'default_factory_takes_validated_data', False):
                    data[field_name] = default_factory()
            elif not field_info.is_required():
                default_value = getattr(field_info, 'default', None)
                if default_value is not None:
                    data[field_name] = default_value

    def _render_field(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any = None,
        error: Any = None,
        required_fields: list[str] | None = None,
        context: RenderContext | None = None,
        layout: str = 'vertical',
    ) -> str:
        """``error`` is the field's error node (see ``pydantic_schemaforms.error_tree``)."""
        return self._field_renderer.render_field(
            field_name, field_schema, value, error, required_fields, context, layout
        )

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
    width: 100%;
    max-width: none;
}

.pydantic-form [class*="col-"],
.md-form [class*="col-"] {
    min-width: 0;
    flex: 1 1 auto;
}

.pydantic-form [class*="section"],
.pydantic-form [data-schemaforms-section],
.pydantic-form fieldset,
.md-form [class*="section"],
.md-form [data-schemaforms-section],
.md-form fieldset {
    width: 100%;
    max-width: none;
    box-sizing: border-box;
}
</style>
"""

    def _singularize_label(self, label: str) -> str:
        """Best-effort singularization for indexed collection labels."""

        if label.endswith('ies') and len(label) > 3:
            return f'{label[:-3]}y'
        if label.endswith('s') and len(label) > 1:
            return label[:-1]
        return label

    def _humanize_error_loc(self, loc: tuple[Any, ...]) -> str:
        """Turn an error location like ``('pets', 1, 'name')`` into ``Pet #2 — Name``."""

        if not loc:
            return 'Form'

        parts: list[str] = []
        for token in loc:
            if isinstance(token, int) or (isinstance(token, str) and token.isdigit()):
                index = int(token)
                if parts:
                    parts[-1] = f'{self._singularize_label(parts[-1])} #{index + 1}'
                else:
                    parts.append(f'Item #{index + 1}')
                continue
            parts.append(str(token).replace('_', ' ').strip().title())
        return ' — '.join(parts)

    def _render_error_summary(self, errors: dict[Any, Any]) -> str:
        """Render a framework-aware top-level summary for validation errors."""

        flattened = list(iter_errors(errors))
        if not flattened:
            return ''

        item_parts = []
        for loc, message in flattened:
            # NOSONAR comment below: humanized_field is read via
            # {humanized_field} interpolation in the t-string below.
            humanized_field = self._humanize_error_loc(loc)  # NOSONAR
            item_parts.append(
                render_html(t'<li><strong>{humanized_field}:</strong> {message}</li>')
            )
        return self._theme.render_error_summary('\n'.join(item_parts))

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
        return csrf_input.render(token=token or '', name=csrf_field_name)

    def _render_layout_field(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any,
        ui_info: dict[str, Any],
        context: RenderContext,
    ) -> str:
        return self._layout_engine.render_layout_field(
            field_name,
            field_schema,
            value,
            ui_info,
            context,
        )

    def _render_submit_button(self) -> str:
        button_class = self._theme.button_class() or self.class_defaults.button_class()
        return self._theme.render_submit_button(button_class)

    def _build_debug_panel(
        self,
        *,
        form_html: str,
        model_cls: type[FormModel],
        data: dict[str, Any] | None,
        errors: dict[str, Any] | None,
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
            validation_rules: dict[str, Any] = {}
            for name, prop in properties.items():
                rule: dict[str, Any] = {'required': name in required}
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

        # rendered_tab/source_tab/schema_tab/validation_tab/live_tab are
        # already html.escape()'d above -- they're rendered *as visible text*
        # inside <pre> (showing the raw HTML/JSON as a string, not executing
        # it), so they're wrapped in SafeHTML here to avoid double-escaping.
        _rendered_tab = SafeHTML(rendered_tab)
        _source_tab = SafeHTML(source_tab)
        _schema_tab = SafeHTML(schema_tab)
        _validation_tab = SafeHTML(validation_tab)
        _live_tab = SafeHTML(live_tab)

        panel_body = render_html(t"""
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
            <div class="pf-debug-tab pf-active" data-pf-pane="rendered"><pre>{_rendered_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="source"><pre>{_source_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="schema"><pre>{_schema_tab}</pre><pre>{_validation_tab}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="live"><pre class="pf-debug-live-output">{_live_tab}</pre></div>
        </div>
    </details>
</div>
""")

        # Static CSS/JS below (rule 4 exception) -- no user data is
        # interpolated, so it stays a plain string appended as trusted,
        # developer-authored markup.
        panel_assets = SafeHTML("""
<style>
.pf-debug-panel { margin-top: 1.5rem; border: 1px solid var(--sf-outline-variant, #e0e0e0); border-radius: 8px; background: var(--sf-surface-low, #fafafa); }
.pf-debug-summary { cursor: pointer; padding: 0.6rem 0.85rem; font-weight: 600; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
.pf-debug-tabs { padding: 0.35rem 0.85rem 0.75rem; }
.pf-debug-tablist { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
.pf-debug-tab-btn { border: 1px solid var(--sf-outline-variant, #d0d7de); background: var(--sf-surface, #ffffff); color: inherit; padding: 0.25rem 0.65rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
.pf-debug-tab-btn.pf-active { background: var(--sf-primary, #0d6efd); color: var(--sf-on-primary, #ffffff); border-color: var(--sf-primary, #0d6efd); }
.pf-debug-tab { display: none; }
.pf-debug-tab.pf-active { display: block; }
.pf-debug-tab pre { white-space: pre-wrap; word-break: break-word; font-size: 0.85rem; background: var(--sf-surface, #ffffff); border: 1px dashed var(--sf-outline-variant, #d0d7de); padding: 0.65rem; border-radius: 6px; margin: 0.35rem 0; overflow: auto; }
</style>
<script>
(function() {
    document.querySelectorAll('.pf-debug-panel').forEach(function(panel) {
        var buttons = panel.querySelectorAll('[data-pf-tab]');
        var panes = panel.querySelectorAll('[data-pf-pane]');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var target = btn.getAttribute('data-pf-tab');
                buttons.forEach(function(b) { b.classList.remove('pf-active'); });
                panes.forEach(function(p) { p.classList.remove('pf-active'); });
                btn.classList.add('pf-active');
                var pane = panel.querySelector('[data-pf-pane="' + target + '"]');
                if (pane) { pane.classList.add('pf-active'); }
            });
        });

        // Live payload updater
        var form = document.querySelector('form');
        var liveOutput = panel.querySelector('.pf-debug-live-output');
        if (form && liveOutput) {
            function updateLivePayload() {
                var formData = new FormData(form);
                var data = {};
                var seen = {};

                // Parse form data including arrays (pets[0].name, etc.)
                for (var pair of formData.entries()) {
                    var key = pair[0];
                    var value = pair[1];

                    // Handle array notation like pets[0].name
                    var arrayMatch = key.match(/^(\\w+)\\[(\\d+)\\]\\.(\\w+)$/);
                    if (arrayMatch) {
                        var arrayName = arrayMatch[1];
                        var index = parseInt(arrayMatch[2]);
                        var fieldName = arrayMatch[3];

                        if (!data[arrayName]) {
                            data[arrayName] = [];
                        }
                        if (!data[arrayName][index]) {
                            data[arrayName][index] = {};
                        }
                        data[arrayName][index][fieldName] = value;
                        seen[key] = true;
                    } else if (key in seen) {
                        // Multiple values for same key - convert to array
                        if (!Array.isArray(data[key])) {
                            data[key] = [data[key]];
                        }
                        data[key].push(value);
                    } else {
                        data[key] = value;
                        seen[key] = true;
                    }
                }

                // Handle checkboxes (unchecked = not in FormData)
                var checkboxes = form.querySelectorAll('input[type=\"checkbox\"]');
                checkboxes.forEach(function(cb) {
                    if (!cb.name) return;
                    if (!(cb.name in data)) {
                        data[cb.name] = false;
                    } else if (data[cb.name] === 'on') {
                        data[cb.name] = true;
                    }
                });

                var payload = { data: data, errors: {} };
                liveOutput.textContent = JSON.stringify(payload, null, 2);
            }

            // Update on any input change
            form.addEventListener('input', updateLivePayload);
            form.addEventListener('change', updateLivePayload);

            // Initial update after a brief delay to catch dynamic content
            setTimeout(updateLivePayload, 100);
        }
    });
})();
</script>
""")

        return panel_body + panel_assets


def render_form_html(
    form_model_cls: type[FormModel],
    form_data: dict[str, Any] | None = None,
    errors: dict[str, str] | SchemaFormValidationError | None = None,
    framework: str = 'bootstrap',
    layout: str = 'vertical',
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    *,
    include_html_markers: bool = True,
    **kwargs: Any,
) -> str:
    """Render a FormModel to a complete HTML `<form>` -- the library's primary
    entry point (see the package docstring).

    `submit_url` is required as a keyword-only kwarg (via **kwargs) since the
    library never chooses a submission target on its own. `csrf_mode` (a
    `CSRFMode` or its string value) and `csrf_token_provider` control CSRF
    field rendering -- see `CSRFMode`. `self_contained`/`include_framework_assets`/
    `asset_mode` control whether the selected framework's CSS/JS is inlined
    into the returned HTML. Remaining **kwargs (e.g. `csrf_mode`,
    `include_submit_button`) are forwarded to `EnhancedFormRenderer.render_form_from_model`.
    """

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
        material_variant=kwargs.pop('material_variant', None),
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


def render_display_html(
    form_model_cls: type[FormModel],
    data: Any,
    framework: str = 'bootstrap',
    layout: str = 'vertical',
    *,
    edit_urls: dict[str, str] | None = None,
    self_contained: bool = False,
    include_framework_assets: bool = False,
    asset_mode: str = 'vendored',
    material_variant: str | None = None,
    include_html_markers: bool = True,
) -> str:
    """Render validated data as a read-only review page; see `FormModel.render_display`."""

    from .rendering.display_renderer import render_display

    renderer = EnhancedFormRenderer(
        framework=framework,
        include_framework_assets=include_framework_assets or self_contained,
        asset_mode=asset_mode,
        material_variant=material_variant,
    )
    metadata = build_schema_metadata(form_model_cls)
    output = render_display(
        renderer,
        metadata,
        data,
        layout=layout,
        general_title=_general_group_title(form_model_cls, metadata),
        edit_urls=edit_urls,
    )
    return wrap_with_schemaforms_markers(output, enabled=include_html_markers)


async def render_form_html_async(
    form_model_cls: type[FormModel],
    form_data: dict[str, Any] | None = None,
    errors: dict[str, str] | SchemaFormValidationError | None = None,
    framework: str = 'bootstrap',
    layout: str = 'vertical',
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    *,
    include_html_markers: bool = True,
    **kwargs: Any,
) -> str:
    """Same as render_form_html(), but runs it in the default executor via
    `loop.run_in_executor` so it doesn't block the event loop -- rendering
    itself is synchronous CPU-bound work, not async I/O."""

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
        include_html_markers=include_html_markers,
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
