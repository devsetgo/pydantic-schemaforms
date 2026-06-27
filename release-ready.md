# Release-Readiness Audit — pydantic-schemaforms

_Audited: 2026-06-13 against branch `dev` at commit `ce451ea`._

This document records every gap between the current codebase state and a clean 1.0 / production-stable release. Items are grouped by severity; **Critical** issues must be resolved before a 1.0 tag. **Major** issues are significant enough to warrant resolution before a public announcement. **Minor** issues are quality improvements that won't block shipping but reduce friction for users and future contributors.

---

## Critical

### C1 — Two `render_form_html` functions with the same name, silently different behaviour

**Where:** `pydantic_schemaforms/render_form.py` and `pydantic_schemaforms/enhanced_renderer.py`

Both modules define a public `render_form_html`. The top-level re-export (`from pydantic_schemaforms import render_form_html`) resolves to `render_form.py`, which silently appends `<div id="form-response"></div>` and a vendored HTMX `<script>` tag to every render. The README Quick Start examples import from `pydantic_schemaforms.enhanced_renderer` instead, which does not add these. A user switching import paths gets quietly different HTML output.

**Recommendation:** Pick one canonical function. `render_form.py` is the backwards-compat shim; its extra HTMX div is opt-in behaviour, not a sensible default. Either:
- Remove `render_form.py` and consolidate HTMX opt-in into `enhanced_renderer.render_form_html` via a keyword flag (`include_htmx_response_div=False`), or
- Make `render_form.py` a thin alias that merely calls the enhanced version without the hidden side-effects, and document the HTMX extra clearly.

Update `__init__.py` to re-export only one function.

---

### C2 — `asyncio.get_event_loop()` fallback is deprecated / broken on Python 3.14

**Where:** `enhanced_renderer.py:326`, `enhanced_renderer.py:1265`, `render_form.py:143`, `validation.py:921`

