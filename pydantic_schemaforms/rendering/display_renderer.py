"""Read-only rendering of validated data: review and confirmation pages.

Walks the same field tree as the form, with the same labels, order and
sections, but shows values instead of inputs. Every value reaches the page
through ``html(t'...')``, so nothing submitted is ever trusted as markup, and
values are never linked, since a submitted URL may be ``javascript:``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from pydantic import BaseModel, SecretBytes, SecretStr

from pydantic_schemaforms.show_when import field_rules, is_shown, prune
from pydantic_schemaforms.tstring import SafeHTML, html

from .layout_engine import GROUPED_LAYOUTS, LayoutEngine, check_layout, is_sub_form_group
from .schema_parser import (
    GROUP_ELEMENTS,
    SchemaMetadata,
    arrange_fields,
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
    def __init__(
        self,
        renderer: 'EnhancedFormRenderer',
        schema_defs: dict[str, Any],
        *,
        live: bool = False,
    ) -> None:
        self._renderer = renderer
        self._schema_defs = schema_defs
        self._field_renderer = renderer._field_renderer  # noqa: SLF001
        self._theme = renderer.theme
        # live: a wizard review step filled in the browser. Each value carries a
        # slot naming its input, relative to the list item it sits in.
        self._live = live
        self._path: list[str] = []

    @contextmanager
    def _scope(self, name: str) -> Iterator[None]:
        self._path.append(name)
        try:
            yield
        finally:
            self._path.pop()

    @contextmanager
    def _list_item(self) -> Iterator[None]:
        saved, self._path = self._path, []
        try:
            yield
        finally:
            self._path = saved

    def _slot(self, name: str, field_schema: dict[str, Any]) -> SafeHTML:
        """``data-review-*`` attributes telling the review script how to show a value."""

        if not self._live:
            return SafeHTML('')
        element = self._element(field_schema)
        slot = '.'.join([*self._path, name])  # NOSONAR - read in the t-strings below
        if element in _BOOLEAN_ELEMENTS:
            kind = 'yesno'
        elif element == 'password' or field_schema.get('writeOnly'):
            kind = 'mask'
        elif element in _LAST_FOUR_ELEMENTS:
            kind = 'last4'
        elif element in _CHOICE_ELEMENTS:
            labels = json.dumps(self._choice_map(field_schema))  # NOSONAR
            return html(
                t' data-review-slot="{slot}" data-review-format="choice"'
                t' data-review-choices="{labels}"'
            )
        elif element == 'file':
            kind = 'file'
        elif element in ('datetime', 'datetime-local'):
            kind = 'datetime'
        else:
            kind = 'text'
        return html(t' data-review-slot="{slot}" data-review-format="{kind}"')

    def _element(self, field_schema: dict[str, Any]) -> str:
        if field_schema.get('format') == 'password':
            return 'password'
        return self._field_renderer._infer_ui_element(field_schema)  # noqa: SLF001

    def _is_shown(self, field_schema: dict[str, Any], scope: Any = None) -> bool:
        if extract_ui_info(field_schema).get('hidden'):
            return False
        if scope is not None and not is_shown(field_schema, scope):
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

    def _choice_map(self, field_schema: dict[str, Any]) -> dict[str, str]:
        ui_info = extract_ui_info(field_schema)
        _options, choices = self._field_renderer._extract_ui_options(ui_info, field_schema)  # noqa: SLF001
        choices = (
            choices
            or field_schema.get('enum')
            or (field_schema.get('items') or {}).get('enum')
            or []
        )
        return {
            str(option['value']): str(option['label'])
            for option in self._field_renderer._normalize_options(choices, None)  # noqa: SLF001
        }

    def _text(self, field_schema: dict[str, Any], value: Any) -> tuple[str, bool]:
        """The text shown for a non-composite field, and whether it counts as empty."""

        element = self._element(field_schema)
        ui_info = extract_ui_info(field_schema)
        if element in _BOOLEAN_ELEMENTS:
            is_true = value is True or str(value).lower() in _TRUE_STRINGS
            return ('Yes' if is_true else 'No'), False
        if _is_empty(value):  # NOSONAR - S2583 is wrong: most values are not empty
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

    def _rows(self, rows: list[tuple[str, str, bool, SafeHTML]]) -> str:
        if not rows:
            return ''
        theme = self._theme
        list_class = theme.display_class('list')  # NOSONAR
        term_class = theme.display_class('term')  # NOSONAR
        value_class = theme.display_class('value')
        parts = []
        for title, text, is_empty, _slot in rows:
            extra_class, _style = self._value_markup(text, is_empty)
            _dd_class = f'{value_class} {extra_class}'.strip()  # NOSONAR
            parts.append(
                str(
                    html(
                        t'<dt class="{term_class}">{title}</dt>'
                        t'<dd class="{_dd_class}"{_style}{_slot}>{text}</dd>'
                    )
                )
            )
        _rows = SafeHTML(''.join(parts))  # NOSONAR
        return str(html(t'<dl class="{list_class}">{_rows}</dl>'))

    def _empty_paragraph(self) -> str:
        css = self._theme.display_class('empty')  # NOSONAR
        return str(html(t'<p class="{css}">{EMPTY_TEXT}</p>'))

    def _table(self, columns: list[tuple[str, dict[str, Any]]], items: list[Any]) -> str:
        if self._live and self._path:
            return self._live_table(columns, items)
        if not items:
            return self._empty_paragraph()
        theme = self._theme
        wrapper_class = theme.display_class('table_wrapper')  # NOSONAR
        table_class = theme.table_class({})  # NOSONAR
        headers = [
            str(html(t'<th scope="col">{self._title(name, schema)}</th>'))
            for name, schema in columns
        ]
        columns_have_rules = any(field_rules(schema) for _n, schema in columns)
        rows = []
        for item in items:
            data = item if isinstance(item, dict) else {}
            cells = [
                str(self._cell(name, schema, data.get(name)))
                if not columns_have_rules or is_shown(schema, data)
                else '<td></td>'
                for name, schema in columns
            ]
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

    def _live_table(self, columns: list[tuple[str, dict[str, Any]]], items: list[Any]) -> str:
        """A list the review script rebuilds from the live items: a row template
        whose slots are named relative to the item, plus today's rows as a start."""

        list_name = '.'.join(self._path)  # NOSONAR - read in the t-string below
        with self._list_item():
            row_template = ''.join(str(self._cell(name, schema, None)) for name, schema in columns)
            static = self._live_rows(columns, items)
        theme = self._theme
        wrapper_class = theme.display_class('table_wrapper')  # NOSONAR
        table_class = theme.table_class({})  # NOSONAR
        _headers = SafeHTML(  # NOSONAR
            ''.join(
                str(html(t'<th scope="col">{self._title(name, schema)}</th>'))
                for name, schema in columns
            )
        )
        _template = SafeHTML(row_template)  # NOSONAR
        _static = SafeHTML(static)  # NOSONAR
        _empty = SafeHTML(
            self._empty_paragraph().replace('<p ', '<p data-review-empty ', 1)
        )  # NOSONAR
        _hidden = SafeHTML('' if items else ' hidden')  # NOSONAR
        _empty_hidden = SafeHTML(' hidden' if items else '')  # NOSONAR
        return str(
            html(
                t'<div class="{wrapper_class}" data-review-table{_hidden}>'
                t'<table class="{table_class}"><thead><tr>{_headers}</tr></thead>'
                t'<tbody data-review-list="{list_name}"><template><tr>{_template}</tr></template>'
                t'{_static}</tbody></table></div>'
                t'<div{_empty_hidden} data-review-empty-wrapper>{_empty}</div>'
            )
        )

    def _live_rows(self, columns: list[tuple[str, dict[str, Any]]], items: list[Any]) -> str:
        rows = []
        for item in items:
            data = item if isinstance(item, dict) else {}
            _cells = SafeHTML(  # NOSONAR
                ''.join(str(self._cell(name, schema, data.get(name))) for name, schema in columns)
            )
            rows.append(str(html(t'<tr>{_cells}</tr>')))
        return ''.join(rows)

    def _cell(self, name: str, field_schema: dict[str, Any], value: Any) -> SafeHTML:
        if self._is_composite(self._element(field_schema)):
            with self._scope(name):
                _content = SafeHTML(self._composite_body(field_schema, value))  # NOSONAR
            return html(t'<td>{_content}</td>')
        text, is_empty = self._text(field_schema, value)
        extra_class, _style = self._value_markup(text, is_empty)
        _class = html(t' class="{extra_class}"') if extra_class else SafeHTML('')  # NOSONAR
        _slot = self._slot(name, field_schema)  # NOSONAR
        return html(t'<td{_class}{_style}{_slot}>{text}</td>')

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
            # Live, an empty sub-form still needs its slots: it may be filled in now.
            if _is_empty(value) and not self._live:
                return self._empty_paragraph()
            return self._fields(ordered_properties(definition), value or {})

        item_ref = resolve_list_item_ref(field_schema)
        definition = self._schema_defs.get(item_ref or '')
        if definition:
            items = value if isinstance(value, list) else []
            # A column stays if any row shows it; other rows leave that cell blank.
            # Live, the rows change in the browser, so every column stays.
            shown = [
                (n, s)
                for n, s in ordered_properties(definition)
                if self._is_shown(s) and (self._live or any(is_shown(s, item) for item in items))
            ]
            return self._table(shown, items)

        # DataTableLayout.as_layout_value() bundles the rows with their model.
        model_cls = value.get('model_cls') if isinstance(value, dict) else None
        if isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
            metadata = build_schema_metadata(model_cls)  # type: ignore[arg-type]
            table_renderer = _DisplayRenderer(self._renderer, metadata.schema_defs)
            shown = [(n, s) for n, s in metadata.fields if table_renderer._is_shown(s)]
            return table_renderer._table(shown, _plain(value.get('rows')) or [])
        return self._generic(value)

    def _fields(self, fields: list[tuple[str, dict[str, Any]]], data: Any) -> str:
        """Each ``ui_group`` as a titled section, in order. ``ui_cols`` is left out:
        narrow columns of label-and-value pairs read worse than a list."""

        parts: list[str] = []
        for title, items in arrange_fields(fields):
            body = self._ungrouped_fields(items, data)
            if title is None or not body:
                parts.append(body)
            else:
                parts.append(
                    self._renderer._layout_engine._render_layout_card(title, body, '')  # noqa: SLF001
                )
        return '\n'.join(part for part in parts if part)

    def _ungrouped_fields(self, fields: list[tuple[str, dict[str, Any]]], data: Any) -> str:
        """Definition lists for runs of plain fields, sections between them."""

        values = data if isinstance(data, dict) else {}
        parts: list[str] = []
        rows: list[tuple[str, str, bool, SafeHTML]] = []
        for name, field_schema in fields:
            # Live, a field hidden by a rule may show again, so the script decides.
            if not self._is_shown(field_schema, None if self._live else values):
                continue
            value = values.get(name)
            if self._is_composite(self._element(field_schema)):
                parts.extend((self._rows(rows), self.section(name, field_schema, value)))
                rows = []
            else:
                title = self._title(name, field_schema)
                rows.append(
                    (title, *self._text(field_schema, value), self._slot(name, field_schema))
                )
        parts.append(self._rows(rows))
        return '\n'.join(part for part in parts if part)

    def ungrouped(self, fields: list[tuple[str, dict[str, Any]]], data: Any) -> str:
        return self._ungrouped_fields(fields, data)

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
        with self._scope(name):
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
            if name in edit_urls and is_shown(field_schema, data):
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
        name, field_schema = fields[0]
        if is_sub_form_group(fields, group_names):
            if not is_shown(field_schema, values):
                continue
            body = display.section(
                name,
                field_schema,
                values.get(name),
                in_group=in_group,
                edit_url=edit_urls.get(name),
            )
        else:
            # The tab, panel or card is the group's section, so it needs no second one.
            body = display.ungrouped(fields, values)
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
    values, _errors = prune(
        metadata.schema.get('properties') or {},
        metadata.schema_defs,
        plain if isinstance(plain, dict) else {},
    )
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


