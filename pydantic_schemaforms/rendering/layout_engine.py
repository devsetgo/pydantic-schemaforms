"""Shared layout primitives plus the rendering layout engine."""

from __future__ import annotations

import secrets
from html import escape
from typing import TYPE_CHECKING, Any, Union
from collections.abc import Callable

from pydantic_schemaforms.layout_base import BaseLayout
from pydantic_schemaforms.templates import FormTemplates
from pydantic_schemaforms.tstring import SafeHTML, html
from .context import RenderContext
from .form_style import BOOTSTRAP_TAB_PANEL_TEMPLATE, get_form_style
from pydantic_schemaforms.error_tree import has_errors
from .schema_parser import SchemaMetadata

if TYPE_CHECKING:  # pragma: no cover
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer


Renderable = Union[str, list[str]]
_DEFAULT_FORM_STYLE = get_form_style('default', 'default')
LayoutRenderer = Callable[
    [str, dict[str, Any], Any, dict[str, Any], RenderContext, 'LayoutEngine'], str
]


# Set on the schema of a composite field rendered as the sole content of a
# tab or accordion panel, whose heading already shows the field's title, so
# the field must not draw a second titled card (see nested_model_renderer).
IN_GROUP_FLAG = '_in_group'

# Leading space: appended directly after another class in the templates.
_ACTIVE_CLASS = ' active'


def _unique_id_prefix(kind: str) -> str:
    """Fresh per render, so two tabbed or accordion layouts on one page (or one
    layout rendered twice) never share element ids."""
    return f'{kind}-{secrets.token_hex(4)}'


def _wrap_side_by_side_column(col: str) -> str:
    _col = SafeHTML(str(col))
    return html(t'<div class="side-by-side-column">{_col}</div>')


class HorizontalLayout(BaseLayout):
    """Horizontal layout using flexbox."""

    template = """<div class="horizontal-layout ${class_}" style="display: flex; flex-direction: row; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | list[BaseLayout] | None = None,
        *,
        gap: str = '1rem',
        align_items: str = 'flex-start',
        justify_content: str = 'flex-start',
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.gap = gap
        self.align_items = align_items
        self.justify_content = justify_content

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [
            f'gap: {self.gap}',
            f'align-items: {self.align_items}',
            f'justify-content: {self.justify_content}',
        ]

        current_style = kwargs.get('style', '')
        kwargs['style'] = '; '.join(filter(None, [current_style, *additional_styles]))

        return super().render(**kwargs)


class VerticalLayout(BaseLayout):
    """Vertical layout using flexbox."""

    template = """<div class="vertical-layout ${class_}" style="display: flex; flex-direction: column; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | list[BaseLayout] | None = None,
        *,
        gap: str = '1rem',
        align_items: str = 'stretch',
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.gap = gap
        self.align_items = align_items

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [f'gap: {self.gap}', f'align-items: {self.align_items}']

        current_style = kwargs.get('style', '')
        kwargs['style'] = '; '.join(filter(None, [current_style, *additional_styles]))

        return super().render(**kwargs)


class GridLayout(BaseLayout):
    """CSS Grid layout for complex arrangements."""

    template = """<div class="grid-layout ${class_}" style="display: grid; grid-template-columns: ${columns}; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | list[BaseLayout] | None = None,
        *,
        columns: str = '1fr 1fr',
        gap: str = '1rem',
        rows: str | None = None,
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.columns = columns
        self.gap = gap
        self.rows = rows

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [f'gap: {self.gap}']

        if self.rows:
            additional_styles.append(f'grid-template-rows: {self.rows}')

        current_style = kwargs.get('style', '')
        kwargs['style'] = '; '.join(filter(None, [current_style, *additional_styles]))
        kwargs['columns'] = self.columns

        return super().render(**kwargs)


class ResponsiveGridLayout(GridLayout):
    """Responsive grid that adapts to screen size."""

    def __init__(
        self,
        content: Renderable | BaseLayout | list[BaseLayout] | None = None,
        *,
        min_column_width: str = '300px',
        gap: str = '1rem',
        **kwargs: Any,
    ) -> None:
        columns = f'repeat(auto-fit, minmax({min_column_width}, 1fr))'
        super().__init__(content, columns=columns, gap=gap, **kwargs)


class TabLayout(BaseLayout):
    """Tab layout with JavaScript interactivity."""

    template = """
