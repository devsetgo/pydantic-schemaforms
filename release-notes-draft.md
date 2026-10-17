## ⚠️ This release has breaking changes

Complex forms are now built **one way**: declare other `FormModel`s as typed fields of a
parent model and choose a presentation with `layout=`. Data in and out is nested JSON. The
old form-orchestration classes are gone.

**Upgrading:** see the [upgrade guide](https://devsetgo.github.io/pydantic-schemaforms/stable/complex_forms/#upgrading).
Every removed class raises `FormLayoutRemovedError` with the exact replacement, so your app
tells you what to change.

**Before** (8 wrapper classes):

```python
class ContactTab(VerticalLayout):
    form = Contact

class Tabs(TabbedLayout):
    contact = ContactTab()

class Profile(FormModel):
    tabs: Tabs = Field(input_type="layout")
```

**After** (one model):

```python
class Profile(FormModel):
    contact: Contact = Field(title="Contact")
    address: Address = Field(title="Address")

render_form_html(Profile, layout="tabbed", submit_url="/profile")
result = Profile.validate(await request.form(), submit_url="/profile")
```

### 💥 Breaking changes

- **Form-orchestration classes removed:** `TabbedLayout`, `ListLayout`, `SectionDesign`,
  `FormDesign`, `FormLayoutBase` and the old `VerticalLayout`/`HorizontalLayout` wrappers. Use
  nested `FormModel` fields plus `layout=`. The top-level `VerticalLayout`/`HorizontalLayout`
  names now refer to the flex layout primitives. `pydantic_schemaforms.layouts` is deleted.
- **`result.data` is always nested:** `validate(flatten=True)` is removed.
- **`result.errors` is a nested tree** shaped like the data (`errors["pets"][1]["age"]`) instead
  of wire-path keys like `"pets[1].age"`. Form-wide errors are under `"_errors"`;
  `result.error_list()` gives a flat list.
- **`handle_form()` / `handle_form_async()`** return nested `data` and `errors`.
- **Grouped layouts need sub-forms:** `tabbed`, `side-by-side`, `accordion` and `wizard` on a
  form with no sub-form fields raise `ValueError`; the keyword-guessing tab grouping is gone.
- **An emptied repeating sub-form now fails its `min_length`** instead of passing as the default.
- **`validate()` no longer turns unexpected exceptions into form errors;** only validation
  errors do.

### ✨ New

- **Sub-forms:** a field typed as another `FormModel` renders as a titled section, optionally
  collapsible (`ui_collapsible`, `ui_collapsed`); `list[FormModel]` renders as a repeating
  sub-form.
- **New layouts:** `accordion`, and a **step wizard** (`layout="wizard"`) with a progress
  header, Back/Next, per-step validation, one POST for the whole form, and a no-JavaScript
  fallback.
- **`validate()` accepts the raw request form** (FastAPI/Starlette `FormData`, Flask/Werkzeug
  `MultiDict`) as well as JSON.
- **`ValidationResult`** gains `error_list()`, `instance`, `original_data` and
  `render_with_errors(errors=...)`.
- **The example app now covers everything:** every layout, every input type with each of its
  options, and every kind of validation, enforced by tests.
- **AI-assistant instructions** (`python -m pydantic_schemaforms.ai_instructions`) now document
  every widget option, field option and validation rule.

### 🐛 Fixes

- `radio`, `checkbox_group` and `combobox` now keep the user's choice when a form is re-shown
  after an error.
- `ui_element="hidden"` no longer renders a visible label.
- Custom date/time formats now apply to ISO strings (JSON data).
- The file-upload preview and the Material theme's scripts work (they never ran before).
- Material: colour hex readout restored; select label no longer overlaps its placeholder;
  required fields in hidden tabs no longer block submission silently.
- `Field(icon=...)` and other `ui_*` options are no longer dropped when combined.
- Form decoding no longer allocates a list as long as a submitted index (memory exhaustion).

**Full details:** [CHANGELOG](https://github.com/devsetgo/pydantic-schemaforms/blob/main/CHANGELOG.md)

## Changes

### 💥 Breaking Changes

- Breaking Change: Migrate to Nested Forms and Remove Legacy Layouts (#227) (@devsetgo)

### Features

- Enhancement: Replace OpenAI PR Autofill Workflow With devsetgo/ai-pr-assistant (#224) (@devsetgo)

### GitHub Actions

- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.2.1 to 8.3.0 (#225) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump devsetgo/ai-pr-assistant from 26.09.19.pre.002 to 26.09.20 (#226) (@[dependabot[bot]](https://github.com/apps/dependabot))

### Maintenance

- Chore: Bump Version to 26.4.1 (#228) (@devsetgo)

## Contributors

@devsetgo and [@dependabot[bot]](https://github.com/apps/dependabot)
