"""
Material Design 3 Form Renderer
===============================

Implements proper Material Design 3 components and patterns for form rendering.
Uses Material Web Components (MWC) and Material Design 3 tokens.
"""

from typing import Any, Dict, List, Optional, Type
from html import escape
from .enhanced_renderer import EnhancedFormRenderer
from .schema_form import FormModel


class MaterialDesign3Renderer(EnhancedFormRenderer):
    """
    Material Design 3 form renderer with proper Material components.
    Implements Material Design 3 guidelines and components.
    """

    def __init__(self):
        """Initialize Material Design 3 renderer."""
        super().__init__(framework="material")
        self.component_library = "mdc"  # Material Design Components

    def render_form_from_model(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        include_csrf: bool = False,
        include_submit_button: bool = True,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """
        Render a complete Material Design 3 form.
        """
        schema = model_cls.model_json_schema()
        data = data or {}
        errors = errors or {}

        # Start form with Material Design structure
        form_html = self._build_material_form_structure(
            schema, data, errors, submit_url, method, include_csrf, include_submit_button, layout, **kwargs
        )

        return form_html

    def _build_material_form_structure(
        self,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        submit_url: str,
        method: str,
        include_csrf: bool,
        include_submit_button: bool,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """Build Material Design 3 form structure."""

        # Material Design 3 form wrapper
        form_parts = [
            '<!-- Material Design 3 Form -->',
            '<div class="mdc-form-container">',
            f'<form method="{method}" action="{submit_url}" class="mdc-form" novalidate>',
        ]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append(self._render_csrf_field())

        # Get fields and sort by UI order
        fields = list(schema["properties"].items())
        fields.sort(key=lambda x: x[1].get("ui", {}).get("order", 999))
        required_fields = schema.get("required", [])

        # Render fields based on layout - use Material Design specific methods
        if layout == "tabbed":
            form_parts.extend(self._render_material_tabbed_layout(fields, data, errors, required_fields))
        elif layout == "side-by-side":
            form_parts.extend(self._render_material_side_by_side_layout(fields, data, errors, required_fields))
        else:
            # Render each field with Material Design components
            for field_name, field_schema in fields:
                field_html = self._render_material_field(
                    field_name, field_schema, data.get(field_name), errors.get(field_name), required_fields, layout
                )
                form_parts.append(field_html)

        # Add submit button if requested
        if include_submit_button:
            form_parts.append(self._render_material_submit_button())

        form_parts.extend(['</form>', '</div>'])

        return '\n'.join(form_parts)

    def _render_material_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: List[str] = None,
        layout: str = "vertical",
    ) -> str:
        """Render a Material Design 3 form field."""
        # Check for UI info in nested 'ui' key or directly in field schema
        ui_info = field_schema.get("ui", {})
        if not ui_info:
            # UI info might be directly in the field schema (from FormField)
            ui_info = field_schema

        # Skip hidden fields
        if ui_info.get("hidden"):
            return self._render_hidden_field(field_name, field_schema, value)

        # Determine field type - check multiple possible keys
        ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
        if not ui_element:
            ui_element = self._infer_ui_element(field_schema)

        # Get field properties
        label = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text") or field_schema.get("description")
        is_required = field_name in (required_fields or [])

        # Render different Material component types
        if ui_element in ["text", "email", "password", "search", "tel", "url"]:
            return self._render_material_text_field(
                field_name, ui_element, label, value, error, help_text, is_required, ui_info, field_schema
            )
        elif ui_element == "textarea":
            return self._render_material_textarea(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "number":
            return self._render_material_number_field(
                field_name, label, value, error, help_text, is_required, ui_info, field_schema
            )
        elif ui_element == "select":
            return self._render_material_select(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "checkbox":
            return self._render_material_checkbox(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "radio":
            return self._render_material_radio_group(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element in ["date", "time", "datetime-local"]:
            return self._render_material_date_time_field(
                field_name, ui_element, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "range":
            return self._render_material_slider(
                field_name, label, value, error, help_text, is_required, ui_info, field_schema
            )
        elif ui_element == "color":
            return self._render_material_color_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "file":
            return self._render_material_file_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        else:
            # Fallback to text field
            return self._render_material_text_field(
                field_name, "text", label, value, error, help_text, is_required, ui_info, field_schema
            )

    def _render_material_text_field(
        self,
        field_name: str,
        input_type: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 text field with floating label."""

        # Build attributes
        attrs = []
        if is_required:
            attrs.append('required')
        if ui_info.get("disabled"):
            attrs.append('disabled')
        if ui_info.get("readonly"):
            attrs.append('readonly')
        if field_schema.get("minLength"):
            attrs.append(f'minlength="{field_schema["minLength"]}"')
        if field_schema.get("maxLength"):
            attrs.append(f'maxlength="{field_schema["maxLength"]}"')
        if field_schema.get("pattern"):
            attrs.append(f'pattern="{escape(field_schema["pattern"])}"')

        # Icon support
        icon = ui_info.get("icon", "")
        leading_icon = ""
        if icon:
            if icon.startswith("material-icons"):
                icon_name = icon.replace("material-icons ", "")
                leading_icon = f'<span class="material-icons mdc-text-field__icon mdc-text-field__icon--leading">{icon_name}</span>'
            elif icon.startswith("bi bi-"):
                icon_name = icon.replace("bi bi-", "")
                leading_icon = f'<i class="bi bi-{icon_name} mdc-text-field__icon mdc-text-field__icon--leading"></i>'

        # Value handling
        value_attr = f'value="{escape(str(value))}"' if value is not None else ''

        # Placeholder
        placeholder = ui_info.get("placeholder", "")
        placeholder_attr = f'placeholder="{escape(placeholder)}"' if placeholder else ''

        # Error state
        error_class = " mdc-text-field--invalid" if error else ""
        error_aria = f'aria-describedby="{field_name}-error"' if error else ""

        # Build the Material text field
        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-text-field mdc-text-field--filled{error_class}">
                {leading_icon}
                <input type="{input_type}"
                       id="{field_name}"
                       name="{field_name}"
                       class="mdc-text-field__input"
                       {value_attr}
                       {placeholder_attr}
                       {error_aria}
                       {' '.join(attrs)}>
                <label class="mdc-floating-label" for="{field_name}">{escape(label)}{' *' if is_required else ''}</label>
                <div class="mdc-line-ripple"></div>
            </div>'''

        # Add help text
        if help_text:
            html += f'''
            <div class="mdc-text-field-helper-line">
                <div class="mdc-text-field-helper-text" id="{field_name}-helper-text">
                    {escape(help_text)}
                </div>
            </div>'''

        # Add error message
        if error:
            html += f'''
            <div class="mdc-text-field-helper-line">
                <div class="mdc-text-field-helper-text mdc-text-field-helper-text--validation-msg"
                     id="{field_name}-error" aria-live="polite">
                    {escape(error)}
                </div>
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_textarea(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 textarea."""

        # Build attributes
        attrs = []
        if is_required:
            attrs.append('required')
        if ui_info.get("disabled"):
            attrs.append('disabled')
        if ui_info.get("readonly"):
            attrs.append('readonly')

        # Value handling
        textarea_value = escape(str(value)) if value is not None else ''

        # Error state
        error_class = " mdc-text-field--invalid" if error else ""

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-text-field mdc-text-field--textarea{error_class}">
                <textarea id="{field_name}"
                         name="{field_name}"
                         class="mdc-text-field__input"
                         rows="4"
                         {' '.join(attrs)}>{textarea_value}</textarea>
                <label class="mdc-floating-label" for="{field_name}">{escape(label)}{' *' if is_required else ''}</label>
                <div class="mdc-line-ripple"></div>
            </div>'''

        if help_text:
            html += f'''
            <div class="mdc-text-field-helper-line">
                <div class="mdc-text-field-helper-text">
                    {escape(help_text)}
                </div>
            </div>'''

        if error:
            html += f'''
            <div class="mdc-text-field-helper-line">
                <div class="mdc-text-field-helper-text mdc-text-field-helper-text--validation-msg">
                    {escape(error)}
                </div>
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_select(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 select field."""

        options = ui_info.get("options", [])
        if not options:
            return f'<!-- No options provided for select field {field_name} -->'

        # Build options HTML
        options_html = ""
        if not is_required:
            options_html += '<option value="">-- Select an option --</option>'

        for option in options:
            if isinstance(option, dict):
                option_value = option.get("value", "")
                option_label = option.get("label", option_value)
            else:
                option_value = option_label = str(option)

            selected = 'selected' if str(value) == str(option_value) else ''
            options_html += f'<option value="{escape(str(option_value))}" {selected}>{escape(str(option_label))}</option>'

        # Error state
        error_class = " mdc-select--invalid" if error else ""

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-select mdc-select--filled{error_class}">
                <div class="mdc-select__anchor">
                    <span class="mdc-select__ripple"></span>
                    <select id="{field_name}"
                           name="{field_name}"
                           class="mdc-select__native-control"
                           {'required' if is_required else ''}>
                        {options_html}
                    </select>
                    <span class="mdc-floating-label">{escape(label)}{' *' if is_required else ''}</span>
                    <span class="mdc-line-ripple"></span>
                </div>
            </div>'''

        if help_text:
            html += f'''
            <div class="mdc-select-helper-line">
                <div class="mdc-select-helper-text">
                    {escape(help_text)}
                </div>
            </div>'''

        if error:
            html += f'''
            <div class="mdc-select-helper-line">
                <div class="mdc-select-helper-text mdc-select-helper-text--validation-msg">
                    {escape(error)}
                </div>
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_checkbox(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 checkbox."""

        checked = 'checked' if value else ''

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-form-field">
                <div class="mdc-checkbox">
                    <input type="checkbox"
                           id="{field_name}"
                           name="{field_name}"
                           class="mdc-checkbox__native-control"
                           value="1"
                           {checked}
                           {'required' if is_required else ''}>
                    <div class="mdc-checkbox__background">
                        <svg class="mdc-checkbox__checkmark" viewBox="0 0 24 24">
                            <path class="mdc-checkbox__checkmark-path"
                                  fill="none"
                                  d="M1.73,12.91 8.1,19.28 22.79,4.59"/>
                        </svg>
                        <div class="mdc-checkbox__mixedmark"></div>
                    </div>
                    <div class="mdc-checkbox__ripple"></div>
                </div>
                <label for="{field_name}" class="mdc-form-field__label">
                    {escape(label)}{' *' if is_required else ''}
                </label>
            </div>'''

        if help_text:
            html += f'''
            <div class="mdc-checkbox-helper-text">
                {escape(help_text)}
            </div>'''

        if error:
            html += f'''
            <div class="mdc-checkbox-helper-text mdc-checkbox-helper-text--validation-msg">
                {escape(error)}
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_radio_group(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 radio button group."""

        options = ui_info.get("options", [])
        if not options:
            return f'<!-- No options provided for radio group {field_name} -->'

        html = f'''
        <div class="mdc-form-field-container">
            <fieldset class="mdc-radio-group" role="radiogroup" aria-labelledby="{field_name}-label">
                <legend id="{field_name}-label" class="mdc-radio-group__label">
                    {escape(label)}{' *' if is_required else ''}
                </legend>'''

        for i, option in enumerate(options):
            if isinstance(option, dict):
                option_value = option.get("value", "")
                option_label = option.get("label", option_value)
            else:
                option_value = option_label = str(option)

            checked = 'checked' if str(value) == str(option_value) else ''
            radio_id = f"{field_name}_{i}"

            html += f'''
                <div class="mdc-form-field">
                    <div class="mdc-radio">
                        <input type="radio"
                               id="{radio_id}"
                               name="{field_name}"
                               class="mdc-radio__native-control"
                               value="{escape(str(option_value))}"
                               {checked}
                               {'required' if is_required else ''}>
                        <div class="mdc-radio__background">
                            <div class="mdc-radio__outer-circle"></div>
                            <div class="mdc-radio__inner-circle"></div>
                        </div>
                        <div class="mdc-radio__ripple"></div>
                    </div>
                    <label for="{radio_id}" class="mdc-form-field__label">
                        {escape(str(option_label))}
                    </label>
                </div>'''

        html += '''
            </fieldset>'''

        if help_text:
            html += f'''
            <div class="mdc-radio-helper-text">
                {escape(help_text)}
            </div>'''

        if error:
            html += f'''
            <div class="mdc-radio-helper-text mdc-radio-helper-text--validation-msg">
                {escape(error)}
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_number_field(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 number field."""
        return self._render_material_text_field(
            field_name, "number", label, value, error, help_text, is_required, ui_info, field_schema
        )

    def _render_material_date_time_field(
        self,
        field_name: str,
        input_type: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 date/time field."""
        return self._render_material_text_field(
            field_name, input_type, label, value, error, help_text, is_required, ui_info, {}
        )

    def _render_material_slider(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 slider."""

        min_val = field_schema.get("minimum", 0)
        max_val = field_schema.get("maximum", 100)
        current_value = value if value is not None else min_val

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-slider-container">
                <label class="mdc-slider-label" for="{field_name}">
                    {escape(label)}{' *' if is_required else ''}
                </label>
                <div class="mdc-slider mdc-slider--discrete">
                    <input type="range"
                           id="{field_name}"
                           name="{field_name}"
                           class="mdc-slider__input"
                           min="{min_val}"
                           max="{max_val}"
                           value="{current_value}"
                           {'required' if is_required else ''}>
                    <div class="mdc-slider__track">
                        <div class="mdc-slider__track--inactive"></div>
                        <div class="mdc-slider__track--active">
                            <div class="mdc-slider__track--active_fill"></div>
                        </div>
                    </div>
                    <div class="mdc-slider__thumb">
                        <div class="mdc-slider__thumb-knob"></div>
                    </div>
                </div>
                <div class="mdc-slider-value" id="{field_name}-value">{current_value}</div>
            </div>'''

        if help_text:
            html += f'''
            <div class="mdc-slider-helper-text">
                {escape(help_text)}
            </div>'''

        if error:
            html += f'''
            <div class="mdc-slider-helper-text mdc-slider-helper-text--validation-msg">
                {escape(error)}
            </div>'''

        html += '\n        </div>'
        return html

    def _render_material_color_field(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 color field."""
        return self._render_material_text_field(
            field_name, "color", label, value, error, help_text, is_required, ui_info, {}
        )

    def _render_material_file_field(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 file upload field."""

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-file-upload">
                <input type="file"
                       id="{field_name}"
                       name="{field_name}"
                       class="mdc-file-upload__input"
                       {'required' if is_required else ''}>
                <label for="{field_name}" class="mdc-file-upload__label">
                    <span class="material-icons">cloud_upload</span>
                    <span class="mdc-file-upload__text">
                        {escape(label)}{' *' if is_required else ''}
                    </span>
                </label>
            </div>'''

        if help_text:
            html += f'''
            <div class="mdc-file-upload-helper-text">
                {escape(help_text)}
            </div>'''

        if error:
            html += f'''
            <div class="mdc-file-upload-helper-text mdc-file-upload-helper-text--validation-msg">
                {escape(error)}
            </div>'''

        html += '\n        </div>'
        return html
    
    def _render_material_tabbed_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render fields in a Material Design tabbed layout."""
        # Group fields into logical tabs
        tabs = self._group_fields_into_tabs(fields)
        
        parts = []
        
        # Create Material Design tab bar
        parts.append('<div class="mdc-tab-bar" role="tablist">')
        parts.append('  <div class="mdc-tab-scroller">')
        parts.append('    <div class="mdc-tab-scroller__scroll-area">')
        parts.append('      <div class="mdc-tab-scroller__scroll-content">')
        
        # Create tab buttons
        for i, (tab_name, _) in enumerate(tabs):
            is_active = i == 0
            tab_id = f"material-tab-{tab_name.lower().replace(' ', '-')}"
            active_class = " mdc-tab--active" if is_active else ""
            aria_selected = "true" if is_active else "false"
            
            parts.append(f'''
        <button class="mdc-tab{active_class}" role="tab" aria-selected="{aria_selected}" 
                onclick="switchMaterialTab('{tab_id}', this)" tabindex="{"0" if is_active else "-1"}">
          <span class="mdc-tab__content">
            <span class="mdc-tab__text-label">{tab_name}</span>
          </span>
          <span class="mdc-tab-indicator{"--active" if is_active else ""}">
            <span class="mdc-tab-indicator__content mdc-tab-indicator__content--underline"></span>
          </span>
          <span class="mdc-tab__ripple"></span>
        </button>
            ''')
        
        parts.append('      </div>')
        parts.append('    </div>')
        parts.append('  </div>')
        parts.append('</div>')
        
        # Create tab content panels
        for i, (tab_name, tab_fields) in enumerate(tabs):
            is_active = i == 0
            tab_id = f"material-tab-{tab_name.lower().replace(' ', '-')}"
            display_style = "block" if is_active else "none"
            
            parts.append(f'<div id="{tab_id}" class="mdc-tab-content" style="display: {display_style};" role="tabpanel">')
            
            # Render fields in this tab
            for field_name, field_schema in tab_fields:
                field_html = self._render_material_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within tabs
                )
                parts.append(field_html)
            
            parts.append('</div>')
        
        return parts
    
    def _render_material_side_by_side_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render fields in a Material Design side-by-side layout."""
        parts = []
        
        # Group fields into pairs for side-by-side arrangement
        field_pairs = []
        for i in range(0, len(fields), 2):
            if i + 1 < len(fields):
                field_pairs.append((fields[i], fields[i + 1]))
            else:
                # Odd number of fields - last field goes alone
                field_pairs.append((fields[i], None))
        
        # Render each pair in a row using Material Design grid
        for left_field, right_field in field_pairs:
            parts.append('<div class="mdc-layout-grid">')
            parts.append('  <div class="mdc-layout-grid__inner">')
            
            # Left column
            parts.append('    <div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-6">')
            if left_field:
                field_name, field_schema = left_field
                field_html = self._render_material_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within each column
                )
                parts.append(field_html)
            parts.append('    </div>')
            
            # Right column
            parts.append('    <div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-6">')
            if right_field:
                field_name, field_schema = right_field
                field_html = self._render_material_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within each column
                )
                parts.append(field_html)
            parts.append('    </div>')
            
            parts.append('  </div>')
            parts.append('</div>')  # Close mdc-layout-grid
        
        return parts

    def _render_material_submit_button(self) -> str:
        """Render Material Design 3 submit button."""
        return '''
        <div class="mdc-form-field-container">
            <button type="submit" class="mdc-button mdc-button--raised">
                <span class="mdc-button__ripple"></span>
                <span class="mdc-button__label">Submit</span>
            </button>
        </div>'''

    def get_material_css(self) -> str:
        """Return Material Design 3 CSS."""
        return """
        <style>
        /* Material Design 3 Form Styles */
        .mdc-form-container {
            font-family: 'Roboto', sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 24px;
        }

        .mdc-form {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .mdc-form-field-container {
            position: relative;
            margin-bottom: 24px;
        }

        /* Material Design Layout Grid */
        .mdc-layout-grid {
            display: flex;
            flex-flow: row wrap;
            align-items: stretch;
            margin: 0 auto;
            box-sizing: border-box;
            padding: 8px;
        }

        .mdc-layout-grid__inner {
            display: flex;
            flex-flow: row wrap;
            align-items: stretch;
            margin: -8px;
            width: calc(100% + 16px);
        }

        .mdc-layout-grid__cell {
            margin: 8px;
            box-sizing: border-box;
        }

        .mdc-layout-grid__cell--span-6 {
            width: calc(50% - 16px);
        }

        @media (max-width: 599px) {
            .mdc-layout-grid__cell--span-6 {
                width: calc(100% - 16px);
            }
        }

        /* Material Design Tab Bar */
        .mdc-tab-bar {
            width: 100%;
            margin-bottom: 24px;
        }

        .mdc-tab-scroller {
            overflow-y: hidden;
        }

        .mdc-tab-scroller__scroll-area {
            overflow-x: scroll;
            margin-bottom: -17px;
        }

        .mdc-tab-scroller__scroll-content {
            display: flex;
            flex: 1 0 auto;
            transform: none;
        }

        .mdc-tab {
            position: relative;
            padding: 0 24px;
            border: none;
            outline: none;
            background: transparent;
            cursor: pointer;
            height: 48px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: rgba(0, 0, 0, 0.6);
            transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
            min-width: 90px;
            flex-shrink: 0;
        }

        .mdc-tab:hover {
            color: rgba(0, 0, 0, 0.87);
        }

        .mdc-tab--active {
            color: #1976d2;
        }

        .mdc-tab__content {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            height: inherit;
            pointer-events: none;
        }

        .mdc-tab__text-label {
            white-space: nowrap;
        }

        .mdc-tab-indicator {
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 2px;
            transform: scaleX(0);
            transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-tab-indicator--active {
            transform: scaleX(1);
        }

        .mdc-tab-indicator__content--underline {
            position: absolute;
            width: 100%;
            height: 100%;
            background-color: #1976d2;
        }

        .mdc-tab__ripple {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        .mdc-tab-content {
            padding: 24px 0;
        }

        /* Text Fields */
        .mdc-text-field {
            position: relative;
            border-radius: 4px 4px 0 0;
            background-color: #f5f5f5;
            border-bottom: 1px solid rgba(0, 0, 0, 0.42);
            padding: 0;
            overflow: hidden;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-text-field:hover {
            background-color: #eeeeee;
            border-bottom-color: rgba(0, 0, 0, 0.87);
        }

        .mdc-text-field--focused {
            background-color: #e3f2fd;
            border-bottom: 2px solid #1976d2;
        }

        .mdc-text-field--invalid {
            border-bottom-color: #d32f2f;
        }

        .mdc-text-field__input {
            width: 100%;
            padding: 20px 16px 8px;
            border: none;
            background: transparent;
            outline: none;
            font-size: 16px;
            color: rgba(0, 0, 0, 0.87);
            box-sizing: border-box;
        }

        .mdc-text-field__input::placeholder {
            color: transparent;
        }

        .mdc-text-field__input:focus::placeholder {
            color: rgba(0, 0, 0, 0.6);
        }

        .mdc-floating-label {
            position: absolute;
            left: 16px;
            top: 20px;
            font-size: 16px;
            color: rgba(0, 0, 0, 0.6);
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            transform-origin: left top;
        }

        .mdc-text-field__input:focus + .mdc-floating-label,
        .mdc-text-field__input:not(:placeholder-shown) + .mdc-floating-label {
            transform: translateY(-12px) scale(0.75);
            color: #1976d2;
        }

        .mdc-text-field--invalid .mdc-floating-label {
            color: #d32f2f;
        }

        .mdc-line-ripple {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background-color: #1976d2;
            transform: scaleX(0);
            transition: transform 0.18s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-text-field__input:focus ~ .mdc-line-ripple {
            transform: scaleX(1);
        }

        /* Textarea */
        .mdc-text-field--textarea {
            background-color: #f5f5f5;
            border: 1px solid rgba(0, 0, 0, 0.23);
            border-radius: 4px;
        }

        .mdc-text-field--textarea .mdc-text-field__input {
            resize: vertical;
            min-height: 100px;
            padding: 20px 16px 8px;
        }

        /* Helper Text */
        .mdc-text-field-helper-line {
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
        }

        .mdc-text-field-helper-text {
            font-size: 12px;
            color: rgba(0, 0, 0, 0.6);
            line-height: 1.25;
        }

        .mdc-text-field-helper-text--validation-msg {
            color: #d32f2f;
        }

        /* Select Fields */
        .mdc-select {
            position: relative;
            background-color: #f5f5f5;
            border-radius: 4px 4px 0 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.42);
            overflow: hidden;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-select:hover {
            background-color: #eeeeee;
            border-bottom-color: rgba(0, 0, 0, 0.87);
        }

        .mdc-select__native-control {
            width: 100%;
            padding: 20px 16px 8px;
            border: none;
            background: transparent;
            outline: none;
            font-size: 16px;
            color: rgba(0, 0, 0, 0.87);
            appearance: none;
            cursor: pointer;
        }

        /* Checkboxes */
        .mdc-form-field {
            display: inline-flex;
            align-items: center;
            margin-bottom: 8px;
        }

        .mdc-checkbox {
            position: relative;
            display: inline-block;
            width: 18px;
            height: 18px;
            margin-right: 12px;
        }

        .mdc-checkbox__native-control {
            position: absolute;
            top: 0;
            left: 0;
            width: 18px;
            height: 18px;
            margin: 0;
            opacity: 0;
            cursor: pointer;
        }

        .mdc-checkbox__background {
            position: absolute;
            top: 0;
            left: 0;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(0, 0, 0, 0.54);
            border-radius: 2px;
            background-color: transparent;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-checkbox__native-control:checked + .mdc-checkbox__background {
            background-color: #1976d2;
            border-color: #1976d2;
        }

        .mdc-checkbox__checkmark {
            position: absolute;
            top: 0;
            left: 0;
            width: 18px;
            height: 18px;
            opacity: 0;
            transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-checkbox__native-control:checked ~ .mdc-checkbox__background .mdc-checkbox__checkmark {
            opacity: 1;
        }

        .mdc-checkbox__checkmark-path {
            stroke: white;
            stroke-width: 2;
            stroke-dasharray: 22.91;
            stroke-dashoffset: 22.91;
            transition: stroke-dashoffset 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-checkbox__native-control:checked ~ .mdc-checkbox__background .mdc-checkbox__checkmark-path {
            stroke-dashoffset: 0;
        }

        /* Radio Buttons */
        .mdc-radio-group {
            border: none;
            padding: 0;
            margin: 0;
        }

        .mdc-radio-group__label {
            font-size: 16px;
            color: rgba(0, 0, 0, 0.87);
            margin-bottom: 12px;
            display: block;
        }

        .mdc-radio {
            position: relative;
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 12px;
        }

        .mdc-radio__native-control {
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 20px;
            margin: 0;
            opacity: 0;
            cursor: pointer;
        }

        .mdc-radio__background {
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 20px;
        }

        .mdc-radio__outer-circle {
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(0, 0, 0, 0.54);
            border-radius: 50%;
            transition: border-color 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-radio__inner-circle {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 10px;
            height: 10px;
            background-color: #1976d2;
            border-radius: 50%;
            transform: translate(-50%, -50%) scale(0);
            transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-radio__native-control:checked + .mdc-radio__background .mdc-radio__outer-circle {
            border-color: #1976d2;
        }

        .mdc-radio__native-control:checked + .mdc-radio__background .mdc-radio__inner-circle {
            transform: translate(-50%, -50%) scale(1);
        }

        /* Buttons */
        .mdc-button {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 88px;
            padding: 0 16px;
            height: 36px;
            border: none;
            border-radius: 4px;
            background-color: #1976d2;
            color: white;
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.75px;
            cursor: pointer;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }

        .mdc-button:hover {
            background-color: #1565c0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .mdc-button:active {
            background-color: #0d47a1;
            transform: translateY(1px);
        }

        .mdc-button__ripple {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }

        /* Sliders */
        .mdc-slider-container {
            margin: 24px 0;
        }

        .mdc-slider-label {
            display: block;
            font-size: 16px;
            color: rgba(0, 0, 0, 0.87);
            margin-bottom: 12px;
        }

        .mdc-slider {
            position: relative;
            width: 100%;
            height: 4px;
            margin: 12px 0;
        }

        .mdc-slider__input {
            position: absolute;
            top: -16px;
            left: 0;
            width: 100%;
            height: 36px;
            margin: 0;
            background: transparent;
            appearance: none;
            cursor: pointer;
        }

        .mdc-slider__input::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: #1976d2;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            cursor: pointer;
        }

        .mdc-slider__track {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            border-radius: 2px;
            background-color: rgba(0, 0, 0, 0.26);
        }

        .mdc-slider__track--active_fill {
            background-color: #1976d2;
            height: 100%;
            border-radius: 2px;
        }

        .mdc-slider-value {
            text-align: center;
            font-size: 14px;
            color: rgba(0, 0, 0, 0.87);
            margin-top: 8px;
        }

        /* File Upload */
        .mdc-file-upload {
            position: relative;
            display: inline-block;
            cursor: pointer;
        }

        .mdc-file-upload__input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }

        .mdc-file-upload__label {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border: 2px dashed rgba(0, 0, 0, 0.23);
            border-radius: 4px;
            background-color: #f5f5f5;
            color: rgba(0, 0, 0, 0.87);
            cursor: pointer;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .mdc-file-upload__label:hover {
            background-color: #eeeeee;
            border-color: rgba(0, 0, 0, 0.54);
        }

        .mdc-file-upload__label .material-icons {
            margin-right: 8px;
            color: rgba(0, 0, 0, 0.54);
        }

        /* Responsive Design */
        @media (max-width: 600px) {
            .mdc-form-container {
                padding: 16px;
            }

            .mdc-form {
                gap: 16px;
            }

            .mdc-form-field-container {
                margin-bottom: 16px;
            }
        }

        /* Focus and Hover States */
        .mdc-text-field__input:focus,
        .mdc-select__native-control:focus {
            outline: none;
        }

        /* Animation for ripple effects */
        @keyframes mdc-ripple {
            0% {
                transform: scale(0);
                opacity: 1;
            }
            100% {
                transform: scale(1);
                opacity: 0;
            }
        }

        /* Error states */
        .mdc-text-field--invalid,
        .mdc-select--invalid {
            border-bottom-color: #d32f2f;
        }

        .mdc-text-field--invalid .mdc-floating-label {
            color: #d32f2f;
        }
        </style>
        """

    def get_material_javascript(self) -> str:
        """Return Material Design 3 JavaScript."""
        return """
        <script>
        // Material Design 3 JavaScript functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize Material Design components
            initializeMaterialComponents();

            // Add focus/blur handlers for floating labels
            initializeFloatingLabels();

            // Add ripple effects
            initializeRippleEffects();

            // Initialize sliders
            initializeSliders();
        });

        function switchMaterialTab(tabId, buttonElement) {
            // Hide all tab content panels
            const tabContents = document.querySelectorAll('.mdc-tab-content');
            const tabButtons = document.querySelectorAll('.mdc-tab');

            tabContents.forEach(content => {
                content.style.display = 'none';
            });

            tabButtons.forEach(button => {
                button.classList.remove('mdc-tab--active');
                button.setAttribute('aria-selected', 'false');
                button.setAttribute('tabindex', '-1');
                const indicator = button.querySelector('.mdc-tab-indicator');
                if (indicator) {
                    indicator.classList.remove('mdc-tab-indicator--active');
                }
            });

            // Show selected tab content
            const selectedContent = document.getElementById(tabId);
            if (selectedContent) {
                selectedContent.style.display = 'block';
            }

            // Mark button as active
            buttonElement.classList.add('mdc-tab--active');
            buttonElement.setAttribute('aria-selected', 'true');
            buttonElement.setAttribute('tabindex', '0');
            const indicator = buttonElement.querySelector('.mdc-tab-indicator');
            if (indicator) {
                indicator.classList.add('mdc-tab-indicator--active');
            }
        }

        function initializeMaterialComponents() {
            // Text field focus handling
            const textFields = document.querySelectorAll('.mdc-text-field');
            textFields.forEach(field => {
                const input = field.querySelector('.mdc-text-field__input');

                input.addEventListener('focus', () => {
                    field.classList.add('mdc-text-field--focused');
                });

                input.addEventListener('blur', () => {
                    field.classList.remove('mdc-text-field--focused');
                });
            });

            // Select field handling
            const selects = document.querySelectorAll('.mdc-select');
            selects.forEach(select => {
                const selectInput = select.querySelector('.mdc-select__native-control');

                selectInput.addEventListener('focus', () => {
                    select.classList.add('mdc-select--focused');
                });

                selectInput.addEventListener('blur', () => {
                    select.classList.remove('mdc-select--focused');
                });
            });
        }

        function initializeFloatingLabels() {
            const inputs = document.querySelectorAll('.mdc-text-field__input');
            inputs.forEach(input => {
                // Check if input has value on load
                if (input.value) {
                    input.classList.add('mdc-text-field--label-floating');
                }

                input.addEventListener('input', () => {
                    if (input.value) {
                        input.classList.add('mdc-text-field--label-floating');
                    } else {
                        input.classList.remove('mdc-text-field--label-floating');
                    }
                });
            });
        }

        function initializeRippleEffects() {
            const buttons = document.querySelectorAll('.mdc-button');
            buttons.forEach(button => {
                button.addEventListener('click', function(e) {
                    const ripple = this.querySelector('.mdc-button__ripple');
                    if (ripple) {
                        ripple.style.animation = 'none';
                        ripple.offsetHeight; // Trigger reflow
                        ripple.style.animation = 'mdc-ripple 0.6s ease-out';
                    }
                });
            });
        }

        function initializeSliders() {
            const sliders = document.querySelectorAll('.mdc-slider__input');
            sliders.forEach(slider => {
                const valueDisplay = document.getElementById(slider.id + '-value');

                slider.addEventListener('input', function() {
                    if (valueDisplay) {
                        valueDisplay.textContent = this.value;
                    }
                });
            });
        }

        // Form validation with Material Design styling
        function validateMaterialForm(form) {
            let isValid = true;
            const inputs = form.querySelectorAll('input, select, textarea');

            inputs.forEach(input => {
                const field = input.closest('.mdc-text-field, .mdc-select, .mdc-form-field');
                const errorElement = field?.parentNode?.querySelector('[class*="validation-msg"]');

                if (input.checkValidity()) {
                    field?.classList.remove('mdc-text-field--invalid', 'mdc-select--invalid');
                    if (errorElement) {
                        errorElement.style.display = 'none';
                    }
                } else {
                    field?.classList.add('mdc-text-field--invalid', 'mdc-select--invalid');
                    if (errorElement) {
                        errorElement.style.display = 'block';
                    }
                    isValid = false;
                }
            });

            return isValid;
        }

        // Add form validation on submit
        document.addEventListener('submit', function(e) {
            if (e.target.classList.contains('mdc-form')) {
                if (!validateMaterialForm(e.target)) {
                    e.preventDefault();
                }
            }
        });
        </script>
        """


def render_material_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Dict[str, str]] = None,
    layout: str = "vertical",
    include_css: bool = True,
    include_js: bool = True,
    **kwargs,
) -> str:
    """
    Render a complete Material Design 3 form.

    Args:
        form_model_cls: Pydantic FormModel class
        form_data: Form data to populate fields
        errors: Validation errors
        layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
        include_css: Whether to include Material CSS
        include_js: Whether to include Material JavaScript
        **kwargs: Additional rendering options

    Returns:
        Complete HTML with Material Design 3 form
    """
    renderer = MaterialDesign3Renderer()

    html_parts = []

    # Add CSS if requested
    if include_css:
        html_parts.append(renderer.get_material_css())

    # Add the form HTML
    form_html = renderer.render_form_from_model(form_model_cls, form_data, errors, layout=layout, **kwargs)
    html_parts.append(form_html)

    # Add JavaScript if requested
    if include_js:
        html_parts.append(renderer.get_material_javascript())

    return '\n'.join(html_parts)
