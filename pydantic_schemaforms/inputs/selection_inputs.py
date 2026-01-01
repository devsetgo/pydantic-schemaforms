"""
Selection input components using Python 3.14 template strings.
Includes SelectInput, RadioGroup, CheckboxInput, and multi-select components.
"""

from html import escape
from string import Template
from typing import Any, Dict, List, Optional

from .base import FormInput, SelectInputBase


class SelectInput(SelectInputBase):
    """Dropdown select input with support for single and multiple selection."""

    ui_element = "select"

    template = """<select ${attributes}>${options}</select>"""

    valid_attributes = SelectInputBase.valid_attributes + ["size", "multiple", "autofocus"]

    def get_input_type(self) -> str:
        return "select"

    def render(self, options: List[Dict[str, Any]], **kwargs) -> str:
        """Render select input with provided options."""
        # Build options HTML
        options_html = self._build_options(options)

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)

        # Don't include type attribute for select
        if "type" in attrs:
            del attrs["type"]

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use template substitution
        try:
            return Template(self.template).substitute(attributes=attributes_str, options=options_html)
        except Exception:
            # Fallback rendering
            return f"<select {attributes_str}>{options_html}</select>"

    def _build_options(self, options: List[Dict[str, Any]]) -> str:
        """Build HTML options from list of option dictionaries."""
        option_parts = []

        for option in options:
            if isinstance(option, dict):
                value = option.get("value", "")
                label = option.get("label", str(value))
                selected = option.get("selected", False)
                disabled = option.get("disabled", False)

                attrs = [f'value="{escape(str(value))}"']

                if selected:
                    attrs.append("selected")
                if disabled:
                    attrs.append("disabled")

                attrs_str = " ".join(attrs)
                option_parts.append(f"<option {attrs_str}>{escape(label)}</option>")
            else:
                # Simple string option
                option_parts.append(
                    f'<option value="{escape(str(option))}">{escape(str(option))}</option>'
                )

        return "\n".join(option_parts)


class MultiSelectInput(SelectInput):
    """Multi-select dropdown with enhanced functionality."""

    ui_element = "multiselect"

    def render(self, options: List[Dict[str, Any]], **kwargs) -> str:
        """Render multi-select with multiple attribute set."""
        kwargs["multiple"] = True
        return super().render(options, **kwargs)


class CheckboxInput(FormInput):
    """Single checkbox input."""

    ui_element = "checkbox"

    template = """<input type="checkbox" ${attributes} />"""

    valid_attributes = FormInput.valid_attributes + ["checked", "value"]

    def get_input_type(self) -> str:
        return "checkbox"

    def render(self, label: Optional[str] = None, **kwargs) -> str:
        """Render checkbox with optional label."""
        # Set default value if not provided
        if "value" not in kwargs:
            kwargs["value"] = "1"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render checkbox
        checkbox_html = f"<input {attributes_str} />"

        if label:
            field_name = kwargs.get("name", "")
            field_id = kwargs.get("id", field_name)
            checkbox_html = f'<label for="{field_id}">{checkbox_html} {escape(label)}</label>'

        return checkbox_html


class CheckboxGroup(SelectInputBase):
    """Group of checkbox inputs for multiple selections."""

    template = """<fieldset class="checkbox-group" ${fieldset_attributes}>
    <legend>${legend}</legend>
    ${checkboxes}
</fieldset>"""

    def get_input_type(self) -> str:
        return "checkbox-group"

    def render(
        self, options: List[Dict[str, Any]], group_name: str, legend: Optional[str] = None, **kwargs
    ) -> str:
        """Render group of checkboxes."""
        checkboxes = []

        for i, option in enumerate(options):
            value = option.get("value", "")
            label = option.get("label", str(value))
            checked = option.get("checked", False)
            disabled = option.get("disabled", False)

            checkbox_id = f"{group_name}_{i}"
            checkbox_attrs = {
                "type": "checkbox",
                "name": group_name,
                "id": checkbox_id,
                "value": value,
            }

            if checked:
                checkbox_attrs["checked"] = True
            if disabled:
                checkbox_attrs["disabled"] = True

            # Add any additional attributes from kwargs
            for attr in ["class", "style"]:
                if attr in kwargs:
                    checkbox_attrs[attr] = kwargs[attr]

            checkbox_input = CheckboxInput()
            checkbox_html = checkbox_input.render(**checkbox_attrs)

            # Wrap in label
            checkbox_item = f"""
            <div class="checkbox-item">
                <label for="{checkbox_id}">
                    {checkbox_html}
                    <span class="checkbox-label">{escape(label)}</span>
                </label>
            </div>
            """
            checkboxes.append(checkbox_item)

        # Build fieldset attributes
        fieldset_attrs = {}
        for attr in ["class", "style", "disabled"]:
            if attr in kwargs:
                fieldset_attrs[attr] = kwargs[attr]

        fieldset_attributes_str = self._build_attributes_string(fieldset_attrs)
        checkboxes_html = "\n".join(checkboxes)
        legend_text = legend or group_name.replace("_", " ").title()

        try:
            return Template(self.template).substitute(
                fieldset_attributes=fieldset_attributes_str,
                legend=escape(legend_text),
                checkboxes=checkboxes_html,
            )
        except Exception:
            # Fallback rendering
            return f"""
            <fieldset class="checkbox-group" {fieldset_attributes_str}>
                <legend>{escape(legend_text)}</legend>
                {checkboxes_html}
            </fieldset>
            """


