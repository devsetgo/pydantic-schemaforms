# Library Review – pydantic-forms

_Date: 2025-11-23_

## Critical / High Priority Findings

- **Runtime dependencies missing from packaging (`pyproject.toml`)** _(Resolved – 2025-11-23)_  
  `pyproject.toml` now declares `pydantic>=2.7`, framework extras, and lists `pydantic_forms` as the packaged module with classifiers aligned to `requires-python = ">=3.14"`. Editable installs and wheels now pull the libraries the code imports.  
  _Files: `pyproject.toml`, `makefile`_

- **`render_form_from_model_async` cannot accept keyword arguments** _(Resolved – 2025-11-23)_  
  The async helper now delegates through a `functools.partial` that preserves keyword arguments before submitting to the executor, preventing `TypeError` when callers pass layout or framework overrides.  
  _Files: `pydantic_forms/enhanced_renderer.py`_

- **Renderer instances keep mutable request-scoped state** _(Resolved – 2025-11-23)_  
  Rendering now flows through an immutable `_RenderContext` dataclass that is threaded through helper methods, eliminating shared mutable attributes and keeping concurrent requests isolated.  
  _Files: `pydantic_forms/enhanced_renderer.py`, `pydantic_forms/simple_material_renderer.py`_

- **Duplicate `BaseInput` class definitions cause inconsistent behavior** _(Resolved – 2025-11-23)_  
  The duplicate class definitions were collapsed into a single abstract `BaseInput`, and all input subclasses now inherit consistent attribute validation and rendering helpers.  
  _Files: `pydantic_forms/inputs/base.py` and consumers_

- **UI metadata ignored for select/multiselect inputs** _(Resolved – 2025-11-23)_  
  `ui_options["choices"]` and enum values were previously dropped, so select fields rendered warning comments instead of dropdowns. `EnhancedFormRenderer` now normalizes tuples/dicts into option maps, propagates attrs such as `multiple`, and the framework layer exposes `MultiSelectInput`, restoring `<select>` output.  
  _Files: `pydantic_forms/enhanced_renderer.py`, `pydantic_forms/rendering/frameworks.py`_

- **File input preview template crashes rendering** _(Resolved – 2025-11-23)_  
  The `FileInput` preview JavaScript embedded template-literal placeholders inside an f-string, causing `NameError: name 'file' is not defined` and suppressing `<input type="file">`. Escaping the `${...}` placeholders keeps the JS intact so the specialized-field tests pass again.  
  _Files: `pydantic_forms/inputs/specialized_inputs.py`_

- **Async/layout render duplication increases drift risk** _(Resolved – 2025-11-23)_  
  A single canonical `render_form_html` in `enhanced_renderer.py` now powers all entry points. The legacy wrapper adds HTMX defaults before delegating, and the async helper offloads the canonical function to a pool, eliminating divergent logic paths.  
  _Files: `pydantic_forms/enhanced_renderer.py`, `pydantic_forms/render_form.py`

## Medium Priority Refactors & Optimizations

- **Renderer modules exceed 1,400 lines**  
  `pydantic_forms/enhanced_renderer.py` and `pydantic_forms/simple_material_renderer.py` contain renderer configuration, layout logic, input dispatch, and async helpers in one file. Splitting responsibilities (schema parsing, layout orchestration, input rendering, framework theming) would drastically improve readability and testability.

- **Multiple layout systems compete**  
  There are two unrelated layout stacks (`pydantic_forms/form_layouts.py` and `pydantic_forms/layouts.py`) plus bespoke layout handling in `EnhancedFormRenderer`. Consolidate around one abstraction (e.g., `BaseLayout`) and have renderers consume it so maintenance effort is not tripled.

- **Schema handling recomputes per request**  
  Every render call invokes `model_cls.model_json_schema()` and walks the resulting dict. For forms that render frequently, cache the schema + UI metadata per model (perhaps via `functools.lru_cache`) and only clone when necessary to inject request data.

- **`templates.py` global cache lacks thread/process coordination**  
  The `_template_cache` dictionary is mutated without locking and only bounded by an eviction of the first key. Consider `functools.lru_cache` or `collections.OrderedDict` plus a lock so multi-threaded renderers do not race.

- **Integration helpers include unused/dead code**  
  Example: `check_framework_availability` in `pydantic_forms/integration.py` is never invoked. Prune unused helpers or wire them into tests to ensure they stay functional.

- **Model list rendering mixes HTML with data extraction**  
  `pydantic_forms/model_list.py` contains several near-identical methods for Bootstrap vs Material output. Extract shared pieces (button rendering, item iteration, error handling) and drive differences via template fragments.

## Testing & Tooling Gaps

- `pytest` is listed in `requirements.txt` but not installed in the dev container; running `pytest` currently fails with `command not found`. Provide a reproducible test command (e.g., `pip install -r requirements.txt && pytest`) or add instructions to the makefile.
- Targeted renderer coverage exists (`tests/test_enhanced_renderer.py`) and now passes, but there is still no CI job or documented workflow confirming the full suite (`pytest tests`). Add a recipe (e.g., `make test`) so contributors can run the same checks locally.
- No regression tests cover the async renderer or model list component. After fixing the issues above, add tests that exercise keyword argument passing and concurrent renders to lock in expected behavior.

## Quick Wins / Follow-Up Tasks

1. ✅ _Done_ — `pyproject.toml` metadata now ships the right package with declared deps.
2. ✅ _Done_ — Async rendering delegates through `functools.partial`; tests still needed.
3. ✅ _Done_ — `_RenderContext` replaces mutable renderer state.
4. ✅ _Done_ — Unified `BaseInput` implementation.
5. ✅ _Done_ — Select/multiselect widgets honor `ui_options` metadata and multi-value attrs, preventing regressions in renderer coverage.
6. ✅ _Done_ — File input preview template no longer throws `NameError`, so specialized inputs render in Bootstrap.
7. ⏳ _Open_ — Still multiple layout stacks; consolidate to reduce maintenance.
8. ⏳ _Open_ — Add caching for `model_json_schema()` and measure perf gains.

These changes will reduce runtime bugs, lower maintenance overhead, and make it easier to add additional frameworks or inputs without duplicating logic across the codebase.
