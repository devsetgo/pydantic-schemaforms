from pydantic_schemaforms.enhanced_renderer import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


class _DebugForm(FormModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=1)


def test_debug_panel_included():
    html = render_form_html(_DebugForm, debug=True)

    assert "pf-debug-panel" in html
    assert "Rendered HTML" in html
    assert "Schema / validation" in html
    assert "minLength" in html  # schema/constraints are surfaced


def test_debug_off_by_default():
    html = render_form_html(_DebugForm)

    assert "pf-debug-panel" not in html
