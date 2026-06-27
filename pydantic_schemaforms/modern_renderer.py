"""Modern renderer backed by the shared EnhancedFormRenderer pipeline.

This module keeps the legacy FormField/FormSection/FormDefinition helpers so
existing builder utilities can continue to construct forms imperatively, but
the actual HTML rendering now flows through EnhancedFormRenderer plus theme
hooks. Doing so eliminates the bespoke HTML/CSS/JS scaffolding that previously
lived in this file and keeps all framework-specific markup in one place.
"""

from __future__ import annotations

import re
from typing import Any
from collections.abc import Callable

from pydantic import create_model

from .enhanced_renderer import EnhancedFormRenderer
from .rendering.schema_parser import build_schema_metadata, resolve_ui_element
from .rendering.themes import RendererTheme
from .schema_form import Field as SchemaField
from .schema_form import FormModel

# Basic mapping from legacy field types to Python annotations used by FormModel
_FIELD_TYPE_ANNOTATIONS: dict[str, Any] = {
    'text': str,
    'email': str,
    'password': str,
    'search': str,
    'tel': str,
    'url': str,
    'textarea': str,
    'select': str,
    'radio': str,
    'date': str,
    'time': str,
    'datetime': str,
    'datetime-local': str,
    'month': str,
    'week': str,
    'color': str,
    'hidden': str,
    'csrf': str,
    'honeypot': str,
    'button': str,
    'submit': str,
    'reset': str,
    'file': str,
    'number': float,
    'range': float,
    'checkbox': bool,
    'toggle': bool,
    'multiselect': list[str],
}

_HONEYPOT_FIELD_NAME = 'honeypot_trap'


def _resolve_annotation(field_type: str) -> Any:
    return _FIELD_TYPE_ANNOTATIONS.get(field_type, str)


class FormField:
    """Legacy form field descriptor preserved for builder compatibility."""

    def __init__(
        self,
        name: str,
        field_type: str | None = None,
        label: str | None = None,
        required: bool = False,
        placeholder: str | None = None,
        help_text: str | None = None,
        value: Any = None,
        options: list[dict[str, Any]] | None = None,
        validators: list[Callable[[Any], Any]] | None = None,
        attributes: dict[str, Any] | None = None,
        input_type: str | None = None,
        ui_section: str | None = None,
        **kwargs: Any,
    ):
        self.name = name
        self.field_type: str = field_type or input_type or kwargs.pop('ui_element', None) or 'text'
        self.label: str = label or name.replace('_', ' ').title()
        self.required = required
        self.placeholder = placeholder
        self.help_text = help_text
        self.value = value
        self.options: list[dict[str, Any]] = options or []
        self.validators: list[Callable[[Any], Any]] = validators or []
        self.attributes: dict[str, Any] = attributes.copy() if attributes else {}
        self.ui_section: str | None = ui_section or kwargs.pop('ui_section', None)
        self.order: Any = kwargs.pop('order', None)
        self.extra_attrs: dict[str, Any] = kwargs
        self.errors: list[str] = []

    def validate(self, value: Any) -> bool:
        """Run stored validators while preserving the legacy API."""

        self.errors = []

        if self.required and (value is None or value == ''):
            self.errors.append(f'{self.label} is required')
            return False

        for validator in self.validators:
            try:
                result = validator(value)
                if result is False:
                    self.errors.append(f'{self.label} failed validation')
            except ValueError as err:
                self.errors.append(str(err))

        return not self.errors

    def as_model_field(self, order: int, section: str | None) -> tuple[type[Any], Any]:
        annotation = _resolve_annotation(self.field_type)
        if self.value is not None:
            default: Any = self.value
        elif not self.required:
            default = None
        else:
            default = ...

        ui_options: dict[str, Any] = {}
        if self.options:
            ui_options['options'] = self.options
        if self.attributes:
            ui_options.update(self.attributes)

        extra_attr_copy = self.extra_attrs.copy()
        css_class = extra_attr_copy.pop('class', None)
        inline_style = extra_attr_copy.pop('style', None)
        for key, val in extra_attr_copy.items():
            if isinstance(val, (list, dict)):
                continue
            ui_options[key] = val

        json_extra: dict[str, Any] = {}
        section_name = section or self.ui_section
        if section_name:
            json_extra['ui_section'] = section_name

        order_value = self.order if self.order is not None else extra_attr_copy.pop('order', None)
        if order_value is None:
            order_value = order
        if order_value is not None:
            json_extra['ui_order'] = order_value

        field_kwargs: dict[str, Any] = {
            'title': self.label,
            'description': self.help_text,
            'ui_element': self.field_type,
            'ui_placeholder': self.placeholder,
            'ui_help_text': self.help_text,
            'ui_order': order,
        }
        if ui_options:
            field_kwargs['ui_options'] = ui_options
        if css_class:
            field_kwargs['ui_class'] = css_class
        if inline_style:
            field_kwargs['ui_style'] = inline_style
        if json_extra:
            field_kwargs['json_schema_extra'] = json_extra

        return annotation, SchemaField(default, **field_kwargs)


