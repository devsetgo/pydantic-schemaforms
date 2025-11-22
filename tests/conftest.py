"""
PyTest configuration and fixtures for pydantic-forms tests.
"""

from datetime import date
from typing import Any, Dict, List, Optional

import pytest
from pydantic import EmailStr, ValidationError

from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
from pydantic_forms.inputs import (
    CheckboxInput,
    ColorInput,
    DateInput,
    DatetimeInput,
    EmailInput,
    FileInput,
    HiddenInput,
    NumberInput,
    PasswordInput,
    RangeInput,
    SearchInput,
    SelectInput,
    TelInput,
    TextArea,
    TextInput,
    URLInput,
)
from pydantic_forms.layouts import GridLayout, HorizontalLayout, VerticalLayout
# Import pydantic-forms components
from pydantic_forms.schema_form import Field, FormModel

# ==================== TEST FIXTURES ====================


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 25,
        "phone": "+1-555-0123",
        "website": "https://johndoe.com",
        "bio": "Software developer",
        "newsletter": True,
        "birth_date": "1998-01-15",
        "favorite_color": "#3498db",
        "rating": 4,
    }


@pytest.fixture
def invalid_form_data():
    """Invalid form data for testing validation."""
    return {
        "name": "",  # Too short
        "email": "invalid-email",  # Invalid format
        "age": -5,  # Invalid range
        "website": "not-a-url",  # Invalid URL
        "bio": "x" * 1001,  # Too long
        "birth_date": "invalid-date",  # Invalid date
    }


@pytest.fixture
def simple_form_model():
    """Simple form model for basic testing."""

    class SimpleForm(FormModel):
        name: str = Field(..., min_length=2, description="Your name", ui_autofocus=True)
        email: EmailStr = Field(..., description="Email address", ui_element="email")
        age: int = Field(..., ge=18, le=120, description="Your age", ui_element="number")
        newsletter: bool = Field(
            False, description="Subscribe to newsletter", ui_element="checkbox"
        )

    return SimpleForm


@pytest.fixture
def complex_form_model():
    """Complex form model with various field types."""

    class ComplexForm(FormModel):
        # Text fields
        first_name: str = Field(..., min_length=2, description="First name", ui_autofocus=True)
        last_name: str = Field(..., min_length=2, description="Last name")
        email: EmailStr = Field(..., description="Email address", ui_element="email")
        phone: Optional[str] = Field(None, description="Phone number", ui_element="tel")
        website: Optional[str] = Field(None, description="Website", ui_element="url")

        # Numeric fields
        age: int = Field(..., ge=13, le=120, description="Age", ui_element="number")
        height: Optional[float] = Field(None, ge=0.5, le=3.0, description="Height in meters")
        rating: int = Field(..., ge=1, le=5, description="Rating", ui_element="range")

        # Date/time fields
        birth_date: Optional[date] = Field(None, description="Birth date", ui_element="date")
        appointment_time: Optional[str] = Field(
            None, description="Appointment", ui_element="datetime-local"
        )

        # Text areas
        bio: Optional[str] = Field(
            None,
            max_length=500,
            description="Biography",
            ui_element="textarea",
            ui_options={"rows": 4},
        )
        comments: Optional[str] = Field(
            None, max_length=200, description="Comments", ui_element="textarea"
        )

        # Selection fields
        country: Optional[str] = Field(None, description="Country")
        gender: Optional[str] = Field(None, description="Gender")

        # Boolean fields
        newsletter: bool = Field(False, description="Newsletter", ui_element="checkbox")
        terms: bool = Field(..., description="Accept terms", ui_element="checkbox")

        # Special fields
        favorite_color: str = Field("#3498db", description="Favorite color", ui_element="color")
        profile_picture: Optional[str] = Field(
            None, description="Profile picture", ui_element="file"
        )

    return ComplexForm


@pytest.fixture
def enhanced_renderer():
    """Enhanced form renderer instance for testing."""
    return EnhancedFormRenderer()


@pytest.fixture
def form_renderer():
    """Form renderer instance for testing."""
    return EnhancedFormRenderer()


@pytest.fixture
def bootstrap_renderer():
    """Bootstrap form renderer."""
    return EnhancedFormRenderer(framework="bootstrap")


@pytest.fixture
def material_renderer():
    """Material Design form renderer."""
    return EnhancedFormRenderer(framework="material")


@pytest.fixture
def plain_renderer():
    """Plain HTML form renderer."""
    return EnhancedFormRenderer(framework="none")


@pytest.fixture
def sample_validation_errors():
    """Sample validation errors for testing."""
    return [
        {"name": "name", "message": "This field is required"},
        {"name": "email", "message": "Invalid email format"},
        {"name": "age", "message": "Must be at least 18"},
    ]


