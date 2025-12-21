import pytest


def test_render_form_page_offline_by_default() -> None:
    from pydantic_forms.integration.builder import create_login_form, render_form_page

    html = render_form_page(create_login_form(), title="Login")
    assert "cdn.jsdelivr.net" not in html
    assert "fonts.googleapis.com" not in html


def test_render_form_page_cdn_opt_in_includes_bootstrap() -> None:
    from pydantic_forms.integration.builder import create_login_form, render_form_page

    html = render_form_page(
        create_login_form(),
        title="Login",
        include_framework_assets=True,
        asset_mode="cdn",
    )
    assert "cdn.jsdelivr.net/npm/bootstrap@5.3.0" in html


def test_form_design_framework_urls_offline_by_default() -> None:
    from pydantic_forms.form_layouts import FormDesign

    design = FormDesign(ui_theme="bootstrap")
    assert design.get_framework_css_url() == ""
    assert design.get_framework_js_url() == ""


def test_material_theme_css_has_no_google_fonts_imports() -> None:
    from pydantic_forms.rendering.themes import MaterialEmbeddedTheme

    css = MaterialEmbeddedTheme._build_css()
    assert "fonts.googleapis.com" not in css
    assert "fonts.gstatic.com" not in css
