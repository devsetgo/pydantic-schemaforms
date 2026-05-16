"""Performance benchmarks using pytest-benchmark.

These track rendering speed for representative models so regressions are
visible in CI output over time. Run with:
    pytest tests/test_benchmarks.py --benchmark-only
Or together with the test suite:
    pytest tests/test_benchmarks.py --benchmark-disable   (just validates, no timing)
"""

from __future__ import annotations

from typing import Optional

from pydantic import EmailStr

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.schema_form import Field, FormModel


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class SimpleForm(FormModel):
    name: str = Field(..., min_length=2, description='Full Name')
    email: EmailStr = Field(..., description='Email', ui_element='email')


class MediumForm(FormModel):
    first_name: str = Field(..., min_length=2, description='First Name', ui_autofocus=True)
    last_name: str = Field(..., min_length=2, description='Last Name')
    email: EmailStr = Field(..., description='Email', ui_element='email')
    age: int = Field(..., ge=18, le=120, description='Age', ui_element='number')
    bio: Optional[str] = Field(None, max_length=500, description='Bio', ui_element='textarea')
    newsletter: bool = Field(False, description='Subscribe', ui_element='checkbox')
    rating: int = Field(3, ge=1, le=5, description='Rating', ui_element='range')


class LargeForm(FormModel):
    first_name: str = Field(..., min_length=2, description='First Name')
    last_name: str = Field(..., min_length=2, description='Last Name')
    email: EmailStr = Field(..., description='Email', ui_element='email')
    phone: Optional[str] = Field(None, description='Phone', ui_element='tel')
    website: Optional[str] = Field(None, description='Website', ui_element='url')
    age: int = Field(..., ge=18, le=120, description='Age', ui_element='number')
    height: Optional[float] = Field(None, ge=0.5, le=3.0, description='Height')
    weight: Optional[float] = Field(None, ge=20.0, le=300.0, description='Weight')
    bio: Optional[str] = Field(None, max_length=500, description='Bio', ui_element='textarea')
    notes: Optional[str] = Field(None, max_length=200, description='Notes', ui_element='textarea')
    country: Optional[str] = Field(None, description='Country')
    city: Optional[str] = Field(None, description='City')
    zip_code: Optional[str] = Field(None, description='ZIP')
    newsletter: bool = Field(False, description='Newsletter', ui_element='checkbox')
    terms: bool = Field(..., description='Terms', ui_element='checkbox')
    rating: int = Field(3, ge=1, le=5, description='Rating', ui_element='range')
    color: str = Field('#3498db', description='Color', ui_element='color')
    birth_date: Optional[str] = Field(None, description='Birth Date', ui_element='date')
    appointment: Optional[str] = Field(None, description='Appointment', ui_element='datetime-local')
    search: Optional[str] = Field(None, description='Search', ui_element='search')


# ---------------------------------------------------------------------------
# Benchmarks: render_form_html (full render with submit button)
# ---------------------------------------------------------------------------


def test_bench_simple_form_bootstrap(benchmark) -> None:
    """Benchmark simple form rendering with Bootstrap theme."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    benchmark(renderer.render_form_from_model, SimpleForm)


def test_bench_simple_form_material(benchmark) -> None:
    """Benchmark simple form rendering with Material theme."""
    renderer = EnhancedFormRenderer(framework='material')
    benchmark(renderer.render_form_from_model, SimpleForm)


def test_bench_simple_form_none(benchmark) -> None:
    """Benchmark simple form rendering with plain HTML theme."""
    renderer = EnhancedFormRenderer(framework='none')
    benchmark(renderer.render_form_from_model, SimpleForm)


def test_bench_medium_form_bootstrap(benchmark) -> None:
    """Benchmark medium form (7 fields) with Bootstrap theme."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    benchmark(renderer.render_form_from_model, MediumForm)


def test_bench_medium_form_material(benchmark) -> None:
    """Benchmark medium form (7 fields) with Material theme."""
    renderer = EnhancedFormRenderer(framework='material')
    benchmark(renderer.render_form_from_model, MediumForm)


def test_bench_large_form_bootstrap(benchmark) -> None:
    """Benchmark large form (20 fields) with Bootstrap theme."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    benchmark(renderer.render_form_from_model, LargeForm)


def test_bench_large_form_material(benchmark) -> None:
    """Benchmark large form (20 fields) with Material theme."""
    renderer = EnhancedFormRenderer(framework='material')
    benchmark(renderer.render_form_from_model, LargeForm)


def test_bench_render_form_html_public_api(benchmark) -> None:
    """Benchmark the public render_form_html API."""
    benchmark(render_form_html, MediumForm, submit_url='/submit')


# ---------------------------------------------------------------------------
# Benchmarks: repeated renders (cache effectiveness)
# ---------------------------------------------------------------------------


def test_bench_repeated_render_same_model(benchmark) -> None:
    """Benchmark repeated renders of the same model (tests cache benefit)."""
    renderer = EnhancedFormRenderer(framework='bootstrap')

    def render_ten_times():
        for _ in range(10):
            renderer.render_form_from_model(SimpleForm)

    benchmark(render_ten_times)


# ---------------------------------------------------------------------------
# Benchmarks: render with pre-filled data and errors
# ---------------------------------------------------------------------------


def test_bench_render_with_data(benchmark) -> None:
    """Benchmark rendering with pre-filled initial data."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    data = {
        'first_name': 'Alice',
        'last_name': 'Smith',
        'age': 30,
        'bio': 'Software developer',
        'newsletter': True,
        'rating': 4,
    }
    benchmark(renderer.render_form_from_model, MediumForm, data)


def test_bench_render_with_errors(benchmark) -> None:
    """Benchmark rendering a form with validation errors displayed."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    errors = {
        'first_name': 'Name is too short',
        'email': 'Invalid email format',
        'age': 'Must be at least 18',
    }
    benchmark(renderer.render_form_from_model, MediumForm, errors=errors)


# ---------------------------------------------------------------------------
# Benchmarks: fields-only rendering (no form wrapper)
# ---------------------------------------------------------------------------


def test_bench_fields_only_medium(benchmark) -> None:
    """Benchmark rendering fields only (no form wrapper) for medium form."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    benchmark(renderer.render_form_fields_only, MediumForm)


def test_bench_fields_only_large(benchmark) -> None:
    """Benchmark rendering fields only (no form wrapper) for large form."""
    renderer = EnhancedFormRenderer(framework='bootstrap')
    benchmark(renderer.render_form_fields_only, LargeForm)
