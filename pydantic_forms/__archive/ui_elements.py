"""
create ui HTML elements for UI Schema using t strings
Pep-750 https://peps.python.org/pep-0750/
there should be a check to ensure only UI elements that are valid for the schema type are used

from pep_750 import t  # hypothetical future import for t strings

HTML Input Attribute Reference
-----------------------------

| Attribute    | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| checked      | Specifies that an input field should be pre-selected (checkbox/radio)       |
| disabled     | Specifies that an input field should be disabled                            |
| max          | Specifies the maximum value for an input field                              |
| maxlength    | Specifies the maximum number of characters for an input field               |
| min          | Specifies the minimum value for an input field                              |
| minlength    | Specifies the minimum number of characters for an input field               |
| multiple     | Specifies that the user is allowed to enter more than one value             |
| pattern      | Specifies a regular expression to check the input value against             |
| placeholder  | Specifies a short hint that describes the expected value of an input field  |
| readonly     | Specifies that an input field is read only (cannot be changed)              |
| required     | Specifies that an input field must be filled out before submitting          |
| size         | Specifies the width (in characters) of an input field                       |
| step         | Specifies the legal number intervals for an input field                     |
| value        | Specifies the default value for an input field                              |
| autocomplete | Specifies whether an input field should have autocomplete enabled           |
| accept       | Specifies the types of files that the server accepts (file input)           |
| rows         | Specifies the visible number of lines in a text area                        |
| cols         | Specifies the visible width of a text area                                  |
| class        | Specifies one or more class names for an element                            |
| style        | Specifies an inline CSS style for an element                                |
| id           | Specifies a unique id for an element                                        |
| name         | Specifies the name of an input element                                      |


Design Pattern to Follow for All UI Elements
1. Define a class for each UI element (e.g., TextInput, PasswordInput, etc.).
2. Each class should have a `template` attribute that contains the HTML structure of the element.
3. The `render` method should accept keyword arguments for all the attributes that can be set on the element.
4. The `render` method should format the template with the provided attributes, ensuring that only valid attributes are included.
5. The `render` method should return the final HTML string.


"""

from collections import namedtuple


# Add this at the top of the file, before any class definitions, to ensure t() is always available.
def t(template: str) -> str:
    # This is a no-op fallback for Python <3.14, but in 3.14+ the t-string syntax will be native.
    return template


Option = namedtuple("Option", ["value", "label", "selected"])


