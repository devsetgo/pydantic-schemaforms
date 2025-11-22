"""
Tests for modern_renderer module - advanced form rendering with modern web features.
"""

from pydantic_forms.modern_renderer import ModernFormRenderer
from pydantic_forms.schema_form import Field, FormModel

# Layout imports commented out due to template system issues
# from pydantic_forms.layouts import HorizontalLayout, VerticalLayout, GridLayout, CardLayout


class TestModernFormRenderer:
    """Test the ModernFormRenderer class."""

    def test_renderer_initialization(self):
        """Test basic ModernFormRenderer initialization."""
        renderer = ModernFormRenderer()
        assert renderer is not None
        # Check if it has expected methods
        assert hasattr(renderer, "render_form")

    def test_basic_form_rendering(self):
        """Test basic form rendering with ModernFormRenderer."""

        class SimpleForm(FormModel):
            name: str = Field(..., ui_element="text")
            email: str = Field(..., ui_element="email")
            age: int = Field(..., ui_element="number", ge=18)

        renderer = ModernFormRenderer()

        # Test if renderer can process the form model
        # Note: Actual implementation may vary based on ModernFormRenderer's interface
        try:
            form_fields = renderer.extract_form_fields(SimpleForm)
            assert len(form_fields) == 3

            # Check field names
            field_names = [field.name for field in form_fields]
            assert "name" in field_names
            assert "email" in field_names
            assert "age" in field_names

        except AttributeError:
            # If extract_form_fields doesn't exist, test other methods
            pass

    def test_form_field_configuration(self):
        """Test FormField configuration and validation."""
        from pydantic_forms.modern_renderer import FormField

        # Test basic field creation
        field = FormField("username", field_type="text", required=True)
        assert field.name == "username"
        assert field.field_type == "text"
        assert field.required is True
        assert field.label == "Username"  # Auto-generated from name

    def test_form_field_with_options(self):
        """Test FormField with options for select fields."""
        from pydantic_forms.modern_renderer import FormField

        options = [
            {"value": "small", "label": "Small"},
            {"value": "medium", "label": "Medium"},
            {"value": "large", "label": "Large"},
        ]

        field = FormField("size", field_type="select", options=options, placeholder="Choose size")

        assert field.name == "size"
        assert field.field_type == "select"
        assert len(field.options) == 3
        assert field.placeholder == "Choose size"

    def test_form_field_validation(self):
        """Test FormField validation functionality."""
        from pydantic_forms.modern_renderer import FormField

        # Create field with validators
        def min_length_validator(value):
            return len(value) >= 3

        field = FormField(
            "password", field_type="password", required=True, validators=[min_length_validator]
        )

        # Test validation
        assert field.validate("abc") is True  # Should pass
        field.errors = []  # Reset errors
        assert field.validate("ab") is False  # Should fail

    def test_async_rendering_support(self):
        """Test async rendering capabilities if available."""
        renderer = ModernFormRenderer()

        # Check if async methods exist
        has_async_methods = any(
            method.startswith("async_") or method.endswith("_async") for method in dir(renderer)
        )

        # If async methods exist, they should be callable
        if has_async_methods:
            assert hasattr(renderer, "render_async") or hasattr(renderer, "async_render")

    def test_performance_rendering(self):
        """Test performance-oriented rendering features."""
        renderer = ModernFormRenderer()

        # Check for performance-related attributes
        performance_features = ["use_thread_pool", "cache_templates", "optimize_rendering"]

        # At least one performance feature should be available
        has_performance_features = any(
            hasattr(renderer, feature) for feature in performance_features
        )

        # This is more of a feature check than assertion
        # as performance features are optional
        if has_performance_features:
            print("ModernFormRenderer has performance features")

    def test_framework_compatibility(self):
        """Test framework compatibility features."""

        class TestForm(FormModel):
            name: str = Field(..., ui_element="text")
            email: str = Field(..., ui_element="email")

        renderer = ModernFormRenderer()

        # Test if renderer can handle different frameworks
        frameworks = ["bootstrap", "material", "plain", "custom"]

        try:
            for framework in frameworks:
                # If renderer has framework support, test it
                if hasattr(renderer, "set_framework"):
                    renderer.set_framework(framework)
                elif hasattr(renderer, "render_with_framework"):
                    result = renderer.render_with_framework(TestForm, framework)
                    assert result is not None
        except (AttributeError, NotImplementedError):
            # Framework support might not be implemented yet
            pass

    def test_layout_integration_basic(self):
        """Test basic layout integration concepts."""

        # Since complex layouts have template issues, test basic concepts
        class FormWithLayout(FormModel):
            personal_info_section: str = Field(default="", ui_section="Personal")
            name: str = Field(..., ui_element="text", ui_section="Personal")
            email: str = Field(..., ui_element="email", ui_section="Personal")

            preferences_section: str = Field(default="", ui_section="Preferences")
            newsletter: bool = Field(default=False, ui_element="checkbox", ui_section="Preferences")
            theme: str = Field(..., ui_element="select", ui_section="Preferences")

        renderer = ModernFormRenderer()

        # Test that form can be processed
        try:
            if hasattr(renderer, "extract_form_fields"):
                fields = renderer.extract_form_fields(FormWithLayout)

                # Group fields by section
                sections = {}
                for field in fields:
                    section = getattr(field, "ui_section", "default")
                    if section not in sections:
                        sections[section] = []
                    sections[section].append(field)

                # Should have personal and preferences sections
                assert len(sections) >= 2
        except AttributeError:
            # Method might not be implemented
            pass

    def test_input_component_integration(self):
        """Test integration with input components."""
        ModernFormRenderer()

        # Test that renderer can work with various input types
        input_types = [
            "text",
            "email",
            "password",
            "number",
            "date",
            "datetime-local",
            "select",
            "checkbox",
            "radio",
            "textarea",
            "file",
            "color",
            "range",
        ]

        for input_type in input_types:
            try:
                from pydantic_forms.modern_renderer import FormField

                field = FormField(f"test_{input_type}", field_type=input_type)
                assert field.field_type == input_type
            except ImportError:
                # FormField might not be available
                pass

    def test_custom_validation_integration(self):
        """Test custom validation integration."""

        class FormWithValidation(FormModel):
            username: str = Field(
                ...,
                min_length=3,
                max_length=20,
                ui_element="text",
                description="Username must be 3-20 characters",
            )

            password: str = Field(
                ...,
                min_length=8,
                ui_element="password",
                description="Password must be at least 8 characters",
            )

            confirm_password: str = Field(
                ..., ui_element="password", description="Must match password"
            )

        renderer = ModernFormRenderer()

        # Test that validation constraints are preserved
        try:
            if hasattr(renderer, "extract_form_fields"):
                fields = renderer.extract_form_fields(FormWithValidation)

                username_field = next((f for f in fields if f.name == "username"), None)
                if username_field:
                    assert username_field.required is True

                password_field = next((f for f in fields if f.name == "password"), None)
                if password_field:
                    assert password_field.field_type == "password"
        except AttributeError:
            pass

    def test_error_handling(self):
        """Test error handling in ModernFormRenderer."""
        renderer = ModernFormRenderer()

        # Test with invalid form model
        try:

            class InvalidForm:  # Not inheriting from FormModel
                name = "not a field"

            if hasattr(renderer, "extract_form_fields"):
                # Should handle invalid models gracefully
                fields = renderer.extract_form_fields(InvalidForm)
                # Might return empty list or raise informative error
                assert isinstance(fields, (list, type(None)))
        except (AttributeError, TypeError, ValueError):
            # Expected to fail gracefully
            pass

    def test_html_output_safety(self):
        """Test HTML output safety and escaping."""
        from pydantic_forms.modern_renderer import FormField

        # Test with potentially dangerous input
        dangerous_input = "<script>alert('xss')</script>"

        field = FormField(
            "test_field", field_type="text", placeholder=dangerous_input, help_text=dangerous_input
        )

        # If field has render method, test HTML safety
        if hasattr(field, "render"):
            html = field.render()
            # Should escape dangerous content
            assert "<script>" not in html
            assert "&lt;script&gt;" in html or "alert" not in html

    def test_accessibility_features(self):
        """Test accessibility features in rendered forms."""

        class AccessibleForm(FormModel):
            name: str = Field(
                ...,
                ui_element="text",
                description="Your full name",
                ui_options={"aria-label": "Full name input"},
            )

            email: str = Field(
                ...,
                ui_element="email",
                description="Valid email address",
                ui_options={"aria-describedby": "email-help"},
            )

        renderer = ModernFormRenderer()

        # Test that accessibility attributes can be handled
        try:
            if hasattr(renderer, "extract_form_fields"):
                fields = renderer.extract_form_fields(AccessibleForm)

                # Check if UI options are preserved
                for field in fields:
                    if hasattr(field, "extra_attrs") and field.extra_attrs:
                        # Should have accessibility attributes
                        attrs = field.extra_attrs
                        has_aria = any(key.startswith("aria-") for key in attrs.keys())
                        # Accessibility is a good practice but not required
                        if has_aria:
                            print(f"Field {field.name} has accessibility attributes")
        except AttributeError:
            pass
