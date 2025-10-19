"""
Pydantic Forms - Example Usage

This example demonstrates the core functionality matching React JSON Schema Forms patterns.
Based on the user's original requirements and successfully tested implementation.
"""

from pydantic import model_validator

from pydantic_forms.enhanced_renderer import SchemaFormValidationError
from pydantic_forms.schema_form import FormModel, Field


class MinimalSchemaModel(FormModel):
    """
    Example form model matching React JSON Schema Forms patterns.
    
    This demonstrates:
    - UI element specifications (ui_element, ui_autofocus, ui_options)
    - Field validation (min_length, max_length)
    - Cross-field validation with custom error messages
    - Automatic form rendering with Bootstrap styling
    """
    
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
        bad_words = ["buy", "sock", "chump","ministry", "company"]
        found = [w for w in bad_words if w in self.biography.lower()]
        if found:
            errors.append(
                {
                    "name": "biography",
                    "property": ".biography",
                    "message": f'The following word(s) are not allowed in the biography: {", ".join(found)}.'
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


def demo_basic_usage():
    """Demonstrate basic form rendering."""
    print("=== Basic Form Rendering ===")
    
    # Generate empty form
    form_html = MinimalSchemaModel.render_form()
    print("✓ Empty form generated successfully")
    print(f"Form HTML length: {len(form_html)} characters")
    
    # Generate form with data
    sample_data = {
        "userName": "john_doe", 
        "password": "MySecurePassword123!",
        "passwordRepeat": "MySecurePassword123!",
        "biography": "I am a software developer who loves Python."
    }
    
    form_with_data = MinimalSchemaModel.render_form(data=sample_data)
    print("✓ Form with data generated successfully")
    
    # Generate form with validation errors
    sample_errors = {
        "password_repeat": "Passwords do not match",
        "biography": "Biography contains forbidden words"
    }
    
    form_with_errors = MinimalSchemaModel.render_form(
        data=sample_data,
        errors=sample_errors,
        framework="bootstrap"
    )
    print("✓ Form with errors generated successfully")
    
    return form_html


def demo_frameworks():
    """Demonstrate different CSS frameworks."""
    print("\n=== Framework Support ===")
    
    frameworks = ["bootstrap", "material", "none"]
    for framework in frameworks:
        form_html = MinimalSchemaModel.render_form(framework=framework)
        print(f"✓ {framework.title()} framework: {len(form_html)} chars")


def demo_validation():
    """Demonstrate Pydantic validation integration."""
    print("\n=== Validation Demo ===")
    
    # Test valid data
    try:
        valid_form = MinimalSchemaModel(
            userName="validuser",
            password="ValidPassword123!",
            passwordRepeat="ValidPassword123!",
            biography="I love programming in Python and building web applications."
        )
        print("✓ Valid data passed validation")
    except Exception as e:
        print(f"✗ Valid data failed: {e}")
    
    # Test validation errors
    try:
        invalid_form = MinimalSchemaModel(
            userName="bob",  # Triggers "I don't like Bob"
            password="ValidPassword123!",
            passwordRepeat="DifferentPassword",  # Password mismatch
            biography="I want to buy socks"  # Contains forbidden words
        )
        print("✗ Invalid data should have failed validation")
    except SchemaFormValidationError as e:
        print(f"✓ Validation correctly caught {len(e.errors)} errors:")
        for error in e.errors:
            print(f"  - {error['name']}: {error['message']}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    # Run demonstrations
    demo_basic_usage()
    demo_frameworks()
    demo_validation()
    
    print("\n" + "="*60)
    print("EXAMPLE FORM OUTPUT")
    print("="*60)
    
    # Show a complete example
    example_form = MinimalSchemaModel.render_form(
        data={
            "userName": "developer123",
            "password": "MySecurePassword123!",
            "passwordRepeat": "MySecurePassword123!",
            "biography": "I am a passionate Python developer who enjoys building modern web applications with frameworks like FastAPI and Flask."
        },
        framework="bootstrap"
    )
    print(example_form)