class TextInput:
    """
    Represents a text input element.
    Required: name, id_
    Optional: required, placeholder, pattern, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """

    template = t(
        """<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}" {required}{placeholder}{pattern}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        # Only include attributes if present and not None/empty
        attrs = {
            "placeholder": (
                f' placeholder="{kwargs["placeholder"]}"' if kwargs.get("placeholder") else ""
            ),
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'

        # Add required indicator if needed
        return add_required_indicator(html, kwargs.get("required"))


class TextArea:
    """
    Represents a text area element.
    Required: name, id_
    Optional: required, placeholder, maxlength, minlength, readonly, disabled, rows, cols, autocomplete, value, class_, style
    """

    template = t(
        """<textarea name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{placeholder}{maxlength}{minlength}{readonly}{disabled}{rows}{cols}{autocomplete}>{value}</textarea>"""
    )

    def render(self, **kwargs):
        attrs = {
            "placeholder": (
                f' placeholder="{kwargs["placeholder"]}"' if kwargs.get("placeholder") else ""
            ),
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "rows": f' rows="{kwargs["rows"]}"' if kwargs.get("rows") else "",
            "cols": f' cols="{kwargs["cols"]}"' if kwargs.get("cols") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "value": kwargs.get("value", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class PasswordInput:
    """
    Represents a password input element.
    Required: name, id_
    Optional: required, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """

    template = t(
        """<input type="password" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class EmailInput:
    """
    Represents an email input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """

    template = t(
        """<input type="email" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class NumberInput:
    """
    Represents a number input element.
    Required: name, id_
    Optional: required, min, max, step, readonly, disabled, value, autocomplete, class_, style
    """

    template = t(
        """<input type="number" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{step}{readonly}{disabled}{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") is not None else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") is not None else "",
            "step": f' step="{kwargs["step"]}"' if kwargs.get("step") is not None else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") is not None else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class CheckboxInput:
    """
    Represents a checkbox input element.
    Required: name, id_
    Optional: required, checked, disabled, value, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="checkbox" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{checked}{disabled}{value}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "checked": " checked" if kwargs.get("checked") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class RadioInput:
    """
    Represents a single radio input element.
    NOTE: For most UI use cases, use RadioGroup instead of RadioInput directly.
    RadioInput is intended for internal use by RadioGroup.
    Required: group_name, value, id_
    Optional: required, checked, disabled, readonly, autocomplete, class_, style, label
    """

    template = t(
        """<input type="radio" name="{group_name}" value="{value}" id="{id_}" class="{class_}" style="{style}"{required}{checked}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "checked": " checked" if kwargs.get("checked") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "group_name": kwargs.get("group_name", ""),
            "value": kwargs.get("value", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["value"].replace("_", " ").capitalize() if attrs["value"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class RadioGroup:
    """
    Represents a group of radio input elements with a group label.
    Required: group_name, options (list of dicts with value, label, checked)
    Optional: id_prefix, class_, style, group_label, direction ('horizontal' or 'vertical'),
              required (when true, at least one radio must be selected)
    """

    def render(self, **kwargs):
        group_name = kwargs.get("group_name", "")
        options = kwargs.get("options", [])
        id_prefix = kwargs.get("id_prefix", group_name)
        # Remove 'form-check' from the outer container for consistency with other inputs
        style = kwargs.get("style", "")
        group_label = kwargs.get("group_label")
        direction = kwargs.get("direction", "horizontal")  # default to horizontal
        # Get required status - this needs to be applied to only one radio in the group
        required = kwargs.get("required", False)

        if not group_label:
            group_label = group_name.replace("_", " ").capitalize() if group_name else ""

        # Set flex direction for alignment
        flex_direction = "row" if direction == "horizontal" else "column"
        radios = []

        # Apply 'required' only to the first radio button in the group
        # This is how HTML validation works for radio groups - only one needs the attribute
        for idx, opt in enumerate(options):
            value = opt.get("value", "")
            label = opt.get("label", value.capitalize())
            checked = opt.get("checked", False)
            id_ = f"{id_prefix}_{value or idx}"

            # Only apply required to first button in the group
            is_required = required and idx == 0

            radios.append(
                f'<div class="form-check" style="margin-right: 1em;">'
                f'{RadioInput().render(group_name=group_name, value=value, id_=id_, class_="", style="", checked=checked, label=label, required=is_required)}'
                f"</div>"
            )
        radios_html = "\n".join(radios)

        # Add a hidden field to show validation message for the group
        validation_html = ""
        if required:
            validation_html = (
                f'<span class="invalid-feedback" style="display: none;">'
                f"Please select one of the options for {group_label}."
                f"</span>"
            )

        # Wrap everything in a container that uses Bootstrap spacing classes for proper alignment.
        return (
            f'<div class="mb-3" style="{style}">'
            f'<label class="form-label" style="display:block; text-align:left; margin-bottom:0.5em;">{group_label}</label>'
            f'<div style="display: flex; flex-direction: {flex_direction}; justify-content: flex-start;">{radios_html}</div>'
            f"{validation_html}"
            f"</div>"
        )


class SelectInput:
    """
    Represents a select input element.
    Required: name, id_, options
    Optional: required, disabled, multiple, size, autocomplete, class_, style, option_list, option_dict
    """

    template = t(
        """<select name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{disabled}{multiple}{size}{autocomplete}>{options}</select>"""
    )

    def render(self, **kwargs):
        # Support: 'options' (raw HTML), 'option_list' (list of (value, label, selected?)),
        # 'option_dict' (dict of value: label), or 'option_named' (list of Option namedtuples or dicts)
        options_html = kwargs.get("options", "")
        option_list = kwargs.get("option_list")
        option_dict = kwargs.get("option_dict")
        option_named = kwargs.get("option_named")
        if option_dict:
            options_html = ""
            for value, label in option_dict.items():
                options_html += f'<option value="{value}">{label}</option>'
        elif option_named:
            options_html = ""
            for opt in option_named:
                # Accept either namedtuple or dict
                if isinstance(opt, dict):
                    value = opt.get("value")
                    label = opt.get("label")
                    selected = opt.get("selected", False)
                else:
                    value = getattr(opt, "value", None)
                    label = getattr(opt, "label", None)
                    selected = getattr(opt, "selected", False)
                sel = " selected" if selected else ""
                options_html += f'<option value="{value}"{sel}>{label}</option>'
        elif option_list:
            options_html = ""
            for opt in option_list:
                value, label = opt[0], opt[1]
                selected = " selected" if len(opt) > 2 and opt[2] else ""
                options_html += f'<option value="{value}"{selected}>{label}</option>'
        attrs = {
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "multiple": " multiple" if kwargs.get("multiple") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "options": options_html,
        }
        label = kwargs.get("label")
        if not label:
            # Always create a label if not provided
            label = kwargs.get("name", "")
            label = label.replace("_", " ").capitalize() if label else ""
        html = self.template.format(**attrs)
        # --- FIX: Only add label if attrs["id_"] is not empty ---
        if attrs["id_"]:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        else:
            html = f"<label>{label}</label> {html}"
        return add_required_indicator(html, kwargs.get("required"))


class DateInput:
    """
    Represents a date input element.
    Required: name, id_
    Optional: required, min, max, readonly, disabled, value, autocomplete, class_, style
    """

    template = t(
        """<input type="date" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{readonly}{disabled}{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class DatetimeInput:
    """
    Represents a datetime input element.
    Required: name, id_
    Optional: required, min, max, readonly, disabled, value, autocomplete, class_, style, use_current (set to True to default to current datetime), with_set_now_button (adds a button to set to current datetime)
    """

    template = t(
        """<input type="datetime-local" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{readonly}{disabled}{value}{autocomplete} />"""
    )

    template_with_button = t(
        """<div style="display: flex; align-items: center; gap: 10px;">
    <input type="datetime-local" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{readonly}{disabled}{value}{autocomplete} />
    <button type="button" onclick="setDatetimeToNow('{id_}')" class="btn btn-sm btn-secondary">Now</button>
    <script>
    function setDatetimeToNow(inputId) {{
        const input = document.getElementById(inputId);
        if (input) {{
            const now = new Date();
            // Format: YYYY-MM-DDThh:mm
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            input.value = `${{year}}-${{month}}-${{day}}T${{hours}}:${{minutes}}`;
        }}
    }}
    {auto_set}
    </script>
    </div>"""
    )

    def render(self, **kwargs):
        # Check if we should use current datetime as default value
        use_current = kwargs.get("use_current", False)
        if use_current and not kwargs.get("value"):
            from datetime import datetime

            # Format datetime as expected by datetime-local input: YYYY-MM-DDThh:mm
            current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M")
            kwargs["value"] = current_datetime

        # Prepare attributes for the input
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }

        # Get label
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""

        # Check if we should add a "Set to Now" button
        with_set_now_button = kwargs.get("with_set_now_button", False)

        # Auto-set script for initial value
        auto_set = ""
        if kwargs.get("auto_set_on_load", False):
            auto_set = f"document.addEventListener('DOMContentLoaded', function() {{ setDatetimeToNow('{attrs['id_']}'); }});"

        # Render the HTML
        if with_set_now_button:
            attrs["auto_set"] = auto_set
            html = self.template_with_button.format(**attrs)
        else:
            html = self.template.format(**attrs)

        # Add label
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class FileInput:
    """
    Represents a file input element.
    Required: name, id_
    Optional: required, accept, multiple, disabled, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="file" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{accept}{multiple}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "accept": f' accept="{kwargs["accept"]}"' if kwargs.get("accept") else "",
            "multiple": " multiple" if kwargs.get("multiple") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class ColorInput:
    """
    Represents a color input element.
    Required: name, id_
    Optional: required, value, disabled, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="color" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{value}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class RangeInput:
    """
    Represents a range input element.
    Required: name, id_
    Optional: required, min, max, step, value, disabled, readonly, autocomplete, class_, style
             track_color, thumb_color, track_height
    """

    template = t(
        """<div class="range-input-container" style="margin-bottom: 10px;">
    <input type="range" name="{name}" id="{id_}" class="{class_}" style="width: 100%; height: {track_height}px; {style}"
     {required}{min}{max}{step}{value}{disabled}{readonly}{autocomplete} />
    <div class="range-value-display" style="text-align: center; margin-top: 5px;">
        <output for="{id_}" id="{id_}_value">{display_value}</output>
    </div>
    <style>
        /* Custom styling for this specific range input */
        #{id_} {
            -webkit-appearance: none; /* Override default appearance */
            background: transparent; /* Make background transparent to show our custom track */
            cursor: pointer;
        }

        /* Track styles - the line the thumb slides on */
        #{id_}::-webkit-slider-runnable-track {
            height: {track_height}px;
            background: {track_color};
            border-radius: 4px;
        }
        #{id_}::-moz-range-track {
            height: {track_height}px;
            background: {track_color};
            border-radius: 4px;
        }

        /* Thumb styles - the draggable handle */
        #{id_}::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: {thumb_size}px;
            height: {thumb_size}px;
            background: {thumb_color};
            border-radius: 50%;
            border: 2px solid white;
            margin-top: -{thumb_offset}px; /* Center the thumb on the track */
        }
        #{id_}::-moz-range-thumb {
            width: {thumb_size}px;
            height: {thumb_size}px;
            background: {thumb_color};
            border-radius: 50%;
            border: 2px solid white;
        }

        /* Focus styles */
        #{id_}:focus {
            outline: none;
        }
        #{id_}:focus::-webkit-slider-runnable-track {
            background: {track_focus_color};
        }
        #{id_}:focus::-moz-range-track {
            background: {track_focus_color};
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const slider = document.getElementById('{id_}');
            const output = document.getElementById('{id_}_value');

            // Update the output value when the page loads
            if (slider && output) {{
                output.textContent = slider.value;

                // Update the output value when the slider is moved
                slider.oninput = function() {{
                    output.textContent = this.value;
                }}
            }}
        }});
    </script>