All four async helpers follow the same pattern:
```python
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.get_event_loop()   # deprecated since 3.10, removed in 3.14
```
On Python 3.14 (the library's *only* supported version) `asyncio.get_event_loop()` raises `DeprecationWarning` when called with no current event loop; in some contexts it raises `RuntimeError`. The fallback branch exists for "no running loop" — but if there is no running loop, calling `loop.run_in_executor()` is also wrong because the returned future never resolves without calling `loop.run_until_complete()`.

**Recommendation:** Remove the fallback entirely. Async entry points must be called inside an async context. If someone calls them outside one they should use `asyncio.run(render_form_html_async(...))`. The try/except should become just:
```python
loop = asyncio.get_running_loop()
return await loop.run_in_executor(None, render_callable)
```

---

### C3 — `FormModel._extract_ui_info` calls callable `json_schema_extra` with wrong signature

**Where:** `schema_form.py:229`

```python
elif callable(extra):
    schema = {}
    extra(schema, cls)  # type: ignore[call-arg]
```
Pydantic 2's `json_schema_extra` callable signature is `(schema: dict) -> None` — it takes one argument, not two. Passing `cls` as the second positional arg will raise `TypeError` at runtime for any field that uses a callable `json_schema_extra`.

**Recommendation:** Remove the second argument: `extra(schema)`. Add a test that exercises the callable branch.

---

### C4 — `__init__.py` Quick Start example will silently fail

**Where:** `pydantic_schemaforms/__init__.py:42-43` (module docstring)

```python
html = create_form_from_model(User).render()
```
`AutoFormBuilder.render()` calls `ModernFormRenderer.render_form(form_def, ...)` which passes `submit_url=form_def.submit_url`. `FormDefinition` defaults `submit_url='/submit'`. So this won't error — but the generated form will POST to `/submit` with no warning, which is a silent footgun for new users.

Additionally, item 4 of the Quick Start:
```python
result = await FormIntegration.async_integration(form, data)
```
`FormIntegration.async_integration` takes a `FormBuilder`, not a generic `form`. The variable name `form` does not make this clear. The example also does not show where `form` comes from, making it incorrect as documentation.

**Recommendation:** Fix both examples in the module docstring. For `create_form_from_model`, show `submit_url` explicitly. For `FormIntegration`, show the full builder construction.

---

## Major

### M1 — README imports `enhanced_renderer.render_form_html` rather than the top-level export

**Where:** `README.md` (all Quick Start code blocks)

The README consistently imports:
```python
from pydantic_schemaforms.enhanced_renderer import render_form_html
```
But the recommended entry point (and the one in `__all__`) is:
```python
from pydantic_schemaforms import render_form_html
```
This makes users think the submodule path is canonical and teaches them an import that will break if the module is restructured. It also hides C1: users who switch to the top-level import get unexpected HTMX markup.

**Recommendation:** After resolving C1, update all README examples to import from the top level. A single "from pydantic_schemaforms import ..." import teaches the right habit.

---

### M2 — `form_validator` decorator swallows all exceptions into `ValueError`

**Where:** `schema_form.py:36-45`

```python
except Exception as e:
    raise ValueError(f'Validation error: {str(e)}')
```
This loses the original exception type, message, and traceback. A `pydantic.ValidationError`, `KeyError`, or any other typed exception is flattened into a generic `ValueError`. Debugging is significantly harder because the stack shows only the re-raise site.

**Recommendation:** Use `raise ... from e` at minimum to preserve the cause chain. Even better: only catch `ValueError` and let other exceptions propagate naturally. If the intent is to normalise all errors to `ValueError`, document it explicitly and preserve the `__cause__`.

---

### M3 — `ValidationResult` and related types missing from `__all__`

**Where:** `pydantic_schemaforms/__init__.py:192-263`

Several important types are imported by `__init__.py` but omitted from `__all__`:
- `ValidationSchema`
- `FieldValidator`
- `MaxLengthRule`, `MinLengthRule`, `RegexRule`, `PhoneRule`, `NumericRangeRule`, `DateRangeRule`, `CustomRule` (partially present: only `RequiredRule` and `EmailRule` are in `__all__`)
- `ValidationResponse`
- `CrossFieldRules`
- `create_email_validator`, `create_password_strength_validator`
- `FormTemplates`, `TemplateString` (exported but not in `__all__`)
- `ModernFormRenderer`, `FormDefinition`, `FormSection`, `FormField` from `modern_renderer`

A user doing `from pydantic_schemaforms import *` gets an inconsistent subset. `dir(pydantic_schemaforms)` returns the right list but `__all__` does not.

**Recommendation:** Audit `__all__` against every top-level import and make it complete, or explicitly document which symbols are intentionally unexported.

---

### M4 — Inline `<style>` emitted on every render with no deduplication mechanism

**Where:** `enhanced_renderer.py:446-483` (`_render_layout_support_styles`)

Every call to `render_form_from_model` emits a `<style data-schemaforms-layout-support>` block with ~30 lines of CSS. On a page with multiple forms this appears multiple times. There is no opt-out.

**Recommendation:** Provide a way to opt out of the inline styles (e.g., `inject_layout_styles=False`), or render the block only once by checking for its presence via a marker attribute. The data attribute `data-schemaforms-layout-support` is already there — use it as the uniqueness key.

---

### M5 — `integration/react.py` and `integration/vue.py` are misleadingly named

**Where:** `pydantic_schemaforms/integration/react.py`, `pydantic_schemaforms/integration/vue.py`

These modules generate JSON schema configuration artifacts (for `react-jsonschema-form` and `vue-formulate` respectively). They do not actually integrate with React or Vue — they output data structures that a frontend developer would need to wire up manually. New users will expect React/Vue component generation or server-side templates, not JSON schema blobs.

**Recommendation:** Rename to `json_schema_form_adapter.py` and `vue_formulate_adapter.py` (or similar). Update `__all__` and `integration/__init__.py` accordingly. Add clear docstrings explaining these are data adapters, not rendering adapters.

---

### M6 — `pytest` configuration has a broken `norecursedirs` entry

**Where:** `pyproject.toml:119`

```toml
norecursedirs = [ "/tests", ".hypothesis", "playwright",]
```
`"/tests"` with a leading slash refers to the filesystem root path `/tests`, not the local `./tests` directory. The entry is effectively a no-op and probably confusing. The actual test exclusions work because `testpaths = ["tests"]` drives collection — but the intent (excluding the tests directory from *within* collection) is mislabeled.

**Recommendation:** Fix to `"tests"` (no leading slash) or remove the entry entirely since `testpaths` already scopes collection.

---

### M7 — Dev dependency has a non-existent or future FastAPI version

**Where:** `pyproject.toml:32`

```toml
dev = [ "fastapi[all]==0.136.1", ...]
```
FastAPI 0.136.1 is not a version that exists as of the audit date. The most recent stable release is in the 0.11x series. This pin will fail `pip install -e ".[dev]"` with a resolution error, breaking fresh development environment setup.

**Recommendation:** Correct to the latest stable FastAPI version available (e.g., `fastapi[all]>=0.110,<1` to match the optional dep range). Pin to a specific known-good version if lockfile reproducibility is required.

---

### M8 — `schema_form.py` uses a stale Pydantic v1 fallback

**Where:** `schema_form.py:169`

```python
schema = cls.model_json_schema() if hasattr(cls, 'model_json_schema') else cls.schema()
```
`cls.schema()` was removed in Pydantic v2. The library declares `pydantic>=2.7,<4` as a dependency, so `model_json_schema` is always present. The `hasattr` check and `cls.schema()` fallback are dead code that will never run, and they add noise that obscures the real logic.

**Recommendation:** Remove the fallback. Call `cls.model_json_schema()` directly.

---

### M9 — `render_form.py` unconditionally appends HTMX response container

**Where:** `render_form.py:83-86`

```python
form_html += '\n<div id="form-response"></div>'
htmx_tag = htmx_script_tag(asset_mode=asset_mode)
if htmx_tag:
    form_html += f'\n{htmx_tag}'
```
The `<div id="form-response">` is appended to every single render regardless of whether the caller uses HTMX. This pollutes the DOM with unused elements and uses a hard-coded ID that will conflict if multiple forms are on the same page.

**Recommendation:** Make this opt-in (`include_htmx_response_container=False` default). If HTMX is desired, the div should use a unique ID derived from the form model name to avoid collisions.

---

## Minor

### m1 — `test_coverage_boost.py` is coverage padding, not behavioural coverage

**Where:** `tests/test_coverage_boost.py`

The file's own docstring says "Coverage-boost tests targeting all files below 90%." It contains 80+ test cases that mostly assert a string is "in" the HTML output without verifying correctness. Typical example:
```python
assert 'Choose' in html
```
These tests catch import errors and very obvious crashes, but they don't verify rendered semantics, error conditions, or security-relevant paths. They artificially inflate the coverage percentage without adding meaningful regression protection.

**Recommendation:** Do not delete — some tests here are genuinely useful. But do not use coverage percentage as a proxy for test quality. Consider replacing the most superficial cases with tests that verify specific HTML attributes, ARIA roles, or error messages. The filename `test_coverage_boost.py` communicates the wrong intent and should be renamed to reflect what the tests actually cover (e.g., `test_input_rendering.py`, `test_integration_utils.py`).

---

### m2 — `form_validator` decorator description refers to a non-existent `FormField` import

**Where:** `schema_form.py:21` (decorator docstring)

The decorator docstring example uses `FormField(...)` but the module imports `FormField` from `form_field.py`. However, the same module does not import `FormField` at all. The example in the docstring will mislead users who copy it.

**Recommendation:** Fix the docstring example to use the correct import (`Field()` from the same module) or import `FormField` appropriately.

---

### m3 — Typing imports use `from typing import Dict, List, Optional` instead of built-ins

**Where:** Many files throughout `pydantic_schemaforms/`, e.g. `schema_form.py:2-6`, `validation.py:15`, `enhanced_renderer.py:17`, `live_validation.py:12`

Python 3.14 has native `dict[str, Any]`, `list[str]`, `str | None` syntax. The library's own CLAUDE.md says "Requires Python 3.14+." Yet `Dict`, `List`, `Optional`, `Tuple`, `Type`, `Union` from `typing` are used throughout. This is not a bug, but it's inconsistent with the 3.14-only positioning and clutters imports.

**Recommendation:** Migrate to built-in collection types and PEP 604/PEP 585 syntax (`dict | None`, `list[str]`, etc.) across the codebase. This is low risk — just a search-and-replace plus `ruff` auto-fix. Makes the "Python 3.14 library" claim consistent with the code.

---

### m4 — `ModernFormRenderer` is deprecated but still the backbone of `FormBuilder`

**Where:** `integration/builder.py:44-51`, `modern_renderer.py:268`

`ModernFormRenderer` is marked deprecated with a warning, but `FormBuilder` — a non-deprecated public class — creates one internally with `_internal=True`. The deprecation warning is only bypassed by the private flag. This means:
1. The deprecation is artificial; the class is still the active rendering path for the builder DSL.
2. If `ModernFormRenderer` is ever actually removed, `FormBuilder` breaks.

**Recommendation:** Either un-deprecate `ModernFormRenderer` (it clearly serves a purpose), or complete the migration so `FormBuilder` uses `EnhancedFormRenderer` directly and `ModernFormRenderer` is only kept as a thin compatibility wrapper. The current half-deprecated state is confusing.

---

### m5 — `_render_layout_support_styles` produces CSS with `!important` overrides

**Where:** `enhanced_renderer.py:456-482`

The CSS block uses `!important` on `flex`, `min-width`, and `max-width` for columns:
```css
.pydantic-form [class*="col-"] {
    min-width: 0;
    flex: 1 1 auto !important;
}
```
`!important` overrides prevent users from customising column layout through their own CSS without also using `!important`. This is a maintainability problem — it makes the library's output resistant to theming.

**Recommendation:** Remove `!important` declarations where possible. Where layout must be enforced, use higher specificity selectors instead.

---

### m6 — `validate_form_data` silently accepts unknown keys from form submissions

**Where:** `validation.py:949-951`

```python
validated_instance = runtime_model(**data)
validated_data = validated_instance.model_dump()
```
Pydantic's default `model_config` ignores extra fields (they are stripped from the validated output). This is actually correct — `test_option_a_policy.py` tests that `is_admin` is stripped. But the behaviour is invisible from the function signature and no documentation explicitly calls it out.

**Recommendation:** Document the "extra fields are silently stripped" contract explicitly in the `validate_form_data` docstring. Consider whether a mode that rejects unknown fields would be useful (e.g., for APIs).

---

### m7 — `FormValidator.generate_client_validation_script` uses innerHTML without escaping

**Where:** `validation.py:664-667`

```javascript
const errorElement = document.createElement('div');
errorElement.className = 'error-message';
errorElement.textContent = error;   // ← OK: textContent is safe
input.parentNode.insertBefore(errorElement, input.nextSibling);
```
This part is safe (uses `textContent`). However, the generated JS inserts error strings from `escape(self.message)` (Python-side HTML escape) into a JS string literal. If `self.message` contains single quotes, the JS may be malformed.

**Recommendation:** The `escape()` call in `_generate_js_validation` only HTML-escapes; the JS string literal delimiters are single quotes. Add JS string escaping too (backslash-escape `'` and `\` in the message before embedding in JS). A helper like `js_string_escape(message)` makes this clear.

---

### m8 — `generate_validation_endpoint_code` returns string templates with bugs

**Where:** `live_validation.py:303-367`

The generated Flask/FastAPI endpoint code strings include:
```python
return f'<div class="invalid-feedback">{errors_html}</div>'
```
inside what is meant to be Python source code string. The `errors_html` variable is itself built from `'<br>'.join(response.errors)` without HTML escaping `response.errors` values. This means generated endpoint code, if used as-is, would XSS-expose error messages.

More broadly, generating code as strings and asking users to paste it is fragile documentation. This is especially risky for security-adjacent code (validation endpoints).

**Recommendation:** Replace the code-generation approach with importable helper functions. Instead of returning a string the user pastes, provide:
```python
from pydantic_schemaforms.live_validation import make_flask_validation_handler
```
This is safer, testable, and keeps users from copying buggy snippets.

---

### m9 — `version_check.py` runs on import but is not itself tested end-to-end

**Where:** `pydantic_schemaforms/version_check.py:51-53`

```python
check_python_version()
verify_template_strings()
```
These run at module load time (when any `pydantic_schemaforms` symbol is imported). `test_coverage_boost.py` mocks `sys.version_info` and `importlib.util.find_spec` to exercise the failure branches, but does not test the module-level execution itself. If the module-level calls are accidentally removed or guarded by a condition in the future, no test would catch it.

**Recommendation:** Add a test that imports `pydantic_schemaforms` in a subprocess with `PYTHONPATH` set and asserts the version check was run (or that the import succeeds on the correct version). This ensures the guard at module load time is not silently bypassed.

---

### m10 — `schema_form.py` has an open TODO in production code

**Where:** `schema_form.py:416-418`

```python
# TODO: Suppress the UserWarning about shadowed fields once the helper
#       grows a local model_config; the runtime class is expected.
```
Open TODOs in library source code signal to consumers that the code is unfinished. The `UserWarning` that results from shadowed fields may appear in user logs unexpectedly.

**Recommendation:** Either resolve the `UserWarning` now (the comment indicates the fix is known: add `model_config = ConfigDict(revalidate_instances='always')` or similar to the runtime model), or at minimum suppress the warning with a targeted `warnings.filterwarnings` call adjacent to the `create_model` call, not a TODO.

---

### m11 — `__init__.py` docstring describes a three-API surface that confuses onboarding

**Where:** `pydantic_schemaforms/__init__.py:19-61`

The Quick Start shows four distinct usage patterns (FormModel, AutoFormBuilder, create_login_form, FormIntegration). For a 1.0 library, having four different "recommended" entry points creates decision paralysis. The module-level docstring is also long (61 lines) and will be the first thing a user reads from `help(pydantic_schemaforms)`.

**Recommendation:** Designate one primary pattern (`FormModel` + `render_form_html`) as the recommended entry point and show it prominently. Document the builder DSL as "alternative for programmatic construction" and the pre-built helpers as "convenience for common cases." Trim the module docstring to 20–30 lines maximum.

---

### m12 — `STATIC_DIR` is computed but never used

**Where:** `pydantic_schemaforms/__init__.py:184`

```python
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
```
`STATIC_DIR` is not in `__all__` and there is no `static/` subdirectory in the package. Searching the codebase, nothing imports `STATIC_DIR`. It is dead code that raises a false expectation about static file serving.

**Recommendation:** Remove `STATIC_DIR` and its `import os` dependency if `os` is used nowhere else in `__init__.py`.

---

### m13 — `pytest-html` referenced in `addopts` but not in dev dependencies

**Where:** `pyproject.toml:122`

```toml
addopts = [ ... "--html=htmlcov/_test_report.html", "--self-contained-html", ...]
```
`pytest-html` is not listed in `[project.optional-dependencies]` or `[project.optional-dependencies.dev]`. Running `pytest` without `pytest-html` installed will produce a warning that `--html` is an unknown option; if `pytest-html` is installed but at the wrong version, `--self-contained-html` may be rejected.

**Recommendation:** Either add `pytest-html` to dev dependencies with an appropriate version pin, or move the `--html` flag out of `addopts` and into a `Makefile` target that explicitly installs and runs with it.

---

### m14 — `__init__.py` `check_python_version` and `verify_template_strings` are called but not re-exported

**Where:** `pydantic_schemaforms/__init__.py:71`

```python
from .version_check import check_python_version, verify_template_strings
```
These are imported by `__init__.py` (making them accidentally importable as `pydantic_schemaforms.check_python_version`) but not in `__all__`. They are internal utilities, not public API.

**Recommendation:** Change the import to not bind names at the package level:
```python
from .version_check import check_python_version as _check, verify_template_strings as _verify
_check()
_verify()
```

---

### m15 — Missing `py.typed` verification in CI

**Where:** `pyproject.toml`, CI (`testing.yml`)

The package ships `py.typed` (confirming PEP 561 compliance), but the CI workflow does not run `pyright` or `mypy` to verify that the published type stubs are actually correct. Users relying on type checking will get incorrect inferences if internal annotations are wrong.

**Recommendation:** Add a `pyright --verifytypes pydantic_schemaforms` step to CI. This confirms that every exported symbol has a complete type annotation and that the `py.typed` marker is truthful.

---

### m16 — `render_form.py` and `enhanced_renderer.py` both re-export `render_form_html_async`

**Where:** `pydantic_schemaforms/__init__.py:125`, `render_form.py:105`, `enhanced_renderer.py:1225`

Same issue as C1 but for the async variant. Three definitions (one in each module), two different behaviours (HTMX wrapper vs. clean output), one top-level name. Resolving C1 should include this.

---

## Documentation Issues

### D1 — README Flask integration example passes `errors=e.errors()` which is wrong format

**Where:** `README.md:527-533`

```python
except ValidationError as e:
    errors = e.errors()
    form_html = UserRegistrationForm.render_form(
        framework="bootstrap",
        submit_url="/",
        errors=errors     # ← errors is List[dict], not Dict[str, str]
    )
```
`e.errors()` returns a `List[dict]` with Pydantic error dicts. The renderer expects `errors: Dict[str, str]` (field name → message string). The example will render with no field errors highlighted — it silently does the wrong thing.

**Recommendation:** Fix the example to match actual usage:
```python
except ValidationError as e:
    errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}
```
(This is actually the pattern shown in the FastAPI examples in the same README — just the Flask section was not updated.)

---

### D2 — CHANGELOG does not document breaking change from `include_framework_assets` default

**Where:** `CHANGELOG.md`

The `include_framework_assets=False` default (meaning users must provide their own Bootstrap/Material CSS) is a potential source of confusion, especially given the README's mixing of `self_contained=True` and external CDN examples. There is no CHANGELOG entry that clearly explains the rendering contract: "the library outputs markup, not a page."

**Recommendation:** Add a CHANGELOG section (or a "How It Works" section to the docs) that clearly states: "render_form_html returns a form fragment, not a full page. Bootstrap/Material CSS must be loaded separately unless you pass `self_contained=True` or `include_framework_assets=True`."

---

### D3 — `docs/` site contains `library-boundary-risk-analysis.md` — an internal design document

**Where:** `docs/library-boundary-risk-analysis.md`

This file appears to be an internal risk analysis document from design/planning phases. It would be confusing in the published docs site and implies the library's own authors have unresolved concerns they haven't disclosed to users.

**Recommendation:** Move this to `docs/internal/` or remove it from the docs site navigation. It is valuable for contributors but should not appear as user-facing documentation.

---

## Summary Table

| ID | Severity | File(s) | One-line description |
|----|----------|---------|----------------------|
| C1 | Critical | `render_form.py`, `enhanced_renderer.py` | Two `render_form_html` with same name, different outputs |
| C2 | Critical | 4 async helpers | `asyncio.get_event_loop()` removed/deprecated in 3.14 |
| C3 | Critical | `schema_form.py:229` | `json_schema_extra` callable called with wrong arity |
| C4 | Critical | `__init__.py` docstring | Quick Start examples are wrong or misleading |
| M1 | Major | `README.md` | README imports submodule path, not top-level |
| M2 | Major | `schema_form.py` | `form_validator` swallows all exceptions into `ValueError` |
| M3 | Major | `__init__.py` | Many public types missing from `__all__` |
| M4 | Major | `enhanced_renderer.py` | Inline `<style>` on every render, no deduplication |
| M5 | Major | `integration/react.py`, `vue.py` | Misleading module names imply frontend framework integration |
| M6 | Major | `pyproject.toml:119` | `/tests` in `norecursedirs` is wrong path |
| M7 | Major | `pyproject.toml:32` | `fastapi[all]==0.136.1` is a non-existent version |
| M8 | Major | `schema_form.py:169` | Dead Pydantic v1 fallback `cls.schema()` |
| M9 | Major | `render_form.py:83` | HTMX response div appended unconditionally |
| m1 | Minor | `test_coverage_boost.py` | Coverage padding, not behavioural tests |
| m2 | Minor | `schema_form.py` docstring | Example references wrong import |
| m3 | Minor | entire codebase | Old `typing` imports instead of built-in collection types |
| m4 | Minor | `builder.py`, `modern_renderer.py` | Deprecated class is still the active builder rendering path |
| m5 | Minor | `enhanced_renderer.py` | Injected CSS uses `!important`, blocks theming |
| m6 | Minor | `validation.py` | Silent stripping of unknown form keys undocumented |
| m7 | Minor | `validation.py:664` | JS-embedded error messages not JS-string-escaped |
| m8 | Minor | `live_validation.py` | Code-gen endpoint strings have XSS in generated code |
| m9 | Minor | `version_check.py` | Module-level guard not end-to-end tested |
| m10 | Minor | `schema_form.py:416` | Open TODO about `UserWarning` in production code |
| m11 | Minor | `__init__.py` | Four entry points in docstring cause onboarding confusion |
| m12 | Minor | `__init__.py:184` | `STATIC_DIR` is dead code; `static/` dir does not exist |
| m13 | Minor | `pyproject.toml` | `pytest-html` in `addopts` but not in dev dependencies |
| m14 | Minor | `__init__.py:71` | Internal version-check functions accidentally public |
| m15 | Minor | CI / `pyproject.toml` | No `pyright --verifytypes` step despite `py.typed` marker |
| m16 | Minor | async helpers | `render_form_html_async` triple-defined; same class as C1 |
| D1 | Docs | `README.md` | Flask example passes wrong `errors` format |
| D2 | Docs | `CHANGELOG.md` | Asset-loading contract not documented |
| D3 | Docs | `docs/` | Internal risk analysis is user-visible in docs site |