<div class="tab-layout ${class_}" style="${style}">
    <div class="tab-navigation" role="tablist">
        ${tab_buttons}
    </div>
    <div class="tab-content">
        ${tab_panels}
    </div>
</div>
${component_assets}
    """

    def __init__(self, tabs: list[dict[str, str]], active_index: int = 0, **kwargs: Any) -> None:
        super().__init__(content='', **kwargs)
        self.tabs = tabs
        self.active_index = active_index

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        attrs: dict[str, Any] = {**self.attributes, **kwargs}
        layout_class = self._merge_classes(attrs)
        layout_style = self._merge_styles(attrs)

        renderer = attrs.get('renderer')
        theme = getattr(renderer, 'theme', None) if renderer else None

        prefix = _unique_id_prefix('tab')
        tab_ids = [f'{prefix}-{i}' for i in range(len(self.tabs))]

        tab_buttons: list[str] = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == self.active_index
            button_template = FormTemplates.TAB_BUTTON
            if theme:
                tpl = getattr(theme.form_style.templates, 'tab_button', None)
                if tpl:
                    button_template = tpl
            tab_buttons.append(
                button_template.render(
                    active_class=_ACTIVE_CLASS if is_active else '',
                    aria_selected='true' if is_active else 'false',
                    tab_id=tab_id,
                    title=tab['title'],
                )
            )

        tab_panels: list[str] = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == self.active_index
            panel_template = FormTemplates.TAB_PANEL
            if theme:
                tpl = getattr(theme.form_style.templates, 'tab_panel', None)
                if tpl:
                    panel_template = tpl

            # Bootstrap tab panels need `show active` to display initial content
            active_class = _ACTIVE_CLASS
            if panel_template is BOOTSTRAP_TAB_PANEL_TEMPLATE:  # type: ignore[name-defined]
                active_class = ' show active'

            tab_panels.append(
                panel_template.render(
                    tab_id=tab_id,
                    active_class=active_class if is_active else '',
                    display_style='block' if is_active else 'none',
                    aria_hidden='false' if is_active else 'true',
                    content=tab['content'],
                )
            )

        template = _DEFAULT_FORM_STYLE.templates.tab_layout
        assets = _DEFAULT_FORM_STYLE.assets.tab_assets
        if theme:
            themed_assets = theme.tab_component_assets()
            if themed_assets:
                assets = themed_assets
            themed_template = getattr(theme, 'tab_layout_template', None)
            if callable(themed_template):
                template = themed_template()

        return template.render(  # type: ignore[union-attr]
            layout_class=layout_class,
            layout_style=layout_style,
            tab_buttons='\n'.join(tab_buttons),
            tab_panels='\n'.join(tab_panels),
            component_assets=assets,
        )


class AccordionLayout(BaseLayout):
    """Accordion layout with collapsible sections."""

    template = """
<div class="accordion-layout ${class_}" style="${style}">
    ${accordion_sections}
