from typing import Any

from pydantic_schemaforms import Field, FormModel, TextInput, register_input_class, render_form_html


class ExtensionInput(TextInput):
    """A phone extension: up to six digits, with a numeric keypad on phones."""

    ui_element = 'extension'

    def render(self, **kwargs: Any) -> str:
        kwargs.setdefault('inputmode', 'numeric')
        kwargs.setdefault('pattern', r'\d{1,6}')
        kwargs.setdefault('maxlength', 6)
        return super().render(**kwargs)


register_input_class(ExtensionInput, aliases=('phone_extension',))


class DirectoryEntry(FormModel):
    name: str = Field(title='Name')
    extension: str = Field('', title='Extension', ui_element='extension')


form_html = render_form_html(DirectoryEntry, submit_url='/directory')
