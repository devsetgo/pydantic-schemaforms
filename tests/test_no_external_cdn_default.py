from __future__ import annotations

from pydantic import Field

from pydantic_forms.render_form import render_form_html
from pydantic_forms.schema_form import FormModel
from pydantic_forms.assets.runtime import vendored_asset_version


class _CdnCheckForm(FormModel):
    name: str = Field(default='', title='Name')


def test_render_form_default_has_no_unpkg() -> None:
    html = render_form_html(_CdnCheckForm)
    assert 'unpkg.com' not in html


def test_render_form_cdn_mode_includes_unpkg() -> None:
    html = render_form_html(_CdnCheckForm, asset_mode='cdn')
    assert 'unpkg.com' in html
    v = vendored_asset_version('htmx')
    assert v is not None
    assert f'htmx.org@{v}' in html
