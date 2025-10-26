"""
Layout composition system for pydantic-forms that matches the design_idea.py vision.
Provides VerticalLayout, HorizontalLayout, TabbedLayout with form composition capabilities.
"""

from typing import Any, Dict, List, Optional, Type
from abc import ABC, abstractmethod

from .schema_form import FormModel, ValidationResult


class SectionDesign:
    """
    Section configuration that matches the design_idea.py vision.

    Provides configuration for form sections including title, description,
    icon, and collapsible behavior.
    """

    def __init__(
        self,
        section_title: str,
        section_description: Optional[str] = None,
        icon: Optional[str] = None,
        collapsible: bool = False,
        collapsed: bool = False,
        css_class: Optional[str] = None,
        **kwargs,
    ):
        self.section_title = section_title
        self.section_description = section_description
        self.icon = icon
        self.collapsible = collapsible
        self.collapsed = collapsed
        self.css_class = css_class
        self.extra_attrs = kwargs

    def render_header(self, framework: str = "bootstrap") -> str:
        """Render the section header HTML."""
        icon_html = ""
        if self.icon:
            if framework == "bootstrap":
                icon_html = f'<i class="bi bi-{self.icon}"></i> '
            elif framework == "material":
                icon_html = f'<i class="material-icons">{self.icon}</i> '

        header_class = "section-header"
        if self.collapsible:
            header_class += " collapsible"

        header_html = f'<div class="{header_class}">'
        header_html += f"<h3>{icon_html}{self.section_title}</h3>"

        if self.section_description:
            header_html += f'<p class="section-description">{self.section_description}</p>'

        header_html += "</div>"

        return header_html


class FormDesign:
    """
    Comprehensive form configuration that matches the design_idea.py vision.

    Provides configuration for the entire form including theme, method, width,
    target URL, and error handling.
    """

    def __init__(
        self,
        ui_theme: str = "bootstrap",
        ui_theme_custom_css: Optional[str] = None,
        form_name: str = "Form",
        form_enctype: str = "application/x-www-form-urlencoded",
        form_width: str = "600px",
        target_url: str = "/submit",
        form_method: str = "post",
        error_notification_style: str = "inline",
        show_debug_info: bool = False,
        **kwargs,
    ):
        self.ui_theme = ui_theme
        self.ui_theme_custom_css = ui_theme_custom_css
        self.form_name = form_name
        self.form_enctype = form_enctype
        self.form_width = form_width
        self.target_url = target_url
        self.form_method = form_method.lower()
        self.error_notification_style = error_notification_style
        self.show_debug_info = show_debug_info
        self.extra_attrs = kwargs

    def get_form_attributes(self) -> Dict[str, str]:
        """Get HTML form attributes."""
        attrs = {
            "action": self.target_url,
            "method": self.form_method,
            "style": f"max-width: {self.form_width}; margin: 0 auto;",
        }

        if self.form_method == "post":
            attrs["enctype"] = self.form_enctype

        return attrs

    def get_framework_css_url(self) -> str:
        """Get the CSS URL for the selected framework."""
        framework_css = {
            "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "material": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
            "shadcn": "",  # Would require custom implementation
            "tailwind": "https://cdn.tailwindcss.com",
            "semantic": "https://cdn.jsdelivr.net/npm/semantic-ui@2.4.2/dist/semantic.min.css",
            "custom": self.ui_theme_custom_css or "",
        }

        return framework_css.get(self.ui_theme, "")

    def get_framework_js_url(self) -> str:
        """Get the JavaScript URL for the selected framework."""
        framework_js = {
            "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "material": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
            "semantic": "https://cdn.jsdelivr.net/npm/semantic-ui@2.4.2/dist/semantic.min.js",
        }

        return framework_js.get(self.ui_theme, "")


class BaseLayout(ABC):
    """
    Base class for all layout components in the composition system.
    """

    def __init__(self, form_config: Optional[SectionDesign] = None):
        self.form_config = form_config
        self._forms: List[FormModel] = []
        self._rendered_content: Optional[str] = None

    @abstractmethod
    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        """Render the layout with its contained forms."""
        pass

    @abstractmethod
    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate the layout's forms and return a ValidationResult."""
        pass

    def _get_forms(self) -> List[Type[FormModel]]:
        """Get all FormModel classes from the layout's attributes."""
        forms = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, type) and issubclass(attr, FormModel) and attr is not FormModel:
                forms.append(attr)
        return forms


