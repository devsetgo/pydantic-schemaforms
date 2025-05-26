from typing import Any, Dict, Optional, Type

from .schema_form import FormModel


class SchemaFormValidationError(Exception):
    """
    Custom exception for schema form validation errors.
    Accepts a list of error dicts.
    """

    def __init__(self, errors: list):
        self.errors = errors
        super().__init__("SchemaForm validation error")


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Dict[str, str]] = None,
    htmx_post_url: str = "/submit",
) -> str:
    """
    Render an HTML form for the given FormModel class using standard HTML inputs and HTMX.
    """
    schema = form_model_cls.get_json_schema()
    form_data = form_data or {}
    errors = errors or {}

    html = [
        f'<form hx-post="{htmx_post_url}" hx-target="#form-response" hx-swap="innerHTML" method="POST">'
    ]
    for field, prop in schema["properties"].items():
        value = form_data.get(field, "")
        error = errors.get(field)
        input_type = "text"
        if prop["type"] == "string":
            if "password" in field.lower():
                input_type = "password"
            elif "email" in field.lower():
                input_type = "email"
            elif "textarea" in field.lower() or prop.get("maxLength", 0) > 200:
                html.append(f'<label for="{field}">{prop["title"]}</label>')
                html.append(
                    f'<textarea id="{field}" name="{field}" placeholder="{prop.get("description", "")}">{value}</textarea>'
                )
                if error:
                    html.append(f'<div class="error" style="color:red;">{error}</div>')
                continue
        elif prop["type"] == "integer":
            input_type = "number"
        elif prop["type"] == "number":
            input_type = "number"
        elif prop["type"] == "boolean":
            input_type = "checkbox"
        html.append(f'<label for="{field}">{prop["title"]}</label>')
        html.append(
            f'<input id="{field}" name="{field}" type="{input_type}" value="{value}" placeholder="{prop.get("description", "")}"/>'
        )
        if error:
            html.append(f'<div class="error" style="color:red;">{error}</div>')
    html.append('<button type="submit">Submit</button>')
    html.append("</form>")
    html.append('<div id="form-response"></div>')
    html.append('<script src="https://unpkg.com/htmx.org@2.0.4"></script>')
    html.append('<script src="https://unpkg.com/imask"></script>')
    return "\n".join(html)
