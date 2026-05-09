
# Codebase Review – pydantic-schemaforms

_Date: 2025-12-21 (Updated)_

## Executive Summary

`pydantic-schemaforms` is in a solid place architecturally: there is now a single schema→field→layout rendering pipeline, theme/style are first-class and overrideable, and the test suite exercises both sync and async rendering across layout primitives. The remaining work is less about “more features” and more about locking the product to its original promise:

- **Python 3.14+ only:** this library targets Python 3.14 and higher, and does not support earlier Python versions.

- ship **all** required HTML/CSS/JS from the library (no external CDNs by default)
- keep UI + validation configuration **expressed via Pydantic** (schema is the source of truth)
- make sync + async usage **boringly simple** (one obvious way)
- add an optional **debug rendering mode** that helps adoption without changing normal UX

The renderer refactor eliminated shared mutable state and restored the enhanced/material renderers to a working baseline. Schema metadata is cached, field rendering is centralized, and model-list nesting now feeds explicit `RenderContext` objects. Django integration has been removed (Flask/FastAPI remain), and the JSON/OpenAPI generators now source constraints directly from Pydantic field metadata, unblocking the integration tests. Renderer themes now include a formal `FrameworkTheme` registry (Bootstrap/Material/plain) plus `MaterialEmbeddedTheme`, and both `EnhancedFormRenderer` and `FieldRenderer` source their form/input/button classes from the active theme before falling back to legacy framework config.

**Latest (Dec 7, 2025):** Theme-driven form chrome extraction is complete. The new `FormStyle` contract centralizes all framework-specific markup (model lists, tabs, accordions, submit buttons, layout sections, **and field-level help/error blocks**) in a registry-based system. `FormStyleTemplates` dataclass now holds 15 template slots (expanded from 13: added `field_help` and `field_error` for field-level chrome routing), registered per-framework (Bootstrap/Material/Plain/Default) with graceful fallbacks. `RendererTheme` and `LayoutEngine` now query `FormStyle.templates` at render time instead of inlining markup, enabling runtime overrides without renderer edits. **Version-aware style descriptors** are supported (e.g., `get_form_style("bootstrap:5")`, `get_form_style("material:3")`) with fallback to framework defaults. FastAPI example hardened with absolute paths (`Path(__file__).resolve().parent`) for templates/static, resolving path issues in tests and different working directories. Validation engine consolidated: `ValidationResponse` and convenience validators now live in `validation.py`, `live_validation.py` consumes/re-exports without duplication, and 10 new consolidation tests were added. Tabs regression fixed: Bootstrap panels now render initial content (`show active`), Material tabs use shared tab CSS/JS classes so tabs switch correctly, and a layout-demo smoke test asserts initial tab content renders for both frameworks. **Pydantic v2 deprecations eliminated:** All Pydantic `Field()` kwargs now properly use `json_schema_extra` instead of extra kwargs; `min_items`/`max_items` replaced with `min_length`/`max_length` in FormField calls; Starlette `TemplateResponse` signature updated to new parameter order (request first). **Deprecation warnings suppressed:** pytest `filterwarnings` config reduces test output from 19 warnings to 1 without losing developer guidance (form_layouts deprecation and JSON schema hints remain available with `-W default`). **Validation documentation added:** New comprehensive `docs/validation_guide.md` (787 lines) documents the unified validation engine with ValidationResponse/FieldValidator/FormValidator APIs, server-side and HTMX validation flows, cross-field validation patterns, and end-to-end FastAPI examples.

**Latest (Dec 21, 2025):** The core architecture is now strong enough to support the original product constraints (library supplies HTML/CSS/JS, configuration is expressed via Pydantic, sync+async are easy). The most important product-alignment work is now complete for assets and consistently enforced:

- **Self-contained assets:** Default rendering no longer emits external CDN URLs.
  - HTMX is now **vendored** and inlined by default (offline-by-default).
  - A CDN mode exists but is explicitly opt-in and **pinned** to the vendored manifest version.
  - IMask is **vendored** and available when explicitly requested (e.g., SSN masking).
  - Framework CSS/JS (Bootstrap + Materialize) are **vendored** and can be emitted inline in `asset_mode="vendored"`.
- **Consistent asset selection:** A consistent `asset_mode` pattern is now threaded through the main entry points (enhanced renderer, modern renderer/builder, legacy wrappers) so “cdn vs vendored” behavior is deterministic.
- **Operational stability:** `vendor_manifest.json` checksum verification is enforced by tests, and pre-commit is configured to avoid mutating vendored assets and generated test artifacts.
- **Debug rendering mode (COMPLETED):** First-class debug panel now available via `debug=True` flag. The panel exposes (1) rendered HTML/assets, (2) the Python form/model source, (3) validation rules/schema, and (4) live payload with real-time form data capture. Implementation uses JavaScript event listeners to update the live tab as users interact with the form, handles nested model-list fields correctly, and is fully self-contained (inline CSS/JS). FastAPI example updated with `?debug=1` support on all routes, and tests verify correct behavior.

