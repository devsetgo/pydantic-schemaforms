#!/usr/bin/env python3
"""
Job application: the fullest wizard example (#276). Imported by
examples/wizard_examples.py, whose router it adds its routes to.

Three pages:

- ``/wizards/job-application/sign-in``: create an applicant account, a plain
  form outside the wizard, with an intro content block and a password match.
- ``/wizards/job-application``: the application. Each step is saved on the
  server (``save_steps``), so the applicant can leave and come back; the page
  also autosaves a draft in the browser and warns before leaving unsaved
  changes. The resume is uploaded on its own step and stored by its ``ref``.
  A review step comes before Submit.
- ``/wizards/job-application/edit``: change a submitted application. A
  one-POST wizard rendered with the saved answers, so its review step shows
  what changed as old → new.

Accounts, drafts and files live in memory, keyed by a cookie: a stand-in for
the app's database and file store. The data is made up.
"""

import secrets
from datetime import date, timedelta
from typing import Any, Literal

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import EmailStr, ValidationInfo, field_validator, model_validator

from examples.fastapi_routes import _material_variant, _variant_query, templates
from examples.wizard_examples import _DEFAULT_STYLE, _PAGE, _US_PHONE, _back_to_index, router
from pydantic_schemaforms import (
    Field,
    FormModel,
    SafeHTML,
    UploadedFile,
    html,
    render_form_html_async,
)

_SESSION_COOKIE = 'sf_job_application'
# One entry per applicant: email, the wizard's draft, stored files and the
# submitted application. In memory for the demo; a real app uses its database.
_APPLICANTS: dict[str, dict[str, Any]] = {}
_RESUME_LIMIT = 2 * 1024 * 1024

_ROLES = [
    {'value': 'frontend', 'label': 'Frontend engineer'},
    {'value': 'backend', 'label': 'Backend engineer'},
    {'value': 'designer', 'label': 'Product designer'},
    {'value': 'pm', 'label': 'Product manager'},
    {'value': 'support', 'label': 'Customer support specialist'},
]
_LOCATIONS = [
    {'value': 'nyc', 'label': 'New York, NY'},
    {'value': 'austin', 'label': 'Austin, TX'},
    {'value': 'seattle', 'label': 'Seattle, WA'},
    {'value': 'remote', 'label': 'Remote (US)'},
]


# --- Sign-in, outside the wizard ----------------------------------------------
class SignInForm(FormModel):
    intro: None = Field(
        ui_element='content',
        ui_content=(
            'Create an applicant account to start. Your application is saved after '
            'each step, so you can stop and come back to it.'
        ),
    )
    email: EmailStr = Field(title='Email', ui_element='email')
    password: str = Field(title='Password', ui_element='password', min_length=10)
    confirm_password: str = Field(title='Confirm password', ui_element='password')

    @field_validator('confirm_password')
    @classmethod
    def _passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value


_SIGN_IN_DEMO = {
    'email': 'jordan@example.com',
    'password': 'example-pass-2027',
    'confirm_password': 'example-pass-2027',
}


# --- The application -----------------------------------------------------------
class Position(FormModel):
    role: Literal['frontend', 'backend', 'designer', 'pm', 'support'] = Field(
        title='Role', ui_element='select', ui_options={'choices': _ROLES}
    )
    location: Literal['nyc', 'austin', 'seattle', 'remote'] = Field(
        title='Location', ui_element='radio', ui_options={'choices': _LOCATIONS}
    )
    start_date: date = Field(title='Earliest start date')
    salary: int = Field(
        title='Expected salary (USD per year)',
        ge=30_000,
        le=500_000,
        multiple_of=1_000,
        description='In whole thousands, such as 120000',
    )


class Resume(FormModel):
    resume: UploadedFile = Field(
        title='Resume (PDF or Word, up to 2 MB)',
        ui_max_size=_RESUME_LIMIT,
        ui_options={'accept': '.pdf,.docx'},
    )
    portfolio: str = Field(
        '',
        title='Portfolio or LinkedIn (optional)',
        pattern=r'^(https?://\S+)?$',
        ui_element='url',
    )
    cover_letter: str = Field(
        '', title='Cover letter (optional)', max_length=2000, ui_element='textarea'
    )


