"""Read-only rendering of validated data: review and confirmation pages.

Walks the same field tree as the form, with the same labels, order and
sections, but shows values instead of inputs. Every value reaches the page
through ``html(t'...')``, so nothing submitted is ever trusted as markup, and
values are never linked, since a submitted URL may be ``javascript:``.
"""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from pydantic import BaseModel, SecretBytes, SecretStr

from pydantic_schemaforms.tstring import SafeHTML, html

from .layout_engine import GROUPED_LAYOUTS, LayoutEngine, check_layout
from .schema_parser import (
    GROUP_ELEMENTS,
    SchemaMetadata,
    build_schema_metadata,
    extract_ui_info,
    ordered_properties,
    resolve_list_item_ref,
    resolve_nested_model_ref,
)

if TYPE_CHECKING:
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

EMPTY_TEXT = 'Not provided'
MASK = '••••••••'

# Content blocks explain how to fill the form in, and the security inputs hold
# nothing the person entered, so neither belongs on a review of the answers.
_SKIPPED_ELEMENTS = frozenset({'hidden', 'content', 'csrf', 'captcha', 'honeypot'})
_LAST_FOUR_ELEMENTS = frozenset(
    {'ssn', 'social_security_number', 'credit_card', 'card', 'cc_number'}
)
_BOOLEAN_ELEMENTS = frozenset({'checkbox', 'toggle', 'toggle_switch', 'checkbox_toggle', 'consent'})
_CHOICE_ELEMENTS = frozenset({'select', 'radio', 'multiselect', 'combobox', 'checkbox_group'})
_TRUE_STRINGS = frozenset({'true', '1', 'on', 'yes'})
# ui_element -> (the ui_options key naming its format, the default format).
_TEMPORAL_FORMATS = {
    'date': ('date_format', '%Y-%m-%d'),
    'birthdate': ('date_format', '%Y-%m-%d'),
    'time': ('time_format', '%H:%M'),
    'datetime': ('datetime_format', '%Y-%m-%d %H:%M'),
    'datetime-local': ('datetime_format', '%Y-%m-%d %H:%M'),
}


def _plain(value: Any) -> Any:
    """Models to dicts and Enum members to their values, leaving the rest alone."""

    if isinstance(value, BaseModel):
        return _plain(value.model_dump(by_alias=True))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _is_empty(value: Any) -> bool:
    return value is None or value == '' or value == [] or value == {}


def _check_edit_urls(edit_urls: dict[str, str], metadata: SchemaMetadata) -> None:
    sections = {name for name, _schema in metadata.group_fields}
    unknown = set(edit_urls) - sections
    if unknown:
        raise ValueError(
            f'edit_urls has {sorted(unknown)}, which are not sub-form fields of this model; '
            f'expected any of {sorted(sections)}.'
        )
    for url in edit_urls.values():
        if urlsplit(url).scheme not in ('', 'http', 'https'):
            raise ValueError(f'edit_urls must be relative or http(s), not {url!r}')


def _format_temporal(element: str, value: Any, ui_info: dict[str, Any]) -> str:
    options = ui_info.get('options')
    option_key, default_format = _TEMPORAL_FORMATS[element]
    custom = options.get(option_key) if isinstance(options, dict) else None
    parsed = value
    if isinstance(value, str):
        parser = time if option_key == 'time_format' else datetime
        try:
            parsed = parser.fromisoformat(value)
        except ValueError:
            return value
    if not isinstance(parsed, (date, time)):
        return str(value)
    return parsed.strftime(custom or default_format)


def _file_name(value: Any) -> str:
    name = getattr(value, 'filename', None)
    return str(name if name else value)


def _masked_text(element: str, value: Any) -> str | None:
    if element == 'password' or isinstance(value, (SecretStr, SecretBytes)):
        return MASK
    if element in _LAST_FOUR_ELEMENTS:
        digits = ''.join(char for char in str(value) if char.isdigit())
        return f'{MASK}{digits[-4:]}'
    return None


