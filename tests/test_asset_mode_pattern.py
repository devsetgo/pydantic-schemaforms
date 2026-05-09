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
    # Bootstrap Icons must be inlined too — library emits bi bi-* classes
    assert "bootstrap-icons" in html
    assert "data:font/woff2;base64," in html

    renderer_cdn = EnhancedFormRenderer(
        framework="bootstrap",
        include_framework_assets=True,
        asset_mode="cdn",
    )
    html_cdn = renderer_cdn.render_form_from_model(Demo)
    assert "cdn.jsdelivr.net/npm/bootstrap@5.3.0" in html_cdn
    assert "cdn.jsdelivr.net/npm/bootstrap-icons@" in html_cdn


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
    # Icons must be self-contained too
    assert "bootstrap-icons" in html
    assert "data:font/woff2;base64," in html


def test_bootstrap_icons_css_tag_modes() -> None:
    from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_tag

    # vendored: inline <style> with embedded woff2
    tag = bootstrap_icons_css_tag(asset_mode="vendored")
    assert tag.startswith("<style>")
    assert "bootstrap-icons" in tag
    assert "data:font/woff2;base64," in tag
    assert 'url("fonts/' not in tag  # relative path must be replaced

    # cdn: pinned jsdelivr link
    cdn_tag = bootstrap_icons_css_tag(asset_mode="cdn")
    assert "cdn.jsdelivr.net" in cdn_tag
    assert "bootstrap-icons" in cdn_tag
    assert "<link" in cdn_tag

    # none: empty
    assert bootstrap_icons_css_tag(asset_mode="none") == ""


def test_bootstrap_icons_css_content_is_raw_css() -> None:
    from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_content

    css = bootstrap_icons_css_content()
    assert "bootstrap-icons" in css
    assert "data:font/woff2;base64," in css
    assert not css.startswith("<")  # raw CSS, not a tag


def test_material_theme_does_not_include_bootstrap_icons() -> None:
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title="Name")

    renderer = EnhancedFormRenderer(
        framework="material",
        include_framework_assets=True,
        asset_mode="vendored",
    )
    html = renderer.render_form_from_model(Demo)
    # Bootstrap Icons are Bootstrap-specific; material theme must not inject them
    assert "data:font/woff2;base64," not in html


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
