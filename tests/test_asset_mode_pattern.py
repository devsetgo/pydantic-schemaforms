def test_enhanced_renderer_include_assets_vendored_inlines_bootstrap() -> None:
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title="Name")

    renderer = EnhancedFormRenderer(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="vendored",
    )
    html = renderer.render_form_from_model(Demo)
    assert "<style>" in html
    assert "cdn.jsdelivr.net" not in html
    # Sanity check vendored bootstrap content is present (protects against packaging issues)
    assert "Bootstrap" in html
    assert "v5.3.0" in html

    renderer_cdn = EnhancedFormRenderer(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="cdn",
    )
    html_cdn = renderer_cdn.render_form_from_model(Demo)
    assert "cdn.jsdelivr.net/npm/bootstrap@5.3.0" in html_cdn


def test_render_form_html_self_contained_bootstrap_inlines_assets() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title="Name")

    html = render_form_html(
        Demo,
        framework="bootstrap",
        self_contained=True,
        submit_url="/demo",
    )
    assert "<style>" in html
    assert "cdn.jsdelivr.net" not in html
    assert "Bootstrap" in html
    assert "v5.3.0" in html


def test_form_builder_include_assets_requires_cdn_mode() -> None:
    from pydantic_schemaforms.integration.builder import FormBuilder

    builder = FormBuilder(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="vendored",
    ).text_input("name", "Name")

    html = builder.render()
    assert "cdn.jsdelivr.net" not in html

    builder_cdn = FormBuilder(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="cdn",
    ).text_input("name", "Name")

    html_cdn = builder_cdn.render()
    assert "cdn.jsdelivr.net/npm/bootstrap@5.3.0" in html_cdn