class ResumeEdit(Resume):
    """On the edit page the resume was already sent, so a new one is optional."""

    resume: UploadedFile | None = Field(  # type: ignore[assignment]
        None,
        title='Replace your resume (optional)',
        description='Leave this empty to keep the resume you sent.',
        ui_max_size=_RESUME_LIMIT,
        ui_options={'accept': '.pdf,.docx'},
    )


class Contact(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    email: EmailStr = Field(title='Email', ui_element='email')
    phone: str = Field(
        title='Phone',
        pattern=_US_PHONE,
        description='A US number, such as (212) 555-0142',
        ui_element='phone',
        ui_options={'phone_format': '(###) ###-####'},
    )
    city: str = Field(title='City', min_length=2, ui_cols=8)
    state: str = Field(title='State', pattern=r'^[A-Z]{2}$', ui_placeholder='TX', ui_cols=4)


class Job(FormModel):
    employer: str = Field(title='Employer', min_length=2)
    title: str = Field(title='Job title', min_length=2)
    started: date = Field(title='Started')
    ended: date | None = Field(None, title='Ended', description='Leave empty for your current job')

    @model_validator(mode='after')
    def _ended_after_started(self) -> 'Job':
        if self.ended is not None and self.ended < self.started:
            raise ValueError('The end date is before the start date')
        return self


class Disclosures(FormModel):
    authorized: Literal['yes', 'no'] = Field(
        title='Are you authorized to work in the US?',
        ui_element='radio',
        ui_options={'choices': [{'value': 'yes', 'label': 'Yes'}, {'value': 'no', 'label': 'No'}]},
    )
    sponsorship: bool = Field(
        False,
        title='I will need visa sponsorship',
        ui_show_when={'field': 'authorized', 'equals': 'no'},
    )
    consent: Literal[True] = Field(
        ui_element='consent',
        title='I confirm my answers are true',
        ui_content=(
            'We keep your application for 12 months and use it only to assess you for '
            'this and similar roles. You can ask us to delete it at any time.'
        ),
        unchecked_message='Please confirm your answers before you submit',
    )


class JobApplicationForm(FormModel):
    position: Position = Field(title='Position')
    documents: Resume = Field(title='Resume')
    contact: Contact = Field(title='Contact details')
    work_history: list[Job] = Field(
        default_factory=list,
        title='Work history',
        max_length=8,
        ui_add_button_label='Add a job',
        ui_item_title_template='{employer}',
    )
    disclosures: Disclosures = Field(title='Disclosures')


class JobApplicationEdit(JobApplicationForm):
    documents: ResumeEdit = Field(title='Resume')  # type: ignore[assignment]


def _demo_application() -> dict[str, Any]:
    today = date.today()
    return {
        'position': {
            'role': 'frontend',
            'location': 'remote',
            'start_date': (today + timedelta(days=30)).isoformat(),
            'salary': 120_000,
        },
        'documents': {
            'portfolio': 'https://example.com/jordan',
            'cover_letter': 'I build accessible, fast interfaces and I would like to help '
            'your team ship forms people enjoy filling in.',
        },
        'contact': {
            'full_name': 'Jordan Example',
            'email': 'jordan@example.com',
            'phone': '(212) 555-0142',
            'city': 'Austin',
            'state': 'TX',
        },
        'work_history': [
            {
                'employer': 'Northwind Design',
                'title': 'Senior frontend engineer',
                'started': '2022-03-01',
                'ended': None,
            },
            {
                'employer': 'Contoso Labs',
                'title': 'Frontend engineer',
                'started': '2019-06-01',
                'ended': '2022-02-28',
            },
        ],
        'disclosures': {'authorized': 'yes', 'sponsorship': False, 'consent': True},
    }


# --- Session plumbing (a stand-in for the app's own) --------------------------
def _applicant(request: Request) -> dict[str, Any] | None:
    return _APPLICANTS.get(request.cookies.get(_SESSION_COOKIE, ''))


def _query(style: str, variant: str | None) -> str:
    return f'style={style}{_variant_query(variant)}'


def _sign_in_redirect(style: str, variant: str | None) -> RedirectResponse:
    return RedirectResponse(
        f'/wizards/job-application/sign-in?{_query(style, variant)}', status_code=303
    )


def _page(request: Request, style: str, title: str, description: str, form_html: str):
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': title,
            'description': description,
            'framework_type': style,
            'form_html': form_html,
            **_PAGE,
            **_back_to_index(style),
        },
    )