class _DisplayRenderer:
    def __init__(self, renderer: 'EnhancedFormRenderer', schema_defs: dict[str, Any]) -> None:
        self._renderer = renderer
        self._schema_defs = schema_defs
        self._field_renderer = renderer._field_renderer  # noqa: SLF001
        self._theme = renderer.theme

    def _element(self, field_schema: dict[str, Any]) -> str:
        if field_schema.get('format') == 'password':
            return 'password'
        return self._field_renderer._infer_ui_element(field_schema)  # noqa: SLF001

    def _is_shown(self, field_schema: dict[str, Any]) -> bool:
        if extract_ui_info(field_schema).get('hidden'):
            return False
        return self._element(field_schema) not in _SKIPPED_ELEMENTS

    def _is_composite(self, element: str) -> bool:
        if element == 'consent':
            return False
        return (
            element in GROUP_ELEMENTS or LayoutEngine.get_renderer_for_element(element) is not None
        )

    def _choice_labels(
        self, field_schema: dict[str, Any], ui_info: dict[str, Any], value: Any
    ) -> str:
        field_renderer = self._field_renderer
        _options, choices = field_renderer._extract_ui_options(ui_info, field_schema)  # noqa: SLF001
        choices = (
            choices
            or field_schema.get('enum')
            or (field_schema.get('items') or {}).get('enum')
            or []
        )
        labels = {
            str(option['value']): str(option['label'])
            for option in field_renderer._normalize_options(choices, None)  # noqa: SLF001
        }
        values = value if isinstance(value, (list, set)) else [value]
        return ', '.join(labels.get(str(item), str(item)) for item in values)

    def _text(self, field_schema: dict[str, Any], value: Any) -> tuple[str, bool]:
        """The text shown for a non-composite field, and whether it counts as empty."""

        element = self._element(field_schema)
        ui_info = extract_ui_info(field_schema)
        if element in _BOOLEAN_ELEMENTS:
            is_true = value is True or str(value).lower() in _TRUE_STRINGS
            return ('Yes' if is_true else 'No'), False
        if _is_empty(value):
            return EMPTY_TEXT, True
        masked = _masked_text(element, value)
        if masked is not None:
            return masked, False
        return self._filled_text(element, field_schema, ui_info, value), False

    def _filled_text(
        self, element: str, field_schema: dict[str, Any], ui_info: dict[str, Any], value: Any
    ) -> str:
        if isinstance(value, bool):
            return 'Yes' if value else 'No'
        if element in _CHOICE_ELEMENTS:
            return self._choice_labels(field_schema, ui_info, value)
        if element in _TEMPORAL_FORMATS:
            return _format_temporal(element, value, ui_info)
        if element == 'file':
            files = value if isinstance(value, list) else [value]
            return ', '.join(_file_name(item) for item in files)
        if isinstance(value, (list, tuple, set)):
            return ', '.join(str(item) for item in value)
        return str(value)

    def _value_markup(self, text: str, is_empty: bool) -> tuple[str, SafeHTML]:
        # HTML collapses a multi-line answer's line breaks and indentation.
        style = 'white-space: pre-wrap' if '\n' in text else ''  # NOSONAR
        _style = html(t' style="{style}"') if style else SafeHTML('')
        css = self._theme.display_class('empty') if is_empty else ''
        return css, _style

    def _rows(self, rows: list[tuple[str, str, bool]]) -> str:
        if not rows:
            return ''
        theme = self._theme
        list_class = theme.display_class('list')  # NOSONAR
        term_class = theme.display_class('term')  # NOSONAR
        value_class = theme.display_class('value')
        parts = []
        for title, text, is_empty in rows:
            extra_class, _style = self._value_markup(text, is_empty)
            _dd_class = f'{value_class} {extra_class}'.strip()  # NOSONAR
            parts.append(
                str(
                    html(
                        t'<dt class="{term_class}">{title}</dt>'
                        t'<dd class="{_dd_class}"{_style}>{text}</dd>'
                    )
                )
            )
        _rows = SafeHTML(''.join(parts))  # NOSONAR
        return str(html(t'<dl class="{list_class}">{_rows}</dl>'))

    def _empty_paragraph(self) -> str:
        css = self._theme.display_class('empty')  # NOSONAR
        return str(html(t'<p class="{css}">{EMPTY_TEXT}</p>'))

    def _table(self, columns: list[tuple[str, dict[str, Any]]], items: list[Any]) -> str:
        if not items:
            return self._empty_paragraph()
        theme = self._theme
        wrapper_class = theme.display_class('table_wrapper')  # NOSONAR
        table_class = theme.table_class({})  # NOSONAR
        headers = [
            str(html(t'<th scope="col">{self._title(name, schema)}</th>'))
            for name, schema in columns
        ]
        rows = []
        for item in items:
            data = item if isinstance(item, dict) else {}
            cells = [str(self._cell(schema, data.get(name))) for name, schema in columns]
            _cells = SafeHTML(''.join(cells))  # NOSONAR
            rows.append(str(html(t'<tr>{_cells}</tr>')))
        _headers = SafeHTML(''.join(headers))  # NOSONAR
        _body = SafeHTML(''.join(rows))  # NOSONAR
        return str(
            html(
                t'<div class="{wrapper_class}"><table class="{table_class}">'
                t'<thead><tr>{_headers}</tr></thead><tbody>{_body}</tbody></table></div>'
            )
        )

    def _cell(self, field_schema: dict[str, Any], value: Any) -> SafeHTML:
        if self._is_composite(self._element(field_schema)):
            _content = SafeHTML(self._composite_body(field_schema, value))  # NOSONAR
            return html(t'<td>{_content}</td>')
        text, is_empty = self._text(field_schema, value)
        extra_class, _style = self._value_markup(text, is_empty)
        _class = html(t' class="{extra_class}"') if extra_class else SafeHTML('')  # NOSONAR
        return html(t'<td{_class}{_style}>{text}</td>')

    @staticmethod
    def _title(name: str, field_schema: dict[str, Any]) -> str:
        return field_schema.get('title') or name.replace('_', ' ').title()

    def _generic(self, value: Any) -> str:
        """A composite this module has no schema for: go by the value's shape."""

        if _is_empty(value):
            return self._empty_paragraph()
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            names = list(dict.fromkeys(key for item in value for key in item))
            return self._table([(name, {}) for name in names], value)
        if isinstance(value, dict):
            return self._fields([(key, {}) for key in value], value)
        text, is_empty = self._text({}, value)  # NOSONAR - read in the t-string below
        css = self._theme.display_class('empty') if is_empty else ''  # NOSONAR
        return str(html(t'<p class="{css}">{text}</p>'))

    def _composite_body(self, field_schema: dict[str, Any], value: Any) -> str:
        model_ref = resolve_nested_model_ref(field_schema)
        definition = self._schema_defs.get(model_ref or '')
        if definition:
            if _is_empty(value):
                return self._empty_paragraph()
            return self._fields(ordered_properties(definition), value)

        item_ref = resolve_list_item_ref(field_schema)
        definition = self._schema_defs.get(item_ref or '')
        if definition:
            shown = [(n, s) for n, s in ordered_properties(definition) if self._is_shown(s)]
            return self._table(shown, value if isinstance(value, list) else [])

        # DataTableLayout.as_layout_value() bundles the rows with their model.
        model_cls = value.get('model_cls') if isinstance(value, dict) else None
        if isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
            metadata = build_schema_metadata(model_cls)  # type: ignore[arg-type]
            table_renderer = _DisplayRenderer(self._renderer, metadata.schema_defs)
            shown = [(n, s) for n, s in metadata.fields if table_renderer._is_shown(s)]
            return table_renderer._table(shown, _plain(value.get('rows')) or [])
        return self._generic(value)

    def _fields(self, fields: list[tuple[str, dict[str, Any]]], data: Any) -> str:
        """Definition lists for runs of plain fields, sections between them."""

        values = data if isinstance(data, dict) else {}
        parts: list[str] = []
        rows: list[tuple[str, str, bool]] = []
        for name, field_schema in fields:
            if not self._is_shown(field_schema):
                continue
            value = values.get(name)
            if self._is_composite(self._element(field_schema)):
                parts.extend((self._rows(rows), self.section(name, field_schema, value)))
                rows = []
            else:
                rows.append((self._title(name, field_schema), *self._text(field_schema, value)))
        parts.append(self._rows(rows))
        return '\n'.join(part for part in parts if part)

    def section(
        self,
        name: str,
        field_schema: dict[str, Any],
        value: Any,
        *,
        in_group: bool = False,
        edit_url: str | None = None,
    ) -> str:
        title = self._title(name, field_schema)
        body = self._composite_body(field_schema, value)
        if edit_url:
            edit_class = self._theme.display_class('edit')  # NOSONAR
            label = f'Edit {title}'  # NOSONAR
            link = html(t'<a class="{edit_class}" href="{edit_url}" aria-label="{label}">Edit</a>')
            body = f'{link}\n{body}'
        if in_group:
            return body
        return self._renderer._layout_engine._render_layout_card(title, body, '')  # noqa: SLF001

    def top_level(
        self,
        fields: list[tuple[str, dict[str, Any]]],
        data: dict[str, Any],
        edit_urls: dict[str, str],
    ) -> str:
        parts: list[str] = []
        pending: list[tuple[str, dict[str, Any]]] = []
        for name, field_schema in fields:
            if name in edit_urls:
                parts.append(self._fields(pending, data))
                pending = []
                parts.append(
                    self.section(name, field_schema, data.get(name), edit_url=edit_urls[name])
                )
            else:
                pending.append((name, field_schema))
        parts.append(self._fields(pending, data))
        return '\n'.join(part for part in parts if part)


