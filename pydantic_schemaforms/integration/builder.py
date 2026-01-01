"""Form builder utilities and convenience helpers for framework integrations."""

from __future__ import annotations

import string
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from ..modern_renderer import FormDefinition, FormField, FormSection, ModernFormRenderer
from ..assets.runtime import framework_css_tag, framework_js_tag
from ..validation import create_validator


class FormBuilder:
    """Enhanced form builder that integrates all pydantic-schemaforms components."""

    def __init__(
        self,
        model: Optional[Type[BaseModel]] = None,
        framework: str = "bootstrap",
        theme: str = "default",
        *,
        include_framework_assets: bool = False,
        asset_mode: str = "vendored",
    ):
        self.model = model
        self.framework = framework
        self.theme = theme
        self.include_framework_assets = include_framework_assets
        self.asset_mode = asset_mode
        self.fields: List[FormField] = []
        self.sections: List[FormSection] = []
        self.validator = create_validator()
        self.renderer = ModernFormRenderer(
            framework=framework,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
        self.layout_type = "vertical"
        self.form_attrs: Dict[str, Any] = {}
        self.csrf_enabled = True
        self.honeypot_enabled = True

    def add_field(self, field: FormField) -> "FormBuilder":
        self.fields.append(field)
        return self

    def add_section(self, section: FormSection) -> "FormBuilder":
        self.sections.append(section)
        return self

    def text_input(self, name: str, label: Optional[str] = None, **kwargs: Any) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="text",
            **kwargs,
        )
        return self.add_field(field)

    def email_input(self, name: str = "email", label: str = "Email", **kwargs: Any) -> "FormBuilder":
        field = FormField(name=name, label=label, input_type="email", **kwargs)
        self.validator.field(name).email()
        return self.add_field(field)

    def password_input(self, name: str = "password", label: str = "Password", **kwargs: Any) -> "FormBuilder":
        field = FormField(name=name, label=label, input_type="password", **kwargs)
        return self.add_field(field)

    def number_input(
        self,
        name: str,
        label: Optional[str] = None,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        **kwargs: Any,
    ) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="number",
            **kwargs,
        )

        if min_val is not None or max_val is not None:
            self.validator.field(name).numeric_range(min_val, max_val)

        return self.add_field(field)

    def select_input(
        self,
        name: str,
        options: List[Dict[str, str]],
        label: Optional[str] = None,
        **kwargs: Any,
    ) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="select",
            options=options,
            **kwargs,
        )
        return self.add_field(field)

    def checkbox_input(self, name: str, label: Optional[str] = None, **kwargs: Any) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="checkbox",
            **kwargs,
        )
        return self.add_field(field)

    def textarea_input(
        self,
        name: str,
        label: Optional[str] = None,
        rows: int = 4,
        **kwargs: Any,
    ) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="textarea",
            attributes={"rows": str(rows)},
            **kwargs,
        )
        return self.add_field(field)

    def date_input(self, name: str, label: Optional[str] = None, **kwargs: Any) -> "FormBuilder":
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="date",
            **kwargs,
        )
        return self.add_field(field)

    def file_input(
        self,
        name: str,
        label: Optional[str] = None,
        accept: Optional[str] = None,
        **kwargs: Any,
    ) -> "FormBuilder":
        attributes: Dict[str, str] = {}
        if accept:
            attributes["accept"] = accept

        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="file",
            attributes=attributes,
            **kwargs,
        )
        return self.add_field(field)

    def required(self, field_name: str, message: Optional[str] = None) -> "FormBuilder":
        self.validator.field(field_name).required(message)
        return self

    def min_length(self, field_name: str, length: int, message: Optional[str] = None) -> "FormBuilder":
        self.validator.field(field_name).min_length(length, message)
        return self

    def max_length(self, field_name: str, length: int, message: Optional[str] = None) -> "FormBuilder":
        self.validator.field(field_name).max_length(length, message)
        return self

    def set_layout(self, layout_type: str) -> "FormBuilder":
        self.layout_type = layout_type
        return self

    def set_form_attributes(self, **attrs: Any) -> "FormBuilder":
        self.form_attrs.update(attrs)
        return self

    def disable_csrf(self) -> "FormBuilder":
        self.csrf_enabled = False
        return self

    def disable_honeypot(self) -> "FormBuilder":
        self.honeypot_enabled = False
        return self

    def build(self) -> FormDefinition:
        return FormDefinition(
            fields=self.fields,
            sections=self.sections,
            framework=self.framework,
            theme=self.theme,
            csrf_enabled=self.csrf_enabled,
            honeypot_enabled=self.honeypot_enabled,
            **self.form_attrs,
        )

    def render(self, data: Optional[Dict[str, Any]] = None, errors: Optional[Dict[str, List[str]]] = None) -> str:
        form_def = self.build()
        return self.renderer.render_form(form_def, data=data or {}, errors=errors or {})

    async def render_async(
        self, data: Optional[Dict[str, Any]] = None, errors: Optional[Dict[str, List[str]]] = None
    ) -> str:
        form_def = self.build()
        return await self.renderer.render_form_async(form_def, data=data or {}, errors=errors or {})

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, Dict[str, List[str]]]:
        if self.model:
            return self.validator.validate_pydantic_model(self.model, data)
        return self.validator.validate(data)

    def get_validation_script(self) -> str:
        return self.validator.generate_client_validation_script()