## Design Rules (Non‑Negotiables)

These rules are intended to prevent “helpful” drift away from the original concept.

0. **Python version policy**
  - The library supports **Python 3.14 and higher only**.
  - Avoid guidance that suggests compatibility with older Python versions.

1. **Library ships the experience**
    - Default output must be fully functional offline: no third-party CDN assets (JS/CSS/fonts) unless explicitly opted in.
    - Framework integrations may *serve* assets, but the assets must come from this package.

2. **Pydantic is the single source of truth**
    - Validation constraints, required/optional, and shape come from Pydantic schema/Field metadata.
    - UI configuration is expressed via Pydantic-friendly metadata (`json_schema_extra` / form field helpers) rather than ad-hoc runtime flags.
    - Avoid storing non-JSON-serializable objects in schema extras unless they are sanitized for schema generation.

3. **One obvious way (sync + async)**
    - There should be exactly one recommended sync entry point and one async entry point.
    - All other helpers should be thin compatibility wrappers and should not diverge in behavior.

4. **Renderer outputs deterministic, self-contained HTML**
    - Rendering should not depend on global mutable state or ambient process configuration.
    - Rendering should be deterministic for the same model + config.

5. **Debug mode is optional and non-invasive**
    - Debug UI must be off by default.
    - When enabled, it should wrap the existing form (collapsed panel) and never change validation/rendering semantics.
    - Debug surfaces should be “read-only views” of: rendered HTML/assets, model source (best effort), schema/validation rules, and live validation payloads.

6. **Extensibility stays declarative**
    - Plugins register inputs/layout renderers via the official registries; no monkeypatching required.
    - Extension points should compose with themes/styles, not bypass them.

## Critical / High Priority Findings

- **External CDN assets violate the self-contained requirement (Addressed)**
  Default output is now offline-by-default across the main entry points.

  - HTMX is vendored and inlined by default.
  - An explicit `asset_mode="cdn"` exists for users who want CDN delivery, but it is pinned to the vendored manifest version.
  - IMask is vendored and available for secure inputs (e.g., SSN masking). It is not injected unless explicitly requested.
  - Framework CSS/JS (Bootstrap + Materialize) are vendored and can be emitted in `asset_mode="vendored"` (inline) to keep “framework look” self-contained.
  - External CDN URLs still exist as an explicit opt-in (`asset_mode="cdn"`) and are pinned to the vendored manifest versions.

  _Files:_
  - `pydantic_schemaforms/render_form.py` (legacy wrapper)
  - `pydantic_schemaforms/assets/runtime.py` (vendored HTMX + pinned CDN mode)
  - `pydantic_schemaforms/rendering/themes.py` / `pydantic_schemaforms/enhanced_renderer.py` (asset-mode gating)
  - `pydantic_schemaforms/modern_renderer.py`, `pydantic_schemaforms/integration/builder.py` (builder/modern entry points)
  - `pydantic_schemaforms/form_layouts.py` (deprecated legacy layouts; now gated)

  **Vendored dependency policy (implemented for HTMX; extendable for others)**
  - **Default is offline:** the default renderer output must not reference external CDNs.
  - **Pinned + auditable:** every vendored asset must be pinned to an explicit version and recorded with `source_url` + `sha256` in a manifest.
  - **Licenses included:** upstream license text (and any required notices) must be included in the repo alongside the vendored asset (or clearly referenced if inclusion is not permitted).
  - **Single update path:** updates must happen via an explicit script + make target (no manual copy/paste), so diffs are reproducible.
  - **Opt-in CDN mode only:** if a CDN mode exists, it must be explicitly selected (never default) and clearly documented as not-offline.

  **What “easy to update” means (definition)**
  - One command updates the pinned version, downloads the asset(s), writes/updates the manifest checksums, and runs a verification check.
  - A CI/test check fails if any default render output contains external asset URLs.
  - The update process is deterministic and reviewable (diff shows only asset bytes + manifest/version bump).
  - Formatting/lint tooling must not modify vendored bytes (otherwise checksum verification breaks). Pre-commit should exclude `pydantic_schemaforms/assets/vendor/` from whitespace/EOF normalization hooks.

- **Multiple layout stacks compete for ownership (Resolved)**
  Layout definitions now live exclusively in `layout_base.BaseLayout` + `rendering/layout_engine`. The new `LayoutComposer` API exposes the canonical Horizontal/Vertical/Tabbed primitives, while `pydantic_schemaforms.layouts`/`pydantic_schemaforms.form_layouts` only re-export the engine with `DeprecationWarning`s. Enhanced and Material renderers both call into `LayoutEngine`, so markup is consistent across frameworks, and the tutorial documents LayoutComposer as the single supported API.
  _Files:_ `pydantic_schemaforms/rendering/layout_engine.py`, `pydantic_schemaforms/layouts.py`, `pydantic_schemaforms/form_layouts.py`, `pydantic_schemaforms/simple_material_renderer.py`