def _grouped_content(
    renderer: 'EnhancedFormRenderer',
    display: _DisplayRenderer,
    metadata: SchemaMetadata,
    values: dict[str, Any],
    layout: str,
    general_title: str,
    edit_urls: dict[str, str],
) -> str:
    engine = renderer._layout_engine  # noqa: SLF001
    group_names = {name for name, _schema in metadata.group_fields}
    in_group = layout != 'side-by-side'
    rendered = []
    for title, fields in engine.group_fields(metadata, layout, general_title):
        name = fields[0][0]
        if name in group_names:
            body = display.section(
                name,
                fields[0][1],
                values.get(name),
                in_group=in_group,
                edit_url=edit_urls.get(name),
            )
        else:
            body = display.top_level(fields, values, {})
            if not body:
                continue
            if not in_group:
                body = engine._render_layout_card(title, body, '')  # noqa: SLF001
        rendered.append({'title': title, 'content': body})
    return engine.render_group_component(rendered, layout)


def render_display(
    renderer: 'EnhancedFormRenderer',
    metadata: SchemaMetadata,
    data: Any,
    *,
    layout: str,
    general_title: str,
    edit_urls: dict[str, str] | None,
) -> str:
    check_layout(layout)
    edit_urls = dict(edit_urls or {})
    _check_edit_urls(edit_urls, metadata)
    plain = _plain(data)
    values: dict[str, Any] = plain if isinstance(plain, dict) else {}
    display = _DisplayRenderer(renderer, metadata.schema_defs)

    # A wizard is a way of filling a form in, not of reading it: flat.
    if layout in GROUPED_LAYOUTS and layout != 'wizard':
        content = _grouped_content(
            renderer, display, metadata, values, layout, general_title, edit_urls
        )
    else:
        content = display.top_level(metadata.fields, values, edit_urls)

    theme = renderer.theme
    form_class = theme.form_class() or renderer.class_defaults.form_class()
    wrapper_class = theme.transform_form_attributes({'class': form_class}).get('class', '')
    _class = f'sf-display {wrapper_class}'.strip()  # NOSONAR
    _content = SafeHTML(content)  # NOSONAR
    wrapper = html(t'<div class="{_class}">{_content}</div>')
    blocks = [theme.before_form(), wrapper, theme.after_form()]
    return '\n'.join(str(block) for block in blocks if block)