def _done_page(request: Request, style: str, title: str, body: SafeHTML, data: dict[str, Any]):
    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': title,
            'message': 'Here is what we received.',
            'display_html': str(body),
            'data': data,
            **_PAGE,
            **_back_to_index(style),
            'try_again_url': f'/wizards/job-application?{_query(style, "")}',
        },
    )


# --- Sign-in routes ------------------------------------------------------------
def _sign_in_options(style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/wizards/job-application/sign-in?{_query(style, variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
    }


_SIGN_IN_DESCRIPTION = 'Step one of the job application example: an account, outside the wizard.'


@router.get('/wizards/job-application/sign-in', response_class=HTMLResponse, tags=['Wizards'])
async def job_sign_in_get(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None, demo: bool = True
):
    """Create an applicant account before the application wizard."""
    form_html = await render_form_html_async(
        SignInForm, form_data=_SIGN_IN_DEMO if demo else None, **_sign_in_options(style, variant)
    )
    return _page(request, style, 'Job application: sign in', _SIGN_IN_DESCRIPTION, form_html)


@router.post('/wizards/job-application/sign-in', response_class=HTMLResponse, tags=['Wizards'])
async def job_sign_in_post(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None
) -> Response:
    result = SignInForm.validate(await request.form(), **_sign_in_options(style, variant))
    if not result.is_valid:
        form_html = await result.render_with_errors_async()
        return _page(request, style, 'Job application: sign in', _SIGN_IN_DESCRIPTION, form_html)
    session = secrets.token_urlsafe(16)
    _APPLICANTS[session] = {
        'email': result.data['email'],
        'draft': None,
        'files': {},
        'submitted': None,
    }
    response = RedirectResponse(f'/wizards/job-application?{_query(style, variant)}', 303)
    response.set_cookie(_SESSION_COOKIE, session, httponly=True, samesite='lax')
    return response


# --- The application wizard ----------------------------------------------------
def _apply_options(style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/wizards/job-application?{_query(style, variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
        'layout': 'wizard',
        'wizard_options': {
            'save_steps': True,
            'review_step': {'title': 'Review and submit'},
            'next_label': 'Save and continue',
        },
        'autosave': True,
        'warn_unsaved': True,
    }


_APPLY_DESCRIPTION = (
    'Each step is saved on the server as you go, so you can stop and come back. '
    'Every step opens with demo answers; on the Resume step, choose any PDF or Word file.'
)


@router.get('/wizards/job-application', response_class=HTMLResponse, tags=['Wizards'])
async def job_application_get(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None, demo: bool = True
) -> Response:
    """The application wizard; signs the applicant in first."""
    applicant = _applicant(request)
    if applicant is None:
        return _sign_in_redirect(style, variant)
    applicant['demo'] = demo
    form_html = await render_form_html_async(
        JobApplicationForm,
        draft=applicant['draft'],
        form_data=_starting_values(applicant),
        **_apply_options(style, variant),
    )
    return _page(request, style, 'Job application', _APPLY_DESCRIPTION, form_html)


@router.post('/wizards/job-application', response_class=HTMLResponse, tags=['Wizards'])
async def job_application_post(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None
) -> Response:
    applicant = _applicant(request)
    if applicant is None:
        return _sign_in_redirect(style, variant)
    result = JobApplicationForm.validate_step(
        await request.form(), draft=applicant['draft'], **_apply_options(style, variant)
    )
    if result.is_complete:
        resume = result.data['documents']['resume']
        applicant['draft'] = None
        applicant['submitted'] = _stored(result.data)
        applicant['resume_name'] = resume.filename
        return _done_page(
            request, style, 'Application sent', _thanks(result.data, style), result.data
        )
    if result.is_valid:
        for upload in result.files:
            upload.ref = secrets.token_hex(8)
            applicant['files'][upload.ref] = upload.read()
        applicant['draft'] = result.draft
    form_html = await result.render_async(data=_starting_values(applicant))
    return _page(request, style, 'Job application', _APPLY_DESCRIPTION, form_html)


def _starting_values(applicant: dict[str, Any]) -> dict[str, Any] | None:
    """The demo answers under the saved steps, so every step opens filled in."""

    return _demo_application() if applicant.get('demo', True) else None


def _stored(data: dict[str, Any]) -> dict[str, Any]:
    """The submitted answers as plain values, for the edit page; the resume
    file stays in the file store."""

    stored = dict(data)
    stored['documents'] = {k: v for k, v in data['documents'].items() if k != 'resume'}
    stored['position'] = {**data['position'], 'start_date': str(data['position']['start_date'])}
    stored['work_history'] = [
        {
            **job,
            'started': str(job['started']),
            'ended': str(job['ended']) if job['ended'] else None,
        }
        for job in data['work_history']
    ]
    return stored


def _thanks(data: dict[str, Any], style: str) -> SafeHTML:
    roles = {choice['value']: choice['label'] for choice in _ROLES}
    name = data['contact']['full_name']
    role = roles[data['position']['role']]
    edit = f'/wizards/job-application/edit?style={style}'
    display = JobApplicationForm.render_display(data, framework=style)
    return html(
        t'<p>Thanks, {name}. We received your application for {role}.</p>'
        t'<p><a href="{edit}">Edit your application</a> to see the review step mark '
        t'what you change.</p>{SafeHTML(display)}'
    )


# --- Editing a submitted application -------------------------------------------
def _edit_options(style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/wizards/job-application/edit?{_query(style, variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
        'layout': 'wizard',
        'wizard_options': {'review_step': {'title': 'Check your changes', 'edit_label': 'Change'}},
    }


_EDIT_DESCRIPTION = (
    'Your submitted application, one form and one POST. Change anything, then the '
    'review step shows each change as old → new before you save.'
)


@router.get('/wizards/job-application/edit', response_class=HTMLResponse, tags=['Wizards'])
async def job_application_edit_get(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None
) -> Response:
    """Change a submitted application; the review step marks every change."""
    applicant = _applicant(request)
    if applicant is None:
        return _sign_in_redirect(style, variant)
    saved = applicant['submitted'] or _demo_application()
    form_html = await render_form_html_async(
        JobApplicationEdit, form_data=saved, **_edit_options(style, variant)
    )
    return _page(request, style, 'Edit your application', _EDIT_DESCRIPTION, form_html)


@router.post('/wizards/job-application/edit', response_class=HTMLResponse, tags=['Wizards'])
async def job_application_edit_post(
    request: Request, style: str = _DEFAULT_STYLE, variant: str | None = None
) -> Response:
    applicant = _applicant(request)
    if applicant is None:
        return _sign_in_redirect(style, variant)
    result = JobApplicationEdit.validate(await request.form(), **_edit_options(style, variant))
    if not result.is_valid:
        form_html = await result.render_with_errors_async()
        return _page(request, style, 'Edit your application', _EDIT_DESCRIPTION, form_html)
    new_resume = result.data['documents'].get('resume')
    if new_resume is not None:
        new_resume.ref = secrets.token_hex(8)
        applicant['files'][new_resume.ref] = new_resume.read()
        applicant['resume_name'] = new_resume.filename
    applicant['submitted'] = _stored(result.data)
    body = html(t'<p>Your changes are saved.</p>{_thanks(result.data, style)}')
    return _done_page(request, style, 'Application updated', body, result.data)
