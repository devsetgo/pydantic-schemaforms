from typing import Any, Literal

import inspect

from pydantic import BaseModel
from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo

from .show_when import check_rule
from .validation import ValidationResult
from .tstring import SafeHTML


_PYDANTIC_FIELD_PARAMS = frozenset(inspect.signature(PydanticField).parameters)


def Field(
    default: Any = ...,
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    examples: list[Any] | None = None,
    exclude: bool | None = None,
    discriminator: str | None = None,
    json_schema_extra: dict[str, Any] | None = None,
    frozen: bool | None = None,
    validate_default: bool | None = None,
    repr: bool = True,
    init_var: bool | None = None,
    kw_only: bool | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    # UI-specific parameters
    input_type: str | None = None,
    ui_element: str | None = None,
    ui_widget: str | None = None,
    ui_autofocus: bool | None = None,
    ui_options: dict[str, Any] | None = None,
    ui_placeholder: str | None = None,
    ui_help_text: str | None = None,
    ui_order: int | None = None,
    ui_disabled: bool | None = None,
    ui_readonly: bool | None = None,
    ui_hidden: bool | None = None,
    ui_class: str | None = None,
    ui_style: str | None = None,
    ui_add_button_label: str | None = None,
    ui_item_title_template: str | None = None,
    ui_collapsible_items: bool | None = None,
    ui_items_expanded: bool | None = None,
    layout_handler: str | None = None,
    layout_renderer: str | None = None,
    unchecked_message: str | None = None,
    ui_content: str | None = None,
    ui_show_when: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Enhanced Field function that supports UI element specifications.
    Compatible with Pydantic Field but adds UI-specific parameters.

    The ui_* params (and input_type/ui_element) only control rendering --
    they are not validation. min_length/max_length/pattern/ge/le/gt/lt
    (Pydantic's own Field constraints, still accepted here) are what
    actually validates; see `get_app_instructions()` for the full
    constraints-vs-ui_options guidance.

    unchecked_message replaces the error shown when a required checkbox
    (``Literal[True]``, or ``bool`` with no default) is left unticked.

    ui_content is the text of a ``content`` block or ``consent`` field. It is
    escaped unless built with ``html(t'...')``. A ``content`` field submits
    nothing and is left out of validation and the returned data, so it needs
    no default: ``intro: None = Field(ui_element='content', ui_content='...')``.

    ui_show_when hides this field until another field has a given value:
    ``{"field": "contact", "equals": "phone"}``, or ``in``, ``truthy``,
    ``not_empty``. A hidden field submits nothing, so it needs a default, and
    ``"required": True`` in the rule makes it required only while it shows.
    """
    if ui_show_when is not None:
        ui_show_when = check_rule(ui_show_when)
        if default is ... and 'default_factory' not in kwargs:
            raise ValueError(
                'A field with ui_show_when needs a default, since it submits nothing while '
                'hidden. For a value required only while shown, add "required": True to the rule.'
            )
    if 'ui_content_html' in kwargs:
        raise TypeError("Pass ui_content=html(t'...') instead of ui_content_html")
    if ui_element == 'content':
        exclude = True
        if default is ...:
            default = None
    # Collect UI attributes
    ui_attrs = {}
    ui_params = {
        # 'input_type' is a widely-used alias for 'ui_element' (resolve_ui_element()
        # checks both). Declared as a real parameter -- rather than left to fall
        # into **kwargs -- because pydantic's Field() only shims *unrecognized*
        # kwargs into json_schema_extra when that dict is otherwise empty; combined
        # with any other ui_* parameter here (which already populates
        # json_schema_extra), an unrecognized 'input_type' kwarg was silently
        # dropped instead of merged.
        'input_type': input_type,
        'ui_element': ui_element,
        'ui_widget': ui_widget,
        'ui_autofocus': ui_autofocus,
        'ui_options': ui_options,
        'ui_placeholder': ui_placeholder,
        'ui_help_text': ui_help_text,
        'ui_order': ui_order,
        'ui_disabled': ui_disabled,
        'ui_readonly': ui_readonly,
        'ui_hidden': ui_hidden,
        'ui_class': ui_class,
        'ui_style': ui_style,
        'ui_add_button_label': ui_add_button_label,
        'ui_item_title_template': ui_item_title_template,
        'ui_collapsible_items': ui_collapsible_items,
        'ui_items_expanded': ui_items_expanded,
        # Same fix as input_type above: LayoutEngine._build_layout_body()
        # reads these straight (no 'ui_' prefix), and they're just as
        # likely to be combined with another ui_*/input_type parameter
        # (input_type='layout' is required to dispatch here at all).
        'layout_handler': layout_handler,
        'layout_renderer': layout_renderer,
        'unchecked_message': unchecked_message,
        'ui_show_when': ui_show_when,
    }
    # JSON Schema generation turns SafeHTML back into a plain str, so which kind
    # it was has to be kept in the key.
    ui_params['ui_content_html' if isinstance(ui_content, SafeHTML) else 'ui_content'] = ui_content

    # Other UI keys (ui_collapsible, ui_step_title, icon, ...) must not fall
    # through to pydantic's **kwargs: it drops unknown kwargs whenever
    # json_schema_extra is already populated, e.g. by ui_help_text above.
    for key in [k for k in kwargs if k not in _PYDANTIC_FIELD_PARAMS]:
        ui_params[key] = kwargs.pop(key)

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
    rich schemas for form rendering using a JSON-schema-form style UI vocabulary.

    AI assistants: run `python -m pydantic_schemaforms.ai_instructions <profile>`
    (claude/copilot/generic) for integration guidance covering CSRF, model_list,
    as_api_model, and validation patterns before hand-rolling a route.
    """

    __runtime_fields__: dict[str, tuple[Any, FieldInfo]] = {}
    __runtime_model_cache__: type['FormModel'] | None = None
    __api_model_cache__: type[BaseModel] | None = None
    _dynamic_field_names: set[str] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__runtime_fields__ = {}
        cls.__runtime_model_cache__ = None
        cls.__api_model_cache__ = None
        cls._dynamic_field_names = set()

    @classmethod
    def get_json_schema(cls) -> dict[str, Any]:
        """Get JSON schema with UI element information extracted from field annotations."""
        cls.ensure_dynamic_fields()
        schema = cls.model_json_schema()
        properties = schema.get('properties', {})
        enhanced_props = {}

        # Get field information from the model
        for field_name, field_info in cls.model_fields.items():
            prop = properties.get(field_name, {})

            # Basic field information
            enhanced = {
                'type': prop.get('type', 'string'),
                'title': prop.get('title', field_name.replace('_', ' ').title()),
                'description': prop.get('description', ''),
            }

            # Forward all standard JSON Schema constraint keys
            _CONSTRAINT_KEYS = {
                'minLength',
                'maxLength',
                'pattern',
                'format',
                'minimum',
                'maximum',
                'exclusiveMinimum',
                'exclusiveMaximum',
                'multipleOf',
                'enum',
                'const',
            }
            for _key in _CONSTRAINT_KEYS:
                if _key in prop:
                    enhanced[_key] = prop[_key]

            # Extract UI elements from field info
            ui_info = cls._extract_ui_info(field_info)
            if ui_info:
                enhanced['ui'] = ui_info

            enhanced_props[field_name] = enhanced

        return {
            'title': schema.get('title', cls.__name__),
            'type': 'object',
            'properties': enhanced_props,
            'required': schema.get('required', []),
        }

    @classmethod
    def get_pydantic_json_schema(
        cls,
        *,
        by_alias: bool = True,
        ref_template: str = '#/$defs/{model}',
        mode: Literal['validation', 'serialization'] = 'validation',
    ) -> dict[str, Any]:
        """Standard, nested-aware JSON Schema (with $defs/$ref) for this form's
        underlying Pydantic model — unlike get_json_schema(), which is a
        flattened, UI-oriented shape used for rendering.
        """
        cls.ensure_dynamic_fields()
        return cls.as_api_model().model_json_schema(
            by_alias=by_alias, ref_template=ref_template, mode=mode
        )

    @classmethod
    def _extract_ui_info(cls, field_info: FieldInfo) -> dict[str, Any]:
        """Extract UI-specific information from field annotations."""
        ui_info = {}

        # Check for UI element type in json_schema_extra
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                for key, value in extra.items():
                    if key.startswith('ui_'):
                        ui_key = key[3:]  # Remove 'ui_' prefix
                        ui_info[ui_key] = value
            elif callable(extra):
                schema = {}
                extra(schema)
                for key, value in schema.items():
                    if key.startswith('ui_'):
                        ui_key = key[3:]  # Remove 'ui_' prefix
                        ui_info[ui_key] = value

        return ui_info

    @classmethod
    def render_form(
        cls,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        framework: str = 'bootstrap',
        *,
        submit_url: str,
        self_contained: bool = False,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
        **kwargs: Any,
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
        from .enhanced_renderer import render_form_html

        return render_form_html(
            cls,
            form_data=data,
            errors=errors,
            framework=framework,
            submit_url=submit_url,
            self_contained=self_contained,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
            **kwargs,
        )

    @classmethod
    async def render_form_async(
        cls,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        framework: str = 'bootstrap',
        *,
        submit_url: str,
        self_contained: bool = False,
        include_framework_assets: bool = False,
        asset_mode: str = 'vendored',
        **kwargs: Any,
    ) -> str:
        """Async render helper for FormModel."""
        from .enhanced_renderer import render_form_html_async

        return await render_form_html_async(
            cls,
            form_data=data,
            errors=errors,
            framework=framework,
            submit_url=submit_url,
            self_contained=self_contained,
            include_framework_assets=include_framework_assets,
            asset_mode=asset_mode,
            **kwargs,
        )

    @classmethod
    def render_display(
        cls,
        data: Any,
        framework: str = 'bootstrap',
        *,
        layout: str = 'vertical',
        edit_urls: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render validated data read-only: a review or confirmation page, with
        the form's labels, order and sections but no inputs.

        Args:
            data: `result.data` from `validate()`, another dict shaped like the
                model, or an instance of a model
            framework: CSS framework to use (bootstrap, material, none)
            layout: Same values as `render_form`; `wizard` shows one flat page
            edit_urls: Sub-form field name to URL, adding an Edit link to that section
            **kwargs: Asset options as for `render_form`, plus `material_variant`

        Passwords are masked, card and social security numbers show only their
        last four digits, and content blocks are left out.

        Returns:
            HTML fragment as string
        """
        from .enhanced_renderer import render_display_html

        return render_display_html(
            cls, data, framework=framework, layout=layout, edit_urls=edit_urls, **kwargs
        )

    @classmethod
    def validate(
        cls,
        data: Any,
        *,
        submit_url: str | None = None,
        framework: str = 'bootstrap',
        **render_kwargs: Any,
    ) -> 'ValidationResult':
        """Validate a submission and return a result that can re-render itself on failure.

        ``data`` is the raw request form (``await request.form()`` in FastAPI,
        ``request.form`` in Flask) or an already nested dict. ``result.data``
        is nested and mirrors the model; ``result.errors`` is a nested error
        tree with the same shape. Render options such as ``layout=`` are kept
        so ``result.render_with_errors()`` needs no arguments.

        Example::

            result = ProfileForm.validate(await request.form(), submit_url="/profile")
            if result.is_valid:
                return save(result.data)
            return HTMLResponse(result.render_with_errors())
        """
        from .validation import validate_form_data

        if 'flatten' in render_kwargs:
            raise TypeError(
                'FormModel.validate(flatten=...) was removed: result.data is always nested JSON '
                'that mirrors the model, e.g. {"pets": [{"name": "Rex"}]}. Drop the argument. '
                'See "Upgrading to nested forms" in the AI instructions '
                '(python -m pydantic_schemaforms.ai_instructions claude).'
            )

        result = validate_form_data(cls, data)
        result._submit_url = submit_url
        result._framework = framework
        result._render_kwargs = render_kwargs
        return result

    @classmethod
    def register_field(
        cls,
        field_name: str,
        *,
        annotation: Any = Any,
        field: FieldInfo | None = None,
    ) -> FieldInfo:
        """Register a new field on the model at runtime."""

        field_info = field or Field(...)
        field_info.annotation = annotation or Any  # type: ignore[misc]

        runtime_fields = dict(getattr(cls, '__runtime_fields__', {}))
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

        processed: set[str] = set(getattr(cls, '_dynamic_field_names', set()))
        new_fields: list[str] = []
        runtime_fields = dict(getattr(cls, '__runtime_fields__', {}))

        for attr_name, attr_value in cls.__dict__.items():
            if not isinstance(attr_value, FieldInfo):
                continue
            if attr_name in processed:
                continue
            new_fields.append(attr_name)
            runtime_fields.setdefault(
                attr_name,
                (
                    getattr(attr_value, 'annotation', Any) or Any,
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
    def get_runtime_model(cls) -> type['FormModel']:
        """Return a model class that includes any registered runtime fields."""

        cls.ensure_dynamic_fields()

        if not getattr(cls, '__runtime_fields__', {}):
            return cls

        if cls.__runtime_model_cache__ is not None:
            return cls.__runtime_model_cache__

        import warnings
        from pydantic import create_model

        field_definitions = {
            name: (annotation, field_info)
            for name, (annotation, field_info) in cls.__runtime_fields__.items()
        }

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning, message='.*shadow.*')
            runtime_model = create_model(  # type: ignore[call-overload]
                f'{cls.__name__}Runtime',
                __base__=cls,
                **field_definitions,  # type: ignore[arg-type]
            )

        cls.__runtime_model_cache__ = runtime_model
        return runtime_model

    @classmethod
    def as_api_model(cls) -> type[BaseModel]:
        """Return a pure Pydantic BaseModel with UI metadata stripped.

        Preserves field types, titles, descriptions, examples, and all
        validation constraints (min_length, ge, pattern, …). Only removes
        keys starting with ``ui_`` from json_schema_extra so that FastAPI's
        OpenAPI output looks like a normal Pydantic model.

        The result is cached per subclass and safe to assign at module level::

            ContactSchema = ContactForm.as_api_model()

            @app.post('/api/contact', response_model=ContactSchema)
            async def api_contact(data: ContactSchema): ...
        """
        if cls.__api_model_cache__ is not None:
            return cls.__api_model_cache__

        import copy
        from pydantic import create_model as _create_model

        cls.ensure_dynamic_fields()

        field_defs: dict[str, tuple[Any, FieldInfo]] = {}
        for name, fi in cls.get_runtime_model().model_fields.items():
            if isinstance(fi.json_schema_extra, dict) and (
                fi.json_schema_extra.get('ui_element') == 'content'
            ):
                continue
            clean = copy.copy(fi)
            if isinstance(fi.json_schema_extra, dict):
                stripped = {
                    k: v for k, v in fi.json_schema_extra.items() if not k.startswith('ui_')
                }
                clean.json_schema_extra = stripped or None
            field_defs[name] = (fi.annotation, clean)

        model = _create_model(  # type: ignore[call-overload]
            cls.__name__,
            __base__=BaseModel,
            **field_defs,  # type: ignore[arg-type]
        )
        cls.__api_model_cache__ = model
        return model

    @classmethod
    def get_example_form_data(cls: type['FormModel']) -> dict:
        example = {}
        for field_name, model_field in cls.model_fields.items():
            typ = getattr(model_field, 'annotation', None)
            if typ is str:
                example[field_name] = 'example'
            elif typ is int:
                example[field_name] = 123
            elif typ is float:
                example[field_name] = 1.23
            elif typ is bool:
                example[field_name] = True
            else:
                example[field_name] = ''
        return example
