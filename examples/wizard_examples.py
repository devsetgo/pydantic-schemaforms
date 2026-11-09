#!/usr/bin/env python3
"""
Wizards: realistic multi-step forms, each showing a different mix of wizard
features (#276). Mounted into main.py's app.

Each example is one entry in WIZARD_EXAMPLES: a FormModel, the options it is
rendered with, and the page shown after a valid submission. The routes below
are generated from that list: ``/wizards`` lists them all, and each has its
own ``/wizards/<slug>`` GET and POST. The data is made up.
"""

import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import EmailStr, field_validator, model_validator

from examples.fastapi_routes import _material_variant, _variant_query, templates
from pydantic_schemaforms import (
    EmailRule,
    Field,
    FormModel,
    SafeHTML,
    UploadedFile,
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


# --- Rental application -------------------------------------------------------
# Monthly rent by unit; the income check needs it.
_UNITS = {
    '2b': ('Unit 2B, 410 Elm St, Austin, TX', 2_400),
    '5a': ('Unit 5A, 410 Elm St, Austin, TX', 3_100),
    '1c': ('Unit 1C, 88 Lake Ave, Round Rock, TX', 1_850),
}
_INCOME_MULTIPLE = 3
_PROOF_LIMIT = 5 * 1024 * 1024


class Home(FormModel):
    unit: Literal['2b', '5a', '1c'] = Field(
        title='Apartment',
        ui_element='select',
        ui_options={
            'choices': [
                {'value': key, 'label': f'{name} (${rent:,} a month)'}
                for key, (name, rent) in _UNITS.items()
            ]
        },
    )
    move_in: date = Field(title='Move-in date')
    lease: Literal['6', '12', '24'] = Field(
        '12',
        title='Lease length',
        ui_element='radio',
        ui_options={
            'choices': [
                {'value': '6', 'label': '6 months'},
                {'value': '12', 'label': '12 months'},
                {'value': '24', 'label': '24 months'},
            ]
        },
    )
    has_pets: bool = Field(False, title='I have pets')
    pets: str = Field(
        '',
        title='Tell us about your pets',
        ui_placeholder='One cat, 9 lb',
        ui_show_when={'field': 'has_pets', 'truthy': True, 'required': True},
    )


class Renter(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    email: EmailStr = Field(title='Email', ui_element='email')
    phone: str = Field(
        title='Phone',
        pattern=_US_PHONE,
        description='A US number, such as (512) 555-0187',
        ui_element='phone',
    )
    employer: str = Field(title='Employer', min_length=2)
    monthly_income: int = Field(title='Monthly income before tax (USD)', ge=0)


class CoApplicant(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    relationship: Literal['partner', 'roommate', 'family'] = Field(
        'roommate',
        title='Relationship',
        ui_element='select',
        ui_options={
            'choices': [
                {'value': 'partner', 'label': 'Partner or spouse'},
                {'value': 'roommate', 'label': 'Roommate'},
                {'value': 'family', 'label': 'Family member'},
            ]
        },
    )
    monthly_income: int = Field(0, title='Monthly income before tax (USD)', ge=0)


class Documents(FormModel):
    proof_of_income: list[UploadedFile] = Field(
        default_factory=list,
        title='Proof of income (up to 3 files)',
        description='Pay stubs or an offer letter, PDF or image, up to 5 MB each. '
        'You can also send them after you apply.',
        ui_max_files=3,
        ui_max_size=_PROOF_LIMIT,
        ui_options={'accept': '.pdf,.jpg,.jpeg,.png'},
    )


class RentalReference(FormModel):
    name: str = Field(title='Name', min_length=2)
    phone: str = Field(title='Phone', pattern=_US_PHONE, ui_element='phone')
    relationship: str = Field(title='How you know them', ui_placeholder='Previous landlord')


class RentalApplicationForm(FormModel):
    """Co-applicants and references as lists, an income check across them, uploads."""

    home: Home = Field(title='The apartment')
    renter: Renter = Field(title='You')
    co_applicants: list[CoApplicant] = Field(
        default_factory=list,
        title='Co-applicants',
        max_length=3,
        ui_add_button_label='Add a co-applicant',
        ui_item_title_template='{full_name}',
    )
    documents: Documents = Field(title='Documents')
    references: list[RentalReference] = Field(
        default_factory=list,
        title='References',
        min_length=1,
        max_length=3,
        ui_add_button_label='Add a reference',
        ui_item_title_template='{name}',
    )

    @model_validator(mode='after')
    def _income_covers_rent(self) -> 'RentalApplicationForm':
        name, rent = _UNITS[self.home.unit]
        income = self.renter.monthly_income + sum(c.monthly_income for c in self.co_applicants)
        needed = rent * _INCOME_MULTIPLE
        if income < needed:
            raise ValueError(
                f'Together you earn ${income:,} a month. {name} needs at least '
                f'${needed:,} ({_INCOME_MULTIPLE} times the rent); add a co-applicant '
                'or pick another apartment.'
            )
        return self


def _rental_application_result(data: dict[str, Any]) -> SafeHTML:
    name, rent = _UNITS[data['home']['unit']]
    files = len(data['documents']['proof_of_income'])
    renter = data['renter']['full_name']
    return html(
        t'<p>Thanks, {renter}. Your application for {name} (${rent:,} a month) is in, '
        t'with {files} document(s).</p>'
    )


# --- Project planner ----------------------------------------------------------
class ProjectBasics(FormModel):
    name: str = Field(title='Project name', min_length=3)
    owner: str = Field(title='Project owner', min_length=2, ui_cols=6)
    budget: int = Field(
        title='Budget (USD)',
        ge=1_000,
        multiple_of=500,
        description='At least $1,000, in steps of $500',
        ui_cols=6,
    )
    start: date = Field(title='Start date', ui_cols=6)
    end: date = Field(title='End date', ui_cols=6)

    @model_validator(mode='after')
    def _end_after_start(self) -> 'ProjectBasics':
        if self.end <= self.start:
            raise ValueError('The end date must be after the start date')
        return self


class TeamMember(FormModel):
    name: str = Field(title='Name', min_length=2)
    email: EmailStr = Field(title='Email', ui_element='email')
    role: Literal['lead', 'engineer', 'designer', 'analyst'] = Field(
        'engineer',
        title='Role',
        ui_element='select',
        ui_options={
            'choices': [
                {'value': 'lead', 'label': 'Lead'},
                {'value': 'engineer', 'label': 'Engineer'},
                {'value': 'designer', 'label': 'Designer'},
                {'value': 'analyst', 'label': 'Analyst'},
            ]
        },
    )


class Milestone(FormModel):
    title: str = Field(title='Milestone', min_length=3)
    due: date = Field(title='Due')


class Task(FormModel):
    title: str = Field(title='Task', min_length=3)
    assignee: str = Field(title='Assignee', min_length=2)
    days: int = Field(1, title='Days', ge=1, le=30)


class ProjectPlanForm(FormModel):
    """Lists on three steps, date checks, and steps you can visit in any order."""

    project: ProjectBasics = Field(title='Project')
    team: list[TeamMember] = Field(
        default_factory=list,
        title='Team',
        min_length=1,
        max_length=8,
        ui_add_button_label='Add a team member',
        ui_item_title_template='{name}',
    )
    milestones: list[Milestone] = Field(
        default_factory=list,
        title='Milestones',
        min_length=1,
        max_length=6,
        ui_add_button_label='Add a milestone',
        ui_item_title_template='{title}',
    )
    tasks: list[Task] = Field(
        default_factory=list,
        title='Tasks',
        max_length=12,
        ui_add_button_label='Add a task',
        ui_item_title_template='{title}',
    )

    @model_validator(mode='after')
    def _milestones_in_range(self) -> 'ProjectPlanForm':
        late = [
            m.title for m in self.milestones if not self.project.start <= m.due <= self.project.end
        ]
        if late:
            raise ValueError(f'Due outside the project dates: {", ".join(late)}')
        return self


def _project_plan_result(data: dict[str, Any]) -> SafeHTML:
    project = data['project']
    days = sum(task['days'] for task in data['tasks'])
    people = len(data['team'])
    milestones = len(data['milestones'])
    return html(
        t'<p>{project["name"]} runs {project["start"]} to {project["end"]} with '
        t'{people} people, {milestones} milestone(s) and {days} day(s) of tasks.</p>'
    )


def _project_plan_demo() -> dict[str, Any]:
    start = date.today() + timedelta(days=14)
    return {
        'project': {
            'name': 'Customer portal refresh',
            'owner': 'Morgan Example',
            'budget': 48_500,
            'start': start.isoformat(),
            'end': (start + timedelta(days=90)).isoformat(),
        },
        'team': [
            {'name': 'Morgan Example', 'email': 'morgan@example.com', 'role': 'lead'},
            {'name': 'Riley Example', 'email': 'riley@example.com', 'role': 'engineer'},
            {'name': 'Avery Example', 'email': 'avery@example.com', 'role': 'designer'},
        ],
        'milestones': [
            {'title': 'Designs approved', 'due': (start + timedelta(days=21)).isoformat()},
            {'title': 'Beta release', 'due': (start + timedelta(days=60)).isoformat()},
            {'title': 'Launch', 'due': (start + timedelta(days=88)).isoformat()},
        ],
        'tasks': [
            {'title': 'Audit current pages', 'assignee': 'Avery Example', 'days': 5},
            {'title': 'Build the account page', 'assignee': 'Riley Example', 'days': 12},
        ],
    }


# --- Car setup -----------------------------------------------------------------
# Starting price by body style, and what each trim and option adds.
_BODIES = {'sedan': ('Sedan', 28_400), 'suv': ('SUV', 34_900), 'truck': ('Pickup truck', 39_200)}
_POWERTRAINS = {'gas': ('Gas', 0), 'hybrid': ('Hybrid', 2_800), 'electric': ('Electric', 7_500)}
_TRIMS = {'base': ('Base', 0), 'sport': ('Sport', 3_200), 'touring': ('Touring', 5_600)}
_PAINT = {
    'white': 'Glacier White',
    'black': 'Midnight Black',
    'silver': 'Lunar Silver',
    'blue': 'Harbor Blue',
    'red': 'Canyon Red',
}
_EXTRAS = {
    'sunroof': ('Panoramic sunroof', 1_400),
    'heated_seats': ('Heated front seats', 600),
    'audio': ('Premium audio', 950),
    'assist': ('Driver assist package', 1_800),
}
_TOW_PACKAGE = 1_100


def _priced(options: dict[str, tuple[str, int]]) -> list[dict[str, str]]:
    return [
        {'value': key, 'label': f'{label} (+${price:,})' if price else label}
        for key, (label, price) in options.items()
    ]


class CarSetupForm(FormModel):
    """Fixed steps from ui_group, a question only trucks get, renamed Back/Next."""

    body: Literal['sedan', 'suv', 'truck'] = Field(
        'suv',
        title='Body style',
        ui_element='radio',
        ui_options={
            'choices': [
                {'value': key, 'label': f'{label}, from ${price:,}'}
                for key, (label, price) in _BODIES.items()
            ]
        },
        ui_group='Body style',
    )
    powertrain: Literal['gas', 'hybrid', 'electric'] = Field(
        'gas',
        title='Powertrain',
        ui_element='radio',
        ui_options={'choices': _priced(_POWERTRAINS)},
        ui_group='Powertrain',
    )
    trim: Literal['base', 'sport', 'touring'] = Field(
        'base',
        title='Trim',
        ui_element='radio',
        ui_options={'choices': _priced(_TRIMS)},
        ui_group='Trim',
    )
    paint: Literal['white', 'black', 'silver', 'blue', 'red'] = Field(
        'white',
        title='Paint',
        ui_element='select',
        ui_options={'choices': [{'value': k, 'label': v} for k, v in _PAINT.items()]},
        ui_group='Color and options',
    )
    extras: list[Literal['sunroof', 'heated_seats', 'audio', 'assist']] = Field(
        default_factory=list,
        title='Options',
        ui_element='checkbox_group',
        ui_options={'choices': _priced(_EXTRAS)},
        ui_group='Color and options',
    )
    tow_package: bool = Field(
        False,
        title=f'Tow package (+${_TOW_PACKAGE:,})',
        ui_show_when={'field': 'body', 'equals': 'truck'},
        ui_group='Color and options',
    )


def _car_price(data: dict[str, Any]) -> int:
    price = _BODIES[data['body']][1] + _POWERTRAINS[data['powertrain']][1]
    price += _TRIMS[data['trim']][1] + sum(_EXTRAS[key][1] for key in data['extras'])
    if data['body'] == 'truck' and data['tow_package']:
        price += _TOW_PACKAGE
    return price


def _car_setup_result(data: dict[str, Any]) -> SafeHTML:
    car = (
        f'{_PAINT[data["paint"]]} {_TRIMS[data["trim"]][0]} '
        f'{_POWERTRAINS[data["powertrain"]][0].lower()} {_BODIES[data["body"]][0].lower()}'
    )
    price = f'${_car_price(data):,}'
    return html(t'<p>Your build: {car}, {price} before tax and fees.</p>')


# --- Insurance claim -----------------------------------------------------------
_PHOTO_LIMIT = 8 * 1024 * 1024


def _policies() -> dict[str, tuple[date, date]]:
    """Policy number to its coverage dates; the claim checks the incident against them."""

    today = date.today()
    return {
        'AU-482913': (today - timedelta(days=200), today + timedelta(days=165)),
        'AU-100274': (today - timedelta(days=500), today - timedelta(days=135)),
    }


class Policyholder(FormModel):
    policy_number: str = Field(
        title='Policy number',
        pattern=r'^[A-Z]{2}-\d{6}$',
        description='As printed on your insurance card, such as AU-482913',
        ui_cols=6,
    )
    full_name: str = Field(title='Full name', min_length=2, ui_cols=6)
    phone: str = Field(
        title='Phone',
        pattern=_US_PHONE,
        ui_element='phone',
        ui_placeholder='(303) 555-0164',
        ui_cols=6,
    )
    email: EmailStr = Field(title='Email', ui_element='email', ui_cols=6)


class OtherParty(FormModel):
    name: str = Field(title='Their name', min_length=2, ui_cols=6)
    insurer: str = Field(title='Their insurer', min_length=2, ui_cols=6)
    plate: str = Field(title='Their license plate', min_length=2, ui_cols=6)
    phone: str = Field('', title='Their phone (optional)', ui_element='phone', ui_cols=6)


class Photos(FormModel):
    photos: list[UploadedFile] = Field(
        default_factory=list,
        title='Photos of the damage (up to 6)',
        description='JPEG, PNG or HEIC, up to 8 MB each. You can add more later.',
        ui_max_files=6,
        ui_max_size=_PHOTO_LIMIT,
        ui_options={'accept': '.jpg,.jpeg,.png,.heic'},
    )


class InsuranceClaimForm(FormModel):
    """Several photos, a step skipped when nobody else was involved, policy dates."""

    policyholder: Policyholder = Field(title='Your policy')
    incident_date: date = Field(title='Date of the incident', ui_group='What happened', ui_cols=6)
    location: str = Field(
        title='Where (city and state)', min_length=3, ui_group='What happened', ui_cols=6
    )
    description: str = Field(
        title='What happened',
        min_length=20,
        max_length=2000,
        ui_element='textarea',
        ui_group='What happened',
    )
    other_party: Literal['yes', 'no'] = Field(
        'no',
        title='Was another vehicle or person involved?',
        ui_element='radio',
        ui_options={'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
        ui_group='What happened',
    )
    other_party_details: OtherParty | None = Field(
        None,
        title='The other party',
        ui_show_when={'field': 'other_party', 'equals': 'yes'},
    )
    evidence: Photos = Field(title='Photos')

    @field_validator('incident_date')
    @classmethod
    def _not_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError('The incident date cannot be in the future')
        return value

    @model_validator(mode='after')
    def _covered(self) -> 'InsuranceClaimForm':
        dates = _policies().get(self.policyholder.policy_number)
        if dates is None:
            raise ValueError('We could not find that policy number; check your insurance card')
        start, end = dates
        if not start <= self.incident_date <= end:
            raise ValueError(
                f'Policy {self.policyholder.policy_number} covers {start:%B %-d, %Y} to '
                f'{end:%B %-d, %Y}; the incident date is outside it'
            )
        return self


def _insurance_claim_result(data: dict[str, Any]) -> SafeHTML:
    holder = data['policyholder']
    photos = len(data['evidence']['photos'])
    claim = f'CL-{secrets.randbelow(900_000) + 100_000}'
    return html(
        t'<p>Thanks, {holder["full_name"]}. Claim {claim} is open on policy '
        t'{holder["policy_number"]}, with {photos} photo(s). An adjuster will call '
        t'{holder["phone"]} within two business days.</p>'
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
    # True when the example's module adds its own routes (the job application).
    own_routes: bool = False


WIZARD_EXAMPLES = [
    WizardExample(
        slug='job-application',
        title='Job application',
        summary=(
            'The fullest example: sign in, apply in saved steps, then edit what you sent '
            'and see every change marked.'
        ),
        features=(
            'A sign-in page before the wizard',
            'Each step saved on the server (save_steps)',
            'Resume upload with a type and size limit',
            'Work history as a repeating list',
            'An edit page that marks what changed',
        ),
        model=None,  # type: ignore[arg-type]
        result=None,  # type: ignore[arg-type]
        own_routes=True,
    ),
    WizardExample(
        slug='project-planner',
        title='Project planner',
        summary='Plan a project: team, milestones and tasks, in any order you like.',
        features=(
            'Jump to any step (linear=False)',
            'Team, milestones and tasks as lists',
            'End after start, and milestones within the dates',
            'Budget with ge and multiple_of',
            'Review step',
        ),
        model=ProjectPlanForm,
        result=_project_plan_result,
        demo=_project_plan_demo,
        options={'wizard_options': {'linear': False, 'review_step': True}},
    ),
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
        slug='car-setup',
        title='Car setup',
        summary='Build a car one choice at a time, then see the price.',
        features=(
            'Fixed steps from ui_group',
            'A tow package only trucks are offered (ui_show_when)',
            'Back and Next renamed (back_label, next_label)',
            'Review step titled "Your build"',
        ),
        model=CarSetupForm,
        result=_car_setup_result,
        demo={
            'body': 'truck',
            'powertrain': 'hybrid',
            'trim': 'sport',
            'paint': 'blue',
            'extras': ['heated_seats', 'assist'],
            'tow_package': True,
        },
        options={
            'wizard_options': {
                'back_label': 'Previous choice',
                'next_label': 'Continue',
                'review_step': {'title': 'Your build'},
            },
            'progress': True,
        },
    ),
    WizardExample(
        slug='rental-application',
        title='Rental application',
        summary=(
            'Apply for an apartment with co-applicants; their incomes together must '
            'cover three times the rent.'
        ),
        features=(
            'Co-applicants and references as repeating lists',
            'An income check across steps (@model_validator)',
            'Several uploads (ui_max_files)',
            'A pets question that shows when needed',
            'Review step and progress ticks',
        ),
        model=RentalApplicationForm,
        result=_rental_application_result,
        demo=lambda: {
            'home': {
                'unit': '2b',
                'move_in': (date.today() + timedelta(days=45)).isoformat(),
                'lease': '12',
                'has_pets': True,
                'pets': 'One cat, 9 lb',
            },
            'renter': {
                'full_name': 'Jordan Example',
                'email': 'jordan@example.com',
                'phone': '(512) 555-0187',
                'employer': 'Northwind Design',
                'monthly_income': 6_000,
            },
            'co_applicants': [
                {'full_name': 'Sam Example', 'relationship': 'partner', 'monthly_income': 2_500}
            ],
            'documents': {},
            'references': [
                {
                    'name': 'Pat Landlord',
                    'phone': '(512) 555-0110',
                    'relationship': 'Previous landlord',
                }
            ],
        },
        options={'wizard_options': {'review_step': True}, 'progress': True},
    ),
    WizardExample(
        slug='insurance-claim',
        title='Insurance claim',
        summary='Report damage to your car, with photos, checked against your policy dates.',
        features=(
            'Several photo uploads (ui_max_files)',
            'An other-party step, skipped when nobody else was involved',
            'Incident date checked against the policy (@model_validator)',
            'Review step and progress ticks',
        ),
        model=InsuranceClaimForm,
        result=_insurance_claim_result,
        demo=lambda: {
            'policyholder': {
                'policy_number': 'AU-482913',
                'full_name': 'Jordan Example',
                'phone': '(303) 555-0164',
                'email': 'jordan@example.com',
            },
            'incident_date': (date.today() - timedelta(days=3)).isoformat(),
            'location': 'Denver, CO',
            'description': 'Another car backed into my parked car at a grocery store lot '
            'and dented the rear bumper.',
            'other_party': 'yes',
            'other_party_details': {
                'name': 'Casey Example',
                'insurer': 'Example Mutual',
                'plate': '8XYZ221',
                'phone': '(303) 555-0199',
            },
            'evidence': {},
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
    if not _example.own_routes:
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


# The job application adds its own routes to this router (sign-in, apply, edit).
from examples import job_application_example  # noqa: E402,F401