</div>"""
    )

    def render(self, **kwargs):
        # Add new color customization parameters with defaults
        track_color = kwargs.get("track_color", "#d3d3d3")  # Default light gray track
        thumb_color = kwargs.get("thumb_color", "#0d6efd")  # Default Bootstrap primary blue thumb
        track_focus_color = kwargs.get(
            "track_focus_color", "#c0c0c0"
        )  # Slightly darker when focused
        track_height = kwargs.get("track_height", 6)  # Default track height in pixels
        thumb_size = kwargs.get("thumb_size", 18)  # Default thumb size in pixels
        thumb_offset = (thumb_size - track_height) / 2  # Calculate offset to center thumb

        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") is not None else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") is not None else "",
            "step": f' step="{kwargs["step"]}"' if kwargs.get("step") is not None else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") is not None else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", "form-range"),  # Default to Bootstrap's form-range
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "display_value": kwargs.get("value", 0),  # Add the current value for display
            "track_color": track_color,
            "thumb_color": thumb_color,
            "track_focus_color": track_focus_color,
            "track_height": track_height,
            "thumb_size": thumb_size,
            "thumb_offset": thumb_offset,
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""

        # Double all curly braces in the template for proper escaping
        escaped_template = self.template.replace("{", "{{").replace("}", "}}")
        # Restore named placeholders
        for key in attrs:
            escaped_template = escaped_template.replace(f"{{{{{key}}}}}", f"{{{key}}}")

        html = escaped_template.format(**attrs)
        return f'<label for="{attrs["id_"]}" style="display: block; margin-bottom: 5px;">{label}</label>{html}'


class HiddenInput:
    """
    Represents a hidden input element.
    Required: name, id_
    Optional: value, autocomplete, class_, style
    """

    template = t(
        """<input type="hidden" name="{name}" id="{id_}" class="{class_}" style="{style}"{value}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        # Hidden inputs typically do not have labels
        return self.template.format(**attrs)