</div>
${component_assets}
    """

    def __init__(self, sections: list[dict[str, str]], **kwargs: Any) -> None:
        super().__init__(content='', **kwargs)
        self.sections = sections

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        attrs: dict[str, Any] = {**self.attributes, **kwargs}
        layout_class = self._merge_classes(attrs)
        layout_style = self._merge_styles(attrs)

        renderer = attrs.get('renderer')
        theme = getattr(renderer, 'theme', None) if renderer else None

        prefix = _unique_id_prefix('accordion')
        section_ids = [f'{prefix}-{i}' for i in range(len(self.sections))]
        accordion_sections: list[str] = []
        for _i, (section_id, section) in enumerate(zip(section_ids, self.sections, strict=False)):
            is_expanded = section.get('expanded', False)
            section_template = FormTemplates.ACCORDION_SECTION
            if theme:
                tpl = getattr(theme.form_style.templates, 'accordion_section', None)
                if tpl:
                    section_template = tpl
            accordion_sections.append(
                section_template.render(
                    section_id=section_id,
                    expanded_class=' expanded' if is_expanded else '',
                    aria_expanded='true' if is_expanded else 'false',
                    display_style='block' if is_expanded else 'none',
                    title=section['title'],
                    content=section['content'],
                )
            )

        template = _DEFAULT_FORM_STYLE.templates.accordion_layout
        assets = _DEFAULT_FORM_STYLE.assets.accordion_assets
        if theme:
            themed_assets = theme.accordion_component_assets()
            if themed_assets:
                assets = themed_assets
            themed_template = getattr(theme, 'accordion_layout_template', None)
            if callable(themed_template):
                template = themed_template()

        return template.render(  # type: ignore[union-attr]
            layout_class=layout_class,
            layout_style=layout_style,
            sections='\n'.join(accordion_sections),
            component_assets=assets,
        )


class WizardLayout(BaseLayout):
    """Step wizard: every step is rendered into the one <form>, and a script
    shows one at a time, so a single POST submits all of them."""

    def __init__(
        self,
        steps: list[dict[str, Any]],
        active_index: int = 0,
        *,
        linear: bool = True,
        show_progress: bool = True,
        back_label: str = 'Back',
        next_label: str = 'Next',
        **kwargs: Any,
    ) -> None:
        super().__init__(content='', **kwargs)
        self.steps = steps
        self.active_index = active_index
        self.linear = linear
        self.show_progress = show_progress
        self.back_label = back_label
        self.next_label = next_label

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        attrs: dict[str, Any] = {**self.attributes, **kwargs}
        renderer = attrs.get('renderer')
        theme = getattr(renderer, 'theme', None) if renderer else None
        form_style = getattr(theme, 'form_style', None) or _DEFAULT_FORM_STYLE
        templates = form_style.templates

        steps_html: list[str] = []
        progress_items: list[str] = []
        for index, step in enumerate(self.steps):
            is_active = index == self.active_index
            steps_html.append(
                templates.wizard_step.render(
                    index=str(index),
                    title=step['title'],
                    content=step['content'],
                    active_class=_ACTIVE_CLASS if is_active else '',
                )
            )
            state = (_ACTIVE_CLASS if is_active else '') + (
                ' has-error' if step.get('has_error') else ''
            )
            progress_items.append(
                templates.wizard_progress_item.render(
                    index=str(index), number=str(index + 1), title=step['title'], state_class=state
                )
            )

        progress_html = (
            templates.wizard_progress.render(items_html='\n'.join(progress_items))
            if self.show_progress
            else ''
        )
        assets = theme.wizard_component_assets() if theme else form_style.assets.wizard_assets
        return templates.wizard_layout.render(
            layout_class=self._merge_classes(attrs),
            linear='true' if self.linear else 'false',
            active_step=str(self.active_index),
            progress_html=progress_html,
            steps_html='\n'.join(steps_html),
            footer_html=templates.wizard_footer.render(
                back_label=self.back_label, next_label=self.next_label
            ),
            component_assets=assets,
        )


class ModalLayout(BaseLayout):
    """Modal dialog layout."""

    template = """
<div class="modal-overlay ${class_}" id="${modal_id}" style="display: none; ${style}">
    <div class="modal-dialog" role="dialog" aria-labelledby="${modal_id}-title">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="${modal_id}-title" class="modal-title">${title}</h2>
                <button class="modal-close" onclick="closeModal('${modal_id}')" aria-label="Close">×</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                ${footer}
            </div>
        </div>
    </div>
