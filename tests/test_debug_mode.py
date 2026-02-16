from pydantic_schemaforms.enhanced_renderer import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel
import pytest


class _DebugForm(FormModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=1)


def test_debug_panel_included():
    html = render_form_html(_DebugForm, debug=True, submit_url="/debug")

    assert "pf-debug-panel" in html
    assert "Rendered HTML" in html
    assert "Schema / validation" in html
    assert "minLength" in html  # schema/constraints are surfaced


def test_debug_off_by_default():
    html = render_form_html(_DebugForm, submit_url="/debug")

    assert "pf-debug-panel" not in html


def test_missing_submit_url_raises_error():
    with pytest.raises(ValueError, match="submit_url is required"):
        render_form_html(_DebugForm)