class SSNInput:
    """
    Represents a social security number input element.
    Required: name, id_
    Optional: required, value, disabled, readonly, autocomplete, class_, style

    Shows a masked SSN in the UI, but submits the masked value with dashes via a hidden input.
    """

    template = t(
        """<div class="{class_}" style="{style}">
    <label for="{id_}_masked">{label}</label>
    <div class="input-group">
        <input type="text" id="{id_}_masked" class="form-control" inputmode="numeric" value="{initial_value}" />
        <input type="hidden" name="{name}" id="{id_}" />
    </div>

    <script src="https://unpkg.com/imask"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function () {{
        let maskedEl = document.getElementById('{id_}_masked');
        let hiddenEl = document.getElementById('{id_}');
        if (maskedEl && hiddenEl) {{
            // Always use the original value attribute, not the possibly masked value in the input
            let initial = maskedEl.getAttribute('value') ? maskedEl.getAttribute('value').replace(/\\D/g, '') : '';
            let mask = IMask(maskedEl, {{
                mask: 'XXX-XX-0000',
                definitions: {{
                    X: {{
                        mask: '0',
                        displayChar: 'X',
                        placeholderChar: 'X'
                    }}
                }}
            }});
            mask.value = initial;
            hiddenEl.value = mask.value;
            mask.on('accept', () => {{
                hiddenEl.value = mask.value;
            }});
        }}
    }});
    </script>
    </div>"""
    )

    def render(self, **kwargs):
        kwargs.get("id_", "")
        label = kwargs.get("label", None)
        if label is None:
            label = kwargs.get("name", "").capitalize() if kwargs.get("name") else ""
        value = kwargs.get("value", "")
        initial_value = value
        attrs = {
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "label": kwargs.get(
                "label", kwargs.get("name", "").capitalize() if kwargs.get("name") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "initial_value": initial_value,
        }
        return self.template.format(**attrs)


class PhoneInput:
    """
    Represents a phone input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style, country_code, mask

    Uses imask.js for phone number masking. Supports custom mask for different countries.
    """

    template = t(
        """<div class="{class_}" style="{style}">
    <label for="{id_}">{label}</label>
    <div class="input-group">
        <input type="text" name="{name}" id="{id_}" class="form-control" inputmode="tel" value="{value}" autocomplete="{autocomplete}" />
    </div>
    <script src="https://unpkg.com/imask"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function () {{
        let phoneEl = document.getElementById('{id_}');
        if (phoneEl) {{
            let initial = phoneEl.getAttribute('value') || '';
            let mask = IMask(phoneEl, {{
                mask: '{mask}'
            }});
            mask.value = initial.replace(/[^\\d+]/g, '');
            phoneEl.value = mask.value;
        }}
    }});
    </script>
    </div>"""
    )

    def render(self, **kwargs):
        id_ = kwargs.get("id_", "")
        label = kwargs.get("label", None)
        if label is None:
            label = kwargs.get("name", "").capitalize() if kwargs.get("name") else ""
        value = kwargs.get("value", "")
        autocomplete = kwargs.get("autocomplete", "tel")
        # Default to US phone mask if not provided
        mask = kwargs.get("mask")
        country_code = kwargs.get("country_code", "+1")
        if not mask:
            if country_code == "+1":
                mask = "+1 (000) 000-0000"
            # Add more country defaults here if desired
            else:
                mask = country_code + " 0000000000"  # fallback, user should override for real use
        attrs = {
            "name": kwargs.get("name", ""),
            "id_": id_,
            "label": label,
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "value": value,
            "autocomplete": autocomplete,
            "mask": mask,
        }
        return self.template.format(**attrs)


class URLInput:
    """
    Represents a URL input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="url" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class CurrencyInput:
    """
    Represents a currency input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


class CreditCardInput:
    """
    Represents a credit card input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style
    """

    template = t(
        """<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />"""
    )

    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": (
                f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else ""
            ),
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label")
        if not label:
            label = attrs["name"].replace("_", " ").capitalize() if attrs["name"] else ""
        html = self.template.format(**attrs)
        html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return add_required_indicator(html, kwargs.get("required"))


