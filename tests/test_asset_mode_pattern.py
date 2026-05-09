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


def test_render_form_html_material_uses_single_dispatch_path() -> None:
    """render_form_html(framework='material') must go through EnhancedFormRenderer.

    Previously the material branch was hardcoded to SimpleMaterialRenderer and
    silently ignored include_framework_assets / asset_mode / self_contained.
    The unified path means those flags now work correctly for all frameworks.
    """
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title="Name")
        email: str = Field(..., ui_element="email", title="Email")

    # Material form rendered without explicit assets — no embedded CSS/JS
    plain = render_form_html(Demo, framework="material", submit_url="/demo")
    assert "md-input" in plain or "md-form" in plain  # Material markup present

    # self_contained=True now works for material (was silently ignored before)
    self_cont = render_form_html(Demo, framework="material", submit_url="/demo", self_contained=True)
    assert "md-input" in self_cont or "md-form" in self_cont
    # The embedded CSS block must be present since self_contained implies include_framework_assets
    assert "<style>" in self_cont


def test_enhanced_form_renderer_material_output_matches_simple_material_renderer() -> None:
    """EnhancedFormRenderer(framework='material') and SimpleMaterialRenderer produce identical HTML."""
    import re
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(..., title="Name")
        email: str = Field(..., ui_element="email", title="Email")
        role: str = Field(..., ui_element="select", options=["admin", "user"], title="Role")
        active: bool = Field(True, title="Active")

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip()

    smr_html = norm(SimpleMaterialRenderer().render_form_from_model(Demo, submit_url="/t"))
    efr_html = norm(EnhancedFormRenderer(framework="material").render_form_from_model(Demo, submit_url="/t"))

    assert smr_html == efr_html


def test_simple_material_renderer_is_backward_compat_alias() -> None:
    """SimpleMaterialRenderer is kept as a thin subclass of EnhancedFormRenderer."""
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer, MaterialDesign3Renderer

    renderer = SimpleMaterialRenderer()
    assert isinstance(renderer, EnhancedFormRenderer)
    assert renderer.framework == "material"

    alias = MaterialDesign3Renderer()
    assert isinstance(alias, EnhancedFormRenderer)
    assert alias.framework == "material"
