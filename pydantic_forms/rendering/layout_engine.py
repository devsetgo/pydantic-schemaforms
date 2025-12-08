"""Shared layout primitives plus the rendering layout engine."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

from ..layout_base import BaseLayout
from ..templates import FormTemplates
from .context import RenderContext
from .form_style import BOOTSTRAP_TAB_PANEL_TEMPLATE, get_form_style

if TYPE_CHECKING:  # pragma: no cover
    from ..enhanced_renderer import EnhancedFormRenderer


Renderable = Union[str, List[str]]
_DEFAULT_FORM_STYLE = get_form_style("default", "default")
LayoutRenderer = Callable[[str, Dict[str, Any], Any, Dict[str, Any], RenderContext, "LayoutEngine"], str]


class HorizontalLayout(BaseLayout):
    """Horizontal layout using flexbox."""

    template = """<div class="horizontal-layout ${class_}" style="display: flex; flex-direction: row; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | List[BaseLayout] | None = None,
        *,
        gap: str = "1rem",
        align_items: str = "flex-start",
        justify_content: str = "flex-start",
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.gap = gap
        self.align_items = align_items
        self.justify_content = justify_content

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [
            f"gap: {self.gap}",
            f"align-items: {self.align_items}",
            f"justify-content: {self.justify_content}",
        ]

        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join(filter(None, [current_style, *additional_styles]))

        return super().render(**kwargs)


class VerticalLayout(BaseLayout):
    """Vertical layout using flexbox."""

    template = """<div class="vertical-layout ${class_}" style="display: flex; flex-direction: column; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | List[BaseLayout] | None = None,
        *,
        gap: str = "1rem",
        align_items: str = "stretch",
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.gap = gap
        self.align_items = align_items

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [f"gap: {self.gap}", f"align-items: {self.align_items}"]

        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join(filter(None, [current_style, *additional_styles]))

        return super().render(**kwargs)


class GridLayout(BaseLayout):
    """CSS Grid layout for complex arrangements."""

    template = """<div class="grid-layout ${class_}" style="display: grid; grid-template-columns: ${columns}; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Renderable | BaseLayout | List[BaseLayout] | None = None,
        *,
        columns: str = "1fr 1fr",
        gap: str = "1rem",
        rows: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        resolved_content = [] if content is None else content
        super().__init__(resolved_content, **kwargs)
        self.columns = columns
        self.gap = gap
        self.rows = rows

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        additional_styles = [f"gap: {self.gap}"]

        if self.rows:
            additional_styles.append(f"grid-template-rows: {self.rows}")

        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join(filter(None, [current_style, *additional_styles]))
        kwargs["columns"] = self.columns

        return super().render(**kwargs)


