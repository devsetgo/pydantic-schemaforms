"""HTTP integration tests using FastAPI TestClient and Flask test client.

These tests spin up real HTTP endpoints and exercise the full request/response
cycle: form render → submit → Pydantic validation → response.  They catch
bugs that unit tests miss (e.g. incorrect content-type, missing field names
in the generated form, validation behaviour under HTTP transport).
"""

from __future__ import annotations

import pytest
from pydantic import EmailStr, ValidationError
from typing import Optional

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


# ---------------------------------------------------------------------------
# Shared test models
# ---------------------------------------------------------------------------


class ContactForm(FormModel):
    name: str = Field(..., min_length=2, description='Full Name')
    email: EmailStr = Field(..., description='Email Address', ui_element='email')
    message: str = Field(..., min_length=5, description='Message', ui_element='textarea')


class LoginForm(FormModel):
    username: str = Field(..., min_length=3, description='Username')
    password: str = Field(..., min_length=8, description='Password', ui_element='password')
    remember_me: bool = Field(False, description='Remember Me', ui_element='checkbox')


class NumericForm(FormModel):
    age: int = Field(..., ge=18, le=120, description='Age', ui_element='number')
    score: float = Field(..., ge=0.0, le=100.0, description='Score')
    active: bool = Field(True, description='Active', ui_element='checkbox')


class OptionalFieldForm(FormModel):
    required_name: str = Field(..., min_length=1, description='Name')
    optional_phone: Optional[str] = Field(None, description='Phone', ui_element='tel')
    optional_age: Optional[int] = Field(None, ge=0, description='Age')


# ---------------------------------------------------------------------------
# FastAPI integration
# ---------------------------------------------------------------------------

fastapi = pytest.importorskip('fastapi', reason='fastapi not installed')

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _make_fastapi_app() -> FastAPI:
    app = FastAPI()

    @app.get('/contact', response_class=HTMLResponse)
    def get_contact_form():
        return render_form_html(ContactForm, submit_url='/contact')

    @app.post('/contact')
    async def post_contact_form(request: Request):
        form_data = await request.form()
        raw = dict(form_data)
        try:
            validated = ContactForm(**raw)
            return JSONResponse(
                {
                    'success': True,
                    'name': validated.name,
                    'email': validated.email,
                    'message': validated.message,
                }
            )
        except ValidationError as e:
            return JSONResponse({'success': False, 'errors': e.errors()}, status_code=422)

    @app.get('/login', response_class=HTMLResponse)
    def get_login_form():
        return render_form_html(LoginForm, submit_url='/login')

    @app.post('/login')
    async def post_login_form(request: Request):
        form_data = await request.form()
        raw = dict(form_data)
        # Normalize checkbox: absent means False, 'on'/'true' means True
        raw.setdefault('remember_me', False)
        if raw.get('remember_me') in ('on', 'true', '1'):
            raw['remember_me'] = True
        try:
            validated = LoginForm(**raw)
            return JSONResponse({'success': True, 'username': validated.username})
        except ValidationError as e:
            return JSONResponse({'success': False, 'errors': e.errors()}, status_code=422)

    @app.get('/numeric', response_class=HTMLResponse)
    def get_numeric_form():
        return render_form_html(NumericForm, submit_url='/numeric')

    @app.post('/numeric')
    async def post_numeric_form(request: Request):
        form_data = await request.form()
        raw = dict(form_data)
        try:
            validated = NumericForm(**raw)
            return JSONResponse({'success': True, 'age': validated.age, 'score': validated.score})
        except ValidationError as e:
            return JSONResponse({'success': False, 'errors': e.errors()}, status_code=422)

    @app.get('/optional', response_class=HTMLResponse)
    def get_optional_form():
        return render_form_html(OptionalFieldForm, submit_url='/optional')

    @app.post('/optional')
    async def post_optional_form(request: Request):
        form_data = await request.form()
        raw = {k: v for k, v in dict(form_data).items() if v != ''}
        try:
            validated = OptionalFieldForm(**raw)
            return JSONResponse({'success': True, 'name': validated.required_name})
        except ValidationError as e:
            return JSONResponse({'success': False, 'errors': e.errors()}, status_code=422)

    return app


