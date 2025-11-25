"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

import asyncio
        }
        form_attrs.update(kwargs)
        # Ensure action isn't overridden by kwargs
        form_attrs["action"] = submit_url

        form_parts = [self._build_form_tag(form_attrs)]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append(self._render_csrf_field())

        fields = metadata.fields
        required_fields = metadata.required_fields
        layout_fields = metadata.layout_fields
        non_layout_fields = metadata.non_layout_fields

        # If we have multiple layout fields and few/no other fields, render as tabs
        if len(layout_fields) > 1 and len(non_layout_fields) == 0:
            # Render layout fields as tabs
            form_parts.extend(
                self._render_layout_fields_as_tabs(
                    layout_fields,
                    data,
                    errors,
                    required_fields,
                    context,
                )
            )
        elif layout == "tabbed":
            form_parts.extend(
                self._render_tabbed_layout(fields, data, errors, required_fields, context)
            )
        elif layout == "side-by-side":
            form_parts.extend(
                self._render_side_by_side_layout(fields, data, errors, required_fields, context)
            )
        else:
            # Render each field with appropriate layout
            for field_name, field_schema in fields:
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    context,
                    layout,
                    errors,  # Pass full errors dictionary
                )
                form_parts.append(field_html)

        # Add submit button if requested
        if include_submit_button:
            form_parts.append(self._render_submit_button())

        form_parts.append("</form>")

        has_model_list_fields = any(
            resolve_ui_element(field_schema) == "model_list" for _name, field_schema in fields
        )

        # Add model list JavaScript if any model_list fields were rendered
        if has_model_list_fields:
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self.framework)
            form_parts.append(list_renderer.get_model_list_javascript())

        return "\n".join(form_parts)

    def render_form_fields_only(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """
        Render only the form fields without the form wrapper.
        This is useful for rendering nested forms within tabs.

        Args:
            model_cls: Pydantic model class with UI element specifications
            data: Form data to populate fields with
            errors: Validation errors to display
            layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
            **kwargs: Additional rendering options

        Returns:
            HTML for form fields only (no <form> tags)
        """
        metadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        # Store current form data for nested forms to access
        self._current_form_data = data

        # Store schema definitions for model_list fields
        self._schema_defs = metadata.schema_defs
        context = RenderContext(form_data=data, schema_defs=self._schema_defs)

        # Handle SchemaFormValidationError format
        if isinstance(errors, dict) and "errors" in errors:
            errors = {err.get("name", ""): err.get("message", "") for err in errors["errors"]}

        fields = metadata.fields
        required_fields = metadata.required_fields

        form_parts = []

        # Render fields based on layout
        for field_name, field_schema in fields:
            field_html = self._render_field(
                field_name,
                field_schema,
                data.get(field_name),
                errors.get(field_name),
                required_fields,
                context,
                layout,
                errors,  # Pass full errors dictionary
            )
            form_parts.append(field_html)

        return "\n".join(form_parts)

    async def render_form_from_model_async(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        include_csrf: bool = False,
        include_submit_button: bool = True,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """
        Async version of render_form_from_model for high-performance applications.

        This method is useful when rendering multiple forms concurrently or when
        integrating with async validation services.
        """
        # For CPU-bound form rendering, we run in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Use default thread pool
            self.render_form_from_model,
            model_cls,
            data,
            errors,
            submit_url,
            method,
            include_csrf,
            include_submit_button,
            layout,
            **kwargs,
        )

    def _build_form_tag(self, attrs: Dict[str, Any]) -> str:
        """Build opening form tag with attributes."""
        attr_strings = []
        for key, value in attrs.items():
            if value is not None:
                attr_strings.append(f'{key}="{escape(str(value))}"')
        return f'<form {" ".join(attr_strings)}>'

    def _render_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        layout: str = "vertical",
        all_errors: Optional[Dict[str, str]] = None,
    ) -> str:
        return self._field_renderer.render_field(
            field_name,
            field_schema,
            value,
            error,
            required_fields,
            context,
            layout,
            all_errors,
        )

    # Field rendering helpers are now provided by FieldRenderer; legacy implementations
    # were removed to keep this class focused on orchestration and layout concerns.

    def _render_tabbed_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render fields in a tabbed layout."""
        return self._layout_engine.render_tabbed_layout(
            fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_layout_fields_as_tabs(
        self,
        layout_fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render layout fields as tabs, with each layout field becoming a tab containing its form."""
        return self._layout_engine.render_layout_fields_as_tabs(
            layout_fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_layout_field_content(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        """Render the content of a layout field (the nested form)."""
        return self._layout_engine.render_layout_field_content(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _get_nested_form_data(
        self,
        field_name: str,
        main_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Adapter to share nested data helper across renderers."""
        data = main_data if main_data is not None else getattr(self, "_current_form_data", {}) or {}
        return get_nested_form_data(field_name, data)

    def _render_side_by_side_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render fields in a side-by-side layout using Bootstrap grid."""
        return self._layout_engine.render_side_by_side_layout(
            fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_model_list_from_schema(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        schema_def: Dict[str, Any],
        values: List[Dict[str, Any]],
        error: Optional[str],
        ui_info: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> str:
        """Render a model list using schema definition instead of model class."""
        # Use simplified rendering for schema-based lists

        html = f"""
        <div class="mb-3">
            <label class="form-label fw-bold">
                {escape(field_schema.get('title', field_name.replace('_', ' ').title()))}
                {' <span class="text-danger">*</span>' if field_name in (required_fields or []) else ''}
            </label>

            <div class="model-list-container"
                 data-field-name="{field_name}"
                 data-min-items="{field_schema.get('minItems', 0)}"
                 data-max-items="{field_schema.get('maxItems', 10)}">

                <div class="model-list-items" id="{field_name}-items">"""

        # Render existing items
        for i, item_data in enumerate(values):
            html += self._render_schema_list_item(
                field_name,
                schema_def,
                i,
                item_data,
                context,
                ui_info,
            )

        # If no items and minItems > 0, add empty items
        min_items = field_schema.get("minItems", 0)
        if not values and min_items > 0:
            for i in range(min_items):
                html += self._render_schema_list_item(
                    field_name,
                    schema_def,
                    i,
                    {},
                    context,
                    ui_info,
                )

        # If no items at all, add one empty item for user convenience
        if not values and min_items == 0:
            html += self._render_schema_list_item(
                field_name,
                schema_def,
                0,
                {},
                context,
                ui_info,
            )

        html += f"""
                </div>

                <div class="model-list-controls mt-2">
                    <button type="button"
                            class="btn btn-outline-primary btn-sm add-item-btn"
                            data-target="{field_name}">
                        <i class="bi bi-plus-circle"></i> Add Item
                    </button>
                </div>
            </div>"""

        help_text = ui_info.get("help_text") or field_schema.get("description")
        if help_text:
            html += f"""
            <div class="form-text text-muted">
                <i class="bi bi-info-circle"></i> {escape(help_text)}
            </div>"""

        if error:
            html += f"""
            <div class="invalid-feedback d-block">
                <i class="bi bi-exclamation-triangle"></i> {escape(error)}
            </div>"""

        html += "</div>"
        return html

    def _extract_nested_errors_for_field(
        self, field_name: str, all_errors: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract nested errors for a specific field from the complete error dictionary.

        For example, if field_name is 'pets' and all_errors contains 'pets[0].weight',
        this returns {'0.weight': 'error message'}.

        Args:
            field_name: The base field name (e.g., 'pets')
            all_errors: Complete error dictionary with nested paths

        Returns:
            Dictionary of nested errors with simplified paths
        """
        nested_errors = {}
        field_prefix = f"{field_name}["

        for error_path, error_message in (all_errors or {}).items():
            if error_path.startswith(field_prefix):
                # Extract the part after the field name prefix
                # e.g., 'pets[0].weight' -> '0].weight' after removing 'pets['
                nested_part = error_path[len(field_prefix) :]  # Remove 'pets['
                if "]." in nested_part:
                    # Replace ]. with . to get '0.weight' from '0].weight'
                    simplified_path = nested_part.replace("].", ".")
                    nested_errors[simplified_path] = error_message

        return nested_errors

    def _render_schema_list_item(
        self,
        field_name: str,
        schema_def: Dict[str, Any],
        index: int,
        item_data: Dict[str, Any],
        context: RenderContext,
        ui_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a single list item from schema definition with collapsible card support."""
        ui_info = ui_info or {}
        collapsible = ui_info.get("collapsible_items", True)
        expanded = ui_info.get("items_expanded", True)
        title_template = ui_info.get("item_title_template", "Item #{index}")

        # Generate dynamic title
        title_vars = {"index": index + 1, **item_data}
        try:
            item_title = title_template.format(**title_vars)
        except (KeyError, ValueError):
            item_title = f"Item #{index + 1}"

        # Determine collapse state
        collapse_class = "" if expanded else "collapse"
        collapse_id = f"{field_name}_item_{index}_content"

        html = f"""
        <div class="model-list-item card border mb-3"
             data-index="{index}"
             data-title-template="{escape(title_template)}"
             data-field-name="{field_name}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">"""

        if collapsible:
            html += f"""
                    <button class="btn btn-link text-decoration-none p-0 text-start"
                            type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#{collapse_id}"
                            aria-expanded="{str(expanded).lower()}"
                            aria-controls="{collapse_id}">
                        <i class="bi bi-chevron-{'down' if expanded else 'right'} me-2"></i>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </button>"""
        else:
            html += f"""
                    <span>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </span>"""

        html += f"""
                </h6>
                <button type="button"
                        class="btn btn-outline-danger btn-sm remove-item-btn"
                        data-index="{index}"
                        data-field-name="{field_name}"
                        title="Remove this item">
                    <i class="bi bi-trash"></i>
                </button>
            </div>"""

        # Card body with collapse support
        if collapsible:
            html += f"""
            <div class="collapse {collapse_class} show" id="{collapse_id}">
                <div class="card-body">"""
        else:
            html += """
            <div class="card-body">"""

        # Render fields in a responsive grid
        html += '<div class="row">'

        # Render each field in the schema
        properties = schema_def.get("properties", {})
        field_count = len([k for k in properties.keys() if not k.startswith("_")])

        # Determine column class based on field count
        if field_count <= 2:
            col_class = "col-12"
        elif field_count <= 4:
            col_class = "col-md-6"
        else:
            col_class = "col-lg-4 col-md-6"

        for field_key, field_schema in properties.items():
            if field_key.startswith("_"):
                continue

            field_value = item_data.get(field_key, "")
            input_name = f"{field_name}[{index}].{field_key}"

            html += f"""
                <div class="{col_class}">
                    {self._render_field(
                        input_name,
                        field_schema,
                        field_value,
                        None,  # error
                        [],   # required_fields
                        context,
                        "vertical",  # layout
                        None  # all_errors (not available in schema rendering)
                    )}
                </div>"""

        html += "</div>"  # Close row

        if collapsible:
            html += """
                </div>
            </div>"""  # Close card-body and collapse
        else:
            html += "</div>"  # Close card-body

        html += "</div>"  # Close card

        return html

    def _render_csrf_field(self) -> str:
        """Render CSRF token field."""
        # This would integrate with your CSRF protection system
        return '<input type="hidden" name="csrf_token" value="__CSRF_TOKEN__" />'

    def _render_layout_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        """Render a layout field by extracting and rendering its embedded form."""
        return self._layout_engine.render_layout_field(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _render_submit_button(self) -> str:
        """Render form submit button."""
        button_class = self.config["button_class"]
        return f'<button type="submit" class="{button_class}">Submit</button>'


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    **kwargs,
) -> str:
    """
    Convenience function to render an HTML form for the given FormModel class.

    Args:
        form_model_cls: Pydantic FormModel class with UI elements
        form_data: Form data to populate fields with
        errors: Validation errors (dict or SchemaFormValidationError)
        framework: CSS framework to use
        layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    # Handle SchemaFormValidationError
    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    # Use SimpleMaterialRenderer for Material Design 3
    if framework == "material":
        from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        return renderer.render_form_from_model(
            form_model_cls, data=form_data, errors=errors, **kwargs
        )

    # Use EnhancedFormRenderer for other frameworks
    renderer = EnhancedFormRenderer(framework=framework)
    return renderer.render_form_from_model(
        form_model_cls, data=form_data, errors=errors, layout=layout, **kwargs
    )


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    **kwargs,
) -> str:
    """
    Async convenience function to render an HTML form for the given FormModel class.

    Args:
        form_model_cls: Pydantic FormModel class with UI elements
        form_data: Form data to populate fields with
        errors: Validation errors (dict or SchemaFormValidationError)
        framework: CSS framework to use
        layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    render_callable = partial(
        render_form_html,
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        layout=layout,
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
