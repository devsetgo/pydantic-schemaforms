"""
Test the exact example from the user's request to ensure compatibility.
"""

from pydantic import model_validator
from pydantic_forms.enhanced_renderer import SchemaFormValidationError
from pydantic_forms.schema_form import FormModel, Field


class MinimalSchemaModel(FormModel):
    userName: str = Field(
        ...,
        alias="userName",
        description="Choose a username (at least 3 characters).",
        min_length=3,
        ui_autofocus=True,
    )
    password: str = Field(
        ...,
        alias="password",
        description="Password must be at least 8 characters and include 1 uppercase letter, 1 number, and 1 special character.",
        min_length=8,
        ui_element="password",
    )
    password_repeat: str = Field(
        ...,
        alias="passwordRepeat",
        description="Re-enter your password. Must match the password above.",
        title="Repeat Password",
        ui_element="password",
    )
    biography: str = Field(
        ...,
        alias="biography",
        description="Write a short biography.",
        title="Biography",
        min_length=1,
        max_length=500,
        ui_element="textarea",
        ui_options={"rows": 6},
    )

    @model_validator(mode="after")
    def check_all_errors(self):
        errors = []
        # Passwords must match
        if self.password != self.password_repeat:
            errors.append(
                {
                    "name": "passwordRepeat",
                    "property": ".passwordRepeat",
                    "message": "Passwords do not match",
                }
            )
        # Biography must not contain any bad words (case-insensitive)
        bad_words = ["buy", "sock", "chump", "ministry", "company"]
        found = [w for w in bad_words if w in self.biography.lower()]
        if found:
            errors.append(
                {
                    "name": "biography",
                    "property": ".biography",
                    "message": f'The following word(s) are not allowed in the biography: {", ".join(found)}.',
                }
            )

        # I don't like Bob
        if "bob" in self.userName.lower():
            errors.append(
                {
                    "name": "userName",
                    "property": ".userName",
                    "message": "I don't like Bob.",
                }
            )
        if errors:
            raise SchemaFormValidationError(errors)
        return self

    model_config = {"populate_by_name": True}


def test_form_rendering():
    """Test form rendering."""
    print("Testing form rendering...")

    # Test empty form
    form_html = MinimalSchemaModel.render_form()
    assert "<form" in form_html
    assert "userName" in form_html
    assert "password" in form_html
    assert "biography" in form_html
    assert "textarea" in form_html
    print("✓ Empty form rendering works")

    # Test form with data
    sample_data = {
        "userName": "johndoe",
        "password": "MyPassword123!",
        "passwordRepeat": "MyPassword123!",
        "biography": "I am a software developer",
    }

    form_with_data = MinimalSchemaModel.render_form(data=sample_data)
    assert 'value="johndoe"' in form_with_data
    assert "I am a software developer" in form_with_data
    print("✓ Form with data rendering works")

    # Test form with errors
    sample_errors = {
        "password_repeat": "Passwords do not match",  # Use actual field name
        "biography": "Biography contains forbidden words",
    }

    form_with_errors = MinimalSchemaModel.render_form(data=sample_data, errors=sample_errors)
    assert "Passwords do not match" in form_with_errors
    assert "Biography contains forbidden words" in form_with_errors
    print("✓ Form with errors rendering works")


def test_validation():
    """Test form validation."""
    print("\nTesting validation...")

    # Test successful validation
    try:
        valid_data = MinimalSchemaModel(
            userName="johndoe",
            password="MyPassword123!",
            passwordRepeat="MyPassword123!",
            biography="I am a software developer who loves coding.",
        )
        print("✓ Valid data validation works")
    except Exception as e:
        print(f"✗ Valid data failed: {e}")

    # Test validation errors
    try:
        invalid_data = MinimalSchemaModel(
            userName="bob",  # Should trigger "I don't like Bob"
            password="MyPassword123!",
            passwordRepeat="DifferentPassword",  # Should trigger password mismatch
            biography="I want to buy socks",  # Should trigger bad words
        )
        print("✗ Invalid data should have failed validation")
    except SchemaFormValidationError as e:
        assert len(e.errors) == 3  # Should have 3 errors
        print(f"✓ Validation errors correctly caught: {len(e.errors)} errors")
        for error in e.errors:
            print(f"  - {error['name']}: {error['message']}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def test_frameworks():
    """Test different CSS frameworks."""
    print("\nTesting CSS frameworks...")

    frameworks = ["bootstrap", "material", "none"]
    for framework in frameworks:
        form_html = MinimalSchemaModel.render_form(framework=framework)
        assert "<form" in form_html
        print(f"✓ {framework} framework works")


if __name__ == "__main__":
    test_form_rendering()
    test_validation()
    test_frameworks()

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)

    print("\nExample form output:")
    print("-" * 30)
    sample_form = MinimalSchemaModel.render_form(
        data={
            "userName": "testuser",
            "password": "SecurePass123!",
            "passwordRepeat": "SecurePass123!",
            "biography": "I love building web applications with Python.",
        },
        framework="bootstrap",
    )
    print(sample_form)
