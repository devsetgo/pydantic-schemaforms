# Fields and Inputs

Each field on the model becomes one input. Most of the time the field's type
is enough to pick the right input; `Field()` adds the label, help text and
anything else the form needs.

```python
--8<-- "docs_src/tutorial/fields/models.py"
```

Use it with the routes from [Handling Submissions](handling-submissions.md);
only the model changes. You get a text box for the name, an email box, a date
picker, a dropdown of plans, a number box limited to 1–500, two radio
buttons, a text area and a checkbox.

## The type picks the input

Without a `ui_element`, the input comes from the field's type:

| Field type | Input |
|---|---|
| `str` | Text box |
| `int`, `float` | Number box (for a `Decimal`, set `ui_element="decimal"` or `"currency"`) |
| `bool` | Checkbox |
| `Literal[True]` | Checkbox that must be ticked; see [Validation](validation.md#required-checkboxes) |
| `date` | Date picker |
| `datetime` | Date and time picker |
| `time` | Time picker |
| `EmailStr` | Email box |
| `AnyUrl` | URL box |
| `Enum`, `Literal[...]` | Dropdown of the values |
| `list[Enum]`, `list[Literal[...]]` | Multi-select |
| Another `FormModel` | A sub-form; see [Nested Forms and Lists](nested-forms.md) |
| `list` of a `FormModel` | A repeating sub-form |

`plan: Plan` above needs nothing else: its dropdown lists `free`, `team` and
`enterprise`, and the submitted value comes back as a `Plan`.

## Choosing a different input

Set `ui_element` when the type alone isn't enough: `"email"` for a plain
`str` holding an email address, `"textarea"` for longer text, `"radio"` to
show a few choices side by side instead of a dropdown, `"password"`,
`"color"`, `"slider"`, `"tags"`, `"file"` and many more.

[Input Types](../reference/inputs.md) lists every `ui_element` with all of
its options.

## Labels, help text and placeholders

| Setting | Shows as |
|---|---|
| `title="Full name"` | The label. Without it, the field name is used: `team_size` becomes "Team Size". |
| `description="..."` | Help text under the input |
| `ui_placeholder="you@example.com"` | Grey hint text inside an empty input |
| `ui_autofocus=True` | The cursor starts in this field |

Help text and error messages are linked to their input for screen readers,
and every input gets a label; see [Accessibility](../reference/accessibility.md).

## Required and optional fields

A field without a default is **required**: the form marks its label with `*`
and won't validate without it. Give it a default to make it optional, or
`None` with an `Optional` type when "no answer" is a valid answer:

```python
birthday: date | None = Field(None, title="Birthday")
```

An optional dropdown gets an empty first choice, and submitting it empty
gives `None`.

## Constraints

Pydantic constraints such as `min_length`, `max_length`, `ge`, `le` and
`pattern` do two things: they're checked when the form is submitted, and they
become HTML attributes (`minlength`, `min`, `max`, `pattern`) so the browser
can catch mistakes before the form is sent. `team_size` above only accepts 1
to 500 either way. The next chapter, [Validation](validation.md), covers them
in detail.

## Show a field only when it applies

`ui_show_when` hides a field until another field has a given value:

=== "FastAPI"

    ```python hl_lines="17-21"
    --8<-- "docs_src/tutorial/show_when/fastapi_app.py"
    ```

=== "Flask"

    ```python hl_lines="16-20"
    --8<-- "docs_src/tutorial/show_when/flask_app.py"
    ```

`field` names the field to watch, and one test decides when this one shows:

| Test | Shows when the other field |
|---|---|
| `"equals": "phone"` | Has this value |
| `"in": ["phone", "post"]` | Has one of these values |
| `"truthy": True` | Is ticked or has a non-empty value (`False` for the opposite) |
| `"not_empty": True` | Has any value (`False` for empty) |

**The server applies the same rule.** A hidden field's submitted value is dropped
before validation, even in a hand-written request, so it produces no errors and
`result.data` holds the field's default. That's why the field must have a default.

**For "required only when shown"**, add `"required": True` to the rule, as above,
rather than declaring the field required.

`field` is relative to the model the rule is on. It can go down into a sub-form
(`"address.country"`) but not up to a parent, so to hide a whole sub-form based on
a parent's field, put the rule on the sub-form field in the parent. Inside a
`model_list`, each item follows its own values.

In `layout="tabbed"`, `"accordion"` and `"wizard"`, a hidden sub-form leaves its
tab, panel or step in place, empty.

## Defaults and pre-filled forms

A fresh form starts from the field defaults: the team size shows 1, the plan
is `free`, the radio button is on "email".

To show existing values, for example to edit a saved record, pass them as
`form_data`:

```python
--8<-- "docs_src/tutorial/fields/prefill.py"
```

When you pass `form_data`, it's used **as is**: fields you leave out are
empty, not filled with their defaults. That's what you want when you
re-render a submission, where an unticked checkbox is simply missing.

??? note "Widget-specific options"

    Some inputs take extra settings through `ui_options`, for example the
    number of rows of a text area or the choices and labels of a select
    built from a plain `str` field:

    ```python
    bio: str = Field("", ui_element="textarea", ui_options={"rows": 6})
    size: str = Field(
        "m",
        ui_element="select",
        ui_options={"choices": [
            {"value": "s", "label": "Small"},
            {"value": "m", "label": "Medium"},
        ]},
    )
    ```

    [Input Types](../reference/inputs.md) lists every option of every input.
    Use `ui_options` only for presentation: a limit such as `min`/`max` must
    be a Pydantic constraint (`ge`/`le`) so it's actually enforced.

Next: [Validation](validation.md).
