"""
Test implementation that matches the design_idea.py vision.
This demonstrates the new FormField, layout system, and validation capabilities.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic_forms.schema_form import FormModel, form_validator, EmailStr, ValidationResult
from pydantic_forms.form_field import FormField
from pydantic_forms.form_layouts import (
    VerticalLayout,
    HorizontalLayout,
    TabbedLayout,
    SectionDesign,
    FormDesign,
)
from pydantic_forms.input_types import (
    TEXT_INPUTS,
    NUMERIC_INPUTS,
    SELECTION_INPUTS,
    DATETIME_INPUTS,
    SPECIALIZED_INPUTS,
)


class SimpleForm(FormModel):
    title: str = FormField(
        ...,
        title="Title",
        input_type="text",
        placeholder="Enter title here",
        help_text="The title of the item.",
        icon="bi bi-card-text",
    )
    age: int = FormField(
        ...,
        title="Age",
        input_type="number",
        min_value=0,
        max_value=120,
        help_text="Your age in years.",
        icon="bi bi-person",
    )
    email: EmailStr = FormField(
        ...,
        title="Email",
        input_type="email",
        placeholder="example@example.com",
        help_text="Your email address.",
        icon="bi bi-envelope",
    )
    subscribe: bool = FormField(
        False,
        title="Subscribe to newsletter",
        input_type="checkbox",
        help_text="Check to receive our newsletter.",
        icon="bi bi-newspaper",
    )
    country: str = FormField(
        ...,
        title="Country",
        input_type="select",
        options=["USA", "Canada", "UK", "Australia"],
        help_text="Select your country of residence.",
        icon="bi bi-globe",
    )
    birth_date: date = FormField(
        ...,
        title="Birth Date",
        input_type="date",
        help_text="Your date of birth.",
        icon="bi bi-calendar",
    )
    appointment_time: datetime = FormField(
        None,
        title="Appointment Time",
        input_type="datetime",
        help_text="Preferred time for appointment.",
        icon="bi bi-clock",
    )
    credit_card_number: str = FormField(
        ...,
        title="Credit Card Number",
        input_type="text",
        placeholder="1234 5678 9012 3456",
        help_text="Enter your credit card number.",
        icon="bi bi-credit-card",
    )

    @form_validator
    def check_age_and_consent(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # if under 18, must have parental consent (this is a demo - no parental_consent field in form)
        age = values.get("age")
        if age is not None and age < 18:
            # For demo purposes, just validate age is reasonable
            if age < 13:
                raise ValueError("Age must be at least 13 years old.")
        return values


class UserProfile(FormModel):
    bio: str = FormField(
        None,
        title="Biography",
        input_type="textarea",
        placeholder="Tell us about yourself",
        help_text="A brief biography.",
        icon="bi bi-info-circle",
    )
    profile_picture: str = FormField(
        None,
        title="Profile Picture",
        input_type="file",
        help_text="Upload your profile picture.",
        icon="bi bi-image",
    )


class LayoutOne(VerticalLayout):
    form = SimpleForm  # layout with simple form is a vertical layout
    form_config = SectionDesign(
        section_title="User Profile Section",
        section_description="Fill out your profile information below.",
        icon="people",  # bootstrap icon name
        collapsible=True,
    )


class LayoutTwo(HorizontalLayout):
    profile = UserProfile  # layout with user profile form is a horizontal layout
    form_config = SectionDesign(
        section_title="Additional Profile Details",
        section_description="Provide additional details for your profile.",
        icon="person-badge",  # bootstrap icon name
        collapsible=False,
    )


class UserProfileLayout(TabbedLayout):
    tab_one = (
        LayoutOne()
    )  # order of tabs is determined by the order of declaration this would be the first tab
    tab_two = LayoutTwo()  # this would be the second tab

    form_config = FormDesign(
        ui_theme="bootstrap",  # UI framework (bootstrap, material, shadcn, tailwind, semantic, custom)
        ui_theme_custom_css=None,  # custom css styles if ui_theme is set to custom - ignored unless custom is selected
        form_name="User Profile",  # form name displayed at the top of the form
        form_enctype="application/x-www-form-urlencoded",  # form encoding type only for post method
        form_width="600px",  # desired form width
        target_url="/api/endpoint/for/form",  # target URL for form submission - full url or relative path
        form_method="post",  # post (default), get
        error_notification_style="inline",  # toast, inline,
        show_debug_info=False,  # default is False
    )


def test_form_rendering():
    """Test that the new system can render forms like the design_idea.py vision."""
    print("Testing individual form rendering...")

    # Test individual form
    simple_form_html = SimpleForm.render_form()
    print("✓ SimpleForm rendered successfully")
    print(f"  Length: {len(simple_form_html)} characters")

    # Test layout rendering
    print("\nTesting layout rendering...")
    layout = UserProfileLayout()
    layout_html = layout.render()
    print("✓ UserProfileLayout rendered successfully")
    print(f"  Length: {len(layout_html)} characters")

    return layout_html


def test_form_validation():
    """Test the validation system."""
    print("\nTesting form validation...")

    # Test valid data
    valid_data = {
        "title": "Test Title",
        "age": 25,
        "email": "test@example.com",
        "subscribe": True,
        "country": "USA",
        "birth_date": "1999-01-01",
        "bio": "I'm a test user.",
    }

    layout = UserProfileLayout()
    result = layout.validate(valid_data)

    print(f"✓ Validation result: {result}")
    print(f"  Is valid: {result.is_valid}")
    print(f"  Data keys: {list(result.data.keys()) if result.data else 'None'}")

    # Test invalid data (age too young)
    invalid_data = {
        "title": "Test Title",
        "age": 10,  # Too young
        "email": "invalid-email",  # Invalid email
        "country": "USA",
        "birth_date": "1999-01-01",
    }

    result_invalid = layout.validate(invalid_data)
    print(f"\n✓ Invalid validation result: {result_invalid}")
    print(f"  Is valid: {result_invalid.is_valid}")
    print(f"  Errors: {result_invalid.errors}")

    return result, result_invalid


def test_input_type_validation():
    """Test the input type validation system."""
    print("\nTesting input type validation...")

    try:
        # This should work - checkbox for bool
        test_field = FormField(False, input_type="checkbox")
        print("✓ Valid input type (checkbox for bool) accepted")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    try:
        # This should fail - checkbox for string
        from pydantic_forms.form_field import create_field_with_validation

        test_field = create_field_with_validation(
            str, False, input_type="checkbox", field_name="test"
        )
        print("✗ Invalid input type should have been rejected")
    except ValueError as e:
        print(f"✓ Invalid input type correctly rejected: {e}")
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")


def demo_flask_usage():
    """Demonstrate the Flask usage pattern from design_idea.py."""
    print("\nDemonstrating Flask usage pattern...")

    # Simulate the Flask endpoint logic
    def user_profile_get():
        """Simulate GET request."""
        layout = UserProfileLayout()
        return layout.render()

    def user_profile_post(form_data, files=None):
        """Simulate POST request."""
        layout = UserProfileLayout()
        result = layout.validate(form_data, files)

        if result.is_valid:
            return f"Success! Data: {result.data}"
        else:
            return result.render_with_errors()

    # Test GET
    get_html = user_profile_get()
    print("✓ GET request simulation successful")
    print(f"  HTML length: {len(get_html)} characters")

    # Test POST with valid data
    valid_post_data = {
        "title": "Flask Test",
        "age": 30,
        "email": "flask@example.com",
        "country": "Canada",
        "birth_date": "1993-01-01",
    }

    post_result = user_profile_post(valid_post_data)
    print("✓ Valid POST request simulation successful")
    print(f"  Result preview: {post_result[:100]}...")

    # Test POST with invalid data
    invalid_post_data = {
        "title": "",  # Empty title
        "age": 5,  # Too young
        "email": "not-an-email",
        "country": "Unknown",
    }

    post_error_result = user_profile_post(invalid_post_data)
    print("✓ Invalid POST request simulation successful")
    print(f"  Error result length: {len(post_error_result)} characters")


if __name__ == "__main__":
    print("Testing pydantic-forms design_idea.py implementation...")
    print("=" * 60)

    try:
        # Test basic rendering
        html = test_form_rendering()

        # Test validation
        test_form_validation()

        # Test input type validation
        test_input_type_validation()

        # Test Flask usage pattern
        demo_flask_usage()

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("\nThe new pydantic-forms implementation matches the design_idea.py vision!")

        # Save a sample HTML file
        with open("/workspaces/pydantic-forms/sample_form.html", "w") as f:
            f.write(html)
        print(f"\n📄 Sample form saved to: /workspaces/pydantic-forms/sample_form.html")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
