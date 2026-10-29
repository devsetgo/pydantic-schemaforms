# Alternatives

Other ways to build forms in Python web apps, and how pydantic-schemaforms
differs. Pick the one that fits your stack.

## What this library is for

pydantic-schemaforms suits apps that render HTML on the server and already
use, or want to use, Pydantic models:

- **One model for everything.** The form, its validation, the validated data
  and, with `as_api_model()`, a JSON API share one Pydantic class.
- **Server-rendered.** You get an HTML string. There is no JavaScript
  framework, no build step and no client-side state; the small scripts it
  adds (live formatting, the wizard, Add and Remove buttons) are optional
  enhancements.
- **Framework-agnostic.** It works with any Python web framework that can
  return a string; the docs show FastAPI and Flask.
- **Escaped by construction.** All HTML is built with t-strings and an
  escaping processor, so values are escaped structurally, not by
  remembering to.

It is not a good fit when your frontend is a single-page app that renders its
own forms, or when you need a visual form designer.

## WTForms

[WTForms](https://wtforms.readthedocs.io/) is the long-standing
framework-agnostic form library, used by Flask-WTF and Starlette-WTF. Forms
are declared with WTForms' own field classes and validators, and you lay out
the fields yourself in templates.

Choose WTForms when your app doesn't use Pydantic or you want full control of
each field's markup in templates. Choose pydantic-schemaforms when you'd
rather declare the form once as a Pydantic model and get the whole form,
including nested sub-forms, lists and layouts, rendered for you.

## Django forms

[Django's forms](https://docs.djangoproject.com/en/stable/topics/forms/),
with ModelForm, are the natural choice inside Django, where they tie into the
ORM, the admin and the template system. pydantic-schemaforms doesn't
integrate with Django's ORM or admin; a Django adapter is on the
[Roadmap](roadmap.md).

## JSON Schema form renderers in the browser

Libraries such as [react-jsonschema-form](https://rjsf-team.github.io/react-jsonschema-form/)
render a form in the browser from a JSON Schema, which a Pydantic model can
produce. They suit apps that already have a React frontend. The form is built
by JavaScript on the client, and the server validates the posted JSON
separately.

pydantic-schemaforms renders on the server, so the form arrives as HTML,
works with plain form posts, and the same model validates the submission. Its
`get_pydantic_json_schema()` output can still feed such a renderer if you
need both.

## Writing the HTML by hand

For one small form, a hand-written `<form>` and a Pydantic model to validate
it is often enough. The work grows with each form: showing errors next to
the right inputs, keeping submitted values, escaping them, labels and
accessibility, nested data, repeating items and layouts. That is what this
library does for you.
