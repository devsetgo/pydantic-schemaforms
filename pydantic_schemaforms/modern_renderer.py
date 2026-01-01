"""Modern renderer backed by the shared EnhancedFormRenderer pipeline.

This module keeps the legacy FormField/FormSection/FormDefinition helpers so
existing builder utilities can continue to construct forms imperatively, but
the actual HTML rendering now flows through EnhancedFormRenderer plus theme
hooks. Doing so eliminates the bespoke HTML/CSS/JS scaffolding that previously
lived in this file and keeps all framework-specific markup in one place.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from pydantic import create_model

from .enhanced_renderer import EnhancedFormRenderer
from .rendering.schema_parser import build_schema_metadata, resolve_ui_element
from .rendering.themes import RendererTheme
from .schema_form import Field as SchemaField
from .schema_form import FormModel

# Basic mapping from legacy field types to Python annotations used by FormModel
_FIELD_TYPE_ANNOTATIONS: Dict[str, Any] = {
    "text": str,
    "email": str,
    "password": str,
    "search": str,
    "tel": str,
    "url": str,
    "textarea": str,
    "select": str,
    "radio": str,
    "date": str,
    "time": str,
    "datetime": str,
    "datetime-local": str,
    "month": str,
    "week": str,
    "color": str,
    "hidden": str,
    "csrf": str,
    "honeypot": str,
    "button": str,
    "submit": str,
    "reset": str,
    "file": str,
    "number": float,
    "range": float,
    "checkbox": bool,
    "toggle": bool,
    "multiselect": List[str],
}

_HONEYPOT_FIELD_NAME = "honeypot_trap"


def _resolve_annotation(field_type: str) -> Any:
    return _FIELD_TYPE_ANNOTATIONS.get(field_type, str)


class FormField:
    """Legacy form field descriptor preserved for builder compatibility."""

    def __init__(
        self,
        name: str,
        field_type: Optional[str] = None,
        label: Optional[str] = None,
        required: bool = False,
        placeholder: Optional[str] = None,
        help_text: Optional[str] = None,
        value: Any = None,
        options: Optional[List[Dict[str, Any]]] = None,
        validators: Optional[List[Callable[[Any], Any]]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        input_type: Optional[str] = None,
        ui_section: Optional[str] = None,
        **kwargs: Any,
    ):
        self.name = name
        self.field_type = (field_type or input_type or kwargs.pop("ui_element", None) or "text")
        self.label = label or name.replace("_", " ").title()
        self.required = required
        self.placeholder = placeholder
        self.help_text = help_text
        self.value = value
        self.options = options or []
        self.validators = validators or []
        self.attributes = attributes.copy() if attributes else {}
        self.ui_section = ui_section or kwargs.pop("ui_section", None)
        self.order = kwargs.pop("order", None)
        self.extra_attrs = kwargs
        self.errors: List[str] = []

    def validate(self, value: Any) -> bool:
        """Run stored validators while preserving the legacy API."""

        self.errors = []

        if self.required and (value is None or value == ""):
            self.errors.append(f"{self.label} is required")
            return False

        for validator in self.validators:
            try:
                result = validator(value)
                if result is False:
                    self.errors.append(f"{self.label} failed validation")
            except ValueError as err:
                self.errors.append(str(err))

        return not self.errors

    def as_model_field(self, order: int, section: Optional[str]) -> Tuple[Type[Any], Any]:
        annotation = _resolve_annotation(self.field_type)
        default = self.value if self.value is not None else (None if not self.required else ...)

        ui_options: Dict[str, Any] = {}
        if self.options:
            ui_options["options"] = self.options
        if self.attributes:
            ui_options.update(self.attributes)

        extra_attr_copy = self.extra_attrs.copy()
        css_class = extra_attr_copy.pop("class", None)
        inline_style = extra_attr_copy.pop("style", None)
        for key, val in list(extra_attr_copy.items()):
            if isinstance(val, (list, dict)):
                continue
            ui_options[key] = val

        json_extra: Dict[str, Any] = {}
        section_name = section or self.ui_section
        if section_name:
            json_extra["ui_section"] = section_name

        order_value = self.order if self.order is not None else extra_attr_copy.pop("order", None)
        if order_value is None:
            order_value = order
        if order_value is not None:
            json_extra["ui_order"] = order_value

        field_kwargs: Dict[str, Any] = {
            "title": self.label,
            "description": self.help_text,
            "ui_element": self.field_type,
            "ui_placeholder": self.placeholder,
            "ui_help_text": self.help_text,
            "ui_order": order,
        }
        if ui_options:
            field_kwargs["ui_options"] = ui_options
        if css_class:
            field_kwargs["ui_class"] = css_class
        if inline_style:
            field_kwargs["ui_style"] = inline_style
        if json_extra:
            field_kwargs["json_schema_extra"] = json_extra

        return annotation, SchemaField(default, **field_kwargs)


class FormSection:
    """Grouping construct retained for backwards-compatibility."""

    def __init__(
        self,
        title: str,
        fields: List[FormField],
        layout: str = "vertical",
        collapsible: bool = False,
        collapsed: bool = False,
        **kwargs: Any,
    ):
        self.title = title
        self.fields = fields
        self.layout = layout
        self.collapsible = collapsible
        self.collapsed = collapsed
        self.extra_attrs = kwargs


class FormDefinition:
    """Declarative representation of a form for the builder utilities."""

    def __init__(
        self,
        title: str = "Form",
        sections: Optional[List[FormSection]] = None,
        fields: Optional[List[FormField]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        css_framework: str = "bootstrap",
        live_validation: bool = True,
        csrf_protection: bool = False,
        honeypot_protection: bool = False,
        layout: Optional[str] = None,
        **kwargs: Any,
    ):
        framework_alias = kwargs.pop("framework", None)
        if framework_alias:
            css_framework = framework_alias

        csrf_alias = kwargs.pop("csrf_enabled", None)
        if csrf_alias is not None:
            csrf_protection = csrf_alias

        honeypot_alias = kwargs.pop("honeypot_enabled", None)
        if honeypot_alias is not None:
            honeypot_protection = honeypot_alias

        self.title = title
        self.sections = sections or []
        self.fields = fields or []
        self.submit_url = submit_url
        self.method = method
        self.css_framework = css_framework
        self.live_validation = live_validation
        self.csrf_protection = csrf_protection
        self.honeypot_protection = honeypot_protection
        self.layout = layout or kwargs.pop("layout", "vertical")
        self.theme = kwargs.pop("theme", None)
        self.extra_attrs = dict(kwargs)
        self._model_cache: Optional[Type[FormModel]] = None

        if self.fields and not self.sections:
            self.sections = [FormSection("Main", self.fields)]

    def _iter_fields(self) -> List[Tuple[FormField, Optional[str]]]:
        ordered: List[Tuple[FormField, Optional[str]]] = []
        for section in self.sections:
            for field in section.fields:
                ordered.append((field, section.title))
        return ordered

    def to_form_model_class(self) -> Type[FormModel]:
        if self._model_cache is not None:
            return self._model_cache

        field_defs: Dict[str, Tuple[Type[Any], Any]] = {}
        for order, (field, section_title) in enumerate(self._iter_fields()):
            annotation, model_field = field.as_model_field(order, section_title)
            field_defs[field.name] = (annotation, model_field)

        if self.honeypot_protection and _HONEYPOT_FIELD_NAME not in field_defs:
            field_defs[_HONEYPOT_FIELD_NAME] = (
                str,
                SchemaField(
                    default="",
                    ui_element="honeypot",
                    ui_help_text="If this field is filled out we assume the submission is a bot.",
                ),
            )

        if not field_defs:
            raise ValueError("FormDefinition must define at least one field")

        model_name = self._model_name()
        self._model_cache = create_model(model_name, __base__=FormModel, **field_defs)
        return self._model_cache

    def _model_name(self) -> str:
        sanitized = re.sub(r"[^0-9a-zA-Z]+", "", self.title) or "Form"
        return f"Generated{sanitized}Form"


class ModernFormRenderer(EnhancedFormRenderer):
    """Thin wrapper around EnhancedFormRenderer for legacy entry points."""

    def __init__(
        self,
        framework: str = "bootstrap",
        theme: Optional[RendererTheme] = None,
        *,
        include_framework_assets: bool = False,
        asset_mode: str = "vendored",
    ):
        super().__init__(
            framework=framework,
            theme=theme,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
        )

    def render_form(
        self,
        form_def: FormDefinition,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        renderer = self._ensure_renderer(form_def.css_framework)
        model_cls = form_def.to_form_model_class()
        layout, render_kwargs = self._prepare_render_kwargs(form_def, kwargs)

        html = renderer.render_form_from_model(
            model_cls,
            data=data,
            errors=errors,
            submit_url=form_def.submit_url,
            method=form_def.method,
            include_csrf=form_def.csrf_protection,
            include_submit_button=True,
            layout=layout,
            **render_kwargs,
        )

        if form_def.live_validation:
            html = f"{html}\n{self._client_validation_script()}"

        return html

    async def render_form_async(
        self,
        form_def: FormDefinition,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        renderer = self._ensure_renderer(form_def.css_framework)
        model_cls = form_def.to_form_model_class()
        layout, render_kwargs = self._prepare_render_kwargs(form_def, kwargs)

        html = await renderer.render_form_from_model_async(
            model_cls,
            data=data,
            errors=errors,
            submit_url=form_def.submit_url,
            method=form_def.method,
            include_csrf=form_def.csrf_protection,
            include_submit_button=True,
            layout=layout,
            **render_kwargs,
        )

        if form_def.live_validation:
            html = f"{html}\n{self._client_validation_script()}"

        return html

    async def render_async(
        self,
        form_def: FormDefinition,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Legacy alias retained for older integration tests."""

        return await self.render_form_async(form_def, data=data, errors=errors, **kwargs)

    async def async_render(
        self,
        form_def: FormDefinition,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Another legacy alias; matches historical API variants."""

        return await self.render_form_async(form_def, data=data, errors=errors, **kwargs)

    def extract_form_fields(self, model_cls: Type[FormModel]) -> List[FormField]:
        """Return lightweight FormField representations for introspection/tests."""

        metadata = build_schema_metadata(model_cls)
        extracted: List[FormField] = []

        for order, (field_name, field_schema) in enumerate(metadata.fields):
            ui_element = resolve_ui_element(field_schema) or "text"
            ui_info = field_schema.get("ui", {}) or field_schema

            options = ui_info.get("options")
            if not isinstance(options, list):
                options = None

            extracted.append(
                FormField(
                    name=field_name,
                    field_type=ui_element,
                    label=field_schema.get("title"),
                    required=field_name in metadata.required_fields,
                    placeholder=ui_info.get("placeholder"),
                    help_text=ui_info.get("help_text") or field_schema.get("description"),
                    options=options,
                    input_type=ui_element,
                    order=order,
                    ui_section=ui_info.get("section") or ui_info.get("ui_section"),
                )
            )

        return extracted

    def _ensure_renderer(self, framework: str) -> "ModernFormRenderer":
        if not framework or framework == self.framework:
            return self

        theme = self._clone_theme()
        return ModernFormRenderer(
            framework=framework,
            theme=theme,
            include_framework_assets=self.include_framework_assets,
            asset_mode=self.asset_mode,
        )

    def _clone_theme(self) -> Optional[RendererTheme]:
        theme_cls = type(self._theme)
        try:
            return theme_cls()  # type: ignore[call-arg]
        except TypeError:
            return RendererTheme(getattr(self._theme, "submit_label", "Submit"))

    def _prepare_render_kwargs(
        self,
        form_def: FormDefinition,
        call_kwargs: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        resolved = dict(form_def.extra_attrs)
        resolved.update(call_kwargs)
        layout = resolved.pop("layout", form_def.layout)
        return layout, resolved

    def _client_validation_script(self) -> str:
        return """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('main-form');
    if (!form) {
        return;
    }

    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            this.classList.add('was-validated');
        });
    });
});
</script>
""".strip()


__all__ = [
    "FormField",
    "FormSection",
    "FormDefinition",
    "ModernFormRenderer",
]