@pytest.fixture
def all_input_types():
    """Dictionary of all input type instances for testing."""
    return {
        "text": TextInput(),
        "password": PasswordInput(),
        "email": EmailInput(),
        "number": NumberInput(),
        "checkbox": CheckboxInput(),
        "select": SelectInput(),
        "date": DateInput(),
        "datetime": DatetimeInput(),
        "file": FileInput(),
        "color": ColorInput(),
        "range": RangeInput(),
        "hidden": HiddenInput(),
        "textarea": TextArea(),
        "search": SearchInput(),
        "tel": TelInput(),
        "url": URLInput(),
    }


@pytest.fixture
def sample_select_options():
    """Sample options for select inputs."""
    return [
        {"value": "us", "label": "United States", "selected": False},
        {"value": "ca", "label": "Canada", "selected": False},
        {"value": "uk", "label": "United Kingdom", "selected": True},
        {"value": "de", "label": "Germany", "selected": False},
    ]


@pytest.fixture
def sample_radio_options():
    """Sample options for radio inputs."""
    return [
        {"value": "male", "label": "Male"},
        {"value": "female", "label": "Female"},
        {"value": "other", "label": "Other"},
    ]


@pytest.fixture
def layout_components():
    """Layout component instances for testing."""
    return {
        "horizontal": HorizontalLayout(),
        "vertical": VerticalLayout(),
        "grid": GridLayout(),
    }


# ==================== PYTEST CONFIGURATION ====================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "framework: mark test as framework-specific")


# ==================== HELPER FUNCTIONS ====================


def assert_html_contains(html: str, expected: str, msg: str = ""):
    """Assert that HTML contains expected content."""
    assert expected in html, f"{msg}. Expected '{expected}' in HTML: {html[:200]}..."


def assert_html_has_attribute(html: str, tag: str, attribute: str, value: str = None):
    """Assert that HTML has a tag with specific attribute."""
    if value:
        expected = f'{tag}.*{attribute}="{value}"'
    else:
        expected = f"{tag}.*{attribute}"

    import re

    assert re.search(
        expected, html, re.IGNORECASE
    ), f"Expected {tag} with {attribute}={value} in HTML"


def assert_form_validates(form_model, data: Dict[str, Any]):
    """Assert that form data validates successfully."""
    try:
        instance = form_model(**data)
        return instance
    except ValidationError as e:
        pytest.fail(f"Form validation failed: {e.errors()}")


def assert_form_validation_fails(
    form_model, data: Dict[str, Any], expected_fields: List[str] = None
):
    """Assert that form data validation fails."""
    with pytest.raises(ValidationError) as exc_info:
        form_model(**data)

    if expected_fields:
        error_fields = [err["loc"][0] for err in exc_info.value.errors()]
        for field in expected_fields:
            assert field in error_fields, f"Expected validation error for field '{field}'"


def normalize_html(html: str) -> str:
    """Normalize HTML for comparison by removing extra whitespace."""
    import re

    # Remove extra whitespace and normalize
    html = re.sub(r"\s+", " ", html.strip())
    html = re.sub(r">\s+<", "><", html)
    return html


def extract_form_fields(html: str) -> List[str]:
    """Extract form field names from HTML."""
    import re

    # Find all name attributes in form inputs
    matches = re.findall(r'name=["\']([^"\']+)["\']', html)
    return matches


# ==================== CUSTOM ASSERTIONS ====================


class FormHTMLAssertion:
    """Custom assertion helper for form HTML testing."""

    def __init__(self, html: str):
        self.html = html
        self.normalized = normalize_html(html)

    def has_input(self, name: str, input_type: str = None) -> "FormHTMLAssertion":
        """Assert form has an input with given name and type."""
        if input_type:
            pattern = f'<input[^>]*name="{name}"[^>]*type="{input_type}"'
        else:
            pattern = f'<input[^>]*name="{name}"'

        import re

        assert re.search(
            pattern, self.html, re.IGNORECASE
        ), f"Expected input with name='{name}' and type='{input_type}'"
        return self

    def has_label(self, text: str) -> "FormHTMLAssertion":
        """Assert form has a label with given text."""
        assert "<label" in self.html and text in self.html, f"Expected label with text '{text}'"
        return self

    def has_required_field(self, name: str) -> "FormHTMLAssertion":
        """Assert form has a required field."""
        pattern = f'name="{name}"[^>]*required'
        import re

        assert re.search(pattern, self.html, re.IGNORECASE), f"Expected required field '{name}'"
        return self

    def has_css_class(self, css_class: str) -> "FormHTMLAssertion":
        """Assert form has elements with specific CSS class."""
        assert (
            f'class="{css_class}"' in self.html or f"class='{css_class}'" in self.html
        ), f"Expected CSS class '{css_class}'"
        return self


@pytest.fixture
def assert_form_html():
    """Factory for FormHTMLAssertion."""

    def _assert_form_html(html: str):
        return FormHTMLAssertion(html)

    return _assert_form_html
