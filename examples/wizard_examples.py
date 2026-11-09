#!/usr/bin/env python3
"""
Wizards: realistic multi-step forms, each showing a different mix of wizard
features (#276). Mounted into main.py's app.

Each example is one entry in WIZARD_EXAMPLES: a FormModel, the options it is
rendered with, and the page shown after a valid submission. The routes below
are generated from that list: ``/wizards`` lists them all, and each has its
own ``/wizards/<slug>`` GET and POST. The data is made up.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import EmailStr, field_validator

from examples.fastapi_routes import _material_variant, _variant_query, templates
from pydantic_schemaforms import (
    EmailRule,
    Field,
    FormModel,
    SafeHTML,
    html,
    render_form_html_async,
)

router = APIRouter()
_DEFAULT_STYLE = 'bootstrap'
# The page template's framework label, shared by every page below.
_PAGE = {'framework': 'fastapi', 'framework_name': 'FastAPI (Async)', 'hide_api_info': True}


# --- Car care appointment -----------------------------------------------------
_SERVICES = [
    {'value': 'oil', 'label': 'Oil change'},
    {'value': 'tires', 'label': 'Tire change'},
    {'value': 'brakes', 'label': 'Brake check'},
    {'value': 'inspection', 'label': 'Yearly inspection'},
]
_MAKES = [
    {'value': 'toyota', 'label': 'Toyota'},
    {'value': 'honda', 'label': 'Honda'},
    {'value': 'ford', 'label': 'Ford'},
    {'value': 'chevrolet', 'label': 'Chevrolet'},
    {'value': 'tesla', 'label': 'Tesla'},
    {'value': 'subaru', 'label': 'Subaru'},
]
# A North American number: area code and exchange can't start with 0 or 1.
# Brackets, dashes, dots and spaces are optional, so it passes with or without
# the live (###) ###-#### formatting.
_US_PHONE = r'^\(?[2-9]\d{2}\)?[-. ]?[2-9]\d{2}[-. ]?\d{4}$'
_SLOTS = [
    {'value': '08:00', 'label': '8:00'},
    {'value': '10:00', 'label': '10:00'},
    {'value': '13:00', 'label': '13:00'},
    {'value': '15:00', 'label': '15:00'},
]


class CarCareForm(FormModel):
    """The loaner-car step applies only when a loaner is asked for (#327)."""

    make: Literal['toyota', 'honda', 'ford', 'chevrolet', 'tesla', 'subaru'] = Field(
        title='Make',
        ui_options={'choices': _MAKES, 'placeholder': 'Choose a make'},
        ui_group='Your car',
    )
    model: str = Field(title='Model', min_length=2, ui_placeholder='Camry', ui_group='Your car')
    year: int = Field(2021, title='Year', ge=1990, le=2027, ui_group='Your car')
    plate: str = Field(title='License plate', min_length=2, ui_group='Your car')
    services: list[Literal['oil', 'tires', 'brakes', 'inspection']] = Field(
        default_factory=lambda: ['oil'],
        title='Services',
        min_length=1,
        ui_element='checkbox_group',
        ui_options={'choices': _SERVICES},
        ui_group='Services',
    )
    day: date = Field(
        default_factory=lambda: date.today() + timedelta(days=7),
        title='Day',
        ui_group='Date and time',
    )
    slot: Literal['08:00', '10:00', '13:00', '15:00'] = Field(
        '10:00',
        title='Time',
        ui_element='radio',
        ui_options={'choices': _SLOTS},
        ui_group='Date and time',
    )
    while_we_work: Literal['wait', 'drop_off', 'loaner'] = Field(
        'wait',
        title='While we work',
        ui_element='radio',
        ui_options={
            'choices': [
                {'value': 'wait', 'label': 'I will wait'},
                {'value': 'drop_off', 'label': 'I will drop it off'},
                {'value': 'loaner', 'label': 'I need a loaner car'},
            ]
        },
        ui_group='Date and time',
    )
    license: str = Field(
        '',
        title="Driver's license number",
        ui_group='Loaner car',
        ui_group_show_when={'field': 'while_we_work', 'equals': 'loaner'},
        ui_show_when={'field': 'while_we_work', 'equals': 'loaner', 'required': True},
    )
    loaner_return: date | None = Field(None, title='Return the loaner by', ui_group='Loaner car')
    name: str = Field(title='Your name', min_length=2, ui_group='Contact')
    phone: str = Field(
        title='Phone',
        pattern=_US_PHONE,
        description='A US number, such as (212) 555-0142',
        ui_element='phone',
        ui_options={'phone_format': '(###) ###-####'},
        ui_group='Contact',
    )


def _car_care_result(data: dict[str, Any]) -> SafeHTML:
    labels = {choice['value']: choice['label'] for choice in _SERVICES}
    services = ', '.join(labels[value] for value in data['services'])
    car = f'{data["year"]} {data["make"].title()} {data["model"]}'
    return html(
        t'<p>Booked for {data["name"]}: {services} for the {car} on {data["day"]} '
        t'at {data["slot"]}.</p>'
    )


# --- Team onboarding ----------------------------------------------------------
class Workspace(FormModel):
    name: str = Field(title='Workspace name', min_length=2)
    address: str = Field(
        title='Web address',
        pattern=r'^[a-z0-9-]{3,30}$',
        description='3-30 lowercase letters, digits or dashes: acme-design',
    )
    size: Literal['1-10', '11-50', '51-200', '200+'] = Field('1-10', title='Team size')


class Invite(FormModel):
    email: str = Field(title='Email', ui_element='email')
    role: Literal['member', 'admin'] = Field('member', title='Role')

    @field_validator('email')
    @classmethod
    def _real_email(cls, value: str) -> str:
        ok, message = EmailRule().validate(value)
        if not ok:
            raise ValueError(message)
        return value


class Preferences(FormModel):
    weekly_digest: bool = Field(True, title='Send me a weekly digest', ui_element='toggle')
    theme: Literal['light', 'dark', 'system'] = Field('system', title='Theme', ui_element='radio')


class TeamOnboardingForm(FormModel):
    """The smallest example, a starter template: three steps and a progress count."""

    workspace: Workspace = Field(title='Workspace')
    invites: list[Invite] = Field(
        default_factory=list,
        title='Invite teammates',
        max_length=10,
        ui_add_button_label='Add a teammate',
    )
    preferences: Preferences = Field(title='Preferences')


def _team_onboarding_result(data: dict[str, Any]) -> SafeHTML:
    workspace = data['workspace']
    count = len(data['invites'])
    return html(
        t'<p>{workspace["name"]} is ready at {workspace["address"]}. '
        t'{count} invitation(s) sent.</p>'
    )


# --- Event registration -------------------------------------------------------
_SESSIONS = [
    {'value': 'keynote', 'label': 'Opening keynote'},
    {'value': 'workshop_a', 'label': 'Workshop A: Forms that scale'},
    {'value': 'workshop_b', 'label': 'Workshop B: Accessible wizards (full)'},
    {'value': 'panel', 'label': 'Closing panel'},
]
_FULL_SESSIONS = {'workshop_b'}
_DIETS = [
    {'value': 'none', 'label': 'No requirements'},
    {'value': 'vegetarian', 'label': 'Vegetarian'},
    {'value': 'vegan', 'label': 'Vegan'},
    {'value': 'gluten_free', 'label': 'Gluten free'},
]
Diet = Literal['none', 'vegetarian', 'vegan', 'gluten_free']


class Attendee(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: EmailStr = Field(title='Email', ui_element='email')
    company: str = Field('', title='Company')
    diet: Diet = Field('none', title='Dietary needs', ui_options={'choices': _DIETS})


class Guest(FormModel):
    name: str = Field(title='Guest name', min_length=2)
    diet: Diet = Field('none', title='Dietary needs', ui_options={'choices': _DIETS})


class Sessions(FormModel):
    picks: list[Literal['keynote', 'workshop_a', 'workshop_b', 'panel']] = Field(
        default_factory=lambda: ['keynote'],
        title='Sessions',
        min_length=1,
        ui_element='checkbox_group',
        ui_options={'choices': _SESSIONS},
    )

    @field_validator('picks')
    @classmethod
    def _has_room(cls, picks: list[str]) -> list[str]:
        full = [choice['label'] for choice in _SESSIONS if choice['value'] in _FULL_SESSIONS]
        if any(pick in _FULL_SESSIONS for pick in picks):
            raise ValueError(f'{", ".join(full)} has no seats left; pick another session')
        return picks


class EventRegistrationForm(FormModel):
    """Guests as a repeating list, a capacity check, and no progress header."""

    attendee: Attendee = Field(title='You')
    guests: list[Guest] = Field(
        default_factory=list,
        title='Guests',
        max_length=3,
        ui_add_button_label='Add a guest',
    )
    sessions: Sessions = Field(title='Sessions')


def _event_registration_result(data: dict[str, Any]) -> SafeHTML:
    labels = {choice['value']: choice['label'] for choice in _SESSIONS}
    picks = ', '.join(labels[value] for value in data['sessions']['picks'])
    guests = len(data['guests'])
    return html(
        t'<p>{data["attendee"]["name"]} is registered with {guests} guest(s) for: {picks}.</p>'
    )


# --- The registry and its routes ----------------------------------------------
@dataclass(frozen=True)
class WizardExample:
    slug: str
    title: str
    summary: str
    features: tuple[str, ...]
    model: type[FormModel]
    result: Callable[[dict[str, Any]], SafeHTML]
    # The values the page opens with, so every example can be tried right away.
    # A function when a value depends on today, such as a date next week.
    demo: dict[str, Any] | Callable[[], dict[str, Any]] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


WIZARD_EXAMPLES = [
    WizardExample(
        slug='car-care',
        title='Car care appointment',
        summary='A short booking wizard whose loaner-car step only appears when you ask for one.',
        features=(
            'Steps from ui_group',
            'A step skipped by its rule (ui_group_show_when)',
            'Services as checkboxes',
            'Review step',
            'Progress ticks in the header',
        ),
        model=CarCareForm,
        result=_car_care_result,
        demo=lambda: {
            'day': (date.today() + timedelta(days=7)).isoformat(),
            'make': 'toyota',
            'model': 'Camry',
            'year': 2021,
            'plate': '7ABC123',
            'services': ['oil', 'brakes'],
            'slot': '10:00',
            'while_we_work': 'wait',
            'name': 'Jordan Example',
            'phone': '(212) 555-0142',
        },
        options={'wizard_options': {'review_step': True}, 'progress': True},
    ),
    WizardExample(
        slug='team-onboarding',
        title='Team onboarding',
        summary='The smallest example: a starter template to copy for your own wizard.',
        features=(
            'Steps from sub-forms',
            'Invite list (model_list) checked with EmailRule',
            'A pattern on the web address',
            'Progress ticks in the header',
        ),
        model=TeamOnboardingForm,
        result=_team_onboarding_result,
        demo={
            'workspace': {
                'name': 'Northwind Design',
                'address': 'northwind-design',
                'size': '11-50',
            },
            'invites': [
                {'email': 'sam@example.com', 'role': 'admin'},
                {'email': 'alex@example.com', 'role': 'member'},
            ],
            'preferences': {'weekly_digest': True, 'theme': 'system'},
        },
        options={'progress': True},
    ),
    WizardExample(
        slug='event-registration',
        title='Event registration',
        summary='Register yourself and your guests, then pick sessions that still have seats.',
        features=(
            'Guests as a repeating list (model_list)',
            'A capacity check (@field_validator)',
            'Dietary choices',
            'No progress header (show_progress=False)',
        ),
        model=EventRegistrationForm,
        result=_event_registration_result,
        demo={
            'attendee': {
                'name': 'Jordan Example',
                'email': 'jordan@example.com',
                'company': 'Northwind Design',
                'diet': 'vegetarian',
            },
            'guests': [{'name': 'Sam Example', 'diet': 'none'}],
            'sessions': {'picks': ['keynote', 'workshop_a']},
        },
        options={'wizard_options': {'show_progress': False, 'next_label': 'Continue'}},
    ),
]


def _demo_values(example: WizardExample) -> dict[str, Any]:
    return example.demo() if callable(example.demo) else example.demo


def _render_options(example: WizardExample, style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/wizards/{example.slug}?style={style}{_variant_query(variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
        'layout': 'wizard',
        **example.options,
    }


def _back_to_index(style: str) -> dict[str, str]:
    """The page's back button goes to the Wizards index, not the home page."""

    return {'back_url': f'/wizards?style={style}', 'back_label': 'Back to Wizard Examples'}


def _form_page(request: Request, example: WizardExample, style: str, form_html: str):
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': example.title,
            'description': example.summary,
            'framework_type': style,
            'form_html': form_html,
            **_PAGE,
            **_back_to_index(style),
        },
    )


def _add_routes(example: WizardExample) -> None:
    path = f'/wizards/{example.slug}'

    async def show(
        request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None, demo: bool = True
    ):
        form_html = await render_form_html_async(
            example.model,
            form_data=_demo_values(example) if demo else None,
            **_render_options(example, style, variant),
        )
        return _form_page(request, example, style, form_html)

    async def submit(request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None):
        options = _render_options(example, style, variant)
        result = example.model.validate(await request.form(), **options)
        if not result.is_valid:
            return _form_page(request, example, style, await result.render_with_errors_async())
        summary = example.result(result.data)
        display = example.model.render_display(
            result.data, framework=style, material_variant=_material_variant(variant)
        )
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': f'{example.title}: done',
                'message': 'Submitted. Here is what was sent.',
                'display_html': str(html(t'{summary}{SafeHTML(display)}')),
                'data': result.data,
                **_PAGE,
                **_back_to_index(style),
                'try_again_url': f'/wizards/{example.slug}?style={style}{_variant_query(variant)}',
            },
        )

    show.__doc__ = f'{example.title}: {example.summary}'
    router.add_api_route(path, show, methods=['GET'], response_class=HTMLResponse, tags=['Wizards'])
    router.add_api_route(
        path, submit, methods=['POST'], response_class=HTMLResponse, tags=['Wizards']
    )