</div>
<script>
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        modal.focus();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal-overlay[style*="flex"]');
        if (openModal) {
            closeModal(openModal.id);
        }
    }
});
</script>
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
.modal-dialog {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    max-width: 90vw;
    max-height: 90vh;
    overflow: auto;
}
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e0e0e0;
}
.modal-title {
    margin: 0;
    font-size: 1.25rem;
}
.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
}
.modal-body {
    padding: 1rem;
}
.modal-footer {
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
    text-align: right;
}
</style>
    """

    def __init__(
        self, modal_id: str, title: str, content: str, footer: str = '', **kwargs: Any
    ) -> None:
        safe_modal_id = ''.join(c if c.isalnum() or c in '_-' else '_' for c in modal_id)
        onclick = f"closeModal('{safe_modal_id}')"
        default_footer = footer or html(t'<button onclick="{onclick}">Close</button>')
        super().__init__(
            content=content,
            modal_id=modal_id,
            title=escape(title),
            footer=default_footer,
            **kwargs,
        )
        self.modal_id = modal_id
        self.title = title
        self.footer = default_footer

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        return super().render(**kwargs)


class CardLayout(BaseLayout):
    """Card layout for grouped content."""

    template = """
<div class="card-layout ${class_}" style="${style}">
    <div class="card-header">
        <h3 class="card-title">${title}</h3>
    </div>
    <div class="card-body">
        ${content}
    </div>
    <div class="card-footer">
        ${footer}
    </div>
