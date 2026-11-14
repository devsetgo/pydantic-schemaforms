<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-create/references/catalog.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Form catalogue

Starting points for common forms. Each model is tested against the current library. Adapt the
fields to the request; add the routes from the pattern in `SKILL.md`.

## Contact form

A topic, a message and a honeypot against spam bots. When `website` comes back filled in, answer
as if the message was sent and drop it.

```python
from typing import Literal

from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Your name', min_length=2, ui_autofocus=True)
    email: EmailStr = Field(title='Email')
    topic: Literal['Question', 'Feedback', 'Bug report'] = Field('Question', title='Topic')
    message: str = Field(title='Message', min_length=10, max_length=2000, ui_element='textarea')
    website: str = Field('', ui_element='honeypot')  # hidden; only bots fill it in
```

## Login and registration

Passwords, a matching confirmation, a required "accept the terms" box. Checks only the app can
make (wrong password, username taken) are added in the route after `validate()`:
`render_form_html(Model, form_data=..., errors={"username": "That username is taken"}, ...)`, or
`errors={"_errors": "Wrong username or password"}` for the whole form. Only put the username
back on a failed login, never the password. Redirect (303) after success.

```python
from typing import Literal

from pydantic import EmailStr, ValidationInfo, field_validator

from pydantic_schemaforms import Field, FormModel


class LoginForm(FormModel):
    username: str = Field(title='Username', ui_autofocus=True)
    password: str = Field(title='Password', ui_element='password')
    remember_me: bool = Field(False, title='Keep me signed in')


class RegistrationForm(FormModel):
    username: str = Field(
        title='Username',
        min_length=3,
        max_length=30,
        pattern=r'^[a-z0-9_]+$',
        description='Lowercase letters, numbers and underscores.',
    )
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm_password: str = Field(title='Confirm password', ui_element='password')
    accept_terms: Literal[True] = Field(
        title='I accept the terms of service',
        unchecked_message='You must accept the terms to create an account',
    )

    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value
```

## Edit form for a saved record (profile, product, settings)

Pre-fill with `form_data={name: row[name] for name in Model.model_fields}`; dates and `Enum`
members can be passed as they are. Only pass the form's own fields, so values such as `id` can't
be edited.

```python
from datetime import date
from enum import Enum

from pydantic_schemaforms import Field, FormModel


class Status(str, Enum):
    draft = 'draft'
    active = 'active'
    archived = 'archived'


class ProductForm(FormModel):
    name: str = Field(title='Name', min_length=2)
    price: float = Field(title='Price', ge=0)
    status: Status = Field(Status.draft, title='Status')
    launch_date: date | None = Field(None, title='Launch date')
    featured: bool = Field(False, title='Featured on the home page')


PRODUCTS = {  # stands in for your database
    1: {
        'id': 1,
        'name': 'Desk lamp',
        'price': 39.5,
        'status': Status.active,
        'launch_date': date(2026, 3, 1),
        'featured': True,
        'created_by': 'ada',
    },
}
```

## Checkout with shipping and billing addresses

One `Address` model used twice; the billing address is an optional sub-form that's validated only
when filled in.

```python
from typing import Literal, Self

from pydantic import EmailStr, model_validator

from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)
    postal_code: str = Field(title='Postal code', pattern=r'^[A-Za-z0-9 -]{3,10}$')
    country: Literal['US', 'CA', 'GB', 'FR', 'DE'] = Field('US', title='Country')


class CheckoutForm(FormModel):
    email: EmailStr = Field(title='Email for the receipt')
    shipping: Address = Field(title='Shipping address')
    billing_same_as_shipping: bool = Field(True, title='Bill to the shipping address')
    billing: Address | None = Field(None, title='Billing address', ui_collapsed=True)

    @model_validator(mode='after')
    def billing_given(self) -> Self:
        if not self.billing_same_as_shipping and self.billing is None:
            raise ValueError('Enter a billing address, or bill to the shipping address')
        return self

    def billing_address(self) -> Address:
        return self.shipping if self.billing_same_as_shipping else self.billing
```

## Order with line items

A repeating sub-form; the total is computed on the server, never trusted from the browser.

