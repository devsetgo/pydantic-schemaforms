"""
Legacy form layout composition helpers.

This module is deprecated in favor of composing ``BaseLayout`` instances directly via
``pydantic_schemaforms.rendering.layout_engine.LayoutComposer`` and rendering them through the
shared ``LayoutEngine``.
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from .layout_base import BaseLayout as SharedBaseLayout
from .assets.runtime import framework_css_tag, framework_js_tag
from .rendering.layout_engine import HorizontalLayout as FlexHorizontalLayout
from .rendering.layout_engine import TabLayout as ComponentTabLayout
from .rendering.layout_engine import VerticalLayout as FlexVerticalLayout
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
        asset_mode: str = "vendored",
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
        self.asset_mode = asset_mode
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
        if self.ui_theme == "custom":
            return self.ui_theme_custom_css or ""

        if self.asset_mode != "cdn":
            return ""

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
        if self.asset_mode != "cdn":
            return ""

        framework_js = {
            "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "material": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
            "semantic": "https://cdn.jsdelivr.net/npm/semantic-ui@2.4.2/dist/semantic.min.js",
        }

        return framework_js.get(self.ui_theme, "")


_DEPRECATION_MESSAGE = (
    "pydantic_schemaforms.form_layouts will be removed in a future release. Compose layouts "
    "using LayoutComposer + LayoutEngine instead."
)


def _warn_form_layouts_deprecated() -> None:
    warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=3)


class FormLayoutBase(SharedBaseLayout, ABC):
    """Base class for layout components that orchestrate FormModel instances."""

    def __init__(self, form_config: Optional[SectionDesign] = None):
        super().__init__(content="")
        _warn_form_layouts_deprecated()
        self.form_config = form_config
        self._forms: List[FormModel] = []
        self._rendered_content: Optional[str] = None

    # ------------------------------------------------------------------
    # Shared helpers so concrete layouts can lean on BaseLayout subclasses
    # ------------------------------------------------------------------
    def _section_header(self, framework: str) -> str:
        if self.form_config and hasattr(self.form_config, "render_header"):
            return self.form_config.render_header(framework)
        return ""

    def _section_class(self, base_class: str) -> str:
        if not self.form_config:
            return base_class

        classes = [base_class]
        collapsible = getattr(self.form_config, "collapsible", False)
        collapsed = getattr(self.form_config, "collapsed", False)
        css_class = getattr(self.form_config, "css_class", "")

        if collapsible:
            classes.append("collapsible")
            if collapsed:
                classes.append("collapsed")

        if css_class:
            classes.append(css_class)

        return " ".join(classes)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Allow layout classes to be used as field types within FormModel schemas."""

        return core_schema.dict_schema()

    @abstractmethod
    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        raise NotImplementedError

    def _render_form_instances(
        self,
        *,
        data: Optional[Dict[str, Any]],
        errors: Optional[Dict[str, Any]],
        framework: str,
    ) -> List[str]:
        """Render nested FormModel instances without wrapping them in nested <form> tags."""

        rendered: List[str] = []
        renderer = self._get_renderer_for_framework(framework)

        for form_cls in self._get_forms():
            if renderer:
                rendered.append(
                    renderer.render_form_fields_only(
                        form_cls,
                        data=data,
                        errors=errors,
                    )
                )
            else:
                # Fallback for unexpected frameworks without dedicated renderer helpers
                rendered.append(
                    form_cls.render_form(
                        data=data,
                        errors=errors,
                        framework=framework,
                        include_submit_button=False,
                    )
                )

        return rendered

    def _get_renderer_for_framework(self, framework: str):
        """Return a renderer capable of rendering fields-only for nested layouts."""

        if framework == "material":
            from .simple_material_renderer import SimpleMaterialRenderer

            return SimpleMaterialRenderer()

        from .enhanced_renderer import EnhancedFormRenderer

        return EnhancedFormRenderer(framework=framework)

    def _get_forms(self) -> List[Type[FormModel]]:
        forms: List[Type[FormModel]] = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, type) and issubclass(attr, FormModel) and attr is not FormModel:
                forms.append(attr)
        return forms


# Backwards compatibility: historical name exported from this module
BaseLayout = FormLayoutBase


