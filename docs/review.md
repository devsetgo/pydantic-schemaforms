# Library Review – pydantic-forms

_Date: 2025-11-25_

## Critical / High Priority Findings

- **Runtime dependencies missing from packaging (`pyproject.toml`)** _(Resolved – 2025-11-23)_  
  `pyproject.toml` now declares `pydantic>=2.7`, framework extras, and lists `pydantic_forms` as the packaged module with classifiers aligned to `requires-python = ">=3.14"`. Editable installs and wheels now pull the libraries the code imports.  
  _Files: `pyproject.toml`, `makefile`_

- **`EnhancedFormRenderer` file corruption prevented imports** _(Resolved – 2025-11-25)_  
  The renderer module had been truncated to an empty file, breaking every caller that imported `EnhancedFormRenderer`/`render_form_html`. The class has been reconstructed, delegating per-field rendering to `FieldRenderer`, wiring `LayoutEngine`, and reinstating the synchronous/async top-level helpers so downstream modules load again.  
  _Files: `pydantic_forms/enhanced_renderer.py`_

- **`render_form_from_model_async` still unusable with kwargs** _(Open – 2025-11-25)_  
  The helper now tries to pass `**kwargs` directly into `loop.run_in_executor`, but that coroutine only accepts positional arguments, so any call that supplies layout/framework overrides raises `TypeError: run_in_executor() got an unexpected keyword argument`. The method needs to wrap `self.render_form_from_model` in `functools.partial` (or build a small closure) before dispatching to the executor so keywords survive the handoff.  
  _Files: `pydantic_forms/enhanced_renderer.py`_

- **Renderer instances keep mutable request-scoped state** _(Open – 2025-11-23)_  
  `_render_field` still lazily creates a `RenderContext` by reading `self._current_form_data` / `_schema_defs`, which are mutated per request on the renderer singleton. Concurrent requests can stomp on one another’s state and leak user data. The renderer needs to pass context explicitly rather than reaching back into shared attributes.  
  _Files: `pydantic_forms/enhanced_renderer.py`, `pydantic_forms/simple_material_renderer.py`_

- **Side-by-side layout crashes with extra arguments** _(Resolved – 2025-11-25)_  
  The duplicate `_render_side_by_side_layout` definition was removed and all callers now route through `LayoutEngine.render_side_by_side_layout`, which composes rows via the shared `FlexHorizontalLayout`. Layout rendering no longer raises `TypeError` and the markup stays consistent with other BaseLayout-powered sections.  
  _Files: `pydantic_forms/enhanced_renderer.py`, `pydantic_forms/rendering/layout_engine.py`_

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
  `pydantic_forms/enhanced_renderer.py` and `pydantic_forms/simple_material_renderer.py` contain renderer configuration, layout logic, input dispatch, and async helpers in one file. Splitting responsibilities (schema parsing, layout orchestration, input rendering, framework theming) would drastically improve readability and testability. _Progress – 2025-11-25_: shared helpers now live in `pydantic_forms/rendering/schema_parser.py` and `pydantic_forms/rendering/field_renderer.py`, and `EnhancedFormRenderer` delegates per-field rendering to the helper, but layout/model-list code is still inline and the Material renderer has not been updated yet.

- **Multiple layout systems compete**  
  There are two unrelated layout stacks (`pydantic_forms/form_layouts.py` and `pydantic_forms/layouts.py`) plus bespoke layout handling in `EnhancedFormRenderer`. Consolidate around one abstraction (e.g., `BaseLayout`) and have renderers consume it so maintenance effort is not tripled. _Progress – 2025-11-25_: tab, layout-field, and side-by-side rendering now use `ComponentTabLayout` / `FlexHorizontalLayout` / `CardLayout`; `ListLayout` also renders through `FlexVerticalLayout`, but `ListLayout`’s per-item cards and other custom layouts still duplicate markup.

- **Schema handling recomputes per request**  
  Every render call invokes `model_cls.model_json_schema()` and walks the resulting dict. For forms that render frequently, cache the schema + UI metadata per model (perhaps via `functools.lru_cache`) and only clone when necessary to inject request data. _Progress – 2025-11-25_: `build_schema_metadata` now wraps the heavy schema generation in an LRU cache with a reset hook, dramatically reducing the cost for repeated renders of the same `FormModel`. We still rely on callers not to mutate the returned metadata.

- **`templates.py` global cache lacks thread/process coordination** _(Resolved – 2025-11-25)_  
  The cache now uses an `OrderedDict` guarded by an `RLock`, applies LRU-style eviction via `_TEMPLATE_CACHE_MAX`, and the concurrent stress test (32 threads × 2,000 iterations) confirmed stable compilation under contention. Rendering APIs in this container remain stubs, so the follow-up test hammers the compilation/cache path only.  
  _Files: `pydantic_forms/templates.py`, ad-hoc stress harness_

- **Integration helpers include unused/dead code** _(Resolved – 2025-11-25)_  
  The `check_framework_availability` helper now has regression coverage in `tests/test_integration.py::test_missing_framework_handling`, so import-time drift will be caught in CI without keeping unused production wiring around. Other integration utilities remain exercised via the same suite.

- **Model list rendering mixes HTML with data extraction** _(Resolved – 2025-11-25)_  
  `ModelListRenderer` now uses a shared `_render_list` pipeline plus `ModelListTheme` fragments to control framework-specific markup. Bootstrap and Material variants reuse the same iteration, button, and error handling logic, while per-item rendering sets up renderer context correctly (fixing the missing `layout/all_errors` wiring) and switches the Material path to `SimpleMaterialRenderer`.  
  _Files: `pydantic_forms/model_list.py`_

## Testing & Tooling Gaps

- `pytest` is listed in `requirements.txt` but not installed in the dev container; running `pytest` currently fails with `command not found`. Provide a reproducible test command (e.g., `pip install -r requirements.txt && pytest`) or add instructions to the makefile.
- Targeted renderer coverage exists (`tests/test_enhanced_renderer.py`) and now passes, but there is still no CI job or documented workflow confirming the full suite (`pytest tests`). Add a recipe (e.g., `make test`) so contributors can run the same checks locally.
- No regression tests cover the async renderer or model list component. After fixing the issues above, add tests that exercise keyword argument passing and concurrent renders to lock in expected behavior.

## Quick Wins / Follow-Up Tasks

1. ✅ _Done_ — `pyproject.toml` metadata now ships the right package with declared deps.
2. ⏳ _Open_ — Async rendering still bypasses keyword arguments; needs `functools.partial` (or similar) before executor dispatch.
3. ⏳ _Open_ — `_RenderContext` is not actually threaded through; renderer continues mutating shared attributes per request.
4. ✅ _Done_ — Unified `BaseInput` implementation.
5. ✅ _Done_ — Select/multiselect widgets honor `ui_options` metadata and multi-value attrs, preventing regressions in renderer coverage.
6. ✅ _Done_ — File input preview template no longer throws `NameError`, so specialized inputs render in Bootstrap.
7. ⏳ _Open_ — Still multiple layout stacks; consolidate to reduce maintenance.
8. ✅ _Done_ — Added an LRU cache for `build_schema_metadata`, plus a manual reset helper for tests/hot reload.
9. ✅ _Done_ — Deduplicated `_render_side_by_side_layout`; layout rendering now flows through `LayoutEngine` and the shared BaseLayout components.

These changes will reduce runtime bugs, lower maintenance overhead, and make it easier to add additional frameworks or inputs without duplicating logic across the codebase.
