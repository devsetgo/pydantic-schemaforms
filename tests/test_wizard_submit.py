"""A wizard's Submit sits in its footer, beside Back, in Next's place."""

import re

import pytest

from pydantic_schemaforms import Field, FormModel, SafeHTML, render_form_html
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.rendering.form_style import (
    FormStyle,
    WIZARD_SUBMIT_RE,
    FormStyleTemplates,
    register_form_style,
)
from pydantic_schemaforms.rendering.themes import RendererTheme
from pydantic_schemaforms.templates import TemplateString


class Trip(FormModel):
    city: str = Field(title='City', ui_group='Where')
    nights: int = Field(1, title='Nights', ui_group='How long')


SUBMIT = r'<button type="submit"(?![^>]*name=)[^>]*>Submit</button>'


def _footer(page: str) -> str:
    match = re.search(r'<div class="wizard-footer">.*?</div>\s*</div>', page, re.DOTALL)
    assert match
    return match.group(0)


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_submit_is_in_the_footer_after_next(framework: str) -> None:
    page = render_form_html(Trip, submit_url='/t', layout='wizard', framework=framework)
    footer = _footer(page)
    assert re.search(
        r'data-wizard-next.*<div class="wizard-submit" data-wizard-submit>', footer, re.DOTALL
    )
    assert re.search(SUBMIT, footer)
    assert len(re.findall(SUBMIT, page)) == 1


def test_save_steps_puts_submit_beside_back_on_the_last_step_only() -> None:
    options = {'submit_url': '/t', 'layout': 'wizard', 'wizard_options': {'save_steps': True}}
    first = Trip.validate_step([('_sf_wizard_step', '0'), ('city', 'Denver')], **options)
    last = _footer(first.render())
    assert 'data-wizard-back' in last and re.search(SUBMIT, last)
    assert 'data-wizard-next' not in last
    assert not re.search(SUBMIT, render_form_html(Trip, **options))


def test_a_custom_footer_without_submit_keeps_it_below_the_form() -> None:
    def footer(**_: object) -> SafeHTML:
        return SafeHTML(
            '<div class="wizard-footer"><button type="button" data-wizard-next>Go</button></div>'
        )

    register_form_style(
        FormStyle(
            framework='custom-wizard-footer',
            templates=FormStyleTemplates(wizard_footer=TemplateString(footer)),
        )
    )

    class CustomTheme(RendererTheme):
        name = 'custom-wizard-footer'

    renderer = EnhancedFormRenderer(theme=CustomTheme())
    page = renderer.render_form_from_model(Trip, submit_url='/t', layout='wizard')
    assert '>Go</button>' in page
    assert not WIZARD_SUBMIT_RE.search(page)
    assert len(re.findall(r'<button type="submit"', page)) == 1
