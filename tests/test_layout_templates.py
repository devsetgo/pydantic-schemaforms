"""Regression tests for tab/accordion layouts using shared templates."""

from pydantic_schemaforms.rendering.layout_engine import AccordionLayout, TabLayout


def test_tab_layout_uses_template_markup() -> None:
    layout = TabLayout(
        [
            {"title": "General", "content": "<p>One</p>"},
            {"title": "Advanced", "content": "<p>Two</p>"},
        ],
        class_="custom-tab",
        style="margin: 1rem",
    )

    html = layout.render()

    assert 'class="tab-layout custom-tab"' in html
    assert 'role="tablist"' in html
    assert html.count('class="tab-button') == 2
    assert html.count('class="tab-panel') == 2


def test_accordion_layout_uses_template_markup() -> None:
    layout = AccordionLayout(
        [
            {"title": "Section A", "content": "<p>A</p>", "expanded": True},
            {"title": "Section B", "content": "<p>B</p>", "expanded": False},
        ],
        class_="custom-accordion",
    )

    html = layout.render()

    assert 'class="accordion-layout custom-accordion"' in html
    assert html.count('class="accordion-section"') == 2
    assert 'aria-expanded="true"' in html
    assert 'aria-expanded="false"' in html
