"""
Enhanced FormField class that matches the design_idea.py vision.
Provides a clean interface for defining form fields with type validation and icon support.
"""

import inspect
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import Field as PydanticField

from .input_types import format_icon_class, get_default_input_type, is_input_type_valid


class FormField:
    """
    Enhanced FormField that provides a clean interface for defining form fields.

    This class matches the design_idea.py vision with explicit parameters for
    input_type, title, help_text, icon, etc.

    This is actually a factory function that returns a Pydantic Field.
    """

    def __new__(
        cls,
        default: Any = ...,
        *,
        # Core field parameters
        title: Optional[str] = None,
        description: Optional[str] = None,
        input_type: Optional[str] = None,
        # UI-specific parameters
        placeholder: Optional[str] = None,
        help_text: Optional[str] = None,
        icon: Optional[str] = None,
        # Validation parameters
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        # Selection parameters
        options: Optional[Union[List[str], List[Dict[str, Any]]]] = None,
        # Boolean parameters
        required: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        autofocus: bool = False,
        # Standard Pydantic Field parameters
        alias: Optional[str] = None,
        examples: Optional[List[Any]] = None,
        exclude: Optional[bool] = None,
        discriminator: Optional[str] = None,
        json_schema_extra: Optional[Dict[str, Any]] = None,
        frozen: Optional[bool] = None,
        validate_default: Optional[bool] = None,
        repr: bool = True,
        init_var: Optional[bool] = None,
        kw_only: Optional[bool] = None,
        strict: Optional[bool] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        multiple_of: Optional[float] = None,
        allow_inf_nan: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Create a FormField with enhanced UI capabilities.

        Args:
            default: Default value for the field
            title: Display title for the field (overrides field name)
            description: Field description (used as label if title not provided)
            input_type: HTML input type (text, email, number, etc.)
            placeholder: Placeholder text
            help_text: Help text displayed below the field
            icon: Icon name (Bootstrap Icons format)
            min_value: Minimum numeric value (maps to ge)
            max_value: Maximum numeric value (maps to le)
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern for validation
            options: Options for select/radio/checkbox inputs
            required: Whether the field is required
            disabled: Whether the field is disabled
            readonly: Whether the field is readonly
            autofocus: Whether the field should auto-focus
            **kwargs: Additional parameters
        """

        # Map min/max_value to Pydantic constraints
        if min_value is not None:
            ge = min_value
        if max_value is not None:
            le = max_value

        # Build json_schema_extra with UI information
        ui_schema = json_schema_extra or {}

        # Add FormField-specific UI data
        ui_schema.update(
            {
                "input_type": input_type,
                "icon": icon,
                "options": options,
                "placeholder": placeholder,
                "help_text": help_text,
                "disabled": disabled,
                "readonly": readonly,
                "autofocus": autofocus,
            }
        )

        # Remove None values
        ui_schema = {k: v for k, v in ui_schema.items() if v is not None}

        # Create and return the underlying Pydantic Field
        # Move any remaining kwargs to json_schema_extra to avoid deprecation warnings
        final_schema = ui_schema.copy()
        final_schema.update(kwargs)

        def _sanitize(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _sanitize(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_sanitize(v) for v in value]
            if inspect.isclass(value):
                return f"{value.__module__}.{value.__name__}"
            if callable(value):
                return getattr(value, "__name__", repr(value))
            return value

        final_schema = {k: _sanitize(v) for k, v in final_schema.items()}

        return PydanticField(
            default=default,
            alias=alias,
            title=title,
            description=description or help_text,
            examples=examples,
            exclude=exclude,
            discriminator=discriminator,
            json_schema_extra=final_schema,
            frozen=frozen,
            validate_default=validate_default,
            repr=repr,
            init_var=init_var,
            kw_only=kw_only,
            pattern=pattern,
            strict=strict,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            min_length=min_length,
            max_length=max_length,
        )

    @classmethod
    def validate_input_type(
        cls, field_annotation: Type, input_type: str, field_name: str = ""
    ) -> None:
        """
        Validate that an input type is compatible with the field's Python type.

        Args:
            field_annotation: The field's type annotation
            input_type: The desired input type
            field_name: The field name for error messages

        Raises:
            ValueError: If the input type is incompatible with the Python type
        """
        # Handle Union types (like Optional[str])
        origin = get_origin(field_annotation)
        if origin is Union:
            args = get_args(field_annotation)
            # For Optional types, get the non-None type
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_annotation = non_none_types[0]

        # Validate the input type
        is_input_type_valid(field_annotation, input_type, field_name)

    @classmethod
    def get_default_input_type(cls, field_annotation: Type) -> str:
        """
        Get the default input type for a field's Python type.

        Args:
            field_annotation: The field's type annotation

        Returns:
            The default input type for the field's type
        """
        # Handle Union types (like Optional[str])
        origin = get_origin(field_annotation)
        if origin is Union:
            args = get_args(field_annotation)
            # For Optional types, get the non-None type
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_annotation = non_none_types[0]

        return get_default_input_type(field_annotation)

    @classmethod
    def format_icon(cls, icon: str, framework: str = "bootstrap") -> str:
        """
        Format an icon class for the specified framework.

        Args:
            icon: The icon name
            framework: The UI framework

        Returns:
            Properly formatted icon class
        """
        return format_icon_class(icon, framework)


def create_field_with_validation(
    field_annotation: Type,
    default: Any = ...,
    input_type: Optional[str] = None,
    field_name: str = "",
    **kwargs,
) -> Any:
    """
    Create a FormField with automatic input type detection and validation.

    This function can be used to create fields where the input type is automatically
    determined from the Python type annotation.

    Args:
        field_annotation: The field's type annotation
        default: Default value for the field
        input_type: Explicit input type (if None, will be auto-detected)
        field_name: The field name for error messages
        **kwargs: Additional FormField parameters

    Returns:
        A configured FormField
    """
    # Auto-detect input type if not provided
    if input_type is None:
        input_type = FormField.get_default_input_type(field_annotation)

    # Validate the input type
    FormField.validate_input_type(field_annotation, input_type, field_name)

    # Create the field
    return FormField(default=default, input_type=input_type, **kwargs)


def TextField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    placeholder: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create a text input field."""
    return FormField(
        default=default,
        input_type="text",
        title=title,
        placeholder=placeholder,
        help_text=help_text,
        icon=icon,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        **kwargs,
    )


def EmailField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    placeholder: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create an email input field."""
    return FormField(
        default=default,
        input_type="email",
        title=title,
        placeholder=placeholder or "example@example.com",
        help_text=help_text,
        icon=icon or "envelope",
        **kwargs,
    )


def NumberField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    placeholder: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    **kwargs,
) -> Any:
    """Create a number input field."""
    return FormField(
        default=default,
        input_type="number",
        title=title,
        placeholder=placeholder,
        help_text=help_text,
        icon=icon,
        min_value=min_value,
        max_value=max_value,
        **kwargs,
    )


def SelectField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    options: List[Union[str, Dict[str, Any]]],
    **kwargs,
) -> Any:
    """Create a select dropdown field."""
    return FormField(
        default=default,
        input_type="select",
        title=title,
        help_text=help_text,
        icon=icon,
        options=options,
        **kwargs,
    )


def CheckboxField(
    default: bool = False,
    *,
    title: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create a checkbox input field."""
    return FormField(
        default=default,
        input_type="checkbox",
        title=title,
        help_text=help_text,
        icon=icon,
        required=False,  # Checkboxes are usually not required
        **kwargs,
    )


def DateField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create a date input field."""
    return FormField(
        default=default,
        input_type="date",
        title=title,
        help_text=help_text,
        icon=icon or "calendar",
        **kwargs,
    )


def TextAreaField(
    default: Any = ...,
    *,
    title: Optional[str] = None,
    placeholder: Optional[str] = None,
    help_text: Optional[str] = None,
    icon: Optional[str] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    rows: int = 4,
    **kwargs,
) -> Any:
    """Create a textarea input field."""
    # Add rows to json_schema_extra
    extra = kwargs.get("json_schema_extra", {})
    extra["rows"] = rows
    kwargs["json_schema_extra"] = extra

    return FormField(
        default=default,
        input_type="textarea",
        title=title,
        placeholder=placeholder,
        help_text=help_text,
        icon=icon,
        min_length=min_length,
        max_length=max_length,
        **kwargs,
    )


__all__ = [
    "FormField",
    "create_field_with_validation",
    "TextField",
    "EmailField",
    "NumberField",
    "SelectField",
    "CheckboxField",
    "DateField",
    "TextAreaField",
]
