"""Layout-specific helpers extracted from the enhanced renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .context import RenderContext
from ..layout_base import BaseLayout

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
        parts: List[str] = []

        parts.append('<ul class="nav nav-tabs" id="formTabs" role="tablist">')
        for i, (tab_name, _) in enumerate(tabs):
            active_class = " active" if i == 0 else ""
            tab_id = f"tab-{tab_name.lower().replace(' ', '-')}"
            parts.append(
                f"""
            <li class="nav-item" role="presentation">
                <button class="nav-link{active_class}" id="{tab_id}-tab" data-bs-toggle="tab"
                        data-bs-target="#{tab_id}" type="button" role="tab"
                        aria-controls="{tab_id}" aria-selected="{"true" if i == 0 else "false"}">
                    {tab_name}
                </button>
            </li>
            """
            )
        parts.append("</ul>")

        parts.append('<div class="tab-content" id="formTabContent">')
        for i, (tab_name, tab_fields) in enumerate(tabs):
            active_class = " show active" if i == 0 else ""
            tab_id = f"tab-{tab_name.lower().replace(' ', '-')}"
            parts.append(
                f'<div class="tab-pane fade{active_class}" id="{tab_id}" role="tabpanel" aria-labelledby="{tab_id}-tab">'
            )

            for field_name, field_schema in tab_fields:
                field_html = self._renderer._render_field(  # noqa: SLF001 - intentional internal call
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    context,
                    "vertical",
                    errors,
                )
                parts.append(field_html)

            parts.append("</div>")

        parts.append("</div>")
        return parts

    def render_layout_fields_as_tabs(
        self,
        layout_fields: List[Tuple[str, Dict[str, Any]]],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        parts: List[str] = []

        parts.append('<ul class="nav nav-tabs" id="layoutTabs" role="tablist">')
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " active" if i == 0 else ""
            tab_id = f"layout-tab-{field_name}"
            tab_title = field_schema.get("title", field_name.replace("_", " ").title())
            parts.append(
                f"""
            <li class="nav-item" role="presentation">
                <button class="nav-link{active_class}" id="{tab_id}-tab" data-bs-toggle="tab"
                        data-bs-target="#{tab_id}" type="button" role="tab"
                        aria-controls="{tab_id}" aria-selected="{"true" if i == 0 else "false"}">
                    {tab_title}
                </button>
            </li>
            """
            )
        parts.append("</ul>")

        parts.append('<div class="tab-content" id="layoutTabContent">')
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " show active" if i == 0 else ""
            tab_id = f"layout-tab-{field_name}"
            parts.append(
                f'<div class="tab-pane fade{active_class}" id="{tab_id}" role="tabpanel" aria-labelledby="{tab_id}-tab">'
            )

            ui_info = field_schema.get("ui", {}) or field_schema
            layout_content = self.render_layout_field_content(
                field_name,
                field_schema,
                data.get(field_name),
                errors.get(field_name),
                ui_info,
                context,
            )
            parts.append(layout_content)
            parts.append("</div>")

        parts.append("</div>")
        return parts

    def render_layout_field_content(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
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

            return self.render_layout_field_content_fallback(
                field_name, field_schema, ui_info, context
            )

        except Exception as exc:  # pragma: no cover - defensive HTML message
            return f"""
            <div class="layout-field-error alert alert-warning">
                <p>Error rendering layout field: {str(exc)}</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

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
            parts.append('<div class="row">')
            parts.append('<div class="col-md-6">')
            if left_field:
                field_name, field_schema = left_field
                parts.append(
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
            parts.append("</div>")

            parts.append('<div class="col-md-6">')
            if right_field:
                field_name, field_schema = right_field
                parts.append(
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
            parts.append("</div>")
            parts.append("</div>")

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
        try:
            if isinstance(value, BaseLayout):
                nested_data = get_nested_form_data(field_name, context.form_data)
                form_html = value.render(
                    data=nested_data,
                    errors=None,
                    renderer=self._renderer,
                    framework=self._renderer.framework,
                )

                section_title = field_schema.get("title", field_name.replace("_", " ").title())
                help_text = ui_info.get("help_text", "")
                return f"""
                <div class="layout-field-section mb-4">
                    <h5 class="layout-field-title">{section_title}</h5>
                    {f'<p class="text-muted">{help_text}</p>' if help_text else ''}
                    <div class="layout-field-content p-3 border rounded">
                        {form_html}
                    </div>
                </div>
                """

            return self.render_layout_field_fallback(field_name, field_schema, ui_info, context)

        except Exception as exc:  # pragma: no cover
            return f"""
            <div class="layout-field-error alert alert-warning">
                <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                <p>Error rendering layout field: {str(exc)}</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

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

                section_title = field_schema.get("title", field_name.replace("_", " ").title())
                help_text = ui_info.get("help_text", "")
                return f"""
                <div class="layout-field-section mb-4">
                    <h5 class="layout-field-title">{section_title}</h5>
                    {f'<p class="text-muted">{help_text}</p>' if help_text else ''}
                    <div class="layout-field-content p-3 border rounded">
                        {form_html}
                    </div>
                </div>
                """
            except Exception as exc:  # pragma: no cover
                return f"""
                <div class="layout-field-placeholder alert alert-info">
                    <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                    <p>Layout demonstration: {form_name}</p>
                    <small class="text-muted">{ui_info.get('help_text', '')}</small>
                    <small class="text-danger d-block">Could not render: {str(exc)}</small>
                </div>
                """

        return f"""
            <div class="layout-field-unknown alert alert-secondary">
                <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                <p>Unknown layout field type</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
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
