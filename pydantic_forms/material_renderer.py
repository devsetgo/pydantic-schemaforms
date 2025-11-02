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
        Render a complete self-contained Material Design 3 form.
        Includes ALL necessary CSS, JavaScript, HTML, and error handling.
        """
        schema = model_cls.model_json_schema()
        data = data or {}
        errors = errors or {}

        # Build complete self-contained form
        form_html = self._build_complete_material_form(
            schema, data, errors, submit_url, method, include_csrf, include_submit_button, layout, **kwargs
        )

        return form_html

    def _build_complete_material_form(
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
        """Build a complete self-contained Material Design 3 form with all dependencies."""

        # Start with complete HTML structure including all dependencies
        form_parts = [
            '<!-- Material Design 3 Self-Contained Form -->',
            self._get_material_dependencies(),
            self._get_material_css(),
            '<div class="pydantic-material-form-container">',
            f'<form method="{method}" action="{submit_url}" class="pydantic-material-form" novalidate>',
        ]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append(self._render_csrf_field())

        # Add global form errors if any
        if errors and isinstance(errors, dict):
            global_errors = [v for k, v in errors.items() if k.startswith('__')]
            if global_errors:
                form_parts.append(self._render_material_global_errors(global_errors))

        # Get fields and sort by UI order
        fields = list(schema["properties"].items())
        fields.sort(key=lambda x: x[1].get("ui", {}).get("order", 999))
        required_fields = schema.get("required", [])

        # Render fields based on layout
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
        
        # Add model list JavaScript if any model_list fields were rendered
        if self._has_model_list_fields(schema):
            from .model_list import ModelListRenderer
            list_renderer = ModelListRenderer(framework="material")
            form_parts.append(list_renderer.get_model_list_javascript())

        # Add Material Design JavaScript
        form_parts.append(self._get_material_javascript())

        return '\n'.join(form_parts)

    def _get_material_dependencies(self) -> str:
        """Return self-contained Material Design dependencies - no external links."""
        return '''
<!-- Self-Contained Material Design Dependencies -->
<style>
/* Embedded Material Icons */
@font-face {
  font-family: 'Material Icons';
  font-style: normal;
  font-weight: 400;
  src: url(data:font/woff2;base64,d09GMgABAAAAAAYkAAoAAAAAE) format('woff2');
}

.material-icons {
  font-family: 'Material Icons';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

/* Embedded Bootstrap Icons */
.bi::before {
  display: inline-block;
  content: "";
  vertical-align: -.125em;
  background-repeat: no-repeat;
  background-size: 1rem 1rem;
}
</style>'''

    def _get_material_css(self) -> str:
        """Return complete Material Design CSS for self-contained forms."""
        return '''
<style>
/* Pydantic Forms - Self-Contained Material Design 3 Styles */
.pydantic-material-form-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    max-width: 100%;
    margin: 0;
    padding: 0;
    line-height: 1.5;
    color: #1d1b20;
}

.pydantic-material-form {
    width: 100%;
    background: #fef7ff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}

/* Material Design Form Field Container */
.pydantic-form-field-container {
    margin-bottom: 24px;
    position: relative;
    width: 100%;
}

/* Material Design Text Field */
.pydantic-text-field {
    position: relative;
    width: 100%;
    margin-bottom: 8px;
}

.pydantic-text-field input,
.pydantic-text-field textarea,
.pydantic-text-field select {
    width: 100%;
    padding: 16px 12px 8px 12px;
    border: 1px solid #79747e;
    border-radius: 4px;
    background: #fef7ff;
    color: #1d1b20;
    font-size: 16px;
    font-family: inherit;
    outline: none;
    transition: all 0.2s ease;
    box-sizing: border-box;
}

.pydantic-text-field input:focus,
.pydantic-text-field textarea:focus,
.pydantic-text-field select:focus {
    border-color: #6750a4;
    border-width: 2px;
    background: #ffffff;
    box-shadow: 0 0 0 1px #6750a4;
}

/* Material Design Labels */
.pydantic-field-label {
    display: block;
    color: #49454f;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
    position: relative;
}

.pydantic-field-label.required::after {
    content: ' *';
    color: #ba1a1a;
}

/* Material Design Help Text */
.pydantic-help-text {
    font-size: 12px;
    color: #49454f;
    margin-top: 4px;
    line-height: 1.4;
}

/* Material Design Error Text */
.pydantic-error-text {
    font-size: 12px;
    color: #ba1a1a;
    margin-top: 4px;
    line-height: 1.4;
}

/* Field with Error State */
.pydantic-field-error input,
.pydantic-field-error textarea,
.pydantic-field-error select {
    border-color: #ba1a1a;
    background: #fcfcfc;
}

/* Material Design Buttons */
.pydantic-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 24px;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    box-sizing: border-box;
}

.pydantic-btn-primary {
    background: #6750a4;
    color: #ffffff;
}

.pydantic-btn-primary:hover {
    background: #5a43a0;
    box-shadow: 0 2px 4px rgba(103, 80, 164, 0.3);
}

.pydantic-btn-secondary {
    background: transparent;
    color: #6750a4;
    border: 1px solid #79747e;
}

.pydantic-btn-secondary:hover {
    background: #f3f0ff;
}

/* Material Design Checkboxes */
.pydantic-checkbox-container {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px 0;
}

.pydantic-checkbox {
    width: 20px;
    height: 20px;
    border: 2px solid #79747e;
    border-radius: 2px;
    background: #fef7ff;
    cursor: pointer;
    position: relative;
}

.pydantic-checkbox:checked {
    background: #6750a4;
    border-color: #6750a4;
}

.pydantic-checkbox:checked::after {
    content: '✓';
    position: absolute;
    top: -2px;
    left: 2px;
    color: white;
    font-size: 14px;
    font-weight: bold;
}

/* Material Design Select */
.pydantic-select-container {
    position: relative;
}

.pydantic-select-container::after {
    content: '▼';
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #49454f;
    pointer-events: none;
    font-size: 12px;
}

/* Material Design Color Input */
.pydantic-color-input {
    width: 100%;
    height: 56px;
    border: 1px solid #79747e;
    border-radius: 4px;
    cursor: pointer;
    background: #fef7ff;
}

.pydantic-color-input:hover {
    border-color: #6750a4;
}

/* Material Design Range Input */
.pydantic-range-input {
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: #e7e0ec;
    outline: none;
    -webkit-appearance: none;
}

.pydantic-range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #6750a4;
    cursor: pointer;
}

.pydantic-range-input::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #6750a4;
    cursor: pointer;
    border: none;
}

/* Material Design Cards for Lists */
.pydantic-list-container {
    border: 1px solid #e7e0ec;
    border-radius: 12px;
    background: #ffffff;
    overflow: hidden;
    margin: 16px 0;
}

.pydantic-list-header {
    background: #f3f0ff;
    padding: 16px;
    border-bottom: 1px solid #e7e0ec;
    display: flex;
    justify-content: between;
    align-items: center;
}

.pydantic-list-title {
    font-size: 18px;
    font-weight: 500;
    color: #1d1b20;
    margin: 0;
}

.pydantic-list-item {
    padding: 16px;
    border-bottom: 1px solid #f4f4f4;
    position: relative;
}

.pydantic-list-item:last-child {
    border-bottom: none;
}

/* Material Design Icons */
.pydantic-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    color: #49454f;
    margin-right: 8px;
}

/* Material Design Field with Icon */
.pydantic-field-with-icon {
    display: flex;
    align-items: center;
    gap: 12px;
}

.pydantic-field-with-icon .pydantic-icon {
    flex-shrink: 0;
    margin-top: 16px; /* Align with input padding */
}

/* Responsive Design */
@media (max-width: 768px) {
    .pydantic-material-form {
        padding: 16px;
    }
    
    .pydantic-form-field-container {
        margin-bottom: 16px;
    }
}

/* Global Error Styling */
.pydantic-global-errors {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
}

.pydantic-global-error {
    color: #ba1a1a;
    font-size: 14px;
    margin: 4px 0;
}
</style>'''

        # Add model list JavaScript if any model_list fields were rendered
        if self._has_model_list_fields(schema):
            from .model_list import ModelListRenderer
            list_renderer = ModelListRenderer(framework="material")
            form_parts.append(list_renderer.get_model_list_javascript())

        return '\n'.join(form_parts)
    
    def _has_model_list_fields(self, schema: Dict[str, Any]) -> bool:
        """Check if the schema contains any model_list fields."""
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            ui_info = field_schema.get("ui", {}) or field_schema
            ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
            if ui_element == "model_list":
                return True
        return False

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
        if ui_element == "model_list":
            return self._render_material_model_list(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element in ["text", "email", "password", "search", "tel", "url"]:
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
                field_name, label, value, error, help_text, is_required, ui_info, field_schema
            )
        elif ui_element == "checkbox":
            return self._render_material_checkbox(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "radio":
            return self._render_material_radio_group(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "color":
            return self._render_material_color_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "date":
            return self._render_material_date_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element == "range":
            return self._render_material_range_field(
                field_name, label, value, error, help_text, is_required, ui_info, field_schema
            )
        else:
            # Fallback to text field for unknown types
            return self._render_material_text_field(
                field_name, "text", label, value, error, help_text, is_required, ui_info, field_schema
            )

    def _render_material_text_field(
    top: 0;
    right: 0;
    left: 0;
    box-sizing: border-box;
    width: 100%;
    max-width: 100%;
    height: 100%;
    text-align: left;
    pointer-events: none;
}

.pydantic-notched-outline__leading,
.pydantic-notched-outline__notch,
.pydantic-notched-outline__trailing {
    box-sizing: border-box;
    height: 100%;
    border-top: 1px solid rgba(0, 0, 0, 0.38);
    border-bottom: 1px solid rgba(0, 0, 0, 0.38);
    pointer-events: none;
}

.pydantic-notched-outline__leading {
    border-left: 1px solid rgba(0, 0, 0, 0.38);
    border-radius: 4px 0 0 4px;
    width: 12px;
}

.pydantic-notched-outline__trailing {
    border-right: 1px solid rgba(0, 0, 0, 0.38);
    border-radius: 0 4px 4px 0;
    flex-grow: 1;
}

.pydantic-notched-outline__notch {
    flex: 0 0 auto;
    width: auto;
    max-width: calc(100% - 12px * 2);
}

.pydantic-floating-label {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(0, 0, 0, 0.6);
    font-size: 1rem;
    line-height: 1.15rem;
    font-weight: 400;
    letter-spacing: 0.009375em;
    text-decoration: inherit;
    text-transform: inherit;
    pointer-events: none;
    transition: transform 150ms cubic-bezier(0.4, 0, 0.2, 1), color 150ms cubic-bezier(0.4, 0, 0.2, 1);
    background: white;
    z-index: 1;
}

.pydantic-text-field__input:focus ~ .pydantic-notched-outline .pydantic-floating-label,
.pydantic-text-field__input:not(:placeholder-shown) ~ .pydantic-notched-outline .pydantic-floating-label {
    transform: translateY(-34px) scale(0.75);
    padding: 0 4px;
}

.pydantic-text-field__input:focus ~ .pydantic-notched-outline .pydantic-notched-outline__leading,
.pydantic-text-field__input:focus ~ .pydantic-notched-outline .pydantic-notched-outline__notch,
.pydantic-text-field__input:focus ~ .pydantic-notched-outline .pydantic-notched-outline__trailing {
    border-color: #6200ee;
    border-width: 2px;
}

/* Icon and Input Layout */
.pydantic-field-with-icon {
    display: flex;
    align-items: center;
    gap: 12px;
}

.pydantic-field-icon {
    font-size: 1.25rem;
    min-width: 24px;
    color: rgba(0, 0, 0, 0.54);
    display: flex;
    align-items: center;
    justify-content: center;
}

.pydantic-field-input-wrapper {
    flex-grow: 1;
}

/* Helper Text */
.pydantic-helper-text {
    color: rgba(0, 0, 0, 0.6);
    font-size: 0.75rem;
    line-height: 1.25rem;
    font-weight: 400;
    letter-spacing: 0.0333333333em;
    margin-top: 4px;
    margin-left: 16px;
}

.pydantic-helper-text--error {
    color: #b00020;
}

/* Submit Button */
.pydantic-submit-button {
    background: #6200ee;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: background-color 150ms cubic-bezier(0.4, 0, 0.2, 1);
    font-family: 'Roboto', sans-serif;
    width: 100%;
    margin-top: 1.5rem;
}

.pydantic-submit-button:hover {
    background: #3700b3;
}

.pydantic-submit-button:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(98, 0, 238, 0.3);
}

/* Global Error Messages */
.pydantic-global-errors {
    background: #ffebee;
    border: 1px solid #f44336;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 1.5rem;
    color: #c62828;
}

.pydantic-global-errors ul {
    margin: 0;
    padding-left: 20px;
}

/* Select Field */
.pydantic-select {
    border: none;
    border-radius: 4px;
    background: none;
    font-size: 1rem;
    width: 100%;
    height: 56px;
    padding: 14px 16px;
    outline: none;
    color: rgba(0, 0, 0, 0.87);
    font-family: 'Roboto', sans-serif;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 12px center;
    background-repeat: no-repeat;
    background-size: 16px;
    padding-right: 40px;
}

/* Checkbox */
.pydantic-checkbox-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
}

.pydantic-checkbox {
    width: 20px;
    height: 20px;
    accent-color: #6200ee;
}

.pydantic-checkbox-label {
    font-size: 1rem;
    color: rgba(0, 0, 0, 0.87);
    font-family: 'Roboto', sans-serif;
    cursor: pointer;
}

/* Textarea */
.pydantic-textarea {
    border: none;
    border-radius: 4px;
    background: none;
    font-size: 1rem;
    width: 100%;
    min-height: 100px;
    padding: 14px 16px;
    outline: none;
    color: rgba(0, 0, 0, 0.87);
    font-family: 'Roboto', sans-serif;
    resize: vertical;
}

/* Responsive Design */
@media (max-width: 768px) {
    .pydantic-form-field-container {
        margin-bottom: 1rem;
    }
    
    .pydantic-field-with-icon {
        gap: 8px;
    }
    
    .pydantic-field-icon {
        font-size: 1.1rem;
        min-width: 20px;
    }
}
</style>'''

    def _get_material_javascript(self) -> str:
        """Return self-contained Material Design JavaScript for form functionality."""
        return '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Pydantic Material Design form functionality
    function initPydanticMaterialForms() {
        // Enhanced form validation and interaction
        const forms = document.querySelectorAll('.pydantic-material-form');
        forms.forEach(form => {
            // Add real-time validation
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    validateField(this);
                });
                
                input.addEventListener('input', function() {
                    // Clear error state on input
                    const container = this.closest('.pydantic-form-field-container');
                    if (container) {
                        container.classList.remove('pydantic-field-error');
                        const errorText = container.querySelector('.pydantic-error-text');
                        if (errorText) {
                            errorText.style.display = 'none';
                        }
                    }
                });
            });
        });
        
        // Field validation function
        function validateField(field) {
            const container = field.closest('.pydantic-form-field-container');
            if (!container) return;
            
            let isValid = true;
            let errorMessage = '';
            
            // Required field validation
            if (field.hasAttribute('required') && !field.value.trim()) {
                isValid = false;
                errorMessage = 'This field is required';
            }
            
            // Email validation
            if (field.type === 'email' && field.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
            }
            
            // Number validation
            if (field.type === 'number' && field.value) {
                const min = field.getAttribute('min');
                const max = field.getAttribute('max');
                const value = parseFloat(field.value);
                
                if (min && value < parseFloat(min)) {
                    isValid = false;
                    errorMessage = `Value must be at least ${min}`;
                } else if (max && value > parseFloat(max)) {
                    isValid = false;
                    errorMessage = `Value must be at most ${max}`;
                }
            }
            
            // Update UI based on validation
            if (isValid) {
                container.classList.remove('pydantic-field-error');
            } else {
                container.classList.add('pydantic-field-error');
                showFieldError(container, errorMessage);
            }
            
            return isValid;
        }
        
        // Show field error
        function showFieldError(container, message) {
            let errorElement = container.querySelector('.pydantic-error-text');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'pydantic-error-text';
                container.appendChild(errorElement);
            }
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        
        // Enhanced checkbox styling
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            if (!checkbox.classList.contains('pydantic-checkbox')) {
                checkbox.classList.add('pydantic-checkbox');
            }
        });
        
        // Form submission validation
        const submitButtons = document.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const form = this.closest('form');
                if (form) {
                    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
                    let formValid = true;
                    
                    inputs.forEach(input => {
                        if (!validateField(input)) {
                            formValid = false;
                        }
                    });
                    
                    if (!formValid) {
                        e.preventDefault();
                        // Scroll to first error
                        const firstError = form.querySelector('.pydantic-field-error');
                        if (firstError) {
                            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }
            });
        });
    }
    
    // Initialize forms
    initPydanticMaterialForms();
    
    // Re-initialize for dynamically added content
    window.pydanticReinitMaterial = initPydanticMaterialForms;
});
</script>'''

    def _render_material_global_errors(self, errors: List[str]) -> str:
        """Render global form errors."""
        error_list = '\n'.join([f'<li>{escape(error)}</li>' for error in errors])
        return f'''
        <div class="pydantic-global-errors">
            <strong>Please correct the following errors:</strong>
            <ul>
                {error_list}
            </ul>
        </div>'''

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
        
        # Add model list JavaScript if any model_list fields were rendered
        if self._has_model_list_fields(schema):
            from .model_list import ModelListRenderer
            list_renderer = ModelListRenderer(framework="material")
            form_parts.append(list_renderer.get_model_list_javascript())

        return '\n'.join(form_parts)
    
    def _has_model_list_fields(self, schema: Dict[str, Any]) -> bool:
        """Check if the schema contains any model_list fields."""
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            ui_info = field_schema.get("ui", {}) or field_schema
            ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
            if ui_element == "model_list":
                return True
        return False

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
        if ui_element == "model_list":
            return self._render_material_model_list(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        elif ui_element in ["text", "email", "password", "search", "tel", "url"]:
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

        # Icon support - simplified for side-by-side layout
        icon = ui_info.get("icon", "")
        leading_icon = ""
        if icon:
            if icon.startswith("material-icons"):
                icon_name = icon.replace("material-icons ", "")
                leading_icon = f'<span class="material-icons">{icon_name}</span>'
            elif icon.startswith("bi bi-"):
                icon_name = icon.replace("bi bi-", "")
                leading_icon = f'<i class="bi bi-{icon_name}"></i>'

        # Value handling
        value_attr = f'value="{escape(str(value))}"' if value is not None else ''

        # Placeholder
        placeholder = ui_info.get("placeholder", "")
        placeholder_attr = f'placeholder="{escape(placeholder)}"' if placeholder else ''

        # Error state
        error_class = " mdc-text-field--invalid" if error else ""
        error_aria = f'aria-describedby="{field_name}-error"' if error else ""

        # Build the Material text field with icon positioned to the left
        if leading_icon:
            # Layout with icon on the left side
            html = f'''
        <div class="pydantic-form-field-container">
            <div class="pydantic-field-with-icon">
                <div class="pydantic-field-icon">
                    {leading_icon}
                </div>
                <div class="pydantic-field-input-wrapper">
                    <div class="pydantic-text-field pydantic-text-field--outlined{error_class}">
                        <input type="{input_type}"
                               id="{field_name}"
                               name="{field_name}"
                               class="pydantic-text-field__input"
                               {value_attr}
                               {placeholder_attr}
                               {error_aria}
                               {' '.join(attrs)}>
                        <div class="pydantic-notched-outline">
                            <div class="pydantic-notched-outline__leading"></div>
                            <div class="pydantic-notched-outline__notch">
                                <label class="pydantic-floating-label" for="{field_name}">{escape(label)}{' *' if is_required else ''}</label>
                            </div>
                            <div class="pydantic-notched-outline__trailing"></div>
                        </div>
                    </div>
                </div>
            </div>'''
        else:
            # Standard layout without icon
            html = f'''
        <div class="pydantic-form-field-container">
            <div class="pydantic-text-field pydantic-text-field--outlined{error_class}">
                <input type="{input_type}"
                       id="{field_name}"
                       name="{field_name}"
                       class="pydantic-text-field__input"
                       {value_attr}
                       {placeholder_attr}
                       {error_aria}
                       {' '.join(attrs)}>
                <div class="pydantic-notched-outline">
                    <div class="pydantic-notched-outline__leading"></div>
                    <div class="pydantic-notched-outline__notch">
                        <label class="pydantic-floating-label" for="{field_name}">{escape(label)}{' *' if is_required else ''}</label>
                    </div>
                    <div class="pydantic-notched-outline__trailing"></div>
                </div>
            </div>'''

        # Add help text
        if help_text:
            html += f'''
            <div class="pydantic-helper-text">
                {escape(help_text)}
            </div>'''

        # Add error message
        if error:
            html += f'''
            <div class="pydantic-helper-text pydantic-helper-text--error">
                {escape(error)}
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
        # Only add placeholder option if no default value and not required
        if not is_required and (value is None or str(value) == ""):
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
        
        # Check if select has a value to set initial floating label state
        has_value = value is not None and str(value) != "" and str(value) != "None"
        floating_class = " mdc-floating-label--float-above" if has_value else ""

        html = f'''
        <div class="mdc-form-field-container">
            <div class="mdc-select mdc-select--filled{error_class}">
                <div class="mdc-select__anchor">
                    <span class="mdc-select__ripple"></span>
                    <select id="{field_name}"
                           name="{field_name}"
                           class="mdc-select__native-control"
                           aria-labelledby="{field_name}-label"
                           {'required' if is_required else ''}>
                        {options_html}
                    </select>
                    <span class="mdc-floating-label{floating_class}" id="{field_name}-label">{escape(label)}{' *' if is_required else ''}</span>
                    <span class="mdc-line-ripple"></span>
                </div>
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

    def _render_material_model_list(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render Material Design 3 model list field."""
        
        from .model_list import ModelListRenderer
        
        list_renderer = ModelListRenderer(framework="material")
        model_class = ui_info.get("model_class")
        
        if not model_class:
            return f'<!-- Error: model_class not specified for model_list field "{field_name}" -->'
        
        # Convert value to list of dicts if needed
        list_values = []
        if value:
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, 'model_dump'):
                        list_values.append(item.model_dump())
                    elif isinstance(item, dict):
                        list_values.append(item)
            elif hasattr(value, 'model_dump'):
                list_values = [value.model_dump()]
            elif isinstance(value, dict):
                list_values = [value]
        
        return list_renderer.render_model_list(
            field_name=field_name,
            label=label,
            model_class=model_class,
            values=list_values,
            error=error,
            help_text=help_text,
            is_required=is_required,
            min_items=ui_info.get('min_items', 0),
            max_items=ui_info.get('max_items', 10)
        )
    
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
        """Render self-contained Material Design submit button."""
        return '''
        <div class="pydantic-form-field-container">
            <button type="submit" class="pydantic-submit-button">
                Submit
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
                const floatingLabel = select.querySelector('.mdc-floating-label');

                // Force check initial state on page load
                setTimeout(() => {
                    if (selectInput.value && selectInput.value !== '') {
                        select.classList.add('mdc-select--activated');
                        if (floatingLabel) {
                            floatingLabel.classList.add('mdc-floating-label--float-above');
                        }
                    }
                }, 0);

                selectInput.addEventListener('focus', () => {
                    select.classList.add('mdc-select--focused');
                    if (floatingLabel) {
                        floatingLabel.classList.add('mdc-floating-label--float-above');
                    }
                });

                selectInput.addEventListener('blur', () => {
                    select.classList.remove('mdc-select--focused');
                    if (!selectInput.value || selectInput.value === '') {
                        if (floatingLabel) {
                            floatingLabel.classList.remove('mdc-floating-label--float-above');
                        }
                    }
                });

                selectInput.addEventListener('change', () => {
                    if (selectInput.value && selectInput.value !== '') {
                        select.classList.add('mdc-select--activated');
                        if (floatingLabel) {
                            floatingLabel.classList.add('mdc-floating-label--float-above');
                        }
                    } else {
                        select.classList.remove('mdc-select--activated');
                        if (floatingLabel) {
                            floatingLabel.classList.remove('mdc-floating-label--float-above');
                        }
                    }
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

            // Handle select floating labels
            const selects = document.querySelectorAll('.mdc-select__native-control');
            selects.forEach(select => {
                const selectContainer = select.closest('.mdc-select');
                const floatingLabel = selectContainer?.querySelector('.mdc-floating-label');
                
                // Check if select has value on load
                if (select.value && select.value !== '' && floatingLabel) {
                    floatingLabel.classList.add('mdc-floating-label--float-above');
                }

                select.addEventListener('change', () => {
                    if (select.value && select.value !== '' && floatingLabel) {
                        floatingLabel.classList.add('mdc-floating-label--float-above');
                    } else if (floatingLabel) {
                        floatingLabel.classList.remove('mdc-floating-label--float-above');
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


import asyncio


async def render_material_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Dict[str, str]] = None,
    layout: str = "vertical",
    include_css: bool = True,
    include_js: bool = True,
    **kwargs,
) -> str:
    """
    Async version of render_material_form_html for high-performance applications.

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
    # For CPU-bound rendering, run in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        render_material_form_html,
        form_model_cls,
        form_data,
        errors,
        layout,
        include_css,
        include_js,
        **kwargs
    )
