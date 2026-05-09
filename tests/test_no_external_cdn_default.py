from __future__ import annotations

from pydantic import Field

from pydantic_schemaforms.render_form import render_form_html
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.assets.runtime import vendored_asset_version


class _CdnCheckForm(FormModel):
    name: str = Field(default='', title='Name')


def test_render_form_default_has_no_unpkg() -> None:
    html = render_form_html(_CdnCheckForm, submit_url="/test")
    assert 'unpkg.com' not in html


def test_render_form_cdn_mode_includes_unpkg() -> None:
    html = render_form_html(_CdnCheckForm, asset_mode='cdn', submit_url="/test")
    assert 'unpkg.com' in html
    v = vendored_asset_version('htmx')
    assert v is not None
    assert f'htmx.org@{v}' in html


def test_self_contained_form_has_no_cdn_urls() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html as enhanced_render

    html = enhanced_render(_CdnCheckForm, submit_url="/test", self_contained=True)
    assert 'cdn.jsdelivr.net' not in html
    assert 'unpkg.com' not in html
    # Bootstrap Icons woff2 must be embedded, not fetched from network
    assert 'data:font/woff2;base64,' in html


def test_bootstrap_icons_vendored_version_is_recorded() -> None:
    v = vendored_asset_version('bootstrap-icons')
    assert v is not None
    assert v.count('.') >= 1  # semver-ish
