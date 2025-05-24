"""
create ui HTML elements for UI Schema using t strings
Pep-750 https://peps.python.org/pep-0750/
there should be a check to ensure only UI elements that are valid for the schema type are used

from pep_750 import t  # hypothetical future import for t strings

HTML Input Attribute Reference
-----------------------------

| Attribute    | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| class        | Specifies one or more class names for an element                            |
| style        | Specifies an inline CSS style for an element                                |

"""
from string.templatelib import Template, Interpolation

# Add the t() fallback if not already present
def t(template: str) -> str:
    return template

class HorizontalLayout:
    """
    Represents a horizontal layout element.
    Required: content
    Optional: style, class_
    """
    template = t("""<div style="display:flex; flex-direction: row;{style}" class="{class_}">{content}</div>""")
    def render(self, **kwargs):
        attrs = {
            "style": kwargs.get("style", ""),
            "class_": kwargs.get("class_", ""),
            "content": kwargs.get("content", ""),
        }
        return self.template.format(**attrs)

class VerticalLayout:
    """
    Represents a vertical layout element.
    Required: content
    Optional: style, class_
    """
    template = t("""<div style="display:flex; flex-direction: column;{style}" class="{class_}">{content}</div>""")
    def render(self, **kwargs):
        attrs = {
            "style": kwargs.get("style", ""),
            "class_": kwargs.get("class_", ""),
            "content": kwargs.get("content", ""),
        }
        return self.template.format(**attrs)

class GridLayout:
    """
    Represents a grid layout element.
    Required: content, columns
    Optional: style, class_
    """
    template = t("""<div style="display:grid; grid-template-columns: {columns};{style}" class="{class_}">{content}</div>""")
    def render(self, **kwargs):
        attrs = {
            "columns": kwargs.get("columns", ""),
            "style": kwargs.get("style", ""),
            "class_": kwargs.get("class_", ""),
            "content": kwargs.get("content", ""),
        }
        return self.template.format(**attrs)

class TabLayout:
    """
    Represents a tab layout element.
    Required: tabs
    Optional: class_, style
    """
    template = t("""<div class="tab-layout {class_}" style="{style}">{tabs}</div>""")
    def render(self, **kwargs):
        attrs = {
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "tabs": kwargs.get("tabs", ""),
        }
        return self.template.format(**attrs)

class AccordionLayout:
    """
    Represents an accordion layout element.
    Required: sections
    Optional: class_, style
    """
    template = t("""<div class="accordion-layout {class_}" style="{style}">{sections}</div>""")
    def render(self, **kwargs):
        attrs = {
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "sections": kwargs.get("sections", ""),
        }
        return self.template.format(**attrs)

class ModalLayout:
    """
    Represents a modal layout element.
    Required: modal_id, content
    Optional: class_, style
    """
    template = t("""<div class="modal {class_}" id="{modal_id}" style="{style}">{content}</div>""")
    def render(self, **kwargs):
        attrs = {
            "class_": kwargs.get("class_", ""),
            "modal_id": kwargs.get("modal_id", ""),
            "style": kwargs.get("style", ""),
            "content": kwargs.get("content", ""),
        }
        return self.template.format(**attrs)

class SidebarLayout:
    """
    Represents a sidebar layout element.
    Required: content
    Optional: class_, style
    """
    template = t("""<div class="sidebar {class_}" style="{style}">{content}</div>""")
    def render(self, **kwargs):
        attrs = {
            "class_": kwargs.get("class_", ""),
            "style": kwargs.get("style", ""),
            "content": kwargs.get("content", ""),
        }
        return self.template.format(**attrs)

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
    print(ssn_input.render(name="ssn", id_="ssn", class_="form-control", style="", required="", value="123-45-6789"))

    phone_input = PhoneInput()
    print(phone_input.render(
        name="phone",
        id_="phone",
        class_="form-control",
        style="",
        required="",
        pattern=r"\d{3}-\d{3}-\d{4}",
        maxlength=12,
        minlength=12,
        value="123-456-7890"
    ))

    url_input = URLInput()
    print(url_input.render(name="website", id_="website", class_="form-control", style="", required="", pattern="https?://.+", value="https://example.com"))

    currency_input = CurrencyInput()
    print(currency_input.render(name="amount", id_="amount", class_="form-control", style="", required="", pattern="^\\$?\\d+(\\.(\\d{2}))?$", value="$100.00"))

    credit_card_input = CreditCardInput()
    print(credit_card_input.render(name="ccn", id_="ccn", class_="form-control", style="", required="", pattern="\\d{16}", value="1234567812345678"))

    horizontal_layout = HorizontalLayout()
    print(horizontal_layout.render(content="Column 1 | Column 2 | Column 3", style="justify-content: space-between;"))

    vertical_layout = VerticalLayout()
    print(vertical_layout.render(content="Row 1<br>Row 2<br>Row 3", style="align-items: flex-start;"))

    grid_layout = GridLayout()
    print(grid_layout.render(content="Item 1|Item 2|Item 3|Item 4", columns="1fr 1fr 1fr 1fr", style="gap: 10px;"))

    tab_layout = TabLayout()
    print(tab_layout.render(tabs='<div class="tab" onclick="openTab(event, \'Tab1\')">Tab 1</div><div class="tab" onclick="openTab(event, \'Tab2\')">Tab 2</div>', class_="custom-tabs", style=""))

    accordion_layout = AccordionLayout()
    print(accordion_layout.render(sections='<div class="section" onclick="toggleSection(this)">Section 1</div><div class="section-content">Content 1</div><div class="section" onclick="toggleSection(this)">Section 2</div><div class="section-content">Content 2</div>', class_="custom-accordion", style=""))

    modal_layout = ModalLayout()
    print(modal_layout.render(content="This is a modal", modal_id="myModal", class_="fade", style="display:none;"))

    sidebar_layout = SidebarLayout()
    print(sidebar_layout.render(content="Sidebar content here", class_="custom-sidebar", style="width:250px;"))