
"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

from __future__ import annotations

import asyncio
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

        has_model_list_fields = any(
            resolve_ui_element(field_schema) == "model_list" for _name, field_schema in fields
        )
        if has_model_list_fields:
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self._model_list_framework())
            output_parts.append(list_renderer.get_model_list_javascript())

        return "\n".join(output_parts)

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


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    **kwargs,
) -> str:
    """Convenience wrapper mirroring the legacy helper."""

    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    if framework == "material":
        from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        return renderer.render_form_from_model(
            form_model_cls,
            data=form_data,
            errors=errors,
            layout=layout,
            **kwargs,
        )

    renderer = EnhancedFormRenderer(framework=framework)
    return renderer.render_form_from_model(
        form_model_cls,
        data=form_data,
        errors=errors,
        layout=layout,
        **kwargs,
    )


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
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
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
