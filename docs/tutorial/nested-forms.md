# Nested Forms and Lists

A bigger form is built from smaller ones. A field typed as another
`FormModel` becomes a **sub-form**, and a field typed as a `list` of one
becomes a **repeating sub-form** with Add and Remove buttons. There are no
special classes to learn: it's ordinary Pydantic nesting.

```python
--8<-- "docs_src/tutorial/nested/models.py"
```

Use it with the routes from [Handling Submissions](handling-submissions.md).
The form shows the nickname, then a "Home address" section, then a "Pets"
list with an "Add a pet" button.

## Sub-forms

`address: Address` renders the `Address` fields as a titled section. The
sub-form's own rules (`min_length=2` on the city) apply as usual, and its
fields can have their own sub-forms, as deep as you need.

Make a section collapsible with `ui_collapsible=True`, or start it collapsed
with `ui_collapsed=True` (it opens by itself when it contains an error). An
optional sub-form is typed `Address | None`.

## Repeating sub-forms

`pets: list[Pet]` renders one card per pet with Add and Remove buttons.
Constraints count items: `max_length=5` allows at most five pets, and
`min_length=1` would require at least one.

| Setting | Effect |
|---|---|
| `ui_add_button_label="Add a pet"` | Text of the Add button |
| `ui_item_title_template="{name}"` | Each card's title, filled from the item's fields; `{index}` is the 1-based position |
| `ui_collapsible_items=False` | Plain cards instead of collapsible ones |
| `ui_items_expanded=False` | Start the cards collapsed |

## Data and errors are nested

`validate()` returns the data shaped exactly like the model:

```python
{
    "nickname": "mk",
    "address": {"street": "1 Main", "city": "Paris"},
    "pets": [{"name": "Rex", "age": 3}, {"name": "Tux", "age": 1}],
}
```

and the errors shaped exactly like the data, so an error is found at the same
path as its value:

```python
{
    "address": {"city": "String should have at least 2 characters"},
    "pets": {1: {"age": "Must be 0 or greater"}},
}
```

- A list's errors are keyed by the item's position, and only failing items appear.
- A message about a whole list, such as too many pets, is a string at the
  list's key, or under `"_errors"` there when some items also have errors:
  `{"pets": {"_errors": "...", 0: {...}}}`.
- `result.error_list()` gives the same errors as a flat list,
  `[{"loc": ["pets", 1, "age"], "msg": "Must be 0 or greater"}]`, which is
  handy for logging and API responses.

When the form is re-rendered, each message appears next to its input and the
summary at the top names the item: "Pet #2 — Age: Must be 0 or greater".

??? note "How the inputs are named"

    The inputs are named `address.city` and `pets[0].name` so the browser can
    submit them, and `validate()` decodes those names back into the nested
    data. You never need to build or parse them yourself, except when you
    post raw form data in a test.

Sub-forms are also what the grouped layouts arrange into tabs, columns,
panels or wizard steps: that's the next chapter, [Layouts](layouts.md).