class ResponsiveGridLayout(GridLayout):
    """Responsive grid that adapts to screen size."""

    def __init__(
        self,
        content: Renderable | BaseLayout | List[BaseLayout] | None = None,
        *,
        min_column_width: str = "300px",
        gap: str = "1rem",
        **kwargs: Any,
    ) -> None:
        columns = f"repeat(auto-fit, minmax({min_column_width}, 1fr))"
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

    def __init__(self, tabs: List[Dict[str, str]], **kwargs: Any) -> None:
        super().__init__(content="", **kwargs)
        self.tabs = tabs

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        attrs: Dict[str, Any] = {**self.attributes, **kwargs}
        layout_class = self._merge_classes(attrs)
        layout_style = self._merge_styles(attrs)

        renderer = attrs.get("renderer")
        theme = getattr(renderer, "theme", None) if renderer else None

        tab_ids = [f"tab-{i}" for i in range(len(self.tabs))]

        tab_buttons: List[str] = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == 0
            button_template = FormTemplates.TAB_BUTTON
            if theme:
                tpl = getattr(theme.form_style.templates, "tab_button", None)
                if tpl:
                    button_template = tpl
            tab_buttons.append(
                button_template.render(
                    active_class=" active" if is_active else "",
                    aria_selected="true" if is_active else "false",
                    tab_id=tab_id,
                    title=escape(tab["title"]),
                )
            )

        tab_panels: List[str] = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == 0
            panel_template = FormTemplates.TAB_PANEL
            if theme:
                tpl = getattr(theme.form_style.templates, "tab_panel", None)
                if tpl:
                    panel_template = tpl

            # Bootstrap tab panels need `show active` to display initial content
            active_class = " active"
            if panel_template is BOOTSTRAP_TAB_PANEL_TEMPLATE:  # type: ignore[name-defined]
                active_class = " show active"

            tab_panels.append(
                panel_template.render(
                    tab_id=tab_id,
                    active_class=active_class if is_active else "",
                    display_style="block" if is_active else "none",
                    aria_hidden="false" if is_active else "true",
                    content=tab["content"],
                )
            )

        template = _DEFAULT_FORM_STYLE.templates.tab_layout
        assets = _DEFAULT_FORM_STYLE.assets.tab_assets
        if theme:
            themed_assets = theme.tab_component_assets()
            if themed_assets:
                assets = themed_assets
            themed_template = getattr(theme, "tab_layout_template", None)
            if callable(themed_template):
                template = themed_template()

        return template.render(
            layout_class=layout_class,
            layout_style=layout_style,
            tab_buttons="\n".join(tab_buttons),
            tab_panels="\n".join(tab_panels),
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

    def __init__(self, sections: List[Dict[str, str]], **kwargs: Any) -> None:
        super().__init__(content="", **kwargs)
        self.sections = sections

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        attrs: Dict[str, Any] = {**self.attributes, **kwargs}
        layout_class = self._merge_classes(attrs)
        layout_style = self._merge_styles(attrs)

        renderer = attrs.get("renderer")
        theme = getattr(renderer, "theme", None) if renderer else None

        section_ids = [f"accordion-{i}" for i in range(len(self.sections))]
        accordion_sections: List[str] = []
        for _i, (section_id, section) in enumerate(zip(section_ids, self.sections, strict=False)):
            is_expanded = section.get("expanded", False)
            section_template = FormTemplates.ACCORDION_SECTION
            if theme:
                tpl = getattr(theme.form_style.templates, "accordion_section", None)
                if tpl:
                    section_template = tpl
            accordion_sections.append(
                section_template.render(
                    section_id=section_id,
                    expanded_class=" expanded" if is_expanded else "",
                    aria_expanded="true" if is_expanded else "false",
                    display_style="block" if is_expanded else "none",
                    title=escape(section["title"]),
                    content=section["content"],
                )
            )

        template = _DEFAULT_FORM_STYLE.templates.accordion_layout
        assets = _DEFAULT_FORM_STYLE.assets.accordion_assets
        if theme:
            themed_assets = theme.accordion_component_assets()
            if themed_assets:
                assets = themed_assets
            themed_template = getattr(theme, "accordion_layout_template", None)
            if callable(themed_template):
                template = themed_template()

        return template.render(
            layout_class=layout_class,
            layout_style=layout_style,
            sections="\n".join(accordion_sections),
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

    def __init__(self, modal_id: str, title: str, content: str, footer: str = "", **kwargs: Any) -> None:
        default_footer = footer or f"<button onclick=\"closeModal('{modal_id}')\">Close</button>"
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

    def __init__(self, title: str, content: str, footer: str = "", **kwargs: Any) -> None:
        super().__init__(content, **kwargs)
        self.title = title
        self.footer = footer

    def render(self, **kwargs: Any) -> str:  # type: ignore[override]
        kwargs["title"] = escape(self.title)
        kwargs["footer"] = self.footer
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
    def horizontal(*content: Any, **kwargs: Any) -> HorizontalLayout:
        return HorizontalLayout(list(content), **kwargs)

    @staticmethod
    def vertical(*content: Any, **kwargs: Any) -> VerticalLayout:
        return VerticalLayout(list(content), **kwargs)

    @staticmethod
    def grid(*content: Any, columns: str = "1fr 1fr", **kwargs: Any) -> GridLayout:
        return GridLayout(list(content), columns=columns, **kwargs)

    @staticmethod
    def responsive_grid(
        *content: Any,
        min_width: str = "300px",
        **kwargs: Any,
    ) -> ResponsiveGridLayout:
        return ResponsiveGridLayout(list(content), min_column_width=min_width, **kwargs)

    @staticmethod
    def tabs(tabs: List[Dict[str, str]], **kwargs: Any) -> TabLayout:
        return TabLayout(tabs, **kwargs)

    @staticmethod
    def accordion(sections: List[Dict[str, str]], **kwargs: Any) -> AccordionLayout:
        return AccordionLayout(sections, **kwargs)

    @staticmethod
    def modal(modal_id: str, title: str, content: str, **kwargs: Any) -> ModalLayout:
        return ModalLayout(modal_id, title, content, **kwargs)

    @staticmethod
    def card(title: str, content: str, **kwargs: Any) -> CardLayout:
        return CardLayout(title, content, **kwargs)


LayoutFactory = LayoutComposer
Layout = LayoutComposer


class LayoutEngine:
    """Encapsulates layout rendering routines for form renderers."""

    _custom_renderers: Dict[str, LayoutRenderer] = {}

    def __init__(self, renderer: "EnhancedFormRenderer") -> None:
        self._renderer = renderer

    # ------------------------------------------------------------------
    # Registration hooks
    # ------------------------------------------------------------------
    @classmethod
    def register_layout_renderer(cls, name: str, renderer: LayoutRenderer) -> None:
        """Register a custom layout renderer callable by name."""

        if not callable(renderer):  # pragma: no cover - defensive
            raise TypeError("renderer must be callable")
        cls._custom_renderers[name] = renderer

    @classmethod
    def reset_layout_renderers(cls) -> None:
        """Clear custom layout renderers (useful in tests)."""

        cls._custom_renderers.clear()

    # ------------------------------------------------------------------
    # Public API used by EnhancedFormRenderer
    # ------------------------------------------------------------------
    def render_tabbed_layout(
        self,
        fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        tabs = self._group_fields_into_tabs(fields)
        if not tabs:
            return []

        tab_payload: List[Dict[str, str]] = []
        for tab_name, tab_fields in tabs:
            field_html_parts: List[str] = []
            for field_name, field_schema in tab_fields:
                field_html_parts.append(
                    self._renderer._render_field(  # noqa: SLF001 - intentional internal call
                        field_name,
                        field_schema,
                        data.get(field_name),
                        errors.get(field_name),
                        required_fields,
                        context,
                        "vertical",
                        errors,
                    )
                )

            tab_payload.append(
                {
                    "title": tab_name,
                    "content": "".join(field_html_parts),
                }
            )

        component = TabLayout(
            tabs=tab_payload,
            class_="tabbed-layout",
        )

        return [
            component.render(
                framework=self._renderer.framework,
                renderer=self._renderer,
            )
        ]

    def render_layout_fields_as_tabs(
        self,
        layout_fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        if not layout_fields:
            return []

        tabs_payload: List[Dict[str, str]] = []
        for field_name, field_schema in layout_fields:
            ui_info = field_schema.get("ui", {}) or field_schema
            layout_content = self.render_layout_field_content(
                field_name,
                field_schema,
                data.get(field_name),
                errors.get(field_name),
                ui_info,
                context,
            )
            tabs_payload.append(
                {
                    "title": field_schema.get("title", field_name.replace("_", " ").title()),
                    "content": layout_content,
                }
            )

        component = TabLayout(
            tabs=tabs_payload,
            class_="layout-tabbed-section",
        )

        return [
            component.render(
                framework=self._renderer.framework,
                renderer=self._renderer,
            )
        ]

    def render_layout_field_content(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        section_title = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text", "")
        body_html = self._build_layout_body(field_name, field_schema, value, ui_info, context)
        return self._render_layout_card(section_title, body_html, help_text)

    def render_layout_field_content_fallback(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        form_mapping = {
            "vertical_tab": "PersonalInfoForm",
            "horizontal_tab": "ContactInfoForm",
            "tabbed_tab": "PreferencesForm",
            "list_tab": "TaskListForm",
        }

        form_name = form_mapping.get(field_name)
        if form_name:
            try:
                if form_name == "PersonalInfoForm":
                    from examples.shared_models import (
                        PersonalInfoForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "ContactInfoForm":
                    from examples.shared_models import (
                        ContactInfoForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "PreferencesForm":
                    from examples.shared_models import (
                        PreferencesForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "TaskListForm":
                    from examples.shared_models import (
                        TaskListForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                else:  # pragma: no cover - exhaustive safety
                    raise ImportError(f"Unknown form: {form_name}")

                nested_data = get_nested_form_data(field_name, context.form_data)
                nested_renderer = self._renderer.__class__(framework=self._renderer.framework)
                return nested_renderer.render_form_fields_only(
                    FormClass,
                    data=nested_data,
                    errors={},
                    layout="vertical",
                )
            except Exception as exc:  # pragma: no cover - fallback messaging
                return f"""
                <div class="layout-field-placeholder alert alert-info">
                    <p>Layout demonstration: {form_name}</p>
                    <small class="text-muted">{ui_info.get('help_text', '')}</small>
                    <small class="text-danger d-block">Could not render: {str(exc)}</small>
                </div>
                """

        return f"""
            <div class="layout-field-unknown alert alert-secondary">
                <p>Unknown layout field type</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

    def render_side_by_side_layout(
        self,
        fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        parts: List[str] = []
        field_pairs = []
        for i in range(0, len(fields), 2):
            field_pairs.append((fields[i], fields[i + 1] if i + 1 < len(fields) else None))

        for left_field, right_field in field_pairs:
            columns: List[str] = []
            if left_field:
                field_name, field_schema = left_field
                columns.append(
                    self._renderer._render_field(  # noqa: SLF001
                        field_name,
                        field_schema,
                        data.get(field_name),
                        errors.get(field_name),
                        required_fields,
                        context,
                        "vertical",
                        errors,
                    )
                )

            if right_field:
                field_name, field_schema = right_field
                columns.append(
                    self._renderer._render_field(  # noqa: SLF001
                        field_name,
                        field_schema,
                        data.get(field_name),
                        errors.get(field_name),
                        required_fields,
                        context,
                        "vertical",
                        errors,
                    )
                )

            layout = HorizontalLayout(
                content=[f'<div class="side-by-side-column">{col}</div>' for col in columns],
                class_="side-by-side-row",
                gap="1.5rem",
                align_items="flex-start",
            )

            parts.append(
                layout.render(
                    data=data,
                    errors=errors,
                    renderer=self._renderer,
                    framework=self._renderer.framework,
                )
            )

        return parts

    def render_layout_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        section_title = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text", "")
        body_html = self._build_layout_body(field_name, field_schema, value, ui_info, context)
        return self._render_layout_card(section_title, body_html, help_text)

    def _build_layout_body(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        try:
            handler_name = ui_info.get("layout_handler") or ui_info.get("layout_renderer")
            if handler_name:
                handler = self._custom_renderers.get(str(handler_name))
                if handler:
                    return handler(field_name, field_schema, value, ui_info, context, self)

            if isinstance(value, BaseLayout):
                nested_data = get_nested_form_data(field_name, context.form_data)
                return value.render(
                    data=nested_data,
                    errors=None,
                    renderer=self._renderer,
                    framework=self._renderer.framework,
                )

            return self.render_layout_field_fallback(field_name, field_schema, ui_info, context)
        except Exception as exc:  # pragma: no cover - defensive message
            return self._layout_error_message(field_name, field_schema, ui_info, exc)

    def render_layout_field_fallback(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        form_mapping = {
            "vertical_tab": "PersonalInfoForm",
            "horizontal_tab": "ContactInfoForm",
            "tabbed_tab": "PreferencesForm",
            "list_tab": "TaskListForm",
        }

        form_name = form_mapping.get(field_name)
        if form_name:
            try:
                if form_name == "PersonalInfoForm":
                    from examples.shared_models import (
                        PersonalInfoForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "ContactInfoForm":
                    from examples.shared_models import (
                        ContactInfoForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "PreferencesForm":
                    from examples.shared_models import (
                        PreferencesForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                elif form_name == "TaskListForm":
                    from examples.shared_models import (
                        TaskListForm as FormClass,  # pylint: disable=import-outside-toplevel
                    )
                else:
                    raise ImportError(f"Unknown form: {form_name}")

                nested_data = get_nested_form_data(field_name, context.form_data)
                form_html = self._renderer.render_form_fields_only(
                    FormClass,
                    data=nested_data,
                    errors={},
                    layout="vertical",
                )
                return form_html
            except Exception as exc:  # pragma: no cover
                return f"""
                <div class="layout-field-placeholder alert alert-info">
                    <p>Layout demonstration: {escape(form_name)}</p>
                    <small class="text-muted">{escape(ui_info.get('help_text', ''))}</small>
                    <small class="text-danger d-block">Could not render: {escape(str(exc))}</small>
                </div>
                """

        return f"""
            <div class="layout-field-unknown alert alert-secondary">
                <p>Unknown layout field type</p>
                <small class="text-muted">{escape(ui_info.get('help_text', ''))}</small>
            </div>
            """

    def _render_layout_card(self, title: str, body_html: str, help_text: str) -> str:
        theme = getattr(self._renderer, "theme", None)
        if theme:
            themed_section = theme.render_layout_section(title, body_html, help_text)
            if themed_section:
                return themed_section

        form_style = getattr(theme, "form_style", None) if theme else None
        templates = getattr(form_style, "templates", None)

        layout_template = getattr(templates, "layout_section", None)
        if layout_template is None:
            layout_template = _DEFAULT_FORM_STYLE.templates.layout_section

        help_template = getattr(templates, "layout_help", None)
        if help_template is None:
            help_template = _DEFAULT_FORM_STYLE.templates.layout_help

        help_html = ""
        if help_text:
            help_html = help_template.render(help_text=escape(help_text))

        return layout_template.render(
            title=escape(title),
            help_html=help_html,
            body_html=body_html,
        )

    def _layout_error_message(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        ui_info: Dict[str, Any],
        exc: Exception,
    ) -> str:
        title = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text", "")
        return f"""
        <div class="layout-field-error alert alert-warning">
            <p>Error rendering layout field "{escape(title)}": {escape(str(exc))}</p>
            {f'<small class="text-muted">{escape(help_text)}</small>' if help_text else ''}
        </div>
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _group_fields_into_tabs(
        self, fields: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, List[Tuple[str, Dict[str, Any]]]]]:
        personal_fields: List[Tuple[str, Dict[str, Any]]] = []
        contact_fields: List[Tuple[str, Dict[str, Any]]] = []
        other_fields: List[Tuple[str, Dict[str, Any]]] = []

        for field_name, field_schema in fields:
            field_lower = field_name.lower()
            if any(keyword in field_lower for keyword in ["name", "username", "password", "bio", "role"]):
                personal_fields.append((field_name, field_schema))
            elif any(keyword in field_lower for keyword in ["email", "phone", "address", "subject", "message"]):
                contact_fields.append((field_name, field_schema))
            else:
                other_fields.append((field_name, field_schema))

        tabs: List[Tuple[str, List[Tuple[str, Dict[str, Any]]]]] = []
        if personal_fields:
            tabs.append(("Personal Info", personal_fields))
        if contact_fields:
            tabs.append(("Contact Details", contact_fields))
        if other_fields:
            tabs.append(("Additional", other_fields))

        if not tabs:
            tabs.append(("Form Fields", fields))
        return tabs


def get_nested_form_data(field_name: str, main_data: Dict[str, Any]) -> Dict[str, Any]:
    """Utility used across renderers to extract nested layout data."""
    if field_name in main_data and isinstance(main_data[field_name], dict):
        return main_data[field_name]

    field_data_mapping = {
        "vertical_tab": ["first_name", "last_name", "email", "birth_date"],
        "horizontal_tab": ["phone", "address", "city", "postal_code"],
        "tabbed_tab": ["notification_email", "notification_sms", "theme", "language"],
        "list_tab": ["project_name", "tasks"],
    }

    nested_data: Dict[str, Any] = {}
    for key in field_data_mapping.get(field_name, []):
        if key in main_data:
            nested_data[key] = main_data[key]

    return nested_data