for _example in WIZARD_EXAMPLES:
    _add_routes(_example)


_INDEX_STYLE = SafeHTML("""<style>
.sf-wizards { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr)); }
.sf-wizards__card { border: 1px solid rgba(127, 127, 127, 0.35); border-radius: 0.75rem; padding: 1rem 1.25rem; }
.sf-wizards__card h2 { font-size: 1.15rem; margin: 0 0 0.5rem; }
.sf-wizards__card p { margin: 0 0 0.5rem; }
.sf-wizards__card ul { margin: 0; padding-left: 1.1rem; font-size: 0.9rem; }
.sf-wizards__options { columns: 2 18rem; padding-left: 1.1rem; }
</style>""")


# Each wizard option on the /layouts demo form, so it can be tried on its own.
_OPTION_DEMOS = [
    ('/layouts?layout=wizard', 'The default wizard: one form, one POST'),
    ('/layouts?layout=wizard&linear=false', 'Jump to any step (linear=False)'),
    ('/layouts?layout=wizard&progress=false&labels=true', 'No header, custom Back/Next labels'),
    ('/layouts?layout=wizard&review=true', 'Review step before Submit (review_step)'),
    ('/layouts?layout=wizard&count=true', 'Tick finished steps (progress=True)'),
    ('/layouts?layout=tabbed&count=true', 'Required-fields bar on other layouts (progress=True)'),
    ('/layouts?layout=wizard&autosave=true&warn=true', 'Autosave a draft (autosave, warn_unsaved)'),
    ('/layouts/save-steps', 'Save each step on the server (save_steps)'),
    ('/wizards/car-care', "Skip a step that doesn't apply (ui_group_show_when)"),
]


