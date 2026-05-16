"""Property-based tests using Hypothesis.

These tests generate arbitrary Pydantic models and form data to find edge
cases that hand-written tests miss. They verify invariants that must hold
for all valid inputs — not just the examples we thought of.
"""

from __future__ import annotations

import string
from typing import Optional

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.schema_form import Field, FormModel

from .test_html_structural import assert_valid_html


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Safe Python identifiers for field names
_IDENT_CHARS = string.ascii_lowercase + '_'
_IDENT_STRATEGY = st.text(
    alphabet=string.ascii_lowercase,
    min_size=2,
    max_size=20,
).filter(lambda s: s.isidentifier() and not s.startswith('_'))

_FIELD_LABEL_STRATEGY = st.text(
    alphabet=string.ascii_letters + string.digits + ' .-_',
    min_size=1,
    max_size=60,
)

_FRAMEWORK_STRATEGY = st.sampled_from(['bootstrap', 'material', 'none'])

_UI_ELEMENT_STRATEGY = st.sampled_from(
    [
        'text',
        'email',
        'password',
        'number',
        'checkbox',
        'textarea',
        'date',
        'tel',
        'url',
        'search',
        'hidden',
    ]
)


# ---------------------------------------------------------------------------
# Property: Any valid str field renders without crashing and produces valid HTML
# ---------------------------------------------------------------------------


@given(
    field_name=_IDENT_STRATEGY,
    description=_FIELD_LABEL_STRATEGY,
    required=st.booleans(),
    framework=_FRAMEWORK_STRATEGY,
)
@settings(max_examples=60, suppress_health_check=[HealthCheck.too_slow])
def test_single_str_field_always_renders(
    field_name: str,
    description: str,
    required: bool,
    framework: str,
) -> None:
    """Any single str field with any description must render valid HTML."""
    default = ... if required else ''
    model_fields = {field_name: (str, Field(default, description=description))}

    DynamicForm = type('DynamicForm', (FormModel,), {'__annotations__': {field_name: str}})
    for fname, (ftype, finfo) in model_fields.items():
        DynamicForm.__annotations__[fname] = ftype
        DynamicForm.model_fields[fname] = finfo

    renderer = EnhancedFormRenderer(framework=framework)
    html = renderer.render_form_from_model(DynamicForm)
    assert_valid_html(html, f'{framework}/{field_name}')
    assert f'name="{field_name}"' in html