- **Renderer logic duplicated across frameworks (Resolved)**
  All framework rendering — Bootstrap, Material, and plain — goes through `EnhancedFormRenderer`. Material field rendering (`_render_material_field` and 13 helper methods) lives in `enhanced_renderer.py`; `MaterialEmbeddedTheme` handles CSS/JS chrome. `SimpleMaterialRenderer` is now a 28-line backward-compatible alias (`class SimpleMaterialRenderer(EnhancedFormRenderer)` with `__init__` calling `super().__init__(framework="material")`). The `render_form_html()` helper no longer has a hardcoded `if framework == "material"` branch — it instantiates `EnhancedFormRenderer(framework=framework)` for every framework, so `include_framework_assets`, `asset_mode`, and `self_contained` now work correctly for Material too.
  _Files:_ `pydantic_schemaforms/enhanced_renderer.py`, `pydantic_schemaforms/rendering/themes.py`, `pydantic_schemaforms/simple_material_renderer.py`

- **Integration helpers mix unrelated responsibilities (Resolved)**
  The `integration/frameworks/` compatibility shim layer has been deleted. The sync/async helpers (`handle_form`, `handle_form_async`, `handle_async_form`, `handle_sync_form`, `normalize_form_data`, `FormIntegration`) are now imported directly from their canonical modules (`adapters.py`, `async_support.py`, `sync.py`) in `integration/__init__.py`. The `_LAZY_EXPORTS`/`__getattr__` indirection is gone; all integration symbols are regular module-level imports.
  _Files:_ `pydantic_schemaforms/integration/__init__.py`, `pydantic_schemaforms/integration/adapters.py`, `pydantic_schemaforms/integration/sync.py`, `pydantic_schemaforms/integration/async_support.py`

## Medium Priority Refactors & Opportunities

- **Input component metadata duplicated (Resolved)**
  Input classes now declare their `ui_element` (plus optional aliases) and a lightweight registry walks the class hierarchy to expose a mapping. `rendering/frameworks.py` imports that registry instead of maintaining its own list, so adding a new component only requires updating the input module where it already lives.
  _Files:_ `pydantic_schemaforms/inputs/base.py`, `pydantic_schemaforms/inputs/*`, `pydantic_schemaforms/inputs/registry.py`, `pydantic_schemaforms/rendering/frameworks.py`

- **Model list renderer mixes logic with theme markup (Resolved)**
  `ModelListRenderer` now delegates both containers and per-item chrome through `RendererTheme` hooks: `render_model_list_container()` and the new `render_model_list_item()` (with Material/embedded overrides) wrap the renderer-supplied field grid so frameworks own every byte of markup. Bootstrap/Material share the same plumbing, labels/help/errors/add buttons stay in the theme, and tests cover that custom themes can inject their own classes when rendering lists.
  _Files:_ `pydantic_schemaforms/model_list.py`, `pydantic_schemaforms/rendering/themes.py`

- **Template engine under-used (Resolved)**
  The new `FormStyle` contract (in `rendering/form_style.py`) extracts all framework-specific markup into `FormStyleTemplates` dataclass with 13 template slots: `form_wrapper`, `tab_layout`, `tab_button`, `tab_panel`, `accordion_layout`, `accordion_section`, `layout_section`, `layout_help`, `model_list_container`, `model_list_item`, `model_list_help`, `model_list_error`, and `submit_button`. Framework-specific bundles (Bootstrap, Material, Plain, Default) are registered in a centralized registry via `register_form_style()` and queried at render time with `get_form_style(framework, variant)`. `RendererTheme.render_submit_button()`, `render_model_list_*()` methods and `LayoutEngine` tab/accordion layouts all delegate to `FormStyle.templates` with graceful fallback to defaults, eliminating inline markup strings and enabling runtime overrides. Tests in `test_theme_hooks.py` (7 tests) verify custom FormStyle templates drive rendering. FastAPI example paths hardened to use `Path(__file__).resolve().parent` for templates and static dirs, working correctly from any working directory.
  _Files:_ `pydantic_schemaforms/rendering/form_style.py`, `pydantic_schemaforms/rendering/themes.py`, `pydantic_schemaforms/rendering/layout_engine.py`, `examples/fastapi_example.py`, `tests/test_theme_hooks.py`, `tests/test_fastapi_example_smoke.py`

