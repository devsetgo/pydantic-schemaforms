"""Every example page on the demo site, in one list.

The home page, the section pages, the sidebar and the "All examples" page are
built from this list, and ``tests/test_examples_coverage.py`` fails when a page
has no entry here or an entry has no page. To add an example, add its route and
one ``Example`` below; nothing else needs a link.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from examples.wizard_examples import WIZARD_EXAMPLES

DOCS = 'https://devsetgo.github.io/pydantic-schemaforms'
STYLES = ('bootstrap', 'material', 'none')


@dataclass(frozen=True)
class Section:
    slug: str
    title: str
    summary: str
    icon: str


@dataclass(frozen=True)
class Example:
    slug: str
    title: str
    section: str
    summary: str
    url: str
    tags: tuple[str, ...] = ()
    docs: str | None = None
    styles: tuple[str, ...] = STYLES
    # Further pages that belong to this example (a POST result, an edit page, ...).
    pages: tuple[str, ...] = ()
    # Other ways to open it, shown as extra links: (label, url).
    variants: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    # Models to show under "How it's built" when the routes don't name them.
    models: tuple[type, ...] = ()
    # A page that is its own whole document, outside the site's shell and sidebar.
    standalone: bool = False

    @property
    def path(self) -> str:
        return self.url.split('?', 1)[0]


SECTIONS = (
    Section(
        'start',
        'Start here',
        'Small, complete forms: a model in, a styled and validated form out.',
        'rocket',
    ),
    Section(
        'inputs',
        'Inputs',
        'Every kind of input the library can draw, from a text box to a code editor.',
        'input',
    ),
    Section(
        'validation',
        'Validation',
        'How mistakes are caught and shown next to the field, on the server and as you type.',
        'check',
    ),
    Section(
        'layouts',
        'Layouts and long forms',
        'Arrange one form as tabs, columns or steps, and make long forms easier to finish.',
        'layout',
    ),
    Section(
        'nested',
        'Nested and repeating data',
        'Forms inside forms, and lists the user can add to, with data that comes back nested.',
        'nested',
    ),
    Section(
        'tables',
        'Tables and import',
        'Upload a CSV file, fix it in an editable table, and save it.',
        'table',
    ),
    Section(
        'security',
        'Security and deployment',
        "Protections the forms come with, and pages that don't depend on outside files.",
        'shield',
    ),
    Section(
        'developers',
        'For developers',
        'JSON APIs from the same model, interactive API docs, and guides for AI assistants.',
        'code',
    ),
)

_EXAMPLES = [
    # --- Start here --------------------------------------------------------------
    Example(
        'signup',
        'Sign-up form',
        'start',
        "The home page's model as a live form: a name, an email, a plan, a date and a box to tick.",
        '/signup',
        tags=('basics', 'validation'),
        docs=f'{DOCS}/tutorial/first-form/',
    ),
    Example(
        'login',
        'Login form',
        'start',
        'A username, a password and a remember-me box: the smallest useful form.',
        '/login',
        tags=('csrf', 'basics'),
        docs=f'{DOCS}/recipes/login-registration/',
    ),
    Example(
        'user',
        'User registration',
        'start',
        'Sign-up with a role picker and checks on every field, shown with the debug panel.',
        '/user?demo=true&debug=true&show_timing=true',
        tags=('basics', 'validation'),
        docs=f'{DOCS}/tutorial/first-form/',
        pages=('/register',),
    ),
    Example(
        'contact',
        'Contact form and JSON API',
        'start',
        'One model serves this form and a JSON endpoint with the same rules.',
        '/contact?demo=true&show_timing=true',
        tags=('json-api', 'basics'),
        docs=f'{DOCS}/advanced/json-api/',
        variants=(('JSON schema', '/api/contact/schema'),),
    ),
    Example(
        'feedback',
        'Feedback form and JSON API',
        'start',
        'A rating and comments, also accepted as JSON by an API route.',
        '/feedback?demo=true&show_timing=true',
        tags=('json-api', 'basics'),
        docs=f'{DOCS}/advanced/json-api/',
        variants=(('JSON schema', '/api/feedback/schema'),),
    ),
    # --- Inputs ------------------------------------------------------------------
    Example(
        'gallery',
        'Widget gallery',
        'inputs',
        'Every input type and alias with every option, grouped in tabs.',
        '/gallery',
        tags=('inputs', 'dark-mode'),
        docs=f'{DOCS}/reference/inputs/',
    ),
    Example(
        'input-types',
        'Input type reference',
        'inputs',
        'A cheat sheet: each input, what it is for, and the one line that declares it.',
        '/input-types',
        tags=('inputs',),
        docs=f'{DOCS}/reference/inputs/',
        styles=('bootstrap',),
    ),
    Example(
        'date-time-formats',
        'Date and time formats',
        'inputs',
        'Dates and times shown the way your users write them, and parsed back on submit.',
        '/date-time-formats',
        tags=('inputs', 'dates'),
        docs=f'{DOCS}/reference/inputs/',
    ),
    Example(
        'menu-order',
        'Collapsible option groups',
        'inputs',
        'A menu order with long option lists folded into groups, and repeating items.',
        '/menu-order/',
        tags=('inputs', 'model_list'),
        docs=f'{DOCS}/reference/inputs/',
    ),
    # --- Validation --------------------------------------------------------------
    Example(
        'validation',
        'Every kind of validation',
        'validation',
        'Field limits, your own checks, form-wide rules and rule classes, all failing at once.',
        '/validation',
        tags=('validation', 'uploads'),
        docs=f'{DOCS}/tutorial/validation/',
        variants=(('Passwords that differ', '/validation?scenario=mismatch'),),
    ),
    Example(
        'live-validation',
        'Live validation',
        'validation',
        'Fields checked on the server as you type, without reloading the page (HTMX).',
        '/live-validation',
        tags=('validation', 'htmx'),
        docs=f'{DOCS}/advanced/live-validation/',
        styles=('bootstrap',),
    ),
    Example(
        'email-dns',
        'Email domain check',
        'validation',
        'Checks that the part after the @ is a real domain that can receive mail.',
        '/email-dns-validation',
        tags=('validation', 'htmx'),
        docs=f'{DOCS}/advanced/live-validation/',
        styles=('bootstrap',),
    ),
    # --- Layouts and long forms ---------------------------------------------------
    Example(
        'layouts',
        'Layouts',
        'layouts',
        'Four sub-forms shown as sections, tabs, columns, an accordion or a step wizard.',
        '/layouts',
        tags=('layout', 'wizard', 'autosave', 'progress'),
        docs=f'{DOCS}/tutorial/layouts/',
        variants=(
            ('Tabbed', '/layouts?layout=tabbed'),
            ('Vertical', '/layouts?layout=vertical'),
            ('Side by side', '/layouts?layout=side-by-side'),
            ('Accordion', '/layouts?layout=accordion'),
            ('Wizard', '/layouts?layout=wizard'),
            ('Material, filled', '/layouts?layout=tabbed&style=material&variant=filled'),
        ),
    ),
    Example(
        'field-groups',
        'Field groups and widths',
        'layouts',
        'Titled sections and fields sharing a row, without nesting the data.',
        '/layouts/field-groups',
        tags=('layout', 'ui_group'),
        docs=f'{DOCS}/tutorial/layouts/',
    ),
    Example(
        'two-forms',
        'Two forms on one page',
        'layouts',
        'Two tabbed forms side by side that switch on their own.',
        '/layouts/two-forms',
        tags=('layout',),
        docs=f'{DOCS}/tutorial/layouts/',
    ),
    Example(
        'wizards',
        'Step wizards',
        'layouts',
        'Eight realistic multi-step forms, and a link to every wizard option.',
        '/wizards',
        tags=('wizard',),
        docs=f'{DOCS}/recipes/wizard-examples/',
    ),
    Example(
        'save-steps',
        'Save and continue',
        'layouts',
        'Each wizard step is saved on the server, so the user can leave and come back.',
        '/layouts/save-steps',
        tags=('wizard', 'save_steps', 'uploads'),
        docs=f'{DOCS}/recipes/save-and-continue/',
    ),
    Example(
        'review',
        'Review what changed',
        'layouts',
        'A wizard opened with saved data ends on a review step marking every change.',
        '/layouts/review',
        tags=('wizard', 'review_step'),
        docs=f'{DOCS}/reference/layouts/',
    ),
    Example(
        'read-only-review',
        'Read-only answers page',
        'layouts',
        "A confirmation page that shows what was submitted, using the form's own labels.",
        '/gallery/review',
        tags=('render_display',),
        docs=f'{DOCS}/tutorial/handling-submissions/',
    ),
    Example(
        'confirm',
        'Confirm before submit',
        'layouts',
        'A form for something hard to undo asks first, in a dialog.',
        '/confirm',
        tags=('confirm',),
        docs=f'{DOCS}/tutorial/handling-submissions/',
    ),
    # --- Nested and repeating data -------------------------------------------------
    Example(
        'pets',
        'Pet registration',
        'nested',
        'An owner with a list of pets the user can add to and remove from.',
        '/pets?demo=true',
        tags=('model_list', 'nested'),
        docs=f'{DOCS}/tutorial/nested-forms/',
    ),
    Example(
        'organization',
        'Organization in tabs',
        'nested',
        'A company with departments and teams, five levels deep, in tabs.',
        '/organization?demo=true',
        tags=('nested', 'model_list', 'layout'),
        docs=f'{DOCS}/tutorial/nested-forms/',
    ),
    Example(
        'organization-shared',
        'Reusing sub-forms',
        'nested',
        'The same address and contact models reused in several places.',
        '/organization-shared?demo=true',
        tags=('nested',),
        docs=f'{DOCS}/tutorial/nested-forms/',
    ),
    Example(
        'showcase',
        'Complete showcase',
        'nested',
        'One long form with nearly every input, validation and protection together.',
        '/showcase?demo=true',
        tags=('inputs', 'validation', 'captcha', 'honeypot'),
        docs=f'{DOCS}/reference/inputs/',
    ),
    # --- Tables and import --------------------------------------------------------
    Example(
        'csv-import',
        'CSV import to a table',
        'tables',
        'Upload employees as CSV, fix the flagged cells in the table, then save.',
        '/employees/import',
        tags=('DataTableLayout', 'uploads'),
        docs=f'{DOCS}/advanced/data-tables/',
        variants=(('Read-only table', '/employees/import?editable=false'),),
    ),
    Example(
        'directory',
        'Employee directory',
        'tables',
        'A searchable, sortable table of saved employees.',
        '/employees/directory',
        tags=('DataTableLayout',),
        docs=f'{DOCS}/advanced/data-tables/',
    ),
    Example(
        'teams',
        'Two tables on one page',
        'tables',
        'Two editable tables in one form, each named for its own field.',
        '/employees/teams',
        tags=('DataTableLayout',),
        docs=f'{DOCS}/advanced/data-tables/',
    ),
    # --- Security and deployment ---------------------------------------------------
    Example(
        'csp',
        'Content-Security-Policy',
        'security',
        "This site blocks any script without the page's random value; watch it block one.",
        '/content-security-policy',
        tags=('csp',),
        docs=f'{DOCS}/advanced/content-security-policy/',
        styles=('bootstrap', 'material'),
    ),
    Example(
        'self-contained',
        'Self-contained page',
        'security',
        'A form with its CSS and JavaScript inside the page, so it loads nothing from outside.',
        '/self-contained',
        tags=('assets',),
        docs=f'{DOCS}/advanced/assets/',
        standalone=True,
    ),
    # --- For developers -----------------------------------------------------------
    Example(
        'ai-instructions',
        'AI assistant instructions',
        'developers',
        'The guides that teach AI coding assistants to use this library correctly.',
        '/ai-instructions',
        tags=('ai',),
        docs=f'{DOCS}/advanced/ai-instructions/',
        styles=('bootstrap',),
    ),
    Example(
        'api-docs',
        'Interactive API docs',
        'developers',
        "FastAPI's own page for this site's JSON endpoints: try them in the browser.",
        '/docs',
        tags=('json-api',),
        docs=f'{DOCS}/advanced/json-api/',
        styles=(),
        variants=(('ReDoc', '/redoc'),),
    ),
]

_WIZARD_TAGS = {
    'job-application': ('wizard', 'save_steps', 'uploads', 'model_list'),
    'project-planner': ('wizard', 'model_list', 'review_step'),
    'car-care': ('wizard', 'ui_group', 'ui_show_when', 'review_step'),
    'car-setup': ('wizard', 'ui_group', 'ui_show_when', 'review_step'),
    'rental-application': ('wizard', 'save_steps', 'model_list', 'uploads', 'review_step'),
    'insurance-claim': ('wizard', 'uploads', 'ui_show_when', 'review_step'),
    'team-onboarding': ('wizard', 'model_list', 'validation'),
    'event-registration': ('wizard', 'model_list', 'validation'),
}

_WIZARD_PAGES = {
    'job-application': (
        '/wizards/job-application/sign-in',
        '/wizards/job-application/edit',
    ),
}

_wizard_at = next(i for i, e in enumerate(_EXAMPLES) if e.slug == 'wizards') + 1
_EXAMPLES[_wizard_at:_wizard_at] = [
    Example(
        f'wizard-{wizard.slug}',
        wizard.title,
        'layouts',
        wizard.summary,
        f'/wizards/{wizard.slug}',
        tags=_WIZARD_TAGS.get(wizard.slug, ('wizard',)),
        docs=f'{DOCS}/recipes/wizard-examples/',
        pages=_WIZARD_PAGES.get(wizard.slug, ()),
        models=(wizard.model,) if wizard.model else (),
    )
    for wizard in WIZARD_EXAMPLES
]

EXAMPLES: tuple[Example, ...] = tuple(_EXAMPLES)
SECTIONS_BY_SLUG = {section.slug: section for section in SECTIONS}


def section_examples(slug: str) -> list[Example]:
    return [example for example in EXAMPLES if example.section == slug]


def example_for_path(path: str) -> Example | None:
    """The example a request path belongs to, for the sidebar's current item."""

    path = path.rstrip('/') or '/'
    for example in EXAMPLES:
        if path in {example.path.rstrip('/') or '/', *example.pages}:
            return example
    return None


def neighbors(example: Example) -> tuple[Example | None, Example | None]:
    """The examples before and after this one, for a walk through the whole catalog."""

    index = EXAMPLES.index(example)
    before = EXAMPLES[index - 1] if index > 0 else None
    after = EXAMPLES[index + 1] if index + 1 < len(EXAMPLES) else None
    return before, after


def all_tags() -> list[str]:
    return sorted({tag for example in EXAMPLES for tag in example.tags}, key=str.lower)
