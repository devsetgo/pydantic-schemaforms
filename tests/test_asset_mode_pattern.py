def test_enhanced_renderer_include_assets_requires_cdn_mode() -> None:
    from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_forms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title="Name")

    renderer = EnhancedFormRenderer(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="vendored",
    )
    html = renderer.render_form_from_model(Demo)
    assert "cdn.jsdelivr.net" not in html

    renderer_cdn = EnhancedFormRenderer(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="cdn",
    )
    html_cdn = renderer_cdn.render_form_from_model(Demo)
    assert "cdn.jsdelivr.net/npm/bootstrap@5.3.0" in html_cdn


def test_form_builder_include_assets_requires_cdn_mode() -> None:
    from pydantic_forms.integration.builder import FormBuilder

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