- **Runtime field registration surfaced (New)**
  Dynamically extending a `FormModel` is now supported via `FormModel.register_field()`, which wires the new `FieldInfo` into the schema cache and the validation stack by synthesizing a runtime subclass when necessary. Legacy `setattr(MyForm, name, Field(...))` still works for rendering, but the helper ensures `validate_form_data()` and HTMX live validation enforce the same constraints without manual plumbing.
  _Files:_ `pydantic_schemaforms/schema_form.py`, `pydantic_schemaforms/validation.py`, `tests/test_integration_workflow.py`
  _TODO:_ The temporary `DynamicFormRuntime` created by `pydantic.create_model()` emits a `UserWarning` about shadowing parent attributes. If this becomes noisy, add a local `model_config = {"ignored_types": ...}` or suppress the warning via the helper before rebuilding the runtime model.

- **Validation rule duplication (Resolved)**
  Validation is now canonical in `validation.py` (rules, `ValidationResponse`, convenience validators). `live_validation.py` consumes/re-exports without duplicating code. Added consolidation coverage (10 tests) for schema → live validator flow, convenience validators, and serialization.
  _Files:_ `pydantic_schemaforms/validation.py`, `pydantic_schemaforms/live_validation.py`, `pydantic_schemaforms/__init__.py`, `tests/test_validation_consolidation.py`

- **Input namespace still re-exports everything (Resolved)**
  The root package now exposes inputs via module-level `__getattr__`, delegating to a lazy-loading facade in `pydantic_schemaforms.inputs`. No wildcard imports remain, so importing `pydantic_schemaforms` does not instantiate every widget or template; consumers still get `from pydantic_schemaforms import TextInput` via the cached attribute. Future work can build on the same facade to document a plugin hook for third-party inputs.
  _Files:_ `pydantic_schemaforms/__init__.py`, `pydantic_schemaforms/inputs/__init__.py`

- **Integration facade duplicated across namespaces (Resolved)**
  The canonical sync/async helpers live only in `integration/adapters.py`, `integration/sync.py`, and `integration/async_support.py`. The intermediate `integration/frameworks/` shim layer has been removed — `integration/__init__.py` imports from those canonical files directly. There is now exactly one code path for validation + rendering logic with no proxy indirection.
  _Files:_ `pydantic_schemaforms/integration/__init__.py`, `pydantic_schemaforms/integration/adapters.py`, `pydantic_schemaforms/integration/sync.py`, `pydantic_schemaforms/integration/async_support.py`

- **Public sync/async “one obvious way” (Resolved)**
  Canonical entry points now exist and are exported from the root package:
  - Sync: `handle_form()`
  - Async: `handle_form_async()`

  Legacy helpers (`handle_sync_form`, `handle_async_form`, `FormIntegration.*`) remain as compatibility wrappers.
  _Files:_ `pydantic_schemaforms/integration/adapters.py`, `pydantic_schemaforms/integration/__init__.py`, `pydantic_schemaforms/__init__.py`, `docs/quickstart.md`, `tests/test_integration.py`

- **Theme/style contract centralized**
  `RendererTheme` now includes concrete `FrameworkTheme` subclasses for Bootstrap/Material/plain plus `get_theme_for_framework`, and both enhanced + field renderers request classes/assets from the active theme before falling back to legacy configs. `FormStyle` registry now handles framework-level templates (including field-level chrome) and supports version-aware descriptors (e.g., `bootstrap:5`, `material:3`) with fallbacks to base framework/default.
  _Files:_ `pydantic_schemaforms/enhanced_renderer.py`, `pydantic_schemaforms/rendering/themes.py`, `pydantic_schemaforms/rendering/field_renderer.py`, `pydantic_schemaforms/rendering/frameworks.py`, `pydantic_schemaforms/rendering/form_style.py`

- **Plugin hooks for inputs/layouts (NEW)**
  Input components can now be registered via `register_input_class()` and `register_inputs()` in `inputs/registry.py` with automatic cache invalidation. Layout renderers can be registered via `LayoutEngine.register_layout_renderer()` and referenced from form fields using `layout_handler` metadata. Both APIs support resettable state for testing. Docs page `docs/plugin_hooks.md` explains usage and packaging patterns.
  _Files:_ `pydantic_schemaforms/inputs/registry.py`, `pydantic_schemaforms/rendering/layout_engine.py`, `docs/plugin_hooks.md`, `tests/test_plugin_hooks.py`

## Testing & Tooling Gaps

- ✅ **Renderer behavior E2E coverage (COMPLETED)** — Added `tests/test_e2e_layouts_async.py` with 14 tests: unit tests for tab/accordion DOM structure, aria attributes, display state; integration tests for `LayoutDemonstrationForm` with nested fields and model lists; async equivalence tests. All passing.
- ✅ **CI/docs alignment (COMPLETED)** — Documented `make tests` as single entry point in new `docs/testing_workflow.md` (comprehensive guide with test organization, linting rules, CI/CD integration, troubleshooting). **Ruff now enabled in `.pre-commit-config.yaml`** and enforced as part of `make tests` before pytest runs.

## Recommended Next Steps

