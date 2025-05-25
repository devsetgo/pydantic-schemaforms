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

"""
from string.templatelib import Template, Interpolation
import uuid

def t(template: str) -> str:
    return template

# --- FIX: Use t(...) not t... ---
class TextInput:
    """
    Represents a text input element.
    Required: name, id_
    Optional: required, placeholder, pattern, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """
    template = t("""<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}" {required}{placeholder}{pattern}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />""")
    def render(self, **kwargs):
        # Only include attributes if present and not None/empty
        attrs = {
            "placeholder": f' placeholder="{kwargs["placeholder"]}"' if kwargs.get("placeholder") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class TextArea:
    """
    Represents a text area element.
    Required: name, id_
    Optional: required, placeholder, maxlength, minlength, readonly, disabled, rows, cols, autocomplete, value, class_, style
    """
    template = t("""<textarea name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{placeholder}{maxlength}{minlength}{readonly}{disabled}{rows}{cols}{autocomplete}>{value}</textarea>""")
    def render(self, **kwargs):
        attrs = {
            "placeholder": f' placeholder="{kwargs["placeholder"]}"' if kwargs.get("placeholder") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "rows": f' rows="{kwargs["rows"]}"' if kwargs.get("rows") else "",
            "cols": f' cols="{kwargs["cols"]}"' if kwargs.get("cols") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "value": kwargs.get("value", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class PasswordInput:
    """
    Represents a password input element.
    Required: name, id_
    Optional: required, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """
    template = t("""<input type="password" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class EmailInput:
    """
    Represents an email input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, readonly, disabled, size, value, autocomplete, class_, style
    """
    template = t("""<input type="email" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{readonly}{disabled}{size}{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class NumberInput:
    """
    Represents a number input element.
    Required: name, id_
    Optional: required, min, max, step, readonly, disabled, value, autocomplete, class_, style
    """
    template = t("""<input type="number" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{step}{readonly}{disabled}{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") is not None else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") is not None else "",
            "step": f' step="{kwargs["step"]}"' if kwargs.get("step") is not None else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") is not None else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class CheckboxInput:
    """
    Represents a checkbox input element.
    Required: name, id_
    Optional: required, checked, disabled, value, readonly, autocomplete, class_, style
    """
    template = t("""<input type="checkbox" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{checked}{disabled}{value}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "checked": " checked" if kwargs.get("checked") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class RadioInput:
    """
    Represents a radio input element.
    Required: group_name, value, id_
    Optional: required, checked, disabled, readonly, autocomplete, class_, style, label
    """
    template = t("""<input type="radio" name="{group_name}" value="{value}" id="{id_}" class="{class_}" style="{style}"{required}{checked}{disabled}{readonly}{autocomplete} />
<label for="{id_}">{label}</label>""")
    def render(self, **kwargs):
        attrs = {
            "checked": " checked" if kwargs.get("checked") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "group_name": kwargs.get("group_name", ""),
            "value": kwargs.get("value", ""),
            "id_": kwargs.get("id_", ""),
            "label": kwargs.get("label", kwargs.get("value", "").capitalize() if kwargs.get("value") else ""),
        }
        return self.template.format(**attrs)

class SelectInput:
    """
    Represents a select input element.
    Required: name, id_, options
    Optional: required, disabled, multiple, size, autocomplete, class_, style, option_list
    """
    template = t("""<select name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{disabled}{multiple}{size}{autocomplete}>{options}</select>""")
    def render(self, **kwargs):
        # Support both 'options' (raw HTML) and 'option_list' (list of (value, label, selected))
        options_html = kwargs.get("options", "")
        option_list = kwargs.get("option_list")
        if option_list:
            options_html = ""
            for opt in option_list:
                value, label = opt[0], opt[1]
                selected = ' selected' if len(opt) > 2 and opt[2] else ''
                options_html += f'<option value="{value}"{selected}>{label}</option>'
        attrs = {
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "multiple": " multiple" if kwargs.get("multiple") else "",
            "size": f' size="{kwargs["size"]}"' if kwargs.get("size") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "options": options_html,
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class DateInput:
    """
    Represents a date input element.
    Required: name, id_
    Optional: required, min, max, readonly, disabled, value, autocomplete, class_, style
    """
    template = t("""<input type="date" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{readonly}{disabled}{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class DatetimeInput:
    """
    Represents a datetime input element.
    Required: name, id_
    Optional: required, min, max, readonly, disabled, value, autocomplete, class_, style
    """
    template = t("""<input type="datetime-local" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{readonly}{disabled}{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class FileInput:
    """
    Represents a file input element.
    Required: name, id_
    Optional: required, accept, multiple, disabled, readonly, autocomplete, class_, style
    """
    template = t("""<input type="file" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{accept}{multiple}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "accept": f' accept="{kwargs["accept"]}"' if kwargs.get("accept") else "",
            "multiple": " multiple" if kwargs.get("multiple") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "required": " required" if kwargs.get("required") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class ColorInput:
    """
    Represents a color input element.
    Required: name, id_
    Optional: required, value, disabled, readonly, autocomplete, class_, style
    """
    template = t("""<input type="color" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{value}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class RangeInput:
    """
    Represents a range input element.
    Required: name, id_
    Optional: required, min, max, step, value, disabled, readonly, autocomplete, class_, style
    """
    template = t("""<input type="range" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{min}{max}{step}{value}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "min": f' min="{kwargs["min"]}"' if kwargs.get("min") is not None else "",
            "max": f' max="{kwargs["max"]}"' if kwargs.get("max") is not None else "",
            "step": f' step="{kwargs["step"]}"' if kwargs.get("step") is not None else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") is not None else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class HiddenInput:
    """
    Represents a hidden input element.
    Required: name, id_
    Optional: value, autocomplete, class_, style
    """
    template = t("""<input type="hidden" name="{name}" id="{id_}" class="{class_}" style="{style}"{value}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
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
    template = t("""<div class="{class_}" style="{style}">
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
    </div>""")

    def render(self, **kwargs):
        id_ = kwargs.get("id_", "")
        label = kwargs.get("label", None)
        if label is None:
            label = kwargs.get("name", "").capitalize() if kwargs.get("name") else ""
        value = kwargs.get("value", "")
        initial_value = value
        attrs = {
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
            "label": kwargs.get("label", kwargs.get("name", "").capitalize() if kwargs.get("name") else ""),
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
    template = t("""<div class="{class_}" style="{style}">
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
    </div>""")

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
    template = t("""<input type="url" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class CurrencyInput:
    """
    Represents a currency input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style
    """
    template = t("""<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

class CreditCardInput:
    """
    Represents a credit card input element.
    Required: name, id_
    Optional: required, pattern, maxlength, minlength, value, disabled, readonly, autocomplete, class_, style
    """
    template = t("""<input type="text" name="{name}" id="{id_}" class="{class_}" style="{style}"{required}{pattern}{maxlength}{minlength}{value}{disabled}{readonly}{autocomplete} />""")
    def render(self, **kwargs):
        attrs = {
            "required": " required" if kwargs.get("required") else "",
            "pattern": f' pattern="{kwargs["pattern"]}"' if kwargs.get("pattern") else "",
            "maxlength": f' maxlength="{kwargs["maxlength"]}"' if kwargs.get("maxlength") else "",
            "minlength": f' minlength="{kwargs["minlength"]}"' if kwargs.get("minlength") else "",
            "value": f' value="{kwargs["value"]}"' if kwargs.get("value") else "",
            "disabled": " disabled" if kwargs.get("disabled") else "",
            "readonly": " readonly" if kwargs.get("readonly") else "",
            "autocomplete": f' autocomplete="{kwargs["autocomplete"]}"' if kwargs.get("autocomplete") else "",
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "name": kwargs.get("name", ""),
            "id_": kwargs.get("id_", ""),
        }
        label = kwargs.get("label", None)
        html = self.template.format(**attrs)
        if label is None:
            label = attrs["name"].capitalize() if attrs["name"] else ""
        if label:
            html = f'<label for="{attrs["id_"]}">{label}</label> {html}'
        return html

if __name__ == "__main__":
    text_input = TextInput()
    print(text_input.render(name="username", id_="username", class_="form-control", style="width: 100%;", required="required", placeholder="Enter your username"))

    password_input = PasswordInput()
    print(password_input.render(name="password", id_="password", class_="form-control", style="width: 100%;", required="required", maxlength=32, autocomplete="off"))

    email_input = EmailInput()
    print(email_input.render(
        name="email",
        id_="email",
        class_="form-control",
        style="width: 100%;",
        required="required",
        placeholder="Enter your email",
        pattern=r"[^@]+@[^@]+\.[^@]+"
    ))

    number_input = NumberInput()
    print(number_input.render(name="age", id_="age", class_="form-control", style="width: 100%;", required="required", min=0, max=120, step=1, value=30))

    checkbox_input = CheckboxInput()
    print(checkbox_input.render(name="subscribe", id_="subscribe", class_="form-check-input", style="", checked=True, value="yes"))

    radio_input = RadioInput()
    print(radio_input.render(group_name="gender", value="male", id_="gender_male", class_="form-check-input", checked=True))

    select_input = SelectInput()
    print(select_input.render(name="country", id_="country", class_="form-select", style="width: 100%;", options='<option value="us">United States</option><option value="ca">Canada</option>', required="required"))

    date_input = DateInput()
    print(date_input.render(name="birthday", id_="birthday", class_="form-control", style="width: 100%;", min="1900-01-01", max="2100-12-31", value="2000-01-01"))

    datetime_input = DatetimeInput()
    print(datetime_input.render(name="event_time", id_="event_time", class_="form-control", style="width: 100%;", required="", min="2023-01-01T00:00", max="2023-12-31T23:59", value="2023-06-15T14:30"))

    file_input = FileInput()
    print(file_input.render(name="resume", id_="resume", class_="form-control", style="", required="", accept=".pdf,.docx", multiple="multiple"))

    color_input = ColorInput()
    print(color_input.render(name="favorite_color", id_="favorite_color", class_="form-control", style="", required="", value="#ff0000"))

    range_input = RangeInput()
    print(range_input.render(name="volume", id_="volume", class_="form-range", style="", required="", min=0, max=100, step=1, value=50))

    hidden_input = HiddenInput()
    print(hidden_input.render(name="secret", id_="secret", class_="form-control", style="", value="hidden_value"))

    ssn_input = SSNInput()
    print(ssn_input.render(name="ssn", id_="ssn", class_="form-control", style="", required="", value="987-65-4321",label="Social Security Number"))

    phone_input = PhoneInput()
    print(phone_input.render(
        name="phone",
        id_="phone",
        class_="form-control",
        style="",
        required="",
        value="838341551",
        country_code="+353"
    ))

    url_input = URLInput()
    print(url_input.render(name="website", id_="website", class_="form-control", style="", required="", pattern="https?://.+", value="https://example.com"))

    currency_input = CurrencyInput()
    print(currency_input.render(name="amount", id_="amount", class_="form-control", style="", required="", pattern="^\\$?\\d+(\\.(\\d{2}))?$", value="$100.00"))

    credit_card_input = CreditCardInput()
    print(credit_card_input.render(name="ccn", id_="ccn", class_="form-control", style="", required="", pattern="\\d{16}", value="1234567812345678"))