@pytest.fixture(scope='module')
def fastapi_client() -> TestClient:
    return TestClient(_make_fastapi_app())


class TestFastAPIFormRender:
    def test_contact_form_renders(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.get('/contact')
        assert resp.status_code == 200
        assert '<form' in resp.text
        assert '</form>' in resp.text

    def test_contact_form_has_all_fields(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.get('/contact')
        assert 'name="name"' in resp.text
        assert 'name="email"' in resp.text
        assert 'name="message"' in resp.text

    def test_login_form_has_password_field(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.get('/login')
        assert resp.status_code == 200
        assert 'type="password"' in resp.text

    def test_numeric_form_has_number_inputs(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.get('/numeric')
        assert resp.status_code == 200
        assert 'name="age"' in resp.text
        assert 'name="score"' in resp.text


class TestFastAPIFormSubmission:
    def test_valid_contact_submission(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/contact',
            data={
                'name': 'Alice Smith',
                'email': 'alice@example.com',
                'message': 'Hello there, this is my message.',
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['success'] is True
        assert body['name'] == 'Alice Smith'
        assert body['email'] == 'alice@example.com'

    def test_invalid_contact_name_too_short(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/contact',
            data={
                'name': 'A',
                'email': 'alice@example.com',
                'message': 'Hello there.',
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body['success'] is False
        field_names = [e['loc'][0] for e in body['errors']]
        assert 'name' in field_names

    def test_invalid_email_format(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/contact',
            data={
                'name': 'Alice',
                'email': 'not-an-email',
                'message': 'Hello there.',
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body['success'] is False

    def test_missing_required_field(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/contact',
            data={
                'name': 'Alice',
                'email': 'alice@example.com',
                # message omitted
            },
        )
        assert resp.status_code == 422

    def test_message_too_short(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/contact',
            data={
                'name': 'Alice',
                'email': 'alice@example.com',
                'message': 'Hi',
            },
        )
        assert resp.status_code == 422

    def test_valid_login(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/login',
            data={
                'username': 'alice_user',
                'password': 'securepassword123',
            },
        )
        assert resp.status_code == 200
        assert resp.json()['success'] is True

    def test_login_username_too_short(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/login',
            data={
                'username': 'ab',
                'password': 'securepassword123',
            },
        )
        assert resp.status_code == 422

    def test_login_password_too_short(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/login',
            data={
                'username': 'alice_user',
                'password': 'short',
            },
        )
        assert resp.status_code == 422

    def test_valid_numeric_submission(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/numeric',
            data={
                'age': '25',
                'score': '87.5',
                'active': 'on',
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['success'] is True
        assert body['age'] == 25

    def test_age_below_minimum(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/numeric',
            data={
                'age': '10',
                'score': '50',
            },
        )
        assert resp.status_code == 422

    def test_age_above_maximum(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/numeric',
            data={
                'age': '200',
                'score': '50',
            },
        )
        assert resp.status_code == 422

    def test_optional_fields_only_required(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post('/optional', data={'required_name': 'Bob'})
        assert resp.status_code == 200
        assert resp.json()['success'] is True

    def test_optional_fields_with_all_values(self, fastapi_client: TestClient) -> None:
        resp = fastapi_client.post(
            '/optional',
            data={
                'required_name': 'Bob',
                'optional_phone': '+1-555-0100',
                'optional_age': '30',
            },
        )
        assert resp.status_code == 200
        assert resp.json()['success'] is True


# ---------------------------------------------------------------------------
# Flask integration
# ---------------------------------------------------------------------------

flask_mod = pytest.importorskip('flask', reason='flask not installed')

from flask import Flask, request as flask_request  # noqa: E402


def _make_flask_app() -> Flask:
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/contact', methods=['GET'])
    def flask_get_contact():
        return render_form_html(ContactForm, submit_url='/contact')

    @app.route('/contact', methods=['POST'])
    def flask_post_contact():
        raw = dict(flask_request.form)
        try:
            validated = ContactForm(**raw)
            return {'success': True, 'name': validated.name, 'email': validated.email}
        except ValidationError as e:
            return {'success': False, 'error_count': len(e.errors())}, 422

    @app.route('/login', methods=['GET'])
    def flask_get_login():
        return render_form_html(LoginForm, submit_url='/login')

    @app.route('/login', methods=['POST'])
    def flask_post_login():
        raw = dict(flask_request.form)
        raw.setdefault('remember_me', False)
        if raw.get('remember_me') in ('on', 'true', '1'):
            raw['remember_me'] = True
        try:
            validated = LoginForm(**raw)
            return {'success': True, 'username': validated.username}
        except ValidationError as e:
            return {'success': False, 'error_count': len(e.errors())}, 422

    return app


@pytest.fixture(scope='module')
def flask_client():
    app = _make_flask_app()
    with app.test_client() as client:
        yield client


class TestFlaskFormRender:
    def test_contact_form_renders(self, flask_client) -> None:
        resp = flask_client.get('/contact')
        assert resp.status_code == 200
        assert b'<form' in resp.data

    def test_contact_form_has_all_fields(self, flask_client) -> None:
        resp = flask_client.get('/contact')
        assert b'name="name"' in resp.data
        assert b'name="email"' in resp.data
        assert b'name="message"' in resp.data

    def test_login_form_renders(self, flask_client) -> None:
        resp = flask_client.get('/login')
        assert resp.status_code == 200
        assert b'type="password"' in resp.data


class TestFlaskFormSubmission:
    def test_valid_contact_submission(self, flask_client) -> None:
        resp = flask_client.post(
            '/contact',
            data={
                'name': 'Bob Jones',
                'email': 'bob@example.com',
                'message': 'Hello from Flask test.',
            },
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert body['name'] == 'Bob Jones'

    def test_invalid_contact_submission(self, flask_client) -> None:
        resp = flask_client.post(
            '/contact',
            data={
                'name': 'B',
                'email': 'bad-email',
                'message': 'Hi',
            },
        )
        assert resp.status_code == 422
        body = resp.get_json()
        assert body['success'] is False
        assert body['error_count'] >= 2

    def test_missing_required_field(self, flask_client) -> None:
        resp = flask_client.post(
            '/contact',
            data={
                'name': 'Bob',
                'email': 'bob@example.com',
            },
        )
        assert resp.status_code == 422

    def test_valid_login(self, flask_client) -> None:
        resp = flask_client.post(
            '/login',
            data={
                'username': 'bob_user',
                'password': 'securepass123',
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_invalid_login_short_password(self, flask_client) -> None:
        resp = flask_client.post(
            '/login',
            data={
                'username': 'bob_user',
                'password': 'short',
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Round-trip tests: render form → extract fields → verify they POST correctly
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """These tests confirm that every field name the form renders is also
    the field name Pydantic expects — a regression guard for field-name drift."""

    def test_contact_form_field_names_match_model(self, fastapi_client: TestClient) -> None:
        import re

        html = fastapi_client.get('/contact').text
        rendered_names = set(re.findall(r'name="([^"]+)"', html))
        model_fields = set(ContactForm.model_fields.keys())
        # Every model field should appear as a form input name
        for field in model_fields:
            assert field in rendered_names, (
                f'Model field "{field}" missing from rendered form inputs'
            )

    def test_login_form_field_names_match_model(self, fastapi_client: TestClient) -> None:
        import re

        html = fastapi_client.get('/login').text
        rendered_names = set(re.findall(r'name="([^"]+)"', html))
        model_fields = set(LoginForm.model_fields.keys())
        for field in model_fields:
            assert field in rendered_names, (
                f'Model field "{field}" missing from rendered form inputs'
            )