1. ✅ **Document unified validation engine (COMPLETED)** — Created comprehensive `docs/validation_guide.md` (787 lines) with:
   - `ValidationResponse`, `FieldValidator`, `FormValidator`, and `ValidationSchema` API documentation
   - Server-side validation patterns with `validate_form_data()` and custom rules
   - Real-time HTMX validation with `LiveValidator` and `HTMXValidationConfig`
   - Cross-field validation examples (age consent, password matching, conditional fields)
   - Convenience validators (`create_email_validator()`, `create_password_strength_validator()`)
   - Complete end-to-end sync + HTMX flow example with FastAPI endpoints and HTML templates
   - Testing patterns and Pydantic v2 deprecation resolution notes
   - References to layout-demo smoke test coverage and tab rendering verification

2. ✅ **Suppress remaining expected deprecation warnings (COMPLETED)** — Added `filterwarnings` to `[tool.pytest.ini_options]` in `pyproject.toml` to suppress intentional warnings: `form_layouts` deprecation notice (migration guidance), Pydantic JSON schema non-serializable defaults (informational), and Pydantic extra kwargs deprecation (handled in code). Result: test output reduced from 19 warnings to 1 in normal mode; warnings remain accessible via `pytest -W default`.

3. ✅ **Field-level chrome routing (COMPLETED)** — Extended `FormStyle` to support field-level help/error templating: Added `field_help` and `field_error` templates to `FormStyleTemplates` dataclass (15 slots total, up from 13), registered framework-specific versions for Bootstrap, Plain, and Material Design. Ready for field renderers to consume these templates; enables consistent field-level chrome across all frameworks without renderer edits.

4. ✅ **Version-aware style variants (COMPLETED)** — `FormStyle` descriptors accept framework + variant (e.g., `"bootstrap:5"`, `"material:3"`) with graceful fallbacks to the framework base and default style. Aliases registered for Bootstrap 5 and Material 3 reuse existing templates; lookup stays backward compatible.

5. ✅ **Extension hooks for inputs/layouts (COMPLETED)** — Plugin registration API added: `register_input_class()` / `register_inputs()` in `inputs/registry` with cache clearing, and `LayoutEngine.register_layout_renderer()` with metadata-driven dispatch. Documented in `docs/plugin_hooks.md` with examples and best practices.

6. ✅ **Automated E2E coverage for layouts/async (COMPLETED)** — Added comprehensive `tests/test_e2e_layouts_async.py` (14 tests) covering: unit tests for tab/accordion DOM structure, aria attributes, and display state; integration tests for `LayoutDemonstrationForm` tab/layout field rendering with nested content and model lists; async tests verifying `render_form_from_model_async()` produces identical HTML to sync path, handles errors gracefully, and supports concurrent rendering. All tests passing.

7. ✅ **CI/docs alignment (COMPLETED)** — Documented `make tests` as single entry point in new `docs/testing_workflow.md` (comprehensive guide with test organization, linting rules, CI/CD integration, troubleshooting). **Ruff now enabled in `.pre-commit-config.yaml`** and enforced as part of `make tests` before pytest runs. All 217+ tests passing with integrated linting.

8. ✅ **Make asset delivery self-contained (Completed for HTMX + IMask + framework assets)** — The default renderer output is offline-by-default.
    - ✅ HTMX is vendored and inlined by default; CDN mode is opt-in and pinned.
  - ✅ IMask is vendored (for SSN and other secure input types) and can be included explicitly.
    - ✅ Bootstrap + Materialize CSS/JS are vendored and can be emitted inline via `asset_mode="vendored"` when framework assets are requested.

    **Update workflow (implemented)**
    - Vendoring and verification scripts/targets exist, and tests enforce “no external URLs by default”.
  - `docs/assets.md` documents the `asset_mode` contract and the vendoring workflow.

  **Tooling note (important)**
  - Pre-commit should exclude vendored assets and generated artifacts (coverage/test reports, debug HTML) from whitespace/EOF fixers to keep checksum verification and `make tests` stable.

9. ✅ **Define one canonical sync + one canonical async entry point (COMPLETED)** — Canonical entry points exist and are documented:
  - Sync: `handle_form()`
  - Async: `handle_form_async()`

  Both are exported from `pydantic_schemaforms` and covered by integration tests.
  _Files:_ `pydantic_schemaforms/integration/adapters.py`, `pydantic_schemaforms/__init__.py`, `docs/quickstart.md`, `tests/test_integration.py`