def render_review_step(
    renderer: 'EnhancedFormRenderer',
    metadata: SchemaMetadata,
    data: Any,
    steps: list[tuple[str, list[tuple[str, dict[str, Any]]]]],
    *,
    live: bool,
    edit_label: str,
) -> str:
    """A wizard's review step: each step's answers under its title, with an Edit button.

    ``live`` (one POST): slots the wizard script fills from the inputs whenever
    the step opens. Otherwise (``save_steps``): the saved data, and Edit posts
    a jump back like the step header does.
    """

    plain = _plain(data)
    values, _errors = prune(
        metadata.schema.get('properties') or {},
        metadata.schema_defs,
        plain if isinstance(plain, dict) else {},
    )
    display = _DisplayRenderer(renderer, metadata.schema_defs, live=live)
    engine = renderer._layout_engine  # noqa: SLF001
    theme = renderer.theme
    group_names = {name for name, _schema in metadata.group_fields}
    edit_class = theme.display_class('edit')  # NOSONAR - read in the t-strings below
    sections = []
    for index, (title, fields) in enumerate(steps):
        name, field_schema = fields[0]
        if is_sub_form_group(fields, group_names):
            if not live and not is_shown(field_schema, values):
                continue
            body = display.section(name, field_schema, values.get(name), in_group=True)
        else:
            body = display.ungrouped(fields, values)
        if not body:
            continue
        label = f'{edit_label} {title}'  # NOSONAR
        if live:
            button = html(
                t'<button type="button" class="{edit_class}" data-wizard-edit="{index}" '
                t'aria-label="{label}">{edit_label}</button>'
            )
        else:
            action = f'goto:{index}'  # NOSONAR
            button = html(
                t'<button type="submit" class="{edit_class}" name="_sf_wizard" value="{action}" '
                t'aria-label="{label}">{edit_label}</button>'
            )
        card = engine._render_layout_card(title, f'{button}\n{body}', '')  # noqa: SLF001
        _card = SafeHTML(card)  # NOSONAR
        sections.append(str(html(t'<div data-review-section>{_card}</div>')))

    empty_class = theme.display_class('empty')  # NOSONAR
    _sections = SafeHTML('\n'.join(sections))  # NOSONAR
    _live = SafeHTML(' data-wizard-review' if live else '')  # NOSONAR
    return str(
        html(
            t'<div class="sf-display sf-review"{_live} data-review-empty-text="{EMPTY_TEXT}" '
            t'data-review-empty-class="{empty_class}" data-review-mask="{MASK}">{_sections}</div>'
        )
    )
