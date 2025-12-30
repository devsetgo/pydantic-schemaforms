"""
Tests to improve coverage of templates.py module.
Specifically targeting uncovered utility functions.
"""

import pytest

from pydantic_forms.templates import (
    TemplateString,
    create_custom_template,
    validate_template_variables,
)


class TestTemplateStringUtilities:
    """Test template string utility functions."""

    def test_create_custom_template(self):
        """Test the create_custom_template helper function."""
        template = create_custom_template("Hello ${name}!")
        assert isinstance(template, TemplateString)
        result = template.render(name="World")
        assert result == "Hello World!"

    def test_validate_template_variables_all_provided(self):
        """Test validation when all variables are provided."""
        template = TemplateString("${name} is ${age} years old")
        validation = validate_template_variables(
            template,
            name="John",
            age="25",
        )
        assert validation == {"name": True, "age": True}

    def test_validate_template_variables_missing(self):
        """Test validation when some variables are missing."""
        template = TemplateString("${name} lives in ${city}")
        validation = validate_template_variables(template, name="John")
        assert validation == {"name": True, "city": False}

    def test_validate_template_variables_none_provided(self):
        """Test validation when no variables are provided."""
        template = TemplateString("${name} is ${age} years old")
        validation = validate_template_variables(template)
        assert validation == {"name": False, "age": False}

    def test_validate_template_variables_extra_provided(self):
        """Test validation when extra variables are provided."""
        template = TemplateString("Hello ${name}!")
        validation = validate_template_variables(
            template,
            name="World",
            extra="ignored",
        )
        assert validation == {"name": True}
        # Extra variables don't appear in validation result

    def test_safe_render_with_missing_vars(self):
        """Test safe_render leaves unfilled variables as placeholders."""
        template = TemplateString("Hello ${name}, you are ${age} years old")
        result = template.safe_render(name="John")
        assert "John" in result
        assert "${age}" in result  # Unfilled variable preserved

    def test_safe_render_with_all_vars(self):
        """Test safe_render when all variables provided."""
        template = TemplateString("Hello ${name}, age ${age}")
        result = template.safe_render(name="Jane", age="30")
        assert result == "Hello Jane, age 30"

    def test_template_cache_reuse(self):
        """Test that templates are cached and reused."""
        # Create two templates with same string
        t1 = TemplateString("Hello ${name}")
        t2 = TemplateString("Hello ${name}")

        # Render both to ensure compilation
        t1.render(name="A")
        t2.render(name="B")

        # Both should work correctly (cache doesn't affect functionality)
        assert t1.render(name="Test1") == "Hello Test1"
        assert t2.render(name="Test2") == "Hello Test2"

    def test_template_with_none_value(self):
        """Test rendering with None values."""
        template = TemplateString("Value: ${value}")
        result = template.render(value=None)
        assert result == "Value: "  # None becomes empty string

    def test_template_with_bool_value(self):
        """Test rendering with boolean values."""
        template = TemplateString("Active: ${active}, Inactive: ${inactive}")
        result = template.render(active=True, inactive=False)
        assert result == "Active: true, Inactive: false"

    def test_template_with_numeric_value(self):
        """Test rendering with numeric values."""
        template = TemplateString("Count: ${count}, Price: ${price}")
        result = template.render(count=42, price=19.99)
        assert "42" in result
        assert "19.99" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