```python
from datetime import date
from decimal import Decimal

from pydantic import computed_field

from pydantic_schemaforms import Field, FormModel


class LineItem(FormModel):
    product: str = Field(title='Product', min_length=2)
    quantity: int = Field(1, title='Quantity', ge=1, le=999)
    unit_price: Decimal = Field(title='Unit price', ge=0, decimal_places=2, ui_element='currency')

    @computed_field
    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price


class OrderForm(FormModel):
    customer: str = Field(title='Customer', ui_autofocus=True)
    delivery_date: date = Field(title='Delivery date')
    items: list[LineItem] = Field(
        default_factory=list,
        title='Line items',
        min_length=1,
        max_length=50,
        ui_add_button_label='Add a line',
        ui_item_title_template='{product}',
    )
    notes: str = Field('', title='Notes', ui_element='textarea')
```

## File upload

The file field is `UploadedFile`; `ui_max_size` and `accept` are checked on the server.

```python
from pydantic_schemaforms import Field, FormModel, UploadedFile

MAX_BYTES = 5 * 1024 * 1024


class UploadForm(FormModel):
    title: str = Field(title='Title', min_length=2)
    document: UploadedFile = Field(
        title='Document',
        description='PDF or Word, up to 5 MB.',
        ui_max_size=MAX_BYTES,
        ui_options={'accept': '.pdf,.docx'},
    )
```

## Job application (wizard)

One step per sub-form; pass `layout="wizard"` to both `render_form_html()` and `validate()`.

```python
from datetime import date
from typing import Literal

from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel


class Applicant(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    email: EmailStr = Field(title='Email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Position(FormModel):
    role: Literal['Engineer', 'Designer', 'Product manager'] = Field(title='Role')
    start_date: date = Field(title='Earliest start date')
    remote: bool = Field(False, title='I want to work remotely')


class Job(FormModel):
    employer: str = Field(title='Employer')
    job_title: str = Field(title='Job title')
    years: int = Field(1, title='Years', ge=0, le=50)


class Motivation(FormModel):
    cover_letter: str = Field(
        title='Why do you want to join?', min_length=50, ui_element='textarea'
    )
    consent: bool = Field(title='You may keep my application on file for 12 months')


class ApplicationForm(FormModel):
    applicant: Applicant = Field(title='About you')
    position: Position = Field(title='Position')
    experience: list[Job] = Field(
        default_factory=list,
        title='Experience',
        max_length=10,
        ui_add_button_label='Add a job',
        ui_item_title_template='{employer}',
    )
    motivation: Motivation = Field(title='Motivation')
```

## Resumable application (save and continue)

For "users can leave and come back" or an upload in a wizard: each step is its own POST, checked
on the server and saved as a draft; uploaded files are stored as soon as their step is valid.

```python
from datetime import date

from pydantic_schemaforms import Field, FormModel, UploadedFile


class AboutYou(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    zip_code: str = Field(title='ZIP code', pattern=r'^\d{5}$')


class Resume(FormModel):
    resume: UploadedFile = Field(
        title='Resume (PDF or text, up to 200 KB)',
        ui_max_size=200 * 1024,
        ui_options={'accept': '.pdf,.txt'},
    )


class Availability(FormModel):
    city: str = Field(title='City', min_length=2)
    start_date: date = Field(title='Earliest start date')


class ApplicationForm(FormModel):
    about_you: AboutYou = Field(title='About you')
    resume: Resume = Field(title='Resume')
    availability: Availability = Field(title='Availability')
```

The routes call `validate_step()` instead of `validate()`, store `result.draft`, and pass it back
as `draft=` on both routes:

```python
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ApplicationForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'save_steps': True, 'review_step': True},
    'include_framework_assets': True,
    'asset_mode': 'cdn',
}

# Stand-ins for a real app's session (or database) and file store.
DRAFTS: dict[str, dict] = {}
FILES: dict[str, bytes] = {}


def load_draft(request: Request) -> dict | None:
    return DRAFTS.get(request.cookies.get('draft_id', ''))


@app.get('/apply', response_class=HTMLResponse)
async def show_application(request: Request):
    return await render_form_html_async(ApplicationForm, draft=load_draft(request), **FORM)


@app.post('/apply', response_class=HTMLResponse)
async def apply(request: Request):
    draft_id = request.cookies.get('draft_id') or secrets.token_urlsafe(16)
    result = ApplicationForm.validate_step(await request.form(), draft=load_draft(request), **FORM)
    if result.is_complete:
        DRAFTS.pop(draft_id, None)
        name = result.data['about_you']['full_name']
        city = result.data['availability']['city']
        return html(t'<p>Thanks, {name}. We will be in touch about {city}.</p>')
    if result.is_valid:
        for upload in result.files:
            upload.ref = secrets.token_hex(8)
            FILES[upload.ref] = upload.read()
        DRAFTS[draft_id] = result.draft
    response = HTMLResponse(await result.render_async())
    response.set_cookie('draft_id', draft_id, httponly=True, samesite='lax')
    return response
```

