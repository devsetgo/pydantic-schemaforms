"""Form builder utilities and convenience helpers for framework integrations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Union

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from pydantic_schemaforms.modern_renderer import (
    FormDefinition,
    FormField,
    FormSection,
    ModernFormRenderer,
)
from pydantic_schemaforms.assets.runtime import (
    bootstrap_icons_css_tag,
    framework_css_tag,
    framework_js_tag,
)
from pydantic_schemaforms.validation import FormValidator, create_validator
from pydantic_schemaforms.tstring import SafeHTML, html as _html_proc


class FormBuilder:
    """Enhanced form builder that integrates all pydantic-schemaforms components."""

    def __init__(
        self,
        model: type[BaseModel] | None = None,
        framework: str = 'bootstrap',
        theme: str = 'default',
        *,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
    ):
        self.model = model
        self.framework = framework
        self.theme = theme
        self.include_framework_assets = include_framework_assets
        self.asset_mode = asset_mode
        self.fields: list[FormField] = []
        self.sections: list[FormSection] = []
        self.validator: FormValidator = create_validator()
        self.renderer: ModernFormRenderer = ModernFormRenderer(
            framework=framework,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
            _internal=True,
        )
        self.layout_type: str = 'vertical'
        self.form_attrs: dict[str, Any] = {}
        self.csrf_enabled: bool = True
        self.honeypot_enabled: bool = True

    def add_field(self, field: FormField) -> 'FormBuilder':
        self.fields.append(field)
        return self

    def add_section(self, section: FormSection) -> 'FormBuilder':
        self.sections.append(section)
        return self

    def text_input(self, name: str, label: str | None = None, **kwargs: Any) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='text',
            **kwargs,
        )
        return self.add_field(field)

    def email_input(
        self, name: str = 'email', label: str = 'Email', **kwargs: Any
    ) -> 'FormBuilder':
        field = FormField(name=name, label=label, input_type='email', **kwargs)
        self.validator.field(name).email()
        return self.add_field(field)

    def password_input(
        self, name: str = 'password', label: str = 'Password', **kwargs: Any
    ) -> 'FormBuilder':
        field = FormField(name=name, label=label, input_type='password', **kwargs)
        return self.add_field(field)

    def number_input(
        self,
        name: str,
        label: str | None = None,
        min_val: float | None = None,
        max_val: float | None = None,
        **kwargs: Any,
    ) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='number',
            **kwargs,
        )

        if min_val is not None or max_val is not None:
            self.validator.field(name).numeric_range(min_val, max_val)

        return self.add_field(field)

    def select_input(
        self,
        name: str,
        options: list[dict[str, str]],
        label: str | None = None,
        **kwargs: Any,
    ) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='select',
            options=options,
            **kwargs,
        )
        return self.add_field(field)

    def checkbox_input(self, name: str, label: str | None = None, **kwargs: Any) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='checkbox',
            **kwargs,
        )
        return self.add_field(field)

    def textarea_input(
        self,
        name: str,
        label: str | None = None,
        rows: int = 4,
        **kwargs: Any,
    ) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='textarea',
            attributes={'rows': str(rows)},
            **kwargs,
        )
        return self.add_field(field)

    def date_input(self, name: str, label: str | None = None, **kwargs: Any) -> 'FormBuilder':
        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='date',
            **kwargs,
        )
        return self.add_field(field)

    def file_input(
        self,
        name: str,
        label: str | None = None,
        accept: str | None = None,
        **kwargs: Any,
    ) -> 'FormBuilder':
        attributes: dict[str, str] = {}
        if accept:
            attributes['accept'] = accept

        field = FormField(
            name=name,
            label=label or name.replace('_', ' ').title(),
            input_type='file',
            attributes=attributes,
            **kwargs,
        )
        return self.add_field(field)

    def required(self, field_name: str, message: str | None = None) -> 'FormBuilder':
        self.validator.field(field_name).required(message)
        return self

    def min_length(self, field_name: str, length: int, message: str | None = None) -> 'FormBuilder':
        self.validator.field(field_name).min_length(length, message)
        return self

    def max_length(self, field_name: str, length: int, message: str | None = None) -> 'FormBuilder':
        self.validator.field(field_name).max_length(length, message)
        return self

    def set_layout(self, layout_type: str) -> 'FormBuilder':
        self.layout_type = layout_type
        return self

    def set_form_attributes(self, **attrs: Any) -> 'FormBuilder':
        self.form_attrs.update(attrs)
        return self

    def disable_csrf(self) -> 'FormBuilder':
        self.csrf_enabled = False
        return self

    def disable_honeypot(self) -> 'FormBuilder':
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

    def render(
        self, data: dict[str, Any] | None = None, errors: dict[str, list[str]] | None = None
    ) -> str:
        form_def = self.build()
        return self.renderer.render_form(form_def, data=data or {}, errors=errors or {})

    async def render_async(
        self, data: dict[str, Any] | None = None, errors: dict[str, list[str]] | None = None
    ) -> str:
        form_def = self.build()
        return await self.renderer.render_form_async(form_def, data=data or {}, errors=errors or {})

    def validate_data(self, data: dict[str, Any]) -> tuple[bool, dict[str, list[str]]]:
        if self.model:
            return self.validator.validate_pydantic_model(self.model, data)
        return self.validator.validate(data)

    def get_validation_script(self) -> str:
        return self.validator.generate_client_validation_script()


class AutoFormBuilder(FormBuilder):
    """Automatically builds forms from Pydantic models."""

    def __init__(self, model: type[BaseModel], **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._build_from_model()

    def _build_from_model(self) -> None:
        if not self.model:
            return

        for field_name, field_info in self.model.model_fields.items():
            field_type = field_info.annotation
            field_default = field_info.default
            input_type = self._get_input_type_for_field(field_type, field_name)  # type: ignore[arg-type]

            form_field = FormField(
                name=field_name,
                label=field_name.replace('_', ' ').title(),
                input_type=input_type,
                value=None
                if (field_default is PydanticUndefined or field_default is ...)
                else field_default,
                required=field_info.is_required(),
            )

            self._add_field_validation(field_name, field_info)
            self.add_field(form_field)

    def _get_input_type_for_field(self, field_type: type, field_name: str) -> str:
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            non_none_types = [t for t in field_type.__args__ if t is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]

        if field_type is str:
            lowered = field_name.lower()
            if 'email' in lowered:
                return 'email'
            if 'password' in lowered:
                return 'password'
            if 'phone' in lowered:
                return 'tel'
            if 'url' in lowered:
                return 'url'
            if lowered in {'description', 'comment', 'notes', 'bio'}:
                return 'textarea'
            return 'text'

        if field_type in (int, float):
            return 'number'

        if field_type is bool:
            return 'checkbox'

        if field_type in (date, datetime):
            return 'date'

        return 'text'

    def _add_field_validation(self, field_name: str, field_info: Any) -> None:
        if field_info.is_required():
            self.validator.field(field_name).required()
        # Additional validation hooks can be added here.


def create_login_form(framework: str = 'bootstrap') -> FormBuilder:
    return (
        FormBuilder(framework=framework)
        .email_input('email', 'Email Address')
        .password_input('password', 'Password')
        .required('email')
        .required('password')
    )


def create_registration_form(framework: str = 'bootstrap') -> FormBuilder:
    builder = (
        FormBuilder(framework=framework)
        .text_input('first_name', 'First Name')
        .text_input('last_name', 'Last Name')
        .email_input('email', 'Email Address')
        .password_input('password', 'Password')
        .password_input('confirm_password', 'Confirm Password')
        .required('first_name')
        .required('last_name')
        .required('email')
        .required('password')
        .required('confirm_password')
        .min_length('password', 8, 'Password must be at least 8 characters')
    )

    from pydantic_schemaforms.validation import CrossFieldRules

    builder.validator.add_cross_field_rule(
        CrossFieldRules.password_confirmation('password', 'confirm_password')
    )

    return builder


def create_contact_form(framework: str = 'bootstrap') -> FormBuilder:
    return (
        FormBuilder(framework=framework)
        .text_input('name', 'Full Name')
        .email_input('email', 'Email Address')
        .text_input('subject', 'Subject')
        .textarea_input('message', 'Message', rows=6)
        .required('name')
        .required('email')
        .required('subject')
        .required('message')
    )


def create_form_from_model(model: type[BaseModel], **kwargs: Any) -> AutoFormBuilder:
    return AutoFormBuilder(model, **kwargs)


def _render_form_page_html(
    *,
    title: str,
    framework_css_tag: str,
    bootstrap_icons_css_tag: str,
    form_html: str,
    framework_js_tag: str,
    validation_script: str,
) -> str:
    _css = SafeHTML(framework_css_tag)
    _icons_css = SafeHTML(bootstrap_icons_css_tag)
    _form = SafeHTML(form_html)
    _js = SafeHTML(framework_js_tag)
    _validation = SafeHTML(validation_script)
    return _html_proc(t"""<!--- Start Pydantic-SchemaForms -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {_css}
    {_icons_css}
    <style>
        body {{ background-color: #f8f9fa; }}
        .form-container {{
            max-width: 600px;
            margin: 2rem auto;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .form-title {{
            text-align: center;
            margin-bottom: 2rem;
            color: #343a40;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="form-container">
            <h1 class="form-title">{title}</h1>
            {_form}
        </div>
    </div>

    {_js}
    {_validation}
</body>
</html>
<!--- End Pydantic-SchemaForms -->""")


def _framework_asset_tags(
    *, framework: str, include_framework_assets: bool, asset_mode: str
) -> dict[str, str]:
    if not include_framework_assets:
        return {'framework_css_tag': '', 'framework_js_tag': '', 'bootstrap_icons_css_tag': ''}

    css_tag = framework_css_tag(framework=framework, asset_mode=asset_mode)
    js_tag = framework_js_tag(framework=framework, asset_mode=asset_mode)
    icons_tag = (
        bootstrap_icons_css_tag(asset_mode=asset_mode)
        if (framework or '').strip().lower() == 'bootstrap'
        else ''
    )
    return {
        'framework_css_tag': css_tag,
        'framework_js_tag': js_tag,
        'bootstrap_icons_css_tag': icons_tag,
    }


def render_form_page(
    form_builder: FormBuilder,
    title: str = 'Form',
    data: dict[str, Any] | None = None,
    errors: dict[str, list[str]] | None = None,
    *,
    include_framework_assets: bool = False,
    asset_mode: str = 'vendored',
    include_html_markers: bool = True,
) -> str:
    form_html = form_builder.render(data or {}, errors or {})
    validation_script = form_builder.get_validation_script()
    template_data = {
        'title': title,
        'form_html': form_html,
        'validation_script': validation_script,
    }
    template_data.update(
        _framework_asset_tags(
            framework=form_builder.framework,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
        )
    )
    from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

    page = _render_form_page_html(**template_data)
    return wrap_with_schemaforms_markers(page, enabled=include_html_markers)


__all__ = [
    'FormBuilder',
    'AutoFormBuilder',
    'create_login_form',
    'create_registration_form',
    'create_contact_form',
    'create_form_from_model',
    'render_form_page',
]
