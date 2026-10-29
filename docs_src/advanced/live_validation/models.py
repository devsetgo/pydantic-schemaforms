from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel, LiveValidator


def live(field: str) -> dict[str, str]:
    """HTMX attributes that send the field to /validate/<field> as the user types."""
    return {
        'hx-post': f'/validate/{field}',
        'hx-trigger': 'blur, input delay:600ms',
        'hx-target': f'#{field}-feedback',
        'hx-swap': 'innerHTML',
    }


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, ui_options=live('name'))
    email: EmailStr = Field(title='Email', ui_options=live('email'))


live_validator = LiveValidator.for_model(ContactForm, debounce_ms=600)