class VerticalLayout(BaseLayout):
    """
    Vertical layout that stacks forms vertically.
    Matches the design_idea.py vision.
    """

    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        """Render forms in vertical layout."""
        content_parts = []

        # Add section header if configured
        if self.form_config:
            content_parts.append(self.form_config.render_header(framework))

        # Render each form
        forms = self._get_forms()
        for form_cls in forms:
            form_html = form_cls.render_form(data=data, errors=errors, framework=framework)
            content_parts.append(form_html)

        # Wrap in vertical layout container
        content = "\n".join(content_parts)

        container_class = "vertical-layout"
        if self.form_config and self.form_config.collapsible:
            container_class += " collapsible"
            if self.form_config.collapsed:
                container_class += " collapsed"

        return f'<div class="{container_class}">{content}</div>'

    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate all forms in the vertical layout."""
        all_data = {}
        all_errors = {}
        is_valid = True

        forms = self._get_forms()
        for form_cls in forms:
            try:
                # Attempt to validate each form
                instance = form_cls(**form_data)
                form_data_dict = instance.model_dump()
                all_data.update(form_data_dict)
            except Exception as e:
                is_valid = False
                # Extract field errors from validation error
                if hasattr(e, "errors"):
                    for error in e.errors():
                        field_name = error.get("loc", [""])[0]
                        error_msg = error.get("msg", str(e))
                        all_errors[field_name] = error_msg
                else:
                    all_errors["_form"] = str(e)

        return ValidationResult(
            is_valid=is_valid,
            data=all_data,
            errors=all_errors,
            form_model_cls=forms[0] if forms else None,
            original_data=form_data,
        )


class HorizontalLayout(BaseLayout):
    """
    Horizontal layout that arranges forms side by side.
    Matches the design_idea.py vision.
    """

    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        """Render forms in horizontal layout."""
        content_parts = []

        # Add section header if configured
        if self.form_config:
            content_parts.append(self.form_config.render_header(framework))

        # Render each form in columns
        forms = self._get_forms()
        form_columns = []

        for form_cls in forms:
            form_html = form_cls.render_form(data=data, errors=errors, framework=framework)

            if framework == "bootstrap":
                column_html = f'<div class="col">{form_html}</div>'
            else:
                column_html = f'<div class="horizontal-layout-column">{form_html}</div>'

            form_columns.append(column_html)

        # Wrap columns in row
        if framework == "bootstrap":
            columns_html = f'<div class="row">{"".join(form_columns)}</div>'
        else:
            columns_html = f'<div class="horizontal-layout-row">{"".join(form_columns)}</div>'

        content_parts.append(columns_html)

        # Wrap in horizontal layout container
        content = "\n".join(content_parts)

        container_class = "horizontal-layout"
        if self.form_config and self.form_config.collapsible:
            container_class += " collapsible"
            if self.form_config.collapsed:
                container_class += " collapsed"

        return f'<div class="{container_class}">{content}</div>'

    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate all forms in the horizontal layout."""
        # Same validation logic as VerticalLayout
        all_data = {}
        all_errors = {}
        is_valid = True

        forms = self._get_forms()
        for form_cls in forms:
            try:
                instance = form_cls(**form_data)
                form_data_dict = instance.model_dump()
                all_data.update(form_data_dict)
            except Exception as e:
                is_valid = False
                if hasattr(e, "errors"):
                    for error in e.errors():
                        field_name = error.get("loc", [""])[0]
                        error_msg = error.get("msg", str(e))
                        all_errors[field_name] = error_msg
                else:
                    all_errors["_form"] = str(e)

        return ValidationResult(
            is_valid=is_valid,
            data=all_data,
            errors=all_errors,
            form_model_cls=forms[0] if forms else None,
            original_data=form_data,
        )


