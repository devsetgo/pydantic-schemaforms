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