@given(
    description=_FIELD_LABEL_STRATEGY,
    framework=_FRAMEWORK_STRATEGY,
    ui_element=_UI_ELEMENT_STRATEGY,
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_ui_element_variants_all_render(
    description: str,
    framework: str,
    ui_element: str,
) -> None:
    """All ui_element values must produce structurally valid HTML in all frameworks."""

    class DynamicForm(FormModel):
        test_field: str = Field('', description=description, ui_element=ui_element)

    renderer = EnhancedFormRenderer(framework=framework)
    html = renderer.render_form_from_model(DynamicForm)
    assert_valid_html(html, f'{framework}/{ui_element}')


# ---------------------------------------------------------------------------
# Property: Numeric range constraints must be honoured in rendered attributes
# ---------------------------------------------------------------------------


@given(
    min_val=st.integers(min_value=0, max_value=50),
    max_val=st.integers(min_value=51, max_value=200),
    framework=_FRAMEWORK_STRATEGY,
)
@settings(max_examples=40)
def test_numeric_constraints_in_html(min_val: int, max_val: int, framework: str) -> None:
    """min/max constraints on int fields must appear in the rendered HTML."""
    assert min_val < max_val

    class BoundedForm(FormModel):
        score: int = Field(..., ge=min_val, le=max_val, description='Score', ui_element='number')

    html = render_form_html(BoundedForm, submit_url='/s')
    assert_valid_html(html)
    assert f'min="{min_val}"' in html
    assert f'max="{max_val}"' in html


# ---------------------------------------------------------------------------
# Property: str length constraints produce valid HTML
# ---------------------------------------------------------------------------


@given(
    min_len=st.integers(min_value=1, max_value=10),
    max_len=st.integers(min_value=11, max_value=200),
    # Only test frameworks known to emit minlength/maxlength HTML attributes.
    # Material theme uses CSS/JS validation instead of HTML attributes.
    framework=st.sampled_from(['bootstrap', 'none']),
)
@settings(max_examples=40)
def test_string_length_constraints_in_html(min_len: int, max_len: int, framework: str) -> None:
    assert min_len < max_len

    class LimitedForm(FormModel):
        bio: str = Field('', min_length=min_len, max_length=max_len, description='Bio')

    renderer = EnhancedFormRenderer(framework=framework)
    html = renderer.render_form_from_model(LimitedForm)
    assert_valid_html(html, f'{framework}/length')
    assert f'minlength="{min_len}"' in html
    assert f'maxlength="{max_len}"' in html


# ---------------------------------------------------------------------------
# Property: Models with optional fields always render without crashing
# ---------------------------------------------------------------------------


@given(
    n_required=st.integers(min_value=1, max_value=4),
    n_optional=st.integers(min_value=0, max_value=4),
    framework=_FRAMEWORK_STRATEGY,
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
def test_mixed_required_optional_fields(n_required: int, n_optional: int, framework: str) -> None:
    """Forms with various mixes of required and optional fields must render."""
    annotations: dict = {}
    field_defs: dict = {}

    for i in range(n_required):
        name = f'req_{i}'
        annotations[name] = str
        field_defs[name] = Field(..., description=f'Required field {i}')

    for i in range(n_optional):
        name = f'opt_{i}'
        annotations[name] = Optional[str]
        field_defs[name] = Field(None, description=f'Optional field {i}')

    MixedForm = type(
        'MixedForm',
        (FormModel,),
        {'__annotations__': annotations, **field_defs},
    )

    renderer = EnhancedFormRenderer(framework=framework)
    html = renderer.render_form_from_model(MixedForm)
    assert_valid_html(html, f'{framework}/mixed')

    # Every required field must appear in the HTML
    for i in range(n_required):
        assert f'name="req_{i}"' in html


# ---------------------------------------------------------------------------
# Property: form HTML always contains a <form> tag
# ---------------------------------------------------------------------------


@given(framework=_FRAMEWORK_STRATEGY)
@settings(max_examples=10)
def test_rendered_form_always_has_form_tag(framework: str) -> None:
    class SimpleForm(FormModel):
        name: str = Field(..., description='Name')

    renderer = EnhancedFormRenderer(framework=framework)
    html = renderer.render_form_from_model(SimpleForm)
    assert '<form' in html
    assert '</form>' in html


# ---------------------------------------------------------------------------
# Property: validation — valid data passes, invalid data fails predictably
# ---------------------------------------------------------------------------


@given(
    name=st.text(min_size=2, max_size=50).filter(lambda s: s.strip()),
    age=st.integers(min_value=18, max_value=120),
)
@settings(max_examples=50)
def test_valid_model_data_always_validates(name: str, age: int) -> None:
    """Valid data matching field constraints must never raise ValidationError."""

    class PersonForm(FormModel):
        name: str = Field(..., min_length=2, description='Name')
        age: int = Field(..., ge=18, le=120, description='Age')

    instance = PersonForm(name=name, age=age)
    assert instance.name == name
    assert instance.age == age


@given(age=st.integers(min_value=-1000, max_value=17))
@settings(max_examples=30)
def test_underage_always_fails_validation(age: int) -> None:
    """Any age below 18 must fail Pydantic validation."""
    from pydantic import ValidationError

    class AgeForm(FormModel):
        age: int = Field(..., ge=18, description='Age')

    with pytest.raises(ValidationError):
        AgeForm(age=age)


@given(length=st.integers(min_value=0, max_value=1))
@settings(max_examples=10)
def test_name_too_short_always_fails(length: int) -> None:
    """Names shorter than min_length=2 must fail validation."""
    from pydantic import ValidationError

    class NameForm(FormModel):
        name: str = Field(..., min_length=2, description='Name')

    short_name = 'x' * length
    with pytest.raises(ValidationError):
        NameForm(name=short_name)


# ---------------------------------------------------------------------------
# Property: render_form_html is idempotent (same model = same structure)
# ---------------------------------------------------------------------------


@given(framework=_FRAMEWORK_STRATEGY)
@settings(max_examples=10)
def test_render_is_stable(framework: str) -> None:
    """Rendering the same model twice must produce the same HTML."""

    class StableForm(FormModel):
        name: str = Field(..., description='Name')
        age: int = Field(..., ge=0, description='Age', ui_element='number')

    renderer = EnhancedFormRenderer(framework=framework)
    html1 = renderer.render_form_from_model(StableForm)
    html2 = renderer.render_form_from_model(StableForm)
    assert html1 == html2