class AutoFormBuilder(FormBuilder):
    """Automatically builds forms from Pydantic models."""

    def __init__(self, model: Type[BaseModel], **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._build_from_model()

    def _build_from_model(self) -> None:
        if not self.model:
            return

        for field_name, field_info in self.model.model_fields.items():
            field_type = field_info.annotation
            field_default = field_info.default
            input_type = self._get_input_type_for_field(field_type, field_name)

            form_field = FormField(
                name=field_name,
                label=field_name.replace("_", " ").title(),
                input_type=input_type,
                default_value=field_default if field_default != ... else None,
                required=field_info.is_required(),
            )

            self._add_field_validation(field_name, field_info)
            self.add_field(form_field)

    def _get_input_type_for_field(self, field_type: Type, field_name: str) -> str:
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
            non_none_types = [t for t in field_type.__args__ if t is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]

        if field_type is str:
            lowered = field_name.lower()
            if "email" in lowered:
                return "email"
            if "password" in lowered:
                return "password"
            if "phone" in lowered:
                return "tel"
            if "url" in lowered:
                return "url"
            if lowered in {"description", "comment", "notes", "bio"}:
                return "textarea"
            return "text"

        if field_type in (int, float):
            return "number"

        if field_type is bool:
            return "checkbox"

        if field_type in (date, datetime):
            return "date"

        return "text"

    def _add_field_validation(self, field_name: str, field_info: Any) -> None:
        if field_info.is_required():
            self.validator.field(field_name).required()
        # Additional validation hooks can be added here.


def create_login_form(framework: str = "bootstrap") -> FormBuilder:
    return (
        FormBuilder(framework=framework)
        .email_input("email", "Email Address")
        .password_input("password", "Password")
        .required("email")
        .required("password")
    )


def create_registration_form(framework: str = "bootstrap") -> FormBuilder:
    builder = (
        FormBuilder(framework=framework)
        .text_input("first_name", "First Name")
        .text_input("last_name", "Last Name")
        .email_input("email", "Email Address")
        .password_input("password", "Password")
        .password_input("confirm_password", "Confirm Password")
        .required("first_name")
        .required("last_name")
        .required("email")
        .required("password")
        .required("confirm_password")
        .min_length("password", 8, "Password must be at least 8 characters")
    )

    from ..validation import CrossFieldRules

    builder.validator.add_cross_field_rule(
        CrossFieldRules.password_confirmation("password", "confirm_password")
    )

    return builder


def create_contact_form(framework: str = "bootstrap") -> FormBuilder:
    return (
        FormBuilder(framework=framework)
        .text_input("name", "Full Name")
        .email_input("email", "Email Address")
        .text_input("subject", "Subject")
        .textarea_input("message", "Message", rows=6)
        .required("name")
        .required("email")
        .required("subject")
        .required("message")
    )


def create_form_from_model(model: Type[BaseModel], **kwargs: Any) -> AutoFormBuilder:
    return AutoFormBuilder(model, **kwargs)


FORM_PAGE_TEMPLATE = string.Template(
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    ${framework_css_tag}
    <style>
        body { background-color: #f8f9fa; }
        .form-container {
            max-width: 600px;
            margin: 2rem auto;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-title {
            text-align: center;
            margin-bottom: 2rem;
            color: #343a40;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-container">
            <h1 class="form-title">${title}</h1>
            ${form_html}
        </div>
    </div>

    ${framework_js_tag}
    ${validation_script}
</body>
</html>
"""
)


def _framework_asset_tags(*, framework: str, include_framework_assets: bool, asset_mode: str) -> Dict[str, str]:
    if not include_framework_assets:
        return {"framework_css_tag": "", "framework_js_tag": ""}

    css_tag = framework_css_tag(framework=framework, asset_mode=asset_mode)
    js_tag = framework_js_tag(framework=framework, asset_mode=asset_mode)
    return {"framework_css_tag": css_tag, "framework_js_tag": js_tag}


def render_form_page(
    form_builder: FormBuilder,
    title: str = "Form",
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[Dict[str, List[str]]] = None,
    *,
    include_framework_assets: bool = False,
    asset_mode: str = "vendored",
) -> str:
    form_html = form_builder.render(data or {}, errors or {})
    validation_script = form_builder.get_validation_script()
    template_data = {
        "title": title,
        "form_html": form_html,
        "validation_script": validation_script,
    }
    template_data.update(
        _framework_asset_tags(
            framework=form_builder.framework,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
    )
    return FORM_PAGE_TEMPLATE.substitute(**template_data)


__all__ = [
    "FormBuilder",
    "AutoFormBuilder",
    "create_login_form",
    "create_registration_form",
    "create_contact_form",
    "create_form_from_model",
    "render_form_page",
]
