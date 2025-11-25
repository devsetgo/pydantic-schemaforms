"""Layout-specific helpers extracted from the enhanced renderer."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .context import RenderContext
from ..layout_base import BaseLayout
from ..layouts import CardLayout, HorizontalLayout as FlexHorizontalLayout
from ..layouts import TabLayout as ComponentTabLayout

if TYPE_CHECKING:  # pragma: no cover
    from ..enhanced_renderer import EnhancedFormRenderer


class LayoutEngine:
    """Encapsulates layout rendering routines for form renderers."""

    def __init__(self, renderer: "EnhancedFormRenderer") -> None:
        self._renderer = renderer

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

        component = ComponentTabLayout(
            tabs=tab_payload,
            class_="tabbed-layout",
        )

        return [component.render(framework=self._renderer.framework)]

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

        component = ComponentTabLayout(
            tabs=tabs_payload,
            class_="layout-tabbed-section",
        )

        return [component.render(framework=self._renderer.framework)]

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
                    from examples.shared_models import PersonalInfoForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "ContactInfoForm":
                    from examples.shared_models import ContactInfoForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "PreferencesForm":
                    from examples.shared_models import PreferencesForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "TaskListForm":
                    from examples.shared_models import TaskListForm as FormClass  # pylint: disable=import-outside-toplevel
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

            layout = FlexHorizontalLayout(
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
                    from examples.shared_models import PersonalInfoForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "ContactInfoForm":
                    from examples.shared_models import ContactInfoForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "PreferencesForm":
                    from examples.shared_models import PreferencesForm as FormClass  # pylint: disable=import-outside-toplevel
                elif form_name == "TaskListForm":
                    from examples.shared_models import TaskListForm as FormClass  # pylint: disable=import-outside-toplevel
                else:
                    raise ImportError(f"Unknown form: {form_name}")

                nested_data = get_nested_form_data(field_name, context.form_data)
                form_html = self._renderer.render_form_from_model(
                    FormClass,
                    data=nested_data,
                    errors={},
                    layout="vertical",
                    include_submit_button=False,
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
        content_parts: List[str] = []
        if help_text:
            content_parts.append(
                f'<p class="text-muted mb-2">{escape(help_text)}</p>'
            )

        content_parts.append(f'<div class="layout-field-content">{body_html}</div>')

        card = CardLayout(
            title=title,
            content="".join(content_parts),
            class_="layout-field-section mb-4",
        )

        return card.render(
            data={},
            errors={},
            renderer=self._renderer,
            framework=self._renderer.framework,
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
