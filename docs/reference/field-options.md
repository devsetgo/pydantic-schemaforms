# Field Options

`pydantic_schemaforms.Field()` takes everything Pydantic's `Field()` takes,
plus the form settings below. The form settings only change how a field is
rendered, apart from `unchecked_message`; validation comes from the type and
the Pydantic constraints.

## Label and help

| Option | Effect |
|---|---|
| `title="..."` | The label. Without it, the field name is used: `team_size` becomes "Team Size". |
| `description="..."` | Help text under the input. Also appears in the JSON Schema. |
| `ui_help_text="..."` | Help text for the form only; shown instead of `description` |
| `ui_placeholder="..."` | Grey hint text inside an empty input |

## Choosing the input

| Option | Effect |
|---|---|
| `ui_element="..."` | The input to render, such as `"textarea"`, `"radio"` or `"currency"`. Without it, the input comes from the field's type. See [Input Types](inputs.md). |
| `input_type="..."` | Same as `ui_element`. |
| `ui_options={...}` | Settings for that input, such as `rows`, `choices` or `language`. Keys an input doesn't use become HTML attributes on it, for example `{"autocomplete": "username"}`. |

## Behaviour

| Option | Effect |
|---|---|
| `ui_autofocus=True` | The cursor starts in this field |
| `ui_disabled=True` | The input is greyed out. Browsers don't submit disabled inputs, so the field gets its default when validated. |
| `ui_readonly=True` | The input can't be changed but is submitted |
| `ui_hidden=True` | Rendered as `<input type="hidden">`, same as `ui_element="hidden"` |
| `ui_order=n` | Position among the fields (lower first); fields otherwise follow declaration order |
| `ui_class="..."` | Extra CSS classes on the input |
| `ui_style="..."` | Inline CSS on the input |
| `unchecked_message="..."` | The error shown when a required checkbox (`Literal[True]`, or `bool` with no default) is left unticked |

## Sub-forms and lists

Options on a field typed as a `FormModel` or a `list` of one, described in
[Layouts](layouts.md#sub-form-field-options):

- Sub-form: `ui_collapsible`, `ui_collapsed`, `ui_step_title`, `ui_order`.
- Repeating sub-form: `ui_add_button_label`, `ui_item_title_template`,
  `ui_collapsible_items`, `ui_items_expanded`.

Composite controls registered through
[Plugin Hooks](../advanced/plugin-hooks.md) use `input_type="layout"` with
`layout_handler="..."`.

## Pydantic options

Any Pydantic `Field()` option works as usual. The ones that matter to forms:

| Option | In the form |
|---|---|
| `default`, `default_factory` | The value a fresh form starts with. A field without one is required and its label gets `*`. |
| `min_length`, `max_length` | Checked on submit; `minlength`/`maxlength` attributes on text inputs. On a list, the fewest and most items. |
| `ge`, `le` | Checked on submit; `min`/`max` attributes on number inputs |
| `gt`, `lt` | Checked on submit only |
| `multiple_of` | Checked on submit; `step` attribute on number inputs (a `float` field otherwise gets `step="any"`) |
| `pattern` | Checked on submit; `pattern` attribute on text inputs |
| `alias` | The input is named after the alias, and `result.data` uses the field name |
| `examples` | Shown in the JSON Schema and in FastAPI's API docs, not in the form |
| `validate_default=True` | Runs validators on a default too |

A constraint that must hold always goes here, not in `ui_options`: only these
are checked on the server.