</div>
<style>
.card-layout {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}
.card-header {
    padding: 1rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
    border-radius: 8px 8px 0 0;
}
.card-title {
    margin: 0;
    font-size: 1.1rem;
}
.card-body {
    padding: 1rem;
}
.card-footer {
    padding: 1rem;
    background-color: #f8f9fa;
    border-top: 1px solid #e0e0e0;
    border-radius: 0 0 8px 8px;
}
</style>
    """

    def __init__(self, title: str, content: str, footer: str = '', **kwargs: Any) -> None:
        super().__init__(content, **kwargs)
        self.title = title
        self.footer = footer

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        kwargs['title'] = escape(self.title)
        kwargs['footer'] = self.footer
        return super().render(**kwargs)


class LayoutComposer:
    """Single entry point for creating layout primitives."""

    Horizontal = HorizontalLayout
    Vertical = VerticalLayout
    Grid = GridLayout
    ResponsiveGrid = ResponsiveGridLayout
    Tabs = TabLayout
    Accordion = AccordionLayout
    Modal = ModalLayout
    Card = CardLayout

    @staticmethod
    def create_horizontal(*content: Any, **kwargs: Any) -> HorizontalLayout:
        return HorizontalLayout(list(content), **kwargs)

    @staticmethod
    def create_vertical(*content: Any, **kwargs: Any) -> VerticalLayout:
        return VerticalLayout(list(content), **kwargs)

    @staticmethod
    def create_grid(*content: Any, columns: str = '1fr 1fr', **kwargs: Any) -> GridLayout:
        return GridLayout(list(content), columns=columns, **kwargs)

    @staticmethod
    def responsive_grid(
        *content: Any,
        min_width: str = '300px',
        **kwargs: Any,
    ) -> ResponsiveGridLayout:
        return ResponsiveGridLayout(list(content), min_column_width=min_width, **kwargs)

    @staticmethod
    def create_tabs(tabs: list[dict[str, str]], **kwargs: Any) -> TabLayout:
        return TabLayout(tabs, **kwargs)

    @staticmethod
    def create_accordion(sections: list[dict[str, str]], **kwargs: Any) -> AccordionLayout:
        return AccordionLayout(sections, **kwargs)

    @staticmethod
    def create_modal(modal_id: str, title: str, content: str, **kwargs: Any) -> ModalLayout:
        return ModalLayout(modal_id, title, content, **kwargs)

    @staticmethod
    def create_card(title: str, content: str, **kwargs: Any) -> CardLayout:
        return CardLayout(title, content, **kwargs)


LayoutFactory = LayoutComposer
Layout = LayoutComposer


class LayoutEngine:
    """Encapsulates layout rendering routines for form renderers."""

    _custom_renderers: dict[str, LayoutRenderer] = {}
    _builtin_renderer_names: set[str] = set()
    _multipart_predicates: dict[str, Callable[[Any], bool]] = {}

    def __init__(self, renderer: 'EnhancedFormRenderer') -> None:
        self._renderer = renderer

    # ------------------------------------------------------------------
    # Registration hooks
    # ------------------------------------------------------------------
    @classmethod
    def register_layout_renderer(
        cls,
        name: str,
        renderer: LayoutRenderer,
        *,
        builtin: bool = False,
        requires_multipart: Callable[[Any], bool] | None = None,
    ) -> None:
        """Register a custom layout renderer callable by name.

        `builtin=True` marks a renderer shipped by this library itself
        (e.g. DataTableLayout's/model_list's) so it survives
        `reset_layout_renderers()` -- module-level registration only runs
        once per process, so a test-suite-wide reset would otherwise wipe
        it permanently for the rest of the run. One-off/test/app-level
        renderers should leave this False so `reset_layout_renderers()`
        still clears them between tests.

        `requires_multipart`: pass a callable when this renderer might emit
        its own `<input type="file">` inside the field's own output (as
        DataTableLayout's does when `csv_upload` is on) -- a *nested* file
        input like that isn't a top-level FormModel field, so the form's
        own file-field scan (which only sees this field's `layout` element,
        not what it renders) can never discover it on its own, and the
        enclosing `<form>` would silently miss `enctype="multipart/form-
        data"` -- without which a browser sends only the chosen file's
        *name*, never its contents. Called with this field's raw value
        (whatever `as_layout_value()`-equivalent built) at render time;
        return whether *that specific value* needs multipart encoding.
        """

        if not callable(renderer):  # pragma: no cover - defensive
            raise TypeError('renderer must be callable')
        cls._custom_renderers[name] = renderer
        if builtin:
            cls._builtin_renderer_names.add(name)
        if requires_multipart is not None:
            cls._multipart_predicates[name] = requires_multipart

    @classmethod
    def layout_renderer(
        cls,
        name: str,
        *,
        builtin: bool = True,
        requires_multipart: Callable[[Any], bool] | None = None,
    ) -> Callable[[LayoutRenderer], LayoutRenderer]:
        """Decorator form of `register_layout_renderer`, defaulting to
        `builtin=True` since it's meant for this library's own composite
        controls, registered once at import time."""

        def decorator(func: LayoutRenderer) -> LayoutRenderer:
            cls.register_layout_renderer(
                name, func, builtin=builtin, requires_multipart=requires_multipart
            )
            return func

        return decorator

    @classmethod
    def get_renderer_for_element(cls, ui_element: str | None) -> LayoutRenderer | None:
        """Look up a registered renderer directly by a field's own
        ui_element/input_type string (the second, independent keyspace --
        see `_build_layout_body` for the `layout_handler`-keyed lookup used
        by `input_type='layout'` fields instead)."""

        return cls._custom_renderers.get(ui_element) if ui_element else None

    @classmethod
    def layout_field_needs_multipart(cls, handler_name: str | None, value: Any) -> bool:
        """Whether a `layout_handler`-dispatched field's *current value*
        will render its own file input -- see `requires_multipart` above."""

        if not handler_name:
            return False
        predicate = cls._multipart_predicates.get(handler_name)
        return bool(predicate(value)) if predicate else False

    @classmethod
    def reset_layout_renderers(cls) -> None:
        """Clear non-builtin custom layout renderers (useful in tests)."""

        # Snapshot the names to delete into a set first -- deleting from
        # cls._custom_renderers while iterating it directly would raise
        # RuntimeError: dictionary changed size during iteration.
        non_builtin_names = set(cls._custom_renderers) - cls._builtin_renderer_names
        for name in non_builtin_names:
            cls._multipart_predicates.pop(name, None)
            del cls._custom_renderers[name]

    # ------------------------------------------------------------------
    # Public API used by EnhancedFormRenderer
    # ------------------------------------------------------------------
    def render_groups(
        self,
        metadata: SchemaMetadata,
        data: dict[str, Any],
        errors: dict[Any, Any],
        context: RenderContext,
        *,
        mode: str,
        general_title: str = 'General',
        wizard_options: dict[str, Any] | None = None,
    ) -> list[str]:
        """Render a parent form as groups -- its own plain fields first, then
        one group per sub-form field (nested model, model_list, layout field),
        in field order -- shown as tabs, side-by-side columns, accordion panels,
        or wizard steps."""

        if not metadata.group_fields:
            raise ValueError(
                f"layout='{mode}' needs groups to arrange, but this form has no sub-form "
                'fields. Split it into nested FormModel fields, e.g. '
                '`contact: Contact = Field(title="Contact")`, or use layout="vertical". '
                'See docs/tutorial/layouts.md.'
            )

        group_names = {name for name, _schema in metadata.group_fields}
        plain_fields = [(n, sch) for n, sch in metadata.fields if n not in group_names]
        groups: list[tuple[str, list[tuple[str, dict[str, Any]]]]] = []
        if plain_fields:
            groups.append((general_title, plain_fields))
        for name, schema in metadata.group_fields:
            title = schema.get('title') or name.replace('_', ' ').title()
            if mode == 'wizard':
                title = schema.get('ui_step_title') or title
            groups.append((title, [(name, schema)]))

        # A tab/panel/step heading already shows a sub-form's title, so the
        # sub-form must not draw its own titled card inside it. Columns have no heading.
        in_group = mode in ('tabbed', 'accordion', 'wizard')

        rendered: list[dict[str, Any]] = []
        active_index: int | None = None
        for index, (title, fields) in enumerate(groups):
            parts = []
            for name, schema in fields:
                if in_group and name in group_names:
                    schema = {**schema, IN_GROUP_FLAG: True}
                parts.append(
                    self._renderer._render_field(  # noqa: SLF001
                        name,
                        schema,
                        data.get(name),
                        errors.get(name),
                        metadata.required_fields,
                        context,
                        'vertical',
                    )
                )
            body = '\n'.join(parts)
            if mode == 'side-by-side' and fields is plain_fields:
                body = self._render_layout_card(title, body, '')
            group_has_error = any(has_errors(errors.get(n)) for n, _ in fields)
            if active_index is None and group_has_error:
                active_index = index
            rendered.append({'title': title, 'content': body, 'has_error': group_has_error})

        active_index = active_index or 0
        renderer_kwargs = {'framework': self._renderer.framework, 'renderer': self._renderer}

        if mode == 'tabbed':
            component: BaseLayout = TabLayout(
                tabs=rendered, active_index=active_index, class_='form-groups-tabbed'
            )
        elif mode == 'accordion':
            sections = [
                {**group, 'expanded': index == active_index} for index, group in enumerate(rendered)
            ]
            component = AccordionLayout(sections=sections, class_='form-groups-accordion')
        elif mode == 'wizard':
            component = WizardLayout(
                steps=rendered,
                active_index=active_index,
                class_='form-groups-wizard',
                **(wizard_options or {}),
            )
        else:
            columns = [_wrap_side_by_side_column(group['content']) for group in rendered]
            component = HorizontalLayout(
                content=columns,
                class_='form-groups-side-by-side',
                gap='1.5rem',
                align_items='flex-start',
            )
        return [component.render(**renderer_kwargs)]

    def render_layout_field(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any,
        ui_info: dict[str, Any],
        context: RenderContext,
    ) -> str:
        section_title = field_schema.get('title', field_name.replace('_', ' ').title())
        help_text = ui_info.get('help_text', '')
        body_html = self._build_layout_body(field_name, field_schema, value, ui_info, context)
        return self._render_layout_card(section_title, body_html, help_text)

    def _build_layout_body(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        value: Any,
        ui_info: dict[str, Any],
        context: RenderContext,
    ) -> str:
        handler_name = ui_info.get('layout_handler') or ui_info.get('layout_renderer')
        handler = self._custom_renderers.get(str(handler_name)) if handler_name else None
        if handler is None:
            # NOSONAR comment below: title is read via {title} interpolation below.
            title = field_schema.get('title', field_name.replace('_', ' ').title())  # NOSONAR
            return html(t"""<div class="layout-field-unknown alert alert-warning">
    <p>Layout field "{title}" has no registered layout_handler.</p>
    <small>input_type="layout" needs layout_handler=... naming a renderer registered with
    LayoutEngine.layout_renderer(). To compose forms, nest FormModels as fields instead
    (see docs/tutorial/nested-forms.md).</small>