class FormSection:
    """Grouping construct retained for backwards-compatibility."""

    def __init__(
        self,
        title: str,
        fields: list[FormField],
        layout: str = 'vertical',
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
        title: str = 'Form',
        sections: list[FormSection] | None = None,
        fields: list[FormField] | None = None,
        submit_url: str = '/submit',
        method: str = 'POST',
        css_framework: str = 'bootstrap',
        live_validation: bool = True,
        csrf_protection: bool = False,
        honeypot_protection: bool = False,
        layout: str | None = None,
        **kwargs: Any,
    ):
        framework_alias = kwargs.pop('framework', None)
        if framework_alias:
            css_framework = framework_alias

        csrf_alias = kwargs.pop('csrf_enabled', None)
        if csrf_alias is not None:
            csrf_protection = csrf_alias

        honeypot_alias = kwargs.pop('honeypot_enabled', None)
        if honeypot_alias is not None:
            honeypot_protection = honeypot_alias

        self.title = title
        self.sections: list[FormSection] = sections or []
        self.fields: list[FormField] = fields or []
        self.submit_url = submit_url
        self.method = method
        self.css_framework = css_framework
        self.live_validation = live_validation
        self.csrf_protection = csrf_protection
        self.honeypot_protection = honeypot_protection
        self.layout: str = layout or kwargs.pop('layout', 'vertical')
        self.theme: Any = kwargs.pop('theme', None)
        self.extra_attrs: dict[str, Any] = dict(kwargs)
        self._model_cache: type[FormModel] | None = None

        if self.fields and not self.sections:
            self.sections = [FormSection('Main', self.fields)]

    def _iter_fields(self) -> list[tuple[FormField, str | None]]:
        ordered: list[tuple[FormField, str | None]] = []
        for section in self.sections:
            for field in section.fields:
                ordered.append((field, section.title))
        return ordered

    def to_form_model_class(self) -> type[FormModel]:
        if self._model_cache is not None:
            return self._model_cache

        field_defs: dict[str, tuple[type[Any], Any]] = {}
        for order, (field, section_title) in enumerate(self._iter_fields()):
            annotation, model_field = field.as_model_field(order, section_title)
            field_defs[field.name] = (annotation, model_field)

        if self.honeypot_protection and _HONEYPOT_FIELD_NAME not in field_defs:
            field_defs[_HONEYPOT_FIELD_NAME] = (
                str,
                SchemaField(
                    default='',
                    ui_element='honeypot',
                    ui_help_text='If this field is filled out we assume the submission is a bot.',
                ),
            )

        if not field_defs:
            raise ValueError('FormDefinition must define at least one field')

        model_name = self._model_name()
        self._model_cache = create_model(model_name, __base__=FormModel, **field_defs)  # type: ignore[call-overload]
        return self._model_cache  # type: ignore[return-value]

    def _model_name(self) -> str:
        sanitized = re.sub(r'[^0-9a-zA-Z]+', '', self.title) or 'Form'
        return f'Generated{sanitized}Form'


class ModernFormRenderer(EnhancedFormRenderer):
    """Renderer used internally by FormBuilder.

    Thin subclass of :class:`~pydantic_schemaforms.EnhancedFormRenderer` retained
    as the rendering backbone of the :class:`~pydantic_schemaforms.FormBuilder` DSL.
    Prefer instantiating ``EnhancedFormRenderer`` directly for standalone use.
    """

    def __init__(
        self,
        framework: str = 'bootstrap',
        theme: RendererTheme | None = None,
        *,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
        _internal: bool = False,
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
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
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
            html = f'{html}\n{self._client_validation_script()}'

        return html

    async def render_form_async(
        self,
        form_def: FormDefinition,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
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
            html = f'{html}\n{self._client_validation_script()}'

        return html

    async def render_async(
        self,
        form_def: FormDefinition,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Legacy alias retained for older integration tests."""

        return await self.render_form_async(form_def, data=data, errors=errors, **kwargs)

    async def async_render(
        self,
        form_def: FormDefinition,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Another legacy alias; matches historical API variants."""

        return await self.render_form_async(form_def, data=data, errors=errors, **kwargs)

    def extract_form_fields(self, model_cls: type[FormModel]) -> list[FormField]:
        """Return lightweight FormField representations for introspection/tests."""

        metadata = build_schema_metadata(model_cls)
        extracted: list[FormField] = []

        for order, (field_name, field_schema) in enumerate(metadata.fields):
            ui_element = resolve_ui_element(field_schema) or 'text'
            ui_info = field_schema.get('ui', {}) or field_schema

            options = ui_info.get('options')
            if not isinstance(options, list):
                options = None

            extracted.append(
                FormField(
                    name=field_name,
                    field_type=ui_element,
                    label=field_schema.get('title'),
                    required=field_name in metadata.required_fields,
                    placeholder=ui_info.get('placeholder'),
                    help_text=ui_info.get('help_text') or field_schema.get('description'),
                    options=options,
                    input_type=ui_element,
                    order=order,
                    ui_section=ui_info.get('section') or ui_info.get('ui_section'),
                )
            )

        return extracted

    def _ensure_renderer(self, framework: str) -> 'ModernFormRenderer':
        if not framework or framework == self.framework:
            return self

        theme = self._clone_theme()
        return ModernFormRenderer(
            framework=framework,
            theme=theme,
            include_framework_assets=self.include_framework_assets,
            asset_mode=self.asset_mode,
            _internal=True,
        )

    def _clone_theme(self) -> RendererTheme | None:
        theme_cls = type(self._theme)
        try:
            return theme_cls()  # type: ignore[call-arg]
        except TypeError:
            return RendererTheme(getattr(self._theme, 'submit_label', 'Submit'))

    def _prepare_render_kwargs(
        self,
        form_def: FormDefinition,
        call_kwargs: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        resolved = dict(form_def.extra_attrs)
        resolved.update(call_kwargs)
        layout = resolved.pop('layout', form_def.layout)
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
    'FormField',
    'FormSection',
    'FormDefinition',
    'ModernFormRenderer',
]
