
"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

from __future__ import annotations

import asyncio
import html
import inspect
import json
from functools import partial
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .rendering.context import RenderContext
from .rendering.field_renderer import FieldRenderer
from .rendering.frameworks import get_framework_config
from .rendering.layout_engine import LayoutEngine, get_nested_form_data
from .rendering.schema_parser import SchemaMetadata, build_schema_metadata, resolve_ui_element
from .rendering.themes import RendererTheme, get_theme_for_framework
from .schema_form import FormModel


class SchemaFormValidationError(Exception):
    """Raised when validation errors match the SchemaForm contract."""

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__("Schema form validation error")


class EnhancedFormRenderer:
    """Render Pydantic FormModels into HTML using UI metadata."""

    def __init__(
        self,
        framework: str = "bootstrap",
        theme: Optional[RendererTheme] = None,
        *,
        include_framework_assets: bool = False,
        asset_mode: str = "vendored",
    ):
        self.framework = framework
        self.include_framework_assets = include_framework_assets
        resolved_theme = theme or get_theme_for_framework(
            framework,
            include_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
        self._theme: RendererTheme = resolved_theme
        self.asset_mode = asset_mode
        if hasattr(self._theme, "config"):
            self.config = self._theme.config
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
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        include_csrf: bool = False,
        include_submit_button: bool = True,
        layout: str = "vertical",
        debug: bool = False,
        **kwargs,
    ) -> str:
        """Render a complete HTML form from a FormModel definition."""

        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        if isinstance(errors, dict) and "errors" in errors:
            errors = {err.get("name", ""): err.get("message", "") for err in errors["errors"]}

        default_form_class = self._theme.form_class() or self.config.get("form_class", "")
        form_attrs = {
            "method": method,
            "action": submit_url,
            "class": default_form_class,
            "novalidate": True,
        }
        form_attrs.update(kwargs)
        form_attrs["action"] = submit_url  # kwargs must not override action
        form_attrs = self._theme.transform_form_attributes(form_attrs)

        csrf_markup = self._render_csrf_field() if include_csrf else ""
        form_body_parts: List[str] = []

        fields = metadata.fields
        required_fields = metadata.required_fields
        layout_fields = metadata.layout_fields
        non_layout_fields = metadata.non_layout_fields

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
        elif layout == "tabbed":
            form_body_parts.extend(
                self._render_tabbed_layout(fields, data, errors, required_fields, context)
            )
        elif layout == "side-by-side":
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

        submit_markup = self._render_submit_button() if include_submit_button else ""

        form_markup = self._theme.render_form_wrapper(
            form_attrs=form_attrs,
            csrf_token=csrf_markup,
            form_content="\n".join(form_body_parts),
            submit_markup=submit_markup,
        )

        output_parts = [form_markup]

        # Include model-list JavaScript when any model-list markup is present.
        # Layout fields can render nested models (via render_form_fields_only), so scanning
        # only the top-level schema fields would miss model-list widgets inside layouts.
        has_model_list_fields = any(
            resolve_ui_element(field_schema) == "model_list" for _name, field_schema in fields
        )
        has_model_list_markup = (
            "model-list-container" in form_markup
            or "add-item-btn" in form_markup
            or "remove-item-btn" in form_markup
        )
        has_model_list_script = "function initializeModelLists" in form_markup

        if (has_model_list_fields or has_model_list_markup) and not has_model_list_script:
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self._model_list_framework())
            output_parts.append(list_renderer.get_model_list_javascript())

        combined_output = "\n".join(output_parts)

        if not debug:
            return combined_output

        return combined_output + self._build_debug_panel(
            form_html=combined_output,
            model_cls=model_cls,
            data=data,
            errors=errors,
            metadata=metadata,
        )

    def render_form_fields_only(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """Render only the field markup for nested usage."""

        metadata: SchemaMetadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        context = RenderContext(form_data=data, schema_defs=metadata.schema_defs)

        if isinstance(errors, dict) and "errors" in errors:
            errors = {err.get("name", ""): err.get("message", "") for err in errors["errors"]}

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

        return "\n".join(form_parts)

    async def render_form_from_model_async(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        include_csrf: bool = False,
        include_submit_button: bool = True,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """Async wrapper for render_form_from_model."""

        render_callable = partial(
            self.render_form_from_model,
            model_cls,
            data,
            errors,
            submit_url,
            method,
            include_csrf,
            include_submit_button,
            layout,
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
        layout: str = "vertical",
        all_errors: Optional[Dict[str, str]] = None,
    ) -> str:
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
        return self._layout_engine.render_tabbed_layout(fields, data, errors, required_fields, context)

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
        field_prefix = f"{field_name}["

        for error_path, error_message in (all_errors or {}).items():
            if error_path.startswith(field_prefix):
                nested_part = error_path[len(field_prefix) :]
                if "]." in nested_part:
                    nested_errors[nested_part.replace("].", ".")] = error_message

        return nested_errors

    def _render_csrf_field(self) -> str:
        return '<input type="hidden" name="csrf_token" value="__CSRF_TOKEN__" />'

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
        button_class = self._theme.button_class() or self.config.get("button_class", "")
        return self._theme.render_submit_button(button_class)

    def _model_list_framework(self) -> str:
        """Allow subclasses to control which framework powers model list assets."""

        return self.framework

    def _build_debug_panel(
        self,
        *,
        form_html: str,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]],
        errors: Optional[Dict[str, Any]],
        metadata: SchemaMetadata,
    ) -> str:
        """Return a collapsed debug panel with tabs for rendered output, source, schema, and errors."""

        safe_data = data or {}
        safe_errors = errors or {}

        try:
            model_source = inspect.getsource(model_cls)
        except Exception as exc:  # pragma: no cover - defensive
            model_source = f"Source not available for {model_cls.__name__}: {exc}"

        try:
            schema_json = json.dumps(model_cls.model_json_schema(), indent=2, default=str)
        except Exception as exc:  # pragma: no cover - defensive
            schema_json = f"Schema generation failed: {exc}"

        try:
            schema = model_cls.model_json_schema()
            required = set(schema.get("required", []) or [])
            properties = schema.get("properties", {}) or {}
            validation_rules: Dict[str, Any] = {}
            for name, prop in properties.items():
                rule: Dict[str, Any] = {"required": name in required}
                for key in (
                    "type",
                    "format",
                    "pattern",
                    "minimum",
                    "maximum",
                    "minLength",
                    "maxLength",
                    "enum",
                ):
                    if key in prop:
                        rule[key] = prop[key]
                validation_rules[name] = rule
        except Exception as exc:  # pragma: no cover - defensive
            validation_rules = {"__error__": f"Could not derive constraints: {exc}"}

        rendered_tab = html.escape(form_html)
        source_tab = html.escape(model_source)
        schema_tab = html.escape(schema_json)
        validation_tab = html.escape(json.dumps(validation_rules, indent=2, default=str))
        live_tab = html.escape(json.dumps({"errors": safe_errors, "data": safe_data}, indent=2, default=str))

        panel = r"""
<div class="pf-debug-panel">
    <details>
        <summary class="pf-debug-summary">Debug panel (development only)</summary>
        <div class="pf-debug-tabs">
            <div class="pf-debug-tablist" role="tablist">
                <button type="button" class="pf-debug-tab-btn pf-active" data-pf-tab="rendered">Rendered HTML</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="source">Form/model source</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="schema">Schema / validation</button>
                <button type="button" class="pf-debug-tab-btn" data-pf-tab="live">Live payload</button>
            </div>
            <div class="pf-debug-tab pf-active" data-pf-pane="rendered"><pre>{rendered}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="source"><pre>{source}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="schema"><pre>{schema}</pre><pre>{rules}</pre></div>
            <div class="pf-debug-tab" data-pf-pane="live"><pre class="pf-debug-live-output">{live}</pre></div>
        </div>
    </details>
</div>
<style>
.pf-debug-panel { margin-top: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; }
.pf-debug-summary { cursor: pointer; padding: 0.6rem 0.85rem; font-weight: 600; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
.pf-debug-tabs { padding: 0.35rem 0.85rem 0.75rem; }
.pf-debug-tablist { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
.pf-debug-tab-btn { border: 1px solid #d0d7de; background: #ffffff; padding: 0.25rem 0.65rem; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
.pf-debug-tab-btn.pf-active { background: #0d6efd; color: #ffffff; border-color: #0d6efd; }
.pf-debug-tab { display: none; }
.pf-debug-tab.pf-active { display: block; }
.pf-debug-tab pre { white-space: pre-wrap; word-break: break-word; font-size: 0.85rem; background: #ffffff; border: 1px dashed #d0d7de; padding: 0.65rem; border-radius: 6px; margin: 0.35rem 0; overflow: auto; }
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
                    var arrayMatch = key.match(/^(\w+)\[(\d+)\]\.(\w+)$/);
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
                var checkboxes = form.querySelectorAll('input[type="checkbox"]');
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
"""

        panel = panel.replace("{rendered}", rendered_tab)
        panel = panel.replace("{source}", source_tab)
        panel = panel.replace("{schema}", schema_tab)
        panel = panel.replace("{rules}", validation_tab)
        panel = panel.replace("{live}", live_tab)
        return panel


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    debug: bool = False,
    *,
    include_framework_assets: bool = False,
    asset_mode: str = "vendored",
    **kwargs,
) -> str:
    """Convenience wrapper mirroring the legacy helper."""

    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    if framework == "material":
        from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        return renderer.render_form_from_model(
            form_model_cls,
            data=form_data,
            errors=errors,
            layout=layout,
            debug=debug,
            **kwargs,
        )

    renderer = EnhancedFormRenderer(framework=framework)
    if include_framework_assets or asset_mode != "vendored":
        renderer = EnhancedFormRenderer(
            framework=framework,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
    return renderer.render_form_from_model(
        form_model_cls,
        data=form_data,
        errors=errors,
        layout=layout,
        debug=debug,
        **kwargs,
    )


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    debug: bool = False,
    **kwargs,
) -> str:
    """Async counterpart to render_form_html."""

    render_callable = partial(
        render_form_html,
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        layout=layout,
        debug=debug,
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
