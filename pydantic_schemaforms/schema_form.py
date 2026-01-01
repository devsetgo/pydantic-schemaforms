from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

from pydantic import BaseModel
from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo

# Import the new FormField


def form_validator(func: Callable) -> Callable:
    """
    Decorator for form validation methods that matches the design_idea.py vision.

    This decorator provides a clean way to define cross-field validation on FormModel classes.
    It wraps the function to provide better error handling and integration with the form system.

    Usage:
        class MyForm(FormModel):
            age: int = FormField(..., input_type="number")
            parental_consent: bool = FormField(False, input_type="checkbox")

            @form_validator
            def check_age_and_consent(cls, values: Dict[str, Any]) -> Dict[str, Any]:
                age = values.get('age')
                consent = values.get('parental_consent')
                if age is not None and age < 18 and not consent:
                    raise ValueError("Parental consent is required for users under 18.")
                return values
    """

    @wraps(func)
    def wrapper(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return func(cls, values)
        except ValueError as e:
            # Convert to a more detailed validation error
            raise ValueError(f"Form validation failed: {str(e)}")
        except Exception as e:
            # Handle unexpected errors
            raise ValueError(f"Validation error: {str(e)}")

    # Mark the function as a form validator
    wrapper._is_form_validator = True
    return classmethod(wrapper)


def Field(
    default: Any = ...,
    *,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[List[Any]] = None,
    exclude: Optional[bool] = None,
    discriminator: Optional[str] = None,
    json_schema_extra: Optional[Dict[str, Any]] = None,
    frozen: Optional[bool] = None,
    validate_default: Optional[bool] = None,
    repr: bool = True,
    init_var: Optional[bool] = None,
    kw_only: Optional[bool] = None,
    pattern: Optional[str] = None,
    strict: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
    # UI-specific parameters
    ui_element: Optional[str] = None,
    ui_widget: Optional[str] = None,
    ui_autofocus: Optional[bool] = None,
    ui_options: Optional[Dict[str, Any]] = None,
    ui_placeholder: Optional[str] = None,
    ui_help_text: Optional[str] = None,
    ui_order: Optional[int] = None,
    ui_disabled: Optional[bool] = None,
    ui_readonly: Optional[bool] = None,
    ui_hidden: Optional[bool] = None,
    ui_class: Optional[str] = None,
    ui_style: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """
    Enhanced Field function that supports UI element specifications.
    Compatible with Pydantic Field but adds UI-specific parameters.
    """
    # Collect UI attributes
    ui_attrs = {}
    ui_params = {
        "ui_element": ui_element,
        "ui_widget": ui_widget,
        "ui_autofocus": ui_autofocus,
        "ui_options": ui_options,
        "ui_placeholder": ui_placeholder,
        "ui_help_text": ui_help_text,
        "ui_order": ui_order,
        "ui_disabled": ui_disabled,
        "ui_readonly": ui_readonly,
        "ui_hidden": ui_hidden,
        "ui_class": ui_class,
        "ui_style": ui_style,
    }

    # Filter out None values and add to json_schema_extra
    for key, value in ui_params.items():
        if value is not None:
            ui_attrs[key] = value

    # Merge with existing json_schema_extra
    if json_schema_extra is None:
        json_schema_extra = {}
    json_schema_extra.update(ui_attrs)

    # Call the original Pydantic Field function
    return PydanticField(
        default=default,
        alias=alias,
        title=title,
        description=description,
        examples=examples,
        exclude=exclude,
        discriminator=discriminator,
        json_schema_extra=json_schema_extra,
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
        max_length=max_length,
        min_length=min_length,
        **kwargs,
    )


class FormModel(BaseModel):
    """
    Enhanced base class for form models with UI element support.
    Supports UI element specifications through field annotations and generates
    rich schemas for form rendering similar to React JSON Schema Forms.
    """

    __runtime_fields__: Dict[str, Tuple[Any, FieldInfo]] = {}
    __runtime_model_cache__: Optional[Type["FormModel"]] = None
    _dynamic_field_names: Set[str] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__runtime_fields__ = {}
        cls.__runtime_model_cache__ = None
        cls._dynamic_field_names = set()

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """Get JSON schema with UI element information extracted from field annotations."""
        cls.ensure_dynamic_fields()
        schema = cls.model_json_schema() if hasattr(cls, "model_json_schema") else cls.schema()
        properties = schema.get("properties", {})
        enhanced_props = {}

        # Get field information from the model
        for field_name, field_info in cls.model_fields.items():
            prop = properties.get(field_name, {})

            # Basic field information
            enhanced = {
                "type": prop.get("type", "string"),
                "title": prop.get("title", field_name.replace("_", " ").title()),
                "description": prop.get("description", ""),
            }

            # Add validation constraints
            if enhanced["type"] == "string":
                if "minLength" in prop:
                    enhanced["minLength"] = prop["minLength"]
                if "maxLength" in prop:
                    enhanced["maxLength"] = prop["maxLength"]
                if "pattern" in prop:
                    enhanced["pattern"] = prop["pattern"]
            elif enhanced["type"] in ("number", "integer"):
                if "minimum" in prop:
                    enhanced["minimum"] = prop["minimum"]
                if "maximum" in prop:
                    enhanced["maximum"] = prop["maximum"]
            if "enum" in prop:
                enhanced["enum"] = prop["enum"]

            # Extract UI elements from field info
            ui_info = cls._extract_ui_info(field_info)
            if ui_info:
                enhanced["ui"] = ui_info

            enhanced_props[field_name] = enhanced

        return {
            "title": schema.get("title", cls.__name__),
            "type": "object",
            "properties": enhanced_props,
            "required": schema.get("required", []),
        }

    @classmethod
    def _extract_ui_info(cls, field_info: FieldInfo) -> Dict[str, Any]:
        """Extract UI-specific information from field annotations."""
        ui_info = {}

        # Check for UI element type in json_schema_extra
        if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                for key, value in extra.items():
                    if key.startswith("ui_"):
                        ui_key = key[3:]  # Remove 'ui_' prefix
                        ui_info[ui_key] = value
            elif callable(extra):
                # Handle callable json_schema_extra
                schema = {}
                extra(schema, cls)
                for key, value in schema.items():
                    if key.startswith("ui_"):
                        ui_key = key[3:]  # Remove 'ui_' prefix
                        ui_info[ui_key] = value

        return ui_info

    @classmethod
    def render_form(
        cls,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        framework: str = "bootstrap",
        **kwargs,
    ) -> str:
        """
        Render the form as HTML using the enhanced form renderer.

        Args:
            data: Form data to populate fields with
            errors: Validation errors to display
            framework: CSS framework to use (bootstrap, material, shadcn)
            **kwargs: Additional rendering options

        Returns:
            Complete HTML form as string
        """
        from .enhanced_renderer import EnhancedFormRenderer

        renderer = EnhancedFormRenderer(framework=framework)
        return renderer.render_form_from_model(cls, data=data, errors=errors, **kwargs)

    @classmethod
    def register_field(
        cls,
        field_name: str,
        *,
        annotation: Any = Any,
        field: Optional[FieldInfo] = None,
    ) -> FieldInfo:
        """Register a new field on the model at runtime."""

        field_info = field or Field(...)
        field_info.annotation = annotation or Any
        setattr(cls, field_name, field_info)

        runtime_fields = dict(getattr(cls, "__runtime_fields__", {}))
        runtime_fields[field_name] = (annotation or Any, field_info)
        cls.__runtime_fields__ = runtime_fields
        cls.__runtime_model_cache__ = None
        cls.ensure_dynamic_fields()

        try:  # Reset schema cache so renderers pick up new field definitions
            from .rendering.schema_parser import reset_schema_metadata_cache

            reset_schema_metadata_cache()
        except Exception:  # pragma: no cover - best effort in loose import situations
            pass

        return field_info

    @classmethod
    def ensure_dynamic_fields(cls) -> bool:
        """Detect FieldInfo attributes assigned after class creation."""

        processed: set[str] = set(getattr(cls, "_dynamic_field_names", set()))
        new_fields: List[str] = []
        runtime_fields = dict(getattr(cls, "__runtime_fields__", {}))

        for attr_name, attr_value in cls.__dict__.items():
            if not isinstance(attr_value, FieldInfo):
                continue
            if attr_name in processed:
                continue
            new_fields.append(attr_name)
            runtime_fields.setdefault(
                attr_name,
                (
                    getattr(attr_value, "annotation", Any) or Any,
                    attr_value,
                ),
            )
            cls.__runtime_model_cache__ = None

        if not new_fields:
            return False

        cls.__runtime_fields__ = runtime_fields
        cls._dynamic_field_names = processed.union(new_fields)
        return True

    @classmethod
    def get_runtime_model(cls) -> Type["FormModel"]:
        """Return a model class that includes any registered runtime fields."""

        cls.ensure_dynamic_fields()

        if not getattr(cls, "__runtime_fields__", {}):
            return cls

        if cls.__runtime_model_cache__ is not None:
            return cls.__runtime_model_cache__

        from pydantic import create_model

        field_definitions = {
            name: (annotation, field_info)
            for name, (annotation, field_info) in cls.__runtime_fields__.items()
        }

        runtime_model = create_model(
            f"{cls.__name__}Runtime",
            __base__=cls,
            **field_definitions,
        )
        # TODO: Suppress the UserWarning about shadowed fields once the helper
        #       grows a local model_config; the runtime class is expected.

        cls.__runtime_model_cache__ = runtime_model
        return runtime_model

    @classmethod
    def get_example_form_data(cls: Type["FormModel"]) -> dict:
        example = {}
        for field_name, model_field in cls.model_fields.items():
            typ = getattr(model_field, "annotation", None)
            if typ is str:
                example[field_name] = "example"
            elif typ is int:
                example[field_name] = 123
            elif typ is float:
                example[field_name] = 1.23
            elif typ is bool:
                example[field_name] = True
            else:
                example[field_name] = ""
        return example


class ValidationResult:
    """
    Validation result object that provides clean error handling for forms.

    This matches the design_idea.py vision where validation returns an object
    with .is_valid, .data, and .render_with_errors() methods.
    """

    def __init__(
        self,
        is_valid: bool,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        form_model_cls: Optional[Type[FormModel]] = None,
        original_data: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid = is_valid
        self.data = data or {}
        self.errors = errors or {}
        self.form_model_cls = form_model_cls
        self.original_data = original_data or {}

    def render_with_errors(self, framework: str = "bootstrap", **kwargs) -> str:
        """
        Render the form with validation errors displayed.

        Args:
            framework: CSS framework to use
            **kwargs: Additional rendering options

        Returns:
            HTML form with errors displayed
        """
        if not self.form_model_cls:
            raise ValueError("Cannot render form: form_model_cls not provided")

        return self.form_model_cls.render_form(
            data=self.original_data, errors=self.errors, framework=framework, **kwargs
        )

    def __str__(self) -> str:
        if self.is_valid:
            return f"ValidationResult(valid=True, data={self.data})"
        else:
            return f"ValidationResult(valid=False, errors={self.errors})"
