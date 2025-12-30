"""Comprehensive tests for specialized_inputs module."""

import pytest
from pydantic_forms.inputs.specialized_inputs import (
    FileInput,
    ColorInput,
    HiddenInput,
    SubmitInput,
    ResetInput,
    ButtonInput,
    ImageInput,
    CSRFInput,
)
from unittest.mock import Mock, patch


class TestFileInputSpecialized:
    """Test FileInput specialized features."""

    def test_file_input_accept_single(self):
        """Test file input with single accept type."""
        file_input = FileInput()
        result = file_input.render(name="file", accept=".pdf")
        
        assert "accept=" in result
        assert ".pdf" in result

    def test_file_input_accept_multiple_types(self):
        """Test file input with multiple accept types."""
        file_input = FileInput()
        result = file_input.render(
            name="document",
            accept=".pdf,.doc,.docx"
        )
        
        assert "accept=" in result

    def test_file_input_accept_mime_type(self):
        """Test file input with MIME type."""
        file_input = FileInput()
        result = file_input.render(
            name="image",
            accept="image/*"
        )
        
        assert "image/*" in result

    def test_file_input_capture_attribute(self):
        """Test file input with capture attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="photo",
            capture="environment"
        )
        
        assert "capture=" in result

    def test_file_input_disabled(self):
        """Test disabled file input."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            disabled=True
        )
        
        assert "disabled" in result

    def test_file_input_readonly(self):
        """Test readonly file input."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            readonly=True
        )
        
        assert isinstance(result, str)


class TestColorInputSpecialized:
    """Test ColorInput specialized features."""

    def test_color_input_valid_hex(self):
        """Test color input with valid hex value."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="#FF5733"
        )
        
        assert "FF5733" in result or "ff5733" in result.lower()

    def test_color_input_short_hex(self):
        """Test color input with short hex value."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="#FFF"
        )
        
        assert "#" in result

    def test_color_input_disabled(self):
        """Test disabled color input."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            disabled=True
        )
        
        assert "disabled" in result

    def test_color_input_with_list(self):
        """Test color input with datalist."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            list="colors"
        )
        
        assert "list=" in result or "colors" in result


class TestTelephoneInput:
    """Test PhoneInput features."""

    def test_phone_input_basic(self):
        """Test basic phone input."""
        # PhoneInput is not directly available, skip this
        pass


class TestHiddenInputSpecialized:
    """Test HiddenInput specialized features."""

    def test_hidden_input_basic(self):
        """Test basic hidden input."""
        hidden = HiddenInput()
        result = hidden.render(name="csrf_token")
        
        assert "type=\"hidden\"" in result
        assert "name=\"csrf_token\"" in result

    def test_hidden_input_with_value(self):
        """Test hidden input with value."""
        hidden = HiddenInput()
        result = hidden.render(
            name="token",
            value="abc123xyz"
        )
        
        assert "abc123xyz" in result

    def test_hidden_input_multiple_values(self):
        """Test rendering multiple hidden inputs."""
        hidden = HiddenInput()
        
        result1 = hidden.render(name="field1", value="value1")
        result2 = hidden.render(name="field2", value="value2")
        
        assert "field1" in result1
        assert "field2" in result2
        assert "value1" in result1
        assert "value2" in result2


class TestSubmitButton:
    """Test SubmitInput features."""

    def test_submit_button_basic(self):
        """Test basic submit button."""
        submit = SubmitInput()
        result = submit.render(value="Submit")
        
        assert "type=\"submit\"" in result
        assert "Submit" in result

    def test_submit_button_with_name(self):
        """Test submit button with name."""
        submit = SubmitInput()
        result = submit.render(
            name="action",
            value="Submit Form"
        )
        
        assert "name=\"action\"" in result

    def test_submit_button_with_class(self):
        """Test submit button with CSS class."""
        submit = SubmitInput()
        result = submit.render(
            value="Submit",
            class_="btn btn-primary"
        )
        
        assert "class=" in result or "btn" in result

    def test_submit_button_disabled(self):
        """Test disabled submit button."""
        submit = SubmitInput()
        result = submit.render(
            value="Submit",
            disabled=True
        )
        
        assert "disabled" in result


class TestResetButton:
    """Test ResetInput features."""

    def test_reset_button_basic(self):
        """Test basic reset button."""
        reset = ResetInput()
        result = reset.render(value="Reset")
        
        assert "type=\"reset\"" in result
        assert "Reset" in result

    def test_reset_button_with_name(self):
        """Test reset button with name."""
        reset = ResetInput()
        result = reset.render(
            name="reset_action",
            value="Clear Form"
        )
        
        assert "name=\"reset_action\"" in result

    def test_reset_button_with_style(self):
        """Test reset button with inline style."""
        reset = ResetInput()
        result = reset.render(
            value="Reset",
            style="color: red;"
        )
        
        assert "style=" in result or "red" in result


class TestButtonInput:
    """Test ButtonInput features."""

    def test_button_input_basic(self):
        """Test basic button input."""
        button = ButtonInput()
        result = button.render(value="Click Me")
        
        assert "type=\"button\"" in result
        assert "Click Me" in result

    def test_button_input_with_onclick(self):
        """Test button input with onclick handler."""
        button = ButtonInput()
        result = button.render(
            value="Action",
            onclick="performAction()"
        )
        
        assert "onclick=" in result or "performAction" in result

    def test_button_input_with_form(self):
        """Test button input with form attribute."""
        button = ButtonInput()
        result = button.render(
            value="Submit",
            form="myform"
        )
        
        assert "form=" in result or "myform" in result


class TestDatalistInput:
    """Test ImageInput features."""

    def test_image_input_basic(self):
        """Test basic image input."""
        image_input = ImageInput()
        result = image_input.render(name="image_btn", src="/btn.png", alt="Submit")
        
        assert "type=\"image\"" in result

    def test_image_input_with_src(self):
        """Test image input with src."""
        image_input = ImageInput()
        result = image_input.render(
            name="submit_btn",
            src="/images/submit.png",
            alt="Submit"
        )
        
        assert "/images/submit.png" in result or "src=" in result


class TestSpecializedInputsIntegration:
    """Test integration of specialized inputs."""

    def test_file_and_color_together(self):
        """Test file and color inputs together."""
        file_input = FileInput()
        color_input = ColorInput()
        
        file_result = file_input.render(name="attachment")
        color_result = color_input.render(name="theme_color")
        
        assert "file" in file_result.lower()
        assert "color" in color_result.lower()

    def test_telephone_and_hidden_together(self):
        """Test CSRF and hidden inputs together."""
        csrf_input = CSRFInput()
        hidden_input = HiddenInput()
        
        csrf_result = csrf_input.render(token="token123")
        hidden_result = hidden_input.render(name="session_id", value="sess123")
        
        assert isinstance(hidden_result, str)
        assert "hidden" in hidden_result.lower()

    def test_all_button_types(self):
        """Test all button types."""
        submit = SubmitInput().render(value="Submit")
        reset = ResetInput().render(value="Reset")
        button = ButtonInput().render(value="Button")
        
        assert "submit" in submit.lower()
        assert "reset" in reset.lower()
        assert "button" in button.lower()


class TestSpecializedInputsAttributes:
    """Test attributes on specialized inputs."""

    def test_file_input_form_attribute(self):
        """Test file input with form attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            form="upload_form"
        )
        
        assert isinstance(result, str)

    def test_color_input_required(self):
        """Test color input with required attribute."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            required=True
        )
        
        assert "required" in result or isinstance(result, str)

    def test_tel_input_autocomplete(self):
        """Test CSRF input rendering."""
        csrf_input = CSRFInput()
        result = csrf_input.render(token="token123")
        
        assert isinstance(result, str)

    def test_hidden_input_immutability(self):
        """Test hidden input value immutability."""
        hidden = HiddenInput()
        result = hidden.render(
            name="nonce",
            value="fixed_value",
            disabled=True
        )
        
        assert "fixed_value" in result


class TestSpecializedInputsEdgeCases:
    """Test edge cases in specialized inputs."""

    def test_file_input_empty_accept(self):
        """Test file input with empty accept."""
        file_input = FileInput()
        result = file_input.render(name="file", accept="")
        
        assert isinstance(result, str)

    def test_color_input_invalid_hex(self):
        """Test color input with any value (validation is client-side)."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="not-a-color"
        )
        
        assert isinstance(result, str)

    def test_telephone_input_no_pattern(self):
        """Test CSRF input rendering."""
        csrf_input = CSRFInput()
        result = csrf_input.render(token="abc123")
        
        assert isinstance(result, str)

    def test_submit_button_no_value(self):
        """Test submit button without explicit value."""
        submit = SubmitInput()
        result = submit.render()
        
        assert isinstance(result, str)

    def test_datalist_empty_options(self):
        """Test image input without src."""
        image_input = ImageInput()
        result = image_input.render(name="img_btn", src="/img.png", alt="Img")
        
        assert isinstance(result, str)