class VerticalLayout(FormLayoutBase):
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
        content_parts: List[str] = []
        header = self._section_header(framework)
        if header:
            content_parts.append(header)

        content_parts.extend(
            self._render_form_instances(data=data, errors=errors, framework=framework)
        )

        layout = FlexVerticalLayout(
            content=content_parts,
            class_=self._section_class("vertical-layout"),
        )

        return layout.render(
            data=data or {},
            errors=errors or {},
            framework=framework,
        )

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


class HorizontalLayout(FormLayoutBase):
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
        header_html = self._section_header(framework)

        column_content = [
            f'<div class="horizontal-layout-column">{html}</div>'
            for html in self._render_form_instances(data=data, errors=errors, framework=framework)
        ]

        layout = FlexHorizontalLayout(
            content=column_content,
            class_=self._section_class("horizontal-layout"),
            justify_content="space-between",
        )

        layout_html = layout.render(
            data=data or {},
            errors=errors or {},
            framework=framework,
        )

        if header_html:
            return f"{header_html}{layout_html}"
        return layout_html

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


class TabbedLayout(FormLayoutBase):
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
        layouts = self._get_layouts()
        if not layouts:
            return '<div class="alert alert-warning">No layouts found in tabbed layout</div>'

        tabs_payload: List[Dict[str, str]] = []
        for tab_name, layout_instance in layouts:
            layout_html = layout_instance.render(data=data, errors=errors, framework=framework)
            tabs_payload.append(
                {
                    "title": tab_name.replace("_", " ").title(),
                    "content": layout_html,
                }
            )

        tab_component = ComponentTabLayout(
            tabs=tabs_payload,
            class_="tabbed-layout",
        )

        tabs_html = tab_component.render(framework=framework)

        if self.form_config:
            form_title = f'<h2 class="form-title">{self.form_config.form_name}</h2>'
            tabs_html = f"{form_title}{tabs_html}"
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

        asset_mode = getattr(self.form_config, "asset_mode", "vendored")
        css_tag = framework_css_tag(framework=self.form_config.ui_theme, asset_mode=asset_mode)
        js_tag = framework_js_tag(framework=self.form_config.ui_theme, asset_mode=asset_mode)

        # Get form attributes
        form_attrs = self.form_config.get_form_attributes()
        form_attrs_str = " ".join([f'{k}="{v}"' for k, v in form_attrs.items()])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.form_config.form_name}</title>
    {css_tag}
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

    {js_tag}
