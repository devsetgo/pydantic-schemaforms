"""Removed form-orchestration classes.

``TabbedLayout``, ``VerticalLayout``, ``HorizontalLayout``, ``ListLayout``,
``SectionDesign``, ``FormDesign`` and ``FormLayoutBase`` used to compose
several FormModels into one form. Complex forms are now built by nesting
FormModels as ordinary fields of a parent FormModel and choosing a
``layout=`` when rendering.

The names stay importable so existing code fails with
``FormLayoutRemovedError`` -- whose message is the upgrade guide -- at the
point of use (class definition or call), instead of an opaque ImportError.
"""

from __future__ import annotations

from typing import Any, NoReturn

REMOVED_IN = '26.4.1'

_UPGRADE_GUIDE = """\
Complex forms are now built by nesting FormModels as fields of a parent FormModel:

    # before                                          # after
    class ContactTab(VerticalLayout):                 class Profile(FormModel):
        form = Contact                                    contact: Contact = Field(title="Contact")
    class Tabs(TabbedLayout):                             address: Address = Field(title="Address")
        contact = ContactTab()
    class Profile(FormModel):                         render_form_html(Profile, layout="tabbed", submit_url=...)
        tabs: Tabs = Field(input_type="layout")       result = Profile.validate(await request.form(), submit_url=...)

Inputs are named contact.email; result.data and result.errors are nested JSON
({"contact": {"email": ...}}). layout= is "vertical", "tabbed", "side-by-side", "accordion" or "wizard".

Full guide: python -m pydantic_schemaforms.ai_instructions claude  (section "Upgrading to nested forms")
            or docs/complex_forms.md#upgrading"""

_EXTRA_HINTS = {
    'ListLayout': (
        'For a repeating sub-form use a list field instead:\n'
        '    items: list[Item] = Field(default_factory=list, title="Items")'
    ),
    'SectionDesign': (
        'Section titles/help now come from the sub-form field itself:\n'
        '    address: Address = Field(title="Address", ui_help_text="...", ui_collapsible=True)'
    ),
    'FormDesign': (
        'Page chrome (theme, width, action URL) is set on render_form_html(...) / '
        'render_form_page(...) and your own page template.'
    ),
}


class FormLayoutRemovedError(TypeError):
    """Raised on any use of a removed form-orchestration class; the message
    explains how to upgrade."""

    def __init__(self, name: str) -> None:
        hint = _EXTRA_HINTS.get(name, '')
        message = f'{name} was removed in {REMOVED_IN}. {_UPGRADE_GUIDE}'
        if hint:
            message = f'{message}\n\n{hint}'
        super().__init__(message)
        self.removed_name = name


class _RemovedLayout:
    _removed_name = 'FormLayoutBase'

    def __init_subclass__(cls, **kwargs: Any) -> None:
        parent = cls.__mro__[1]
        if parent is not _RemovedLayout:
            raise FormLayoutRemovedError(parent._removed_name)

    def __init__(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise FormLayoutRemovedError(type(self)._removed_name)


def _removed(name: str) -> type:
    doc = f'Removed in {REMOVED_IN}; using it raises FormLayoutRemovedError with upgrade steps.'
    return type(name, (_RemovedLayout,), {'_removed_name': name, '__doc__': doc})


FormLayoutBase = _removed('FormLayoutBase')
VerticalLayout = _removed('VerticalLayout')
HorizontalLayout = _removed('HorizontalLayout')
TabbedLayout = _removed('TabbedLayout')
ListLayout = _removed('ListLayout')
SectionDesign = _removed('SectionDesign')
FormDesign = _removed('FormDesign')
BaseLayout = FormLayoutBase

__all__ = [
    'FormDesign',
    'FormLayoutBase',
    'FormLayoutRemovedError',
    'HorizontalLayout',
    'ListLayout',
    'SectionDesign',
    'TabbedLayout',
    'VerticalLayout',
]
