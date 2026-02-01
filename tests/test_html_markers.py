from __future__ import annotations


def test_render_form_html_wrapped_by_default() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import Field, FormModel

    class _MarkerForm(FormModel):
        name: str = Field(default="", title="Name")

    html = render_form_html(_MarkerForm)
    assert html.splitlines()[0] == "<!--- Start Pydantic-SchemaForms -->"
    assert html.splitlines()[-1] == "<!--- End Pydantic-SchemaForms -->"


def test_legacy_render_form_html_wraps_after_appends() -> None:
    from pydantic_schemaforms.render_form import render_form_html
    from pydantic_schemaforms.schema_form import Field, FormModel

    class _MarkerForm(FormModel):
        name: str = Field(default="", title="Name")

    html = render_form_html(_MarkerForm, submit_url="/test")
    assert html.splitlines()[0] == "<!--- Start Pydantic-SchemaForms -->"
    assert html.splitlines()[-1] == "<!--- End Pydantic-SchemaForms -->"


def test_render_form_page_wrapped_by_default() -> None:
    from pydantic_schemaforms.integration.builder import create_login_form, render_form_page

    html = render_form_page(create_login_form(), title="Login")
    assert html.splitlines()[0] == "<!--- Start Pydantic-SchemaForms -->"
    assert html.splitlines()[-1] == "<!--- End Pydantic-SchemaForms -->"