</body>
</html>"""


class ListLayout(FormLayoutBase):
    """
    Layout that renders a list of repeatable form sections with add/remove functionality.
    Each item in the list is a complete form instance that can be dynamically added or removed.
    """

    def __init__(
        self,
        form_model: Type[FormModel],
        min_items: int = 0,
        max_items: Optional[int] = None,
        add_button_text: str = "Add Item",
        remove_button_text: str = "Remove",
        section_design: Optional[SectionDesign] = None,
        collapsible_items: bool = False,
        items_expanded_by_default: bool = True,
        **kwargs,
    ):
        super().__init__(section_design)
        self.form_model = form_model
        self.min_items = min_items
        self.max_items = max_items
        self.add_button_text = add_button_text
        self.remove_button_text = remove_button_text
        self.collapsible_items = collapsible_items
        self.items_expanded_by_default = items_expanded_by_default
        self.section_design = section_design or SectionDesign(
            section_title=f"{form_model.__name__} List",
            section_description=f"List of {form_model.__name__} items",
        )
        self.form_config = self.section_design

    def get_form_models(self) -> List[Type[FormModel]]:
        """Get all FormModel classes from the layout."""
        return [self.form_model]

    def validate(
        self, form_data: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate all items in the list.

        Args:
            form_data: Dictionary containing form data with item prefixes
            files: Optional file data

        Returns:
            ValidationResult with aggregated errors from all list items
        """
        from .validation import ValidationResult

        all_errors = {}
        valid_items = []

        # Group form data by item index
        item_data = {}
        for key, value in form_data.items():
            if key.startswith("item_"):
                # Extract item index and field name
                parts = key.split("_", 2)
                if len(parts) >= 3:
                    item_index = int(parts[1])
                    field_name = parts[2]

                    if item_index not in item_data:
                        item_data[item_index] = {}
                    item_data[item_index][field_name] = value

        # Validate each item
        for item_index, data in item_data.items():
            try:
                # Create and validate form instance
                form_instance = self.form_model(**data)
                valid_items.append(form_instance)
            except Exception as e:
                # Add validation errors for this item
                item_key = f"item_{item_index}"
                all_errors[item_key] = str(e)

        # Check min/max constraints
        item_count = len(valid_items)
        if item_count < self.min_items:
            all_errors["list_constraint"] = f"At least {self.min_items} items required"
        if self.max_items and item_count > self.max_items:
            all_errors["list_constraint"] = f"Maximum {self.max_items} items allowed"

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            data={"valid_items": valid_items, "item_count": item_count},
        )

    def render(
        self,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
    ) -> str:
        """
        Render the list layout with dynamic add/remove functionality.

        Args:
            data: Dictionary containing list data under 'items' key
            errors: Validation errors for display
            framework: UI framework (bootstrap/material)

        Returns:
            HTML string with the complete list layout
        """
        # Extract renderer from the current context - this is a simplified approach
        # In practice, the renderer would be passed differently
        if framework == "material":
            from .simple_material_renderer import MaterialDesign3Renderer

            renderer = MaterialDesign3Renderer()
        else:
            from .enhanced_renderer import EnhancedFormRenderer

            renderer = EnhancedFormRenderer()

        # Extract list items from data
        list_data = []
        if data and "items" in data:
            list_data = data["items"]
        elif data and isinstance(data, list):
            list_data = data

        # Ensure minimum items
        while len(list_data) < self.min_items:
            list_data.append({})

        # Generate unique identifier for this list
        list_id = f"list_{id(self)}"

        # Render header if section design is provided
        header_html = self._section_header(framework)

        # Render existing items
        items_html = ""
        for i, item_data in enumerate(list_data):
            items_html += self._render_list_item(renderer, item_data, i, list_id, framework, errors)

        # Render add button
        add_button_html = self._render_add_button(list_id, framework)

        # Container CSS class
        container_class = self._section_class(f"list-layout {framework}-list-layout")
        if self.section_design and self.section_design.css_class:
            container_class += f" {self.section_design.css_class}"

        # Render JavaScript for dynamic functionality
        js_html = self._render_javascript(list_id, framework)

        layout_content = []
        if header_html:
            layout_content.append(header_html)

        layout_content.append(
            f"""
            <div class="list-items-container" id="{list_id}-container">
                {items_html}
            </div>
            {add_button_html}
            """
        )

        layout = FlexVerticalLayout(
            content=layout_content,
            class_=container_class,
            gap="1rem",
        )

        layout_html = layout.render(
            data=data or {},
            errors=errors or {},
            framework=framework,
        )

        return f"""
        {layout_html}
        {js_html}
        """

    def _render_list_item(
        self,
        renderer,
        item_data: Dict[str, Any],
        index: int,
        list_id: str,
        framework: str,
        errors: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a single list item with form and remove button."""
        # Create form instance with data
        try:
            form_instance = self.form_model(**item_data) if item_data else self.form_model()
        except Exception:
            # For empty forms, create with default values to avoid validation errors
            form_instance = self.form_model.model_construct()

        # Render the form for this item WITHOUT submit button
        form_html = renderer.render_form_from_model(
            form_instance, framework=framework, include_submit_button=False
        )

        # Add name prefixes to make each item unique
        form_html = self._add_name_prefixes(form_html, index)

        # Add error messages if any
        error_html = ""
        if errors and f"item_{index}" in errors:
            error_html = f'<div class="alert alert-danger">{errors[f"item_{index}"]}</div>'

        # Render remove button (only if we can remove items)
        remove_button_html = ""
        if len(item_data) > self.min_items or not item_data:  # Can remove if above minimum or empty
            remove_button_html = self._render_remove_button(index, list_id, framework)

        item_class = f"list-item {framework}-list-item"

        if self.collapsible_items:
            # Render collapsible card
            return self._render_collapsible_item(
                form_html,
                remove_button_html,
                error_html,
                index,
                list_id,
                framework,
                item_class,
                item_data,
            )
        else:
            # Render standard item
            return f"""
            <div class="{item_class}" data-item-index="{index}">
                {error_html}
                <div class="list-item-content">
                    {form_html}
                </div>
                {remove_button_html}
            </div>
            """

    def _render_collapsible_item(
        self,
        form_html: str,
        remove_button_html: str,
        error_html: str,
        index: int,
        list_id: str,
        framework: str,
        item_class: str,
        item_data: Dict[str, Any],
    ) -> str:
        """Render a collapsible card for the list item."""
        # Generate unique IDs for the collapsible item
        collapse_id = f"{list_id}_item_{index}"

        # Determine if the item should be expanded by default
        expanded_class = "show" if self.items_expanded_by_default else ""
        expanded_attr = "true" if self.items_expanded_by_default else "false"

        # Create a summary for the card header (first few non-empty field values)
        summary = self._create_item_summary(item_data, index)

        if framework == "material":
            return f"""
            <div class="{item_class} collapsible-item" data-item-index="{index}">
                {error_html}
                <div class="collapsible-header" onclick="toggleCollapse('{collapse_id}')">
                    <div class="collapsible-title">
                        <i class="material-icons expand-icon">expand_more</i>
                        <span class="item-summary">{summary}</span>
                    </div>
                    <div class="collapsible-actions">
                        {remove_button_html}
                    </div>
                </div>
                <div class="collapsible-content collapse {expanded_class}" id="{collapse_id}">
                    <div class="list-item-content">
                        {form_html}
                    </div>
                </div>
            </div>
            """
        else:  # bootstrap
            return f"""
            <div class="{item_class} collapsible-item" data-item-index="{index}">
                {error_html}
                <div class="collapsible-header" data-bs-toggle="collapse" data-bs-target="#{collapse_id}"
                     aria-expanded="{expanded_attr}" aria-controls="{collapse_id}">
                    <div class="collapsible-title">
                        <i class="bi bi-chevron-down expand-icon"></i>
                        <span class="item-summary">{summary}</span>
                    </div>
                    <div class="collapsible-actions">
                        {remove_button_html}
                    </div>
                </div>
                <div class="collapse {expanded_class}" id="{collapse_id}">
                    <div class="list-item-content">
                        {form_html}
                    </div>
                </div>
            </div>
            """

    def _create_item_summary(self, item_data: Dict[str, Any], index: int) -> str:
        """Create a summary string for the collapsible item header."""
        if not item_data:
            return f"{self.form_model.__name__} #{index + 1}"

        # Get the first few non-empty values to create a summary
        summary_parts = []
        for _key, value in item_data.items():
            if value and len(summary_parts) < 2:  # Show up to 2 field values
                if isinstance(value, str) and len(value) > 30:
                    value = value[:27] + "..."
                summary_parts.append(str(value))

        if summary_parts:
            return f"{self.form_model.__name__}: {' | '.join(summary_parts)}"
        else:
            return f"{self.form_model.__name__} #{index + 1}"

    def _add_name_prefixes(self, form_html: str, index: int) -> str:
        """Add name prefixes to form inputs to make them unique."""
        import re

        # Add index prefix to name attributes
        form_html = re.sub(r'name="([^"]*)"', rf'name="item_{index}_\1"', form_html)

        # Add index prefix to id attributes
        form_html = re.sub(r'id="([^"]*)"', rf'id="item_{index}_\1"', form_html)

        # Update for attributes to match new ids
        form_html = re.sub(r'for="([^"]*)"', rf'for="item_{index}_\1"', form_html)

        return form_html

    def _render_add_button(self, list_id: str, framework: str) -> str:
        """Render the add button for creating new list items."""
        if framework == "material":
            return f"""
            <button type="button" class="mdc-button mdc-button--raised list-add-btn"
                    data-list-id="{list_id}" onclick="addListItem('{list_id}')">
                <span class="mdc-button__label">
                    <i class="material-icons">add</i> {self.add_button_text}
                </span>
            </button>
            """
        else:  # bootstrap
            return f"""
            <button type="button" class="btn btn-primary list-add-btn"
                    data-list-id="{list_id}" onclick="addListItem('{list_id}')">
                <i class="bi bi-plus"></i> {self.add_button_text}
            </button>
            """

    def _render_remove_button(self, index: int, list_id: str, framework: str) -> str:
        """Render the remove button for deleting list items."""
        if framework == "material":
            return f"""
            <button type="button" class="mdc-button mdc-button--outlined list-remove-btn"
                    data-item-index="{index}" data-list-id="{list_id}"
                    onclick="removeListItem('{list_id}', {index})">
                <span class="mdc-button__label">
                    <i class="material-icons">remove</i> {self.remove_button_text}
                </span>
            </button>
            """
        else:  # bootstrap
            return f"""
            <button type="button" class="btn btn-outline-danger btn-sm list-remove-btn"
                    data-item-index="{index}" data-list-id="{list_id}"
                    onclick="removeListItem('{list_id}', {index})">
                <i class="bi bi-trash"></i> {self.remove_button_text}
            </button>
            """

    def _render_javascript(self, list_id: str, framework: str) -> str:
        """Render JavaScript for dynamic add/remove functionality."""

        # Add collapsible toggle function for Material Design
        collapsible_js = ""
        if self.collapsible_items and framework == "material":
            collapsible_js = """
        function toggleCollapse(collapseId) {
            const content = document.getElementById(collapseId);
            const header = content.previousElementSibling;
            const icon = header.querySelector('.expand-icon');

            if (content.classList.contains('show')) {
                content.classList.remove('show');
                icon.textContent = 'expand_more';
            } else {
                content.classList.add('show');
                icon.textContent = 'expand_less';
            }
        }
        """

        return f"""
        <script>
        {collapsible_js}

        function addListItem(listId) {{
            const container = document.getElementById(listId + '-container');
            const items = container.querySelectorAll('.list-item');
            const newIndex = items.length;

            // Check max items limit
            {f'if (newIndex >= {self.max_items}) {{ alert("Maximum {self.max_items} items allowed"); return; }}' if self.max_items else ''}

            // Clone the first item as a template
            const firstItem = container.querySelector('.list-item');
            if (!firstItem) {{
                console.error('No template item found to clone');
                return;
            }}

            const newItem = firstItem.cloneNode(true);
            newItem.setAttribute('data-item-index', newIndex);

            // Update collapsible IDs if using collapsible items
            {self._render_collapsible_update_js(list_id, framework) if self.collapsible_items else ''}

            // Update all form field names and IDs
            const inputs = newItem.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {{
                // Update name attribute
                if (input.name) {{
                    input.name = input.name.replace(/^item_\\d+_/, `item_${{newIndex}}_`);
                }}
                // Update id attribute
                if (input.id) {{
                    input.id = input.id.replace(/^item_\\d+_/, `item_${{newIndex}}_`);
                }}
                // Clear values
                if (input.type === 'checkbox' || input.type === 'radio') {{
                    input.checked = false;
                }} else {{
                    input.value = '';
                }}
            }});

            // Update labels 'for' attributes
            const labels = newItem.querySelectorAll('label');
            labels.forEach(label => {{
                if (label.getAttribute('for')) {{
                    label.setAttribute('for', label.getAttribute('for').replace(/^item_\\d+_/, `item_${{newIndex}}_`));
                }}
            }});

            // Update help text IDs
            const helpTexts = newItem.querySelectorAll('[id$="-help"]');
            helpTexts.forEach(helpText => {{
                if (helpText.id) {{
                    helpText.id = helpText.id.replace(/^item_\\d+_/, `item_${{newIndex}}_`);
                }}
            }});

            // Update remove button
            const removeBtn = newItem.querySelector('.list-remove-btn');
            if (removeBtn) {{
                removeBtn.setAttribute('data-item-index', newIndex);
                removeBtn.setAttribute('onclick', `removeListItem('${{listId}}', ${{newIndex}})`);
            }}

            // Update item summary for collapsible items
            const summary = newItem.querySelector('.item-summary');
            if (summary) {{
                summary.textContent = `{self.form_model.__name__} #${{newIndex + 1}}`;
            }}

            container.appendChild(newItem);

            // Expand the new item if items are expanded by default
            {f'if ({str(self.items_expanded_by_default).lower()}) {{ const newCollapse = newItem.querySelector(".collapse"); if (newCollapse) newCollapse.classList.add("show"); }}' if self.collapsible_items else ''}
        }}

        function removeListItem(listId, itemIndex) {{
            const container = document.getElementById(listId + '-container');
            const items = container.querySelectorAll('.list-item');

            // Check minimum items limit
            if (items.length <= {self.min_items}) {{
                alert('Minimum {self.min_items} items required');
                return;
            }}

            // Find and remove the item
            const itemToRemove = container.querySelector(`[data-item-index="${{itemIndex}}"]`);
            if (itemToRemove) {{
                itemToRemove.remove();

                // Reindex remaining items
                const remainingItems = container.querySelectorAll('.list-item');
                remainingItems.forEach((item, index) => {{
                    item.setAttribute('data-item-index', index);

                    // Update collapsible IDs
                    {self._render_collapsible_reindex_js(list_id, framework) if self.collapsible_items else ''}

                    // Update all form field names and IDs
                    const inputs = item.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => {{
                        if (input.name) {{
                            input.name = input.name.replace(/^item_\\d+_/, `item_${{index}}_`);
                        }}
                        if (input.id) {{
                            input.id = input.id.replace(/^item_\\d+_/, `item_${{index}}_`);
                        }}
                    }});

                    // Update labels 'for' attributes
                    const labels = item.querySelectorAll('label');
                    labels.forEach(label => {{
                        if (label.getAttribute('for')) {{
                            label.setAttribute('for', label.getAttribute('for').replace(/^item_\\d+_/, `item_${{index}}_`));
                        }}
                    }});

                    // Update help text IDs
                    const helpTexts = item.querySelectorAll('[id$="-help"]');
                    helpTexts.forEach(helpText => {{
                        if (helpText.id) {{
                            helpText.id = helpText.id.replace(/^item_\\d+_/, `item_${{index}}_`);
                        }}
                    }});

                    // Update remove button
                    const removeBtn = item.querySelector('.list-remove-btn');
                    if (removeBtn) {{
                        removeBtn.setAttribute('data-item-index', index);
                        removeBtn.setAttribute('onclick', `removeListItem('${{listId}}', ${{index}})`);
                    }}

                    // Update item summary
                    const summary = item.querySelector('.item-summary');
                    if (summary) {{
                        summary.textContent = `{self.form_model.__name__} #${{index + 1}}`;
                    }}
                }});
            }}
        }}
        </script>
        """

    def _render_collapsible_update_js(self, list_id: str, framework: str) -> str:
        """Generate JavaScript for updating collapsible IDs when adding items."""
        return f"""
            // Update collapsible collapse target
            const collapseTarget = newItem.querySelector('[data-bs-target], .collapsible-content');
            if (collapseTarget) {{
                const newCollapseId = `{list_id}_item_${{newIndex}}`;
                if (framework === 'material') {{
                    collapseTarget.id = newCollapseId;
                    const header = newItem.querySelector('.collapsible-header');
                    if (header) header.setAttribute('onclick', `toggleCollapse('${{newCollapseId}}')`);
                }} else {{
                    collapseTarget.id = newCollapseId;
                    const toggle = newItem.querySelector('[data-bs-target]');
                    if (toggle) {{
                        toggle.setAttribute('data-bs-target', `#${{newCollapseId}}`);
                        toggle.setAttribute('aria-controls', newCollapseId);
                    }}
                }}
            }}
        """

    def _render_collapsible_reindex_js(self, list_id: str, framework: str) -> str:
        """Generate JavaScript for reindexing collapsible IDs when removing items."""
        return f"""
            // Update collapsible IDs
            const collapseTarget = item.querySelector('.collapsible-content, .collapse');
            if (collapseTarget) {{
                const newCollapseId = `{list_id}_item_${{index}}`;
                collapseTarget.id = newCollapseId;
                const header = item.querySelector('.collapsible-header, [data-bs-target]');
                if (header) {{
                    if (header.hasAttribute('onclick')) {{
                        header.setAttribute('onclick', `toggleCollapse('${{newCollapseId}}')`);
                    }} else {{
                        header.setAttribute('data-bs-target', `#${{newCollapseId}}`);
                        header.setAttribute('aria-controls', newCollapseId);
                    }}
                }}
            }}
        """


__all__ = [
    "SectionDesign",
    "FormDesign",
    "BaseLayout",
    "VerticalLayout",
    "HorizontalLayout",
    "TabbedLayout",
    "ListLayout",
]