def add_required_indicator(input_html, is_required=False):
    """
    Helper function to add a visual required indicator to any form input.
    Adds a red asterisk and ensures validation works consistently.

    Args:
        input_html: The HTML string of the input element
        is_required: Boolean indicating if the input is required

    Returns:
        Updated HTML with required indicator if needed
    """
    if not is_required:
        return input_html

    # Add required indicator (red asterisk) to the label
    # Handle different label positioning scenarios
    if "<label" in input_html and "data-required" not in input_html:
        # Insert required indicator after the label opening tag but before any content
        # Don't modify the label text directly, add an asterisk via CSS with data-required attribute
        html = input_html.replace("<label", '<label data-required="true"', 1)
        return html
    else:
        # For inputs without labels, wrap them
        return f"""
        <div class="form-input required-field">
            {input_html}
            <span class="required-indicator" style="color: red; margin-left: 3px;">*</span>
        </div>
        """


# ...existing code...


if __name__ == "__main__":
    text_input = TextInput()
    print(
        text_input.render(
            name="username",
            id_="username",
            class_="form-control",
            style="width: 100%;",
            required="required",
            placeholder="Enter your username",
        )
    )

    password_input = PasswordInput()
    print(
        password_input.render(
            name="password",
            id_="password",
            class_="form-control",
            style="width: 100%;",
            required="required",
            maxlength=32,
            autocomplete="off",
        )
    )

    email_input = EmailInput()
    print(
        email_input.render(
            name="email",
            id_="email",
            class_="form-control",
            style="width: 100%;",
            required="required",
            placeholder="Enter your email",
            pattern=r"[^@]+@[^@]+\.[^@]+",
        )
    )

    number_input = NumberInput()
    print(
        number_input.render(
            name="age",
            id_="age",
            class_="form-control",
            style="width: 100%;",
            required="required",
            min=0,
            max=120,
            step=1,
            value=30,
        )
    )

    checkbox_input = CheckboxInput()
    print(
        checkbox_input.render(
            name="subscribe",
            id_="subscribe",
            class_="form-check-input",
            style="",
            checked=True,
            value="yes",
        )
    )

    radio_input = RadioInput()
    print(
        radio_input.render(
            group_name="gender",
            value="male",
            id_="gender_male",
            class_="form-check-input",
            checked=True,
        )
    )

    select_input = SelectInput()
    print(
        select_input.render(
            name="country",
            id_="country",
            class_="form-select",
            style="width: 100%;",
            options='<option value="us">United States</option><option value="ca">Canada</option>',
            required="required",
        )
    )

    date_input = DateInput()
    print(
        date_input.render(
            name="birthday",
            id_="birthday",
            class_="form-control",
            style="width: 100%;",
            min="1900-01-01",
            max="2100-12-31",
            value="2000-01-01",
        )
    )

    datetime_input = DatetimeInput()
    print(
        datetime_input.render(
            name="event_time",
            id_="event_time",
            class_="form-control",
            style="width: 100%;",
            required="",
            min="2023-01-01T00:00",
            max="2023-12-31T23:59",
            value="2023-06-15T14:30",
        )
    )

    file_input = FileInput()
    print(
        file_input.render(
            name="resume",
            id_="resume",
            class_="form-control",
            style="",
            required="",
            accept=".pdf,.docx",
            multiple="multiple",
        )
    )

    color_input = ColorInput()
    print(
        color_input.render(
            name="favorite_color",
            id_="favorite_color",
            class_="form-control",
            style="",
            required="",
            value="#ff0000",
        )
    )

    range_input = RangeInput()
    print(
        range_input.render(
            name="volume",
            id_="volume",
            class_="form-range",
            style="",
            required="",
            min=0,
            max=100,
            step=1,
            value=50,
        )
    )

    hidden_input = HiddenInput()
    print(
        hidden_input.render(
            name="secret", id_="secret", class_="form-control", style="", value="hidden_value"
        )
    )

    ssn_input = SSNInput()
    print(
        ssn_input.render(
            name="ssn",
            id_="ssn",
            class_="form-control",
            style="",
            required="",
            value="987-65-4321",
            label="Social Security Number",
        )
    )

    phone_input = PhoneInput()
    print(
        phone_input.render(
            name="phone",
            id_="phone",
            class_="form-control",
            style="",
            required="",
            value="838341551",
            country_code="+353",
        )
    )

    url_input = URLInput()
    print(
        url_input.render(
            name="website",
            id_="website",
            class_="form-control",
            style="",
            required="",
            pattern="https?://.+",
            value="https://example.com",
        )
    )

    currency_input = CurrencyInput()
    print(
        currency_input.render(
            name="amount",
            id_="amount",
            class_="form-control",
            style="",
            required="",
            pattern="^\\$?\\d+(\\.(\\d{2}))?$",
            value="$100.00",
        )
    )

    credit_card_input = CreditCardInput()
    print(
        credit_card_input.render(
            name="ccn",
            id_="ccn",
            class_="form-control",
            style="",
            required="",
            pattern="\\d{16}",
            value="1234567812345678",
        )
    )

    radio_group = RadioGroup()
    print(
        radio_group.render(
            group_name="newsletter",
            options=[
                {"value": "daily", "label": "Daily"},
                {"value": "weekly", "label": "Weekly", "checked": True},
                {"value": "monthly", "label": "Monthly"},
            ],
            class_="form-check",
            style="",
            group_label="Newsletter Frequency",
        )
    )