</div>""")
        try:
            return handler(field_name, field_schema, value, ui_info, context, self)
        except Exception as exc:  # pragma: no cover - defensive message
            return self._layout_error_message(field_name, field_schema, ui_info, exc)

    def _render_layout_card(self, title: str, body_html: str, help_text: str) -> str:
        theme = getattr(self._renderer, 'theme', None)
        if theme:
            themed_section = theme.render_layout_section(title, body_html, help_text)
            if themed_section:
                return themed_section

        form_style = getattr(theme, 'form_style', None) if theme else None
        templates = getattr(form_style, 'templates', None)

        layout_template = getattr(templates, 'layout_section', None)
        if layout_template is None:
            layout_template = _DEFAULT_FORM_STYLE.templates.layout_section

        help_template = getattr(templates, 'layout_help', None)
        if help_template is None:
            help_template = _DEFAULT_FORM_STYLE.templates.layout_help

        help_html = ''
        if help_text:
            help_html = help_template.render(help_text=help_text)

        return layout_template.render(
            title=title,
            help_html=help_html,
            body_html=body_html,
        )

    def _layout_error_message(
        self,
        field_name: str,
        field_schema: dict[str, Any],
        ui_info: dict[str, Any],
        exc: Exception,
    ) -> str:
        title = field_schema.get('title', field_name.replace('_', ' ').title())
        help_text = ui_info.get('help_text', '')
        error_message = str(exc)
        help_html = html(t'<small class="text-muted">{help_text}</small>') if help_text else ''
        return html(t'''
        <div class="layout-field-error alert alert-warning">
            <p>Error rendering layout field "{title}": {error_message}</p>
            {help_html}
        </div>
        ''')


GROUPED_LAYOUTS = frozenset({'tabbed', 'side-by-side', 'accordion', 'wizard'})
LAYOUTS = frozenset({'vertical', *GROUPED_LAYOUTS})
WIZARD_OPTIONS = frozenset({'linear', 'show_progress', 'back_label', 'next_label'})


def check_layout(layout: str) -> None:
    """Reject unknown layout names."""

    if layout not in LAYOUTS:
        raise ValueError(f'Unknown layout {layout!r}; expected one of {sorted(LAYOUTS)}.')


def check_wizard_options(options: dict[str, Any] | None) -> dict[str, Any]:
    """Validate `wizard_options=` (a typo would otherwise be silently ignored)."""

    options = dict(options or {})
    unknown = set(options) - WIZARD_OPTIONS
    if unknown:
        raise ValueError(
            f'Unknown wizard_options {sorted(unknown)}; expected any of {sorted(WIZARD_OPTIONS)}.'
        )
    return options