## Settings with a code field

JSON or TOML typed into a code-editor text area, checked by validators.

```python
import json
import tomllib
from typing import Any

from pydantic import field_validator

from pydantic_schemaforms import Field, FormModel


class ServiceSettings(FormModel):
    name: str = Field(title='Service name', pattern=r'^[a-z][a-z0-9-]*$')
    config: str = Field(
        '{\n  "replicas": 2\n}',
        title='Config (JSON)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 10},
    )
    build: str = Field(
        '[tool.build]\ntarget = "release"\n',
        title='Build settings (TOML)',
        ui_element='textarea',
        ui_options={'language': 'toml', 'rows': 6},
    )
    deploy_script: str = Field(
        '',
        title='Deploy script',
        ui_element='textarea',
        ui_options={'language': 'bash', 'code_highlight': False},
    )

    @field_validator('config')
    @classmethod
    def valid_json_object(cls, value: str) -> str:
        try:
            parsed: Any = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Not valid JSON: {exc.msg} (line {exc.lineno})') from None
        if not isinstance(parsed, dict):
            raise ValueError('The config must be a JSON object')
        return value

    @field_validator('build')
    @classmethod
    def valid_toml(cls, value: str) -> str:
        try:
            tomllib.loads(value)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f'Not valid TOML: {exc}') from None
        return value
```

## Survey or feedback

```python
from typing import Literal

from pydantic_schemaforms import Field, FormModel


class SurveyForm(FormModel):
    """A short feedback survey: every question is optional except the overall rating."""

    # A star rating is an int: ge/le are the real limits, the stars are only how it's shown.
    overall: int = Field(title='How was your visit overall?', ge=1, le=5, ui_element='star_rating')
    # Literal choices render as options; radio shows all of them at once.
    recommend: Literal['Yes', 'Maybe', 'No'] = Field(
        'Maybe', title='Would you recommend us?', ui_element='radio'
    )
    # list[Literal[...]] lets the user pick several.
    liked: list[Literal['Staff', 'Price', 'Speed', 'Quality']] = Field(
        default_factory=list, title='What did you like?', ui_element='checkbox_group'
    )
    comments: str = Field('', title='Anything else?', max_length=1000, ui_element='textarea')
```

## Blank tabbed layout

For "a tabbed layout for a blank form": placeholder sections to replace. The same model renders as
an accordion, columns or a wizard by changing `layout=`.

```python
from pydantic_schemaforms import Field, FormModel, render_form_html

# A blank tabbed form: each nested FormModel becomes one tab.
# Replace the placeholder sections and fields with real ones.


class SectionOne(FormModel):
    first_field: str = Field(title='First field')


class SectionTwo(FormModel):
    second_field: str = Field('', title='Second field')


class SectionThree(FormModel):
    third_field: bool = Field(False, title='Third field')


class TabbedForm(FormModel):
    # Plain fields on the main form become the first tab, titled by model_config.
    model_config = {'title': 'General'}

    name: str = Field(title='Name')
    section_one: SectionOne = Field(title='Section one')
    section_two: SectionTwo = Field(title='Section two')
    section_three: SectionThree = Field(title='Section three')


# The same model works as "accordion", "side-by-side" or "wizard": only layout= changes.
form_html = render_form_html(TabbedForm, layout='tabbed', submit_url='/form')
```

## Blank wizard

```python
from pydantic_schemaforms import Field, FormModel, render_form_html

# A blank three-step wizard: each nested FormModel is one step, in declaration order.
# It is still one <form> and one POST; Next checks the current step in the browser.


class StepOne(FormModel):
    name: str = Field(title='Name')


class StepTwo(FormModel):
    details: str = Field('', title='Details', ui_element='textarea')


class StepThree(FormModel):
    confirm: bool = Field(title='I confirm these details are correct')


class WizardForm(FormModel):
    step_one: StepOne = Field(title='Step one')
    step_two: StepTwo = Field(title='Step two')
    step_three: StepThree = Field(title='Step three', ui_step_title='Confirm')


form_html = render_form_html(
    WizardForm,
    layout='wizard',
    wizard_options={'next_label': 'Continue'},
    submit_url='/form',
)
```
