"""Static reference data for the /input-types page: every registered
`ui_element` with a short description and a copy-pasteable Field() example.

Pure documentation data, not wired to the live rendering pipeline -- this
is a plain "here's the code" cheatsheet, not a rendered demo. Grouped to
match the module each input class lives in under pydantic_schemaforms/inputs/.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputTypeEntry:
    ui_element: str
    description: str
    example: str
    aliases: tuple[str, ...] = ()


INPUT_TYPE_CATEGORIES: list[tuple[str, list[InputTypeEntry]]] = [
    (
        'Text Inputs',
        [
            InputTypeEntry(
                'text',
                'Single-line free text. The default when no ui_element is given.',
                "name: str = Field(..., ui_element='text', ui_placeholder='Full name')",
            ),
            InputTypeEntry(
                'textarea',
                'Multi-line free text. Add language= for a Format button, Tab-key '
                'indentation, and syntax highlighting (json/yaml/toml/bash/python).',
                "bio: str = Field('', ui_element='textarea', ui_options={'rows': 4})\n"
                "config: str = Field('{}', ui_element='textarea',\n"
                "                    ui_options={'language': 'json', 'rows': 8})",
            ),
            InputTypeEntry(
                'email',
                'Email input with built-in browser validation and a numeric-friendly '
                'mobile keyboard.',
                "email: str = Field(..., ui_element='email', ui_placeholder='you@example.com')",
            ),
            InputTypeEntry(
                'password',
                "Password input; autocomplete defaults to 'new-password' so browsers "
                "don't offer to autofill a saved password.",
                "password: str = Field(..., ui_element='password')",
            ),
            InputTypeEntry(
                'search',
                'Search input with a search-oriented mobile keyboard.',
                "query: str = Field('', ui_element='search', ui_placeholder='Search...')",
            ),
            InputTypeEntry(
                'url',
                'URL input with browser validation and a default http(s):// pattern.',
                "website: str = Field('', ui_element='url', ui_placeholder='https://example.com')",
            ),
            InputTypeEntry(
                'tel',
                'Plain telephone input, no formatting applied.',
                "phone: str = Field('', ui_element='tel')",
            ),
            InputTypeEntry(
                'phone',
                'Telephone input with a live-formatting mask as the user types.',
                "phone: str = Field('', ui_element='phone',\n"
                "                   ui_options={'phone_format': '(###) ###-####'})",
                aliases=('phone_number',),
            ),
            InputTypeEntry(
                'ssn',
                'Social Security Number input, formatted 123-45-6789 with a numeric keyboard.',
                "ssn: str = Field('', ui_element='ssn')",
                aliases=('social_security_number',),
            ),
            InputTypeEntry(
                'credit_card',
                'Credit card number input, grouped 1234 5678 9012 3456.',
                "card_number: str = Field('', ui_element='credit_card')",
                aliases=('card', 'cc_number'),
            ),
            InputTypeEntry(
                'currency',
                'Currency input with live thousands-separator formatting as the user types.',
                "price: str = Field('', ui_element='currency',\n"
                "                   ui_options={'currency_symbol': '$'})",
                aliases=('money',),
            ),
        ],
    ),
    (
        'Numeric Inputs',
        [
            InputTypeEntry(
                'number',
                'Plain HTML number input.',
                "count: int = Field(0, ui_element='number')",
            ),
            InputTypeEntry(
                'integer',
                'Number input constrained to whole numbers (step=1).',
                "quantity: int = Field(1, ui_element='integer')",
            ),
            InputTypeEntry(
                'decimal',
                'Number input with a configurable decimal precision (sets step from it).',
                "price: float = Field(0.0, ui_element='decimal',\n"
                "                     ui_options={'decimal_places': 2})",
            ),
            InputTypeEntry(
                'percentage',
                'Number input clamped to 0-100 by default.',
                "discount: float = Field(0, ui_element='percentage')",
            ),
            InputTypeEntry(
                'age',
                'Integer input with sensible age bounds (0-150) pre-filled.',
                "age: int = Field(..., ui_element='age')",
            ),
            InputTypeEntry(
                'quantity',
                "Integer input for carts/inventory: min=1, placeholder '1'.",
                "qty: int = Field(1, ui_element='quantity')",
            ),
            InputTypeEntry(
                'score',
                'Number input with a configurable min/max range (default 0-100).',
                "score: float = Field(0, ui_element='score',\n"
                "                     ui_options={'min_score': 0, 'max_score': 10})",
            ),
            InputTypeEntry(
                'range',
                'Native HTML range slider.',
                "volume: int = Field(50, ui_element='range', ge=0, le=100)",
            ),
            InputTypeEntry(
                'slider',
                'Range slider with min/max value labels shown alongside it.',
                "opacity: int = Field(100, ui_element='slider', ge=0, le=100)",
            ),
            InputTypeEntry(
                'rating',
                'Range slider styled to show a 1-N star rating (default max 5).',
                "rating: int = Field(3, ui_element='rating', ui_options={'max_rating': 5})",
                aliases=('rating_stars',),
            ),
            InputTypeEntry(
                'temperature',
                'Number input with a unit indicator (celsius/fahrenheit).',
                "temp: float = Field(20.0, ui_element='temperature',\n"
                "                    ui_options={'unit': 'celsius'})",
            ),
        ],
    ),
    (
        'Date/Time Inputs',
        [
            InputTypeEntry(
                'date',
                'Native HTML date picker (YYYY-MM-DD).',
                "birth_date: date = Field(..., ui_element='date')",
            ),
            InputTypeEntry(
                'time',
                'Native HTML time picker.',
                "appt_time: time = Field(..., ui_element='time')",
            ),
            InputTypeEntry(
                'datetime',
                'Native HTML datetime-local picker.',
                "starts_at: datetime = Field(..., ui_element='datetime')",
                aliases=('datetime-local',),
            ),
            InputTypeEntry(
                'month',
                'Native HTML month picker (YYYY-MM).',
                "billing_month: str = Field(..., ui_element='month')",
            ),
            InputTypeEntry(
                'week',
                'Native HTML week picker (YYYY-Www).',
                "sprint_week: str = Field(..., ui_element='week')",
            ),
            InputTypeEntry(
                'birthdate',
                'Date input pre-configured with sane birthdate bounds.',
                "dob: date = Field(..., ui_element='birthdate')",
            ),
        ],
    ),
    (
        'Selection Inputs',
        [
            InputTypeEntry(
                'checkbox',
                'Single boolean checkbox.',
                "agree: bool = Field(False, ui_element='checkbox', title='I accept the terms')",
            ),
            InputTypeEntry(
                'toggle',
                'Single boolean rendered as a modern switch instead of a checkbox.',
                "enabled: bool = Field(True, ui_element='toggle')",
                aliases=('toggle_switch', 'checkbox_toggle'),
            ),
            InputTypeEntry(
                'checkbox_group',
                'Multiple booleans from one field, rendered as a group of checkboxes. '
                'ui_options collapsible=True turns the legend into a toggle that shows/hides '
                'the options -- purely presentational, does not affect required-ness.',
                "channels: list[str] = Field(default_factory=list, ui_element='checkbox_group',\n"
                "                            ui_options={'choices': ['email', 'sms', 'push'],\n"
                "                                        'collapsible': True})",
            ),
            InputTypeEntry(
                'radio',
                'Single choice from a set of mutually-exclusive options. Also supports '
                'ui_options collapsible/collapsed, same as checkbox_group.',
                "size: str = Field('medium', ui_element='radio',\n"
                "                  ui_options={'choices': ['small', 'medium', 'large']})",
            ),
            InputTypeEntry(
                'select',
                'Native HTML <select> dropdown, single choice. ui_options placeholder= '
                'renders a disabled blank option forcing a real selection, instead of the '
                'browser defaulting to the first option.',
                "plan: str = Field(..., ui_element='select',\n"
                "                  ui_options={'placeholder': 'Choose a plan...', 'choices': [\n"
                "                      {'value': 'free', 'label': 'Free'},\n"
                "                      {'value': 'pro', 'label': 'Pro'},\n"
                '                  ]})',
            ),
            InputTypeEntry(
                'multiselect',
                'Multi-choice dropdown, enhanced with a searchable chips UI over the '
                'real <select multiple>.',
                "tags: list[str] = Field(default_factory=list, ui_element='multiselect',\n"
                "                        ui_options={'options': [\n"
                "                            {'value': 'py', 'label': 'Python'},\n"
                "                            {'value': 'rs', 'label': 'Rust'},\n"
                '                        ]})',
            ),
            InputTypeEntry(
                'combobox',
                'Text input with a suggestion dropdown (native <datalist>) -- free text '
                'is still allowed, unlike select.',
                "city: str = Field('', ui_element='combobox',\n"
                "                  ui_options={'choices': ['New York', 'London', 'Tokyo']})",
            ),
        ],
    ),
    (
        'Files & Specialized Inputs',
        [
            InputTypeEntry(
                'file',
                'File upload input.',
                "files: str = Field(..., ui_element='file',\n"
                "                   ui_options={'accept': '.pdf,.docx', 'multiple': True})",
            ),
            InputTypeEntry(
                'color',
                'Native HTML color picker.',
                "theme_color: str = Field('#3498db', ui_element='color')",
            ),
            InputTypeEntry(
                'hidden',
                'Hidden input, not shown to the user but submitted with the form.',
                "session_id: str = Field(..., ui_element='hidden')",
            ),
            InputTypeEntry(
                'tags',
                'Chip/tag entry: press Enter or comma to add a tag, Backspace to remove '
                'the last one; a hidden input carries the joined value.',
                "keywords: str = Field('', ui_element='tags',\n"
                "                      ui_help_text='Press Enter or comma to add a tag')",
            ),
            InputTypeEntry(
                'star_rating',
                'Individually clickable stars (contrast with rating, which is a slider).',
                "stars: int = Field(0, ui_element='star_rating', ui_options={'max_rating': 5})",
            ),
            InputTypeEntry(
                'captcha',
                'Simple math-challenge CAPTCHA for spam resistance without a third-party service.',
                "captcha: str = Field('', ui_element='captcha')",
            ),
            InputTypeEntry(
                'honeypot',
                'Invisible trap field for bots -- real users never see or fill it; a '
                'filled honeypot means reject the submission.',
                "website_url: str = Field('', ui_element='honeypot')",
            ),
            InputTypeEntry(
                'csrf',
                'Hidden CSRF token field -- typically added by the framework integration, '
                'not hand-declared per form.',
                "csrf_token: str = Field(..., ui_element='csrf')",
            ),
        ],
    ),
]