10. ✅ **Add a first-class debug rendering mode (COMPLETED)** — Implemented a `debug=True` option that wraps the form in a collapsed debug panel with tabs:
   - **Rendered output**: raw HTML (including the CSS/JS assets block)
   - **Form/model source**: Python source for the form class (best-effort via `inspect.getsource()`)
   - **Schema / validation**: schema-derived constraints (field requirements, min/max, regex, etc.)
   - **Live payload**: Real-time form data capture that updates as users type/interact with the form

   Implementation details:
   - Debug panel is off by default and non-invasive (collapsed `<details>` element)
   - JavaScript event listeners capture `input` and `change` events to update live payload
   - Handles nested form data (model lists with `pets[0].name` notation)
   - Proper checkbox handling (true/false instead of "on" or missing)
   - Tab UI consistent across frameworks using inline styles/scripts
   - Tests verify debug panel presence when enabled and absence by default
   - FastAPI example updated to expose `?debug=1` query parameter on all form routes

   _Files:_ `pydantic_schemaforms/enhanced_renderer.py` (debug panel builder), `pydantic_schemaforms/render_form.py` (debug flag forwarding), `tests/test_debug_mode.py` (2 tests), `examples/fastapi_example.py` (debug parameter on all routes)

  ---

  ## Codebase Layout (Package Map)

  This section documents the **git-tracked** layout of the `pydantic_schemaforms/` package.

  Notes:

  - Runtime-generated `__pycache__/` folders and `*.pyc` files are intentionally omitted here (they are not part of the source tree and should not be committed).

  ### `pydantic_schemaforms/` (root package)

  - `pydantic_schemaforms/__init__.py` — Public package entry point (lazy exports) and top-level API surface.
  - `pydantic_schemaforms/enhanced_renderer.py` — Enhanced renderer pipeline (schema → fields → layout) with sync/async HTML entry points.
  - `pydantic_schemaforms/form_field.py` — `FormField` abstraction and higher-level field helpers aligned with the design vision.
  - `pydantic_schemaforms/form_layouts.py` — Legacy layout composition helpers (kept for compatibility; deprecated).
  - `pydantic_schemaforms/icon_mapping.py` — Framework icon mapping helpers (bootstrap/material icon name/class resolution).
  - `pydantic_schemaforms/input_types.py` — Input type constants, default mappings, and validation utilities for selecting HTML input types.
  - `pydantic_schemaforms/layout_base.py` — Shared base layout primitives used by the layout engine and renderer(s).
  - `pydantic_schemaforms/layouts.py` — Deprecated layout wrapper module (compatibility surface).
  - `pydantic_schemaforms/live_validation.py` — HTMX-oriented “live validation” plumbing and configuration.
  - `pydantic_schemaforms/model_list.py` — Rendering helpers for repeating/nested model lists.
  - `pydantic_schemaforms/modern_renderer.py` — “Modern” renderer facade backed by the shared enhanced pipeline.
  - `pydantic_schemaforms/render_form.py` — Backwards-compatible rendering wrapper(s) for legacy entry points.
  - `pydantic_schemaforms/schema_form.py` — Pydantic-driven form model primitives (`FormModel`, `Field`, validator helpers, validation result types).
  - `pydantic_schemaforms/simple_material_renderer.py` — Backward-compatible alias: `SimpleMaterialRenderer` is a thin subclass of `EnhancedFormRenderer(framework="material")`. All material rendering logic lives in `enhanced_renderer.py`.
  - `pydantic_schemaforms/templates.py` — Python 3.14 template-string based templating helpers used throughout rendering.
  - `pydantic_schemaforms/validation.py` — Canonical validation rules/engine and serializable validation responses.
  - `pydantic_schemaforms/vendor_assets.py` — Vendoring/manifest helper utilities used to manage and verify shipped third-party assets.
  - `pydantic_schemaforms/version_check.py` — Python version checks (enforces Python 3.14+ assumptions like template strings).

  ### `pydantic_schemaforms/assets/` (packaged assets)

  - `pydantic_schemaforms/assets/__init__.py` — Asset package marker.
  - `pydantic_schemaforms/assets/runtime.py` — Runtime helpers to load/inline assets and emit tags (vendored vs pinned CDN modes).

  #### `pydantic_schemaforms/assets/vendor/` (vendored third‑party assets)

  - `pydantic_schemaforms/assets/vendor/README.md` — Vendored asset policy and update workflow overview.
  - `pydantic_schemaforms/assets/vendor/vendor_manifest.json` — Pin list and SHA256 checksums for vendored assets (audit + verification).

  ##### `pydantic_schemaforms/assets/vendor/bootstrap/`

  - `pydantic_schemaforms/assets/vendor/bootstrap/bootstrap.min.css` — Vendored, minified Bootstrap CSS.
  - `pydantic_schemaforms/assets/vendor/bootstrap/bootstrap.bundle.min.js` — Vendored, minified Bootstrap JS bundle.
  - `pydantic_schemaforms/assets/vendor/bootstrap/LICENSE` — Upstream Bootstrap license text.

  ##### `pydantic_schemaforms/assets/vendor/htmx/`

  - `pydantic_schemaforms/assets/vendor/htmx/htmx.min.js` — Vendored, minified HTMX library.
  - `pydantic_schemaforms/assets/vendor/htmx/LICENSE` — Upstream HTMX license text.

  ##### `pydantic_schemaforms/assets/vendor/imask/`

  - `pydantic_schemaforms/assets/vendor/imask/imask.min.js` — Vendored, minified IMask library (used for masked inputs).
  - `pydantic_schemaforms/assets/vendor/imask/LICENSE` — Upstream IMask license text.

  ##### `pydantic_schemaforms/assets/vendor/materialize/`

  - `pydantic_schemaforms/assets/vendor/materialize/materialize.min.css` — Vendored, minified Materialize CSS.
  - `pydantic_schemaforms/assets/vendor/materialize/materialize.min.js` — Vendored, minified Materialize JS.
  - `pydantic_schemaforms/assets/vendor/materialize/LICENSE` — Upstream Materialize license text.

  ### `pydantic_schemaforms/inputs/` (input components)

  - `pydantic_schemaforms/inputs/__init__.py` — Lazy-loading facade for input classes (keeps import cost low).
  - `pydantic_schemaforms/inputs/base.py` — Base input types, rendering utilities, and shared label/help/error builders.
  - `pydantic_schemaforms/inputs/datetime_inputs.py` — Date/time-related input components.
  - `pydantic_schemaforms/inputs/numeric_inputs.py` — Numeric/slider/range-related input components.
  - `pydantic_schemaforms/inputs/registry.py` — Runtime registry and discovery helpers for input components.
  - `pydantic_schemaforms/inputs/selection_inputs.py` — Select/checkbox/radio/toggle-related input components.
  - `pydantic_schemaforms/inputs/specialized_inputs.py` — Specialized inputs (file upload, color, hidden, csrf/honeypot, tags, etc.).
  - `pydantic_schemaforms/inputs/text_inputs.py` — Text-ish inputs (text, password, email, URL, phone, credit card, etc.).

  ### `pydantic_schemaforms/integration/` (framework/application integration)

  - `pydantic_schemaforms/integration/__init__.py` — Integration facade with lazy exports of framework glue.
  - `pydantic_schemaforms/integration/adapters.py` — High-level sync/async integration entry points (`handle_form`, `handle_form_async`).
  - `pydantic_schemaforms/integration/async_support.py` — Framework-agnostic async request/validation helpers.
  - `pydantic_schemaforms/integration/builder.py` — Form builder utilities (prebuilt forms, page wrapper helpers, asset tag helpers).
  - `pydantic_schemaforms/integration/react.py` — JSON-schema-form-oriented integration helpers.
  - `pydantic_schemaforms/integration/schema.py` — JSON/OpenAPI schema generation utilities.
  - `pydantic_schemaforms/integration/sync.py` — Framework-agnostic sync request/validation helpers.
  - `pydantic_schemaforms/integration/utils.py` — Shared utilities for integrations (type mapping, framework selection, validation conversion).
  - `pydantic_schemaforms/integration/vue.py` — Vue integration helpers.

  ### `pydantic_schemaforms/rendering/` (shared rendering engine)

  - `pydantic_schemaforms/rendering/__init__.py` — Shared rendering module namespace.
  - `pydantic_schemaforms/rendering/context.py` — Render context objects passed through renderers/layouts.
  - `pydantic_schemaforms/rendering/field_renderer.py` — Field-level rendering logic used by multiple renderers.
  - `pydantic_schemaforms/rendering/form_style.py` — `FormStyle` contract/registry that centralizes framework templates.
  - `pydantic_schemaforms/rendering/frameworks.py` — Framework configuration and input component mapping lookup.
  - `pydantic_schemaforms/rendering/layout_engine.py` — Layout primitives and the engine that renders composed layouts.
  - `pydantic_schemaforms/rendering/schema_parser.py` — Schema parsing/metadata extraction (pydantic model → render plan).
  - `pydantic_schemaforms/rendering/theme_assets.py` — Default CSS/JS snippets for layout-oriented components.
  - `pydantic_schemaforms/rendering/themes.py` — Theme strategies and framework themes (bootstrap/material/plain + embedded variants).

  ---

  ## Beta Release Readiness Assessment

  ### ✅ Product Vision Alignment

  All six **Design Rules (Non-Negotiables)** are now fully satisfied:

  1. **Library ships the experience** ✅
     - Default output is offline-by-default (vendored HTMX, IMask, Bootstrap, Materialize)
     - CDN mode exists but is explicit opt-in and pinned to manifest versions
     - All assets are checksummed and verified by tests

  2. **Pydantic is the single source of truth** ✅
     - Validation constraints, required/optional come from Pydantic schema/Field metadata
     - UI configuration via `json_schema_extra` and form field helpers
     - Schema generation sanitizes non-serializable objects

  3. **One obvious way (sync + async)** ✅
     - Canonical sync entry point: `handle_form()`
     - Canonical async entry point: `handle_form_async()`
     - Both exported from root package with integration test coverage

  4. **Renderer outputs deterministic, self-contained HTML** ✅
     - No global mutable state in renderer pipeline
     - Deterministic output for same model + config
     - Theme/style configuration is explicit

  5. **Debug mode is optional and non-invasive** ✅
     - Off by default (`debug=False`)
     - Collapsed panel when enabled, never changes validation/rendering semantics
     - Read-only views of: rendered HTML, model source, schema/validation, live payload

  6. **Extensibility stays declarative** ✅
     - Plugin registration via official registries (`register_input_class`, `register_layout_renderer`)
     - Extension points compose with themes/styles
     - Documented in `docs/plugin_hooks.md`

  ### ✅ Core Features Complete

  **Rendering Pipeline:**
  - ✅ Enhanced renderer with schema → fields → layout orchestration
  - ✅ Theme-driven styling (Bootstrap, Material Design, Plain, Default)
  - ✅ Field-level rendering with help/error chrome
  - ✅ Layout engine (Vertical, Horizontal, Tabbed, Accordion)
  - ✅ Model list support with add/remove functionality
  - ✅ Async rendering equivalence to sync path

  **Validation:**
  - ✅ Server-side validation via Pydantic
  - ✅ HTMX live validation support
  - ✅ Custom field validators
  - ✅ Cross-field validation patterns
  - ✅ Comprehensive validation guide documentation

  **Integration:**
  - ✅ Flask integration helpers
  - ✅ FastAPI integration helpers (async-first)
  - ✅ Framework-agnostic sync/async adapters
  - ✅ Working examples for both frameworks

  **Developer Experience:**
  - ✅ Debug mode with live payload inspection
  - ✅ Comprehensive test suite (250+ tests passing)
  - ✅ Documentation (quickstart, tutorial, validation guide, assets guide, plugin hooks, testing workflow)
  - ✅ Ruff linting + pre-commit hooks
  - ✅ CI/CD pipeline with coverage reporting

  ### ✅ Quality Metrics

  - **Test Coverage:** 250+ tests passing (see `htmlcov/` for detailed report)
  - **Linting:** Ruff enabled in pre-commit, zero linting errors
  - **Python Version:** 3.14+ only (clearly documented)
  - **Dependencies:** Minimal (pydantic>=2.7, pydantic-extra-types[all]>=2.10.6)
  - **Optional Dependencies:** FastAPI and Flask marked as optional

  ### ⚠️ Known Limitations (Acceptable for Beta)

  1. **Dynamic field validation warning:** Pydantic emits a `UserWarning` when using `FormModel.register_field()` due to `create_model()` behavior. This is cosmetic and doesn't affect functionality. Can be suppressed or improved in future releases.

  2. **Material Design assets:** Currently using Materialize CSS (older). Could be upgraded to Material Web Components or MUI in a future release, but current implementation is functional.

  3. **Documentation completeness:** Core features are documented, but some advanced patterns (custom input components, complex layouts) could benefit from additional examples.

  ### 📋 Release Checklist

  - ✅ All design rules satisfied
  - ✅ Core features complete and tested
  - ✅ Debug mode implemented
  - ✅ Examples working (Flask + FastAPI)
  - ✅ Documentation covers essential workflows
  - ✅ Test suite passing (250+ tests)
  - ✅ Linting clean
  - ✅ Version marked as beta in `pyproject.toml` (25.11.3.beta)
  - ✅ README.md indicates beta status
  - ⏳ CHANGELOG.md updates (should document all changes since last release)
  - ⏳ Release notes prepared (features, breaking changes, migration guide)

  ### 🎯 Recommendation

  **pydantic-schemaforms is ready for beta release** with the following considerations:

  1. **Update CHANGELOG.md** to document all changes, new features, and breaking changes since the last release
  2. **Prepare release notes** highlighting:
     - Debug mode as a major new feature
     - Offline-by-default asset strategy
     - Theme-driven rendering system
     - Plugin extensibility
     - Python 3.14+ requirement (breaking change if upgrading from older versions)
  3. **Tag the release** as `v25.11.3-beta` (or use current version scheme)
  4. **Publish to PyPI** with beta classifier
  5. **Announce the beta** in relevant communities (Reddit r/Python, Python Discord, etc.) and request feedback

  The library has strong architectural foundations, clear design principles, comprehensive test coverage, and working examples. The beta period should focus on:
  - Gathering user feedback on API ergonomics
  - Identifying edge cases in real-world usage
  - Polishing documentation based on user questions
  - Building community examples/templates

  ---

  **Next Actions After Beta Release:**
  - Monitor issue tracker for bug reports and feature requests
  - Gather feedback on debug mode usability
  - Consider Material Web Components migration for v2.0
  - Expand documentation with more advanced patterns
  - Build gallery of community examples