def _with_query(href: str, query: str) -> str:
    return f'{href}{"&" if "?" in href else "?"}{query}'


@router.get('/wizards', response_class=HTMLResponse, tags=['Wizards'])
async def wizards_index(request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None):
    """Every wizard example, with the features each one shows."""
    cards = []
    for example in WIZARD_EXAMPLES:
        href = f'/wizards/{example.slug}?style={style}{_variant_query(variant)}'
        _features = SafeHTML(  # NOSONAR - read in the t-string below
            ''.join(str(html(t'<li>{feature}</li>')) for feature in example.features)
        )
        cards.append(
            str(
                html(
                    t'<article class="sf-wizards__card"><h2><a href="{href}">{example.title}</a></h2>'
                    t'<p>{example.summary}</p><ul>{_features}</ul></article>'
                )
            )
        )
    _cards = SafeHTML(''.join(cards))  # NOSONAR
    query = f'style={style}{_variant_query(variant)}'
    _options = SafeHTML(  # NOSONAR - read in the t-string below
        ''.join(
            str(html(t'<li><a href="{_with_query(href, query)}">{label}</a></li>'))
            for href, label in _OPTION_DEMOS
        )
    )
    page = html(
        t'{_INDEX_STYLE}<div class="sf-wizards">{_cards}</div>'
        t'<h2 class="h5 mt-4">Wizard options</h2>'
        t'<p>Each option on its own, on the layout demo form:</p>'
        t'<ul class="sf-wizards__options">{_options}</ul>'
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Wizards',
            'description': (
                'Realistic multi-step forms, each built to show a different mix of wizard '
                'features. Every one renders under Bootstrap and Material.'
            ),
            'framework_type': style,
            'form_html': str(page),
            **_PAGE,
        },
    )