class RadioInput(FormInput):
    """Single radio button input."""

    template = """<input type="radio" ${attributes} />"""

    valid_attributes = FormInput.valid_attributes + ["checked", "value"]

    def get_input_type(self) -> str:
        return "radio"

    def render(self, **kwargs) -> str:
        """Render a radio input element."""

        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()
        attributes_str = self._build_attributes_string(attrs)
        return f"<input {attributes_str} />"


class RadioGroup(SelectInputBase):
    """Group of radio button inputs for single selection."""

    ui_element = "radio"

    template = """<fieldset class="radio-group" ${fieldset_attributes}>
    <legend>${legend}</legend>
    ${radio_buttons}
</fieldset>"""

    def get_input_type(self) -> str:
        return "radio-group"

    def render(
        self, options: List[Dict[str, Any]], group_name: str, legend: Optional[str] = None, **kwargs
    ) -> str:
        """Render group of radio buttons."""
        radio_buttons = []

        for i, option in enumerate(options):
            value = option.get("value", "")
            label = option.get("label", str(value))
            checked = option.get("checked", False)
            disabled = option.get("disabled", False)

            radio_id = f"{group_name}_{i}"
            radio_attrs = {"type": "radio", "name": group_name, "id": radio_id, "value": value}

            if checked:
                radio_attrs["checked"] = True
            if disabled:
                radio_attrs["disabled"] = True

            # Add any additional attributes from kwargs
            for attr in ["class", "style"]:
                if attr in kwargs:
                    radio_attrs[attr] = kwargs[attr]

            radio_input = RadioInput()
            radio_html = radio_input.render(**radio_attrs)

            # Wrap in label
            radio_item = f"""
            <div class="radio-item">
                <label for="{radio_id}">
                    {radio_html}
                    <span class="radio-label">{escape(label)}</span>
                </label>
            </div>
            """
            radio_buttons.append(radio_item)

        # Build fieldset attributes
        fieldset_attrs = {}
        for attr in ["class", "style", "disabled"]:
            if attr in kwargs:
                fieldset_attrs[attr] = kwargs[attr]

        fieldset_attributes_str = self._build_attributes_string(fieldset_attrs)
        radio_buttons_html = "\n".join(radio_buttons)
        legend_text = legend or group_name.replace("_", " ").title()

        try:
            return Template(self.template).substitute(
                fieldset_attributes=fieldset_attributes_str,
                legend=escape(legend_text),
                radio_buttons=radio_buttons_html,
            )
        except Exception:
            # Fallback rendering
            return f"""
            <fieldset class="radio-group" {fieldset_attributes_str}>
                <legend>{escape(legend_text)}</legend>
                {radio_buttons_html}
            </fieldset>
            """


class ToggleSwitch(CheckboxInput):
    """Toggle switch styled as a modern switch instead of checkbox."""

    ui_element = "toggle"
    ui_element_aliases = ("toggle_switch", "checkbox_toggle")

    def render(self, **kwargs) -> str:
        """Render toggle switch with custom styling."""
        # Add toggle-specific classes
        current_class = kwargs.get("class", "")
        kwargs["class"] = f"{current_class} toggle-switch".strip()

        # Add toggle switch wrapper
        field_name = kwargs.get("name", "")
        field_id = kwargs.get("id", field_name)
        label = kwargs.pop("label", None)

        checkbox_html = super().render(**kwargs)

        toggle_html = f"""
        <div class="toggle-switch-wrapper">
            {checkbox_html}
            <label for="{field_id}" class="toggle-switch-label">
                <span class="toggle-switch-slider"></span>
                {f'<span class="toggle-switch-text">{escape(label)}</span>' if label else ''}
            </label>
        </div>
        """

        return toggle_html


class ComboBoxInput(SelectInput):
    """Combo box input that combines text input with dropdown selection."""

    ui_element = "combobox"

    template = """<div class="combobox-wrapper">
    <input type="text" ${input_attributes} list="${datalist_id}" />
    <datalist id="${datalist_id}">
        ${options}
    </datalist>
</div>"""

    def render(self, options: List[Dict[str, Any]], **kwargs) -> str:
        """Render combo box with datalist."""
        field_name = kwargs.get("name", "")
        datalist_id = f"{field_name}_datalist"

        # Build options for datalist
        options_html = ""
        for option in options:
            if isinstance(option, dict):
                value = option.get("value", "")
                label = option.get("label", str(value))
                options_html += f'<option value="{escape(str(value))}">{escape(label)}</option>\n'
            else:
                options_html += f'<option value="{escape(str(option))}"></option>\n'

        # Build input attributes
        input_attrs = self.validate_attributes(**kwargs)
        if "type" in input_attrs:
            del input_attrs["type"]
        input_attributes_str = self._build_attributes_string(input_attrs)

        try:
            return Template(self.template).substitute(
                input_attributes=input_attributes_str, datalist_id=datalist_id, options=options_html
            )
        except Exception:
            # Fallback rendering
            return f"""
            <div class="combobox-wrapper">
                <input type="text" {input_attributes_str} list="{datalist_id}" />
                <datalist id="{datalist_id}">
                    {options_html}
                </datalist>
            </div>
            """
