"""The pages built from the example catalog: the section pages and "All examples".

Also gives every template the catalog, for the sidebar and the home page.
"""

from __future__ import annotations

import inspect
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from examples.catalog import (
    EXAMPLES,
    SECTIONS,
    SECTIONS_BY_SLUG,
    all_tags,
    example_for_path,
    neighbors,
    section_examples,
)
from examples.example_source import example_sources
from examples.fastapi_routes import templates
from examples.shared_models import SignupForm
from pydantic_schemaforms import render_form_html_async

router = APIRouter(tags=['Site'])

STYLE_LABELS = {'bootstrap': 'Bootstrap', 'material': 'Material', 'none': 'Plain HTML'}


def with_style(url: str, style: str) -> str:
    """The example's URL opened in one style, keeping its own query."""

    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key != 'style']
    query.append(('style', style))
    return urlunsplit(parts._replace(query=urlencode(query)))


def install_template_globals(environment_templates) -> None:
    """Give a template environment the catalog the sidebar and home page read."""

    environment_templates.env.globals.update(
        catalog_sections=SECTIONS,
        signup_source=inspect.getsource(SignupForm),
        section_examples=section_examples,
        current_example=example_for_path,
        catalog_section=SECTIONS_BY_SLUG.get,
        example_neighbors=neighbors,
        example_sources=example_sources,
        style_labels=STYLE_LABELS,
    )
    environment_templates.env.filters['with_style'] = with_style


install_template_globals(templates)


@router.get('/examples', response_class=HTMLResponse)
async def all_examples(request: Request):
    """Every example, with a filter by the library feature it shows."""
    return templates.TemplateResponse(
        request,
        'examples_index.html',
        {
            'request': request,
            'title': 'All examples',
            'sections': [(section, section_examples(section.slug)) for section in SECTIONS],
            'tags': all_tags(),
            'count': len(EXAMPLES),
        },
    )


@router.get('/examples/{section}', response_class=HTMLResponse)
async def section_page(request: Request, section: str):
    """One section's examples, each with a plain summary and its styles."""
    if section not in SECTIONS_BY_SLUG:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        'examples_index.html',
        {
            'request': request,
            'title': SECTIONS_BY_SLUG[section].title,
            'section': SECTIONS_BY_SLUG[section],
            'sections': [(SECTIONS_BY_SLUG[section], section_examples(section))],
            'tags': [],
            'count': len(section_examples(section)),
        },
    )


def _signup_page(request: Request, style: str, form_html: str):
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Sign-up Form',
            'description': (
                'The model on the home page, rendered. Submit it empty or with a bad email '
                'to see each mistake shown next to its field.'
            ),
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.get('/signup', response_class=HTMLResponse)
async def signup_get(request: Request, style: str = 'bootstrap'):
    """The home page's sign-up model as a live form."""
    form_html = await render_form_html_async(
        SignupForm, submit_url=f'/signup?style={style}', framework=style
    )
    return _signup_page(request, style, form_html)


@router.post('/signup', response_class=HTMLResponse)
async def signup_post(request: Request, style: str = 'bootstrap'):
    result = SignupForm.validate(
        await request.form(), submit_url=f'/signup?style={style}', framework=style
    )
    if not result.is_valid:
        return _signup_page(request, style, await result.render_with_errors_async())
    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': 'Signed Up',
            'message': 'This is the validated data your route would receive.',
            'data': result.data,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'try_again_url': f'/signup?style={style}',
        },
    )
