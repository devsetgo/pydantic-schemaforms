from pydantic import create_model

from pydantic_schemaforms import Field, FormModel, render_form_html

# Loaded from a database or a config file at runtime
FIELDS = [
    {'name': 'name', 'title': 'Your name', 'ui_element': 'text', 'required': True},
    {'name': 'email', 'title': 'Email', 'ui_element': 'email', 'required': True},
    {'name': 'rating', 'title': 'Rating', 'ui_element': 'rating', 'required': False},
    {'name': 'comments', 'title': 'Comments', 'ui_element': 'textarea', 'required': False},
]


def build_form(fields: list[dict]) -> type[FormModel]:
    return create_model(
        'FeedbackForm',
        __base__=FormModel,
        **{
            spec['name']: (
                str,
                Field(
                    ... if spec['required'] else '',
                    title=spec['title'],
                    ui_element=spec['ui_element'],
                ),
            )
            for spec in fields
        },
    )


FeedbackForm = build_form(FIELDS)
form_html = render_form_html(FeedbackForm, submit_url='/feedback')
