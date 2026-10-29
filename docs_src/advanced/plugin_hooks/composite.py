from pydantic_schemaforms import Field, FormModel, LayoutEngine, SafeHTML, html, render_form_html


@LayoutEngine.layout_renderer('step_list', builtin=False)
def render_step_list(field_name, field_schema, value, ui_info, context, engine) -> str:
    items = SafeHTML(''.join(html(t'<li>{step}</li>') for step in (value or [])))
    return html(t'<ol class="step-list" data-field="{field_name}">{items}</ol>')


class OnboardingForm(FormModel):
    steps: list[str] = Field(
        ['Account', 'Billing', 'Review'],
        title='Steps',
        input_type='layout',
        layout_handler='step_list',
    )


form_html = render_form_html(OnboardingForm, submit_url='/onboarding')