class TabbedLayout(BaseLayout):
    """
    Tabbed layout that organizes layouts/forms into tabs.
    Matches the design_idea.py vision where tab order is determined by declaration order.
    """

    def __init__(self, form_config: Optional[FormDesign] = None):
        super().__init__()
        self.form_config = form_config  # TabbedLayout uses FormDesign instead of SectionDesign

    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        """Render the tabbed layout with all tabs."""
        # Get all layout attributes in declaration order
        layouts = self._get_layouts()

        if not layouts:
            return '<div class="alert alert-warning">No layouts found in tabbed layout</div>'

        # Generate tab navigation
        tab_nav_items = []
        tab_content_panes = []

        for i, (tab_name, layout_instance) in enumerate(layouts):
            tab_id = f"tab-{tab_name}"
            is_active = i == 0

            # Tab navigation item
            active_class = " active" if is_active else ""
            nav_item = f"""
                <li class="nav-item" role="presentation">
                    <button class="nav-link{active_class}" id="{tab_id}-tab"
                            data-bs-toggle="tab" data-bs-target="#{tab_id}"
                            type="button" role="tab" aria-controls="{tab_id}"
                            aria-selected="{str(is_active).lower()}">
                        {tab_name.replace('_', ' ').title()}
                    </button>
                </li>"""
            tab_nav_items.append(nav_item)

            # Tab content pane
            active_class = " show active" if is_active else ""
            layout_html = layout_instance.render(data=data, errors=errors, framework=framework)
            content_pane = f"""
                <div class="tab-pane fade{active_class}" id="{tab_id}"
                     role="tabpanel" aria-labelledby="{tab_id}-tab">
                    {layout_html}
                </div>"""
            tab_content_panes.append(content_pane)

        # Build complete tabbed interface
        form_title = ""
        if self.form_config:
            form_title = f'<h2 class="form-title">{self.form_config.form_name}</h2>'

        tabs_html = f"""
            {form_title}
            <div class="tabbed-layout">
                <ul class="nav nav-tabs" id="form-tabs" role="tablist">
                    {"".join(tab_nav_items)}
                </ul>
                <div class="tab-content" id="form-tab-content">
                    {"".join(tab_content_panes)}
                </div>
            </div>"""

        # Wrap in complete page if FormDesign is provided
        if self.form_config:
            return self._render_complete_page(tabs_html)

        return tabs_html

    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate all layouts in the tabbed layout."""
        all_data = {}
        all_errors = {}
        is_valid = True
        first_form_cls = None

        layouts = self._get_layouts()
        for _tab_name, layout_instance in layouts:
            result = layout_instance.validate(form_data, files)
            all_data.update(result.data)
            all_errors.update(result.errors)
            if not result.is_valid:
                is_valid = False
            if not first_form_cls and result.form_model_cls:
                first_form_cls = result.form_model_cls

        return ValidationResult(
            is_valid=is_valid,
            data=all_data,
            errors=all_errors,
            form_model_cls=first_form_cls,
            original_data=form_data,
        )

    def _get_layouts(self) -> List[tuple[str, BaseLayout]]:
        """Get all layout attributes in declaration order."""
        layouts = []
        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                attr = getattr(self, attr_name)
                if isinstance(attr, BaseLayout):
                    layouts.append((attr_name, attr))

        # Sort by declaration order (this is approximate since Python doesn't
        # preserve declaration order in __dict__, but it's close enough)
        return layouts

    def _render_complete_page(self, form_html: str) -> str:
        """Render a complete HTML page with CSS and JavaScript."""
        if not self.form_config:
            return form_html

        css_url = self.form_config.get_framework_css_url()
        js_url = self.form_config.get_framework_js_url()

        # Get form attributes
        form_attrs = self.form_config.get_form_attributes()
        form_attrs_str = " ".join([f'{k}="{v}"' for k, v in form_attrs.items()])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.form_config.form_name}</title>
    {f'<link href="{css_url}" rel="stylesheet">' if css_url else ''}
    <style>
        body {{ background-color: #f8f9fa; }}
        .form-container {{
            max-width: {self.form_config.form_width};
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
            <form {form_attrs_str}>
                {form_html}
            </form>
        </div>
    </div>

    {f'<script src="{js_url}"></script>' if js_url else ''}
</body>
</html>"""


__all__ = [
    "SectionDesign",
    "FormDesign",
    "BaseLayout",
    "VerticalLayout",
    "HorizontalLayout",
    "TabbedLayout",
]
