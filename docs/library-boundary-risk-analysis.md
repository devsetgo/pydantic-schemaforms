# Library Boundary & Security Risk Analysis

## Context

Your stated rule is:

- The library renders and validates forms.
- The application owns endpoint routing and submission destinations.
- The library must not make app-specific assumptions.

This is aligned with secure framework design:

1. **App layer decides trust boundaries** (routes, auth, tenancy, CSRF policy).
2. **Library layer stays generic** (rendering, schema parsing, model validation).

---

## Issue 1: App-specific special case in core

**Location:** `pydantic_schemaforms/rendering/layout_engine.py` (`field_name == "comprehensive_tabs"` branch)

### Why this is risky

The core library now contains behavior tied to one example form field name (`comprehensive_tabs`).

That causes:

- **Coupling to demo/app internals:** core behavior depends on one specific field naming convention.
- **Hidden precedence rules:** data can be reshaped unexpectedly when that key appears.
- **Non-obvious behavior for consumers:** users with similarly named fields may get unintended transformations.
- **Maintenance drift:** adding more app-specific exceptions scales badly and becomes fragile.

### Security angle

This is more of an **architectural boundary risk** than a direct exploit by itself.

However, implicit reshaping in core can become security-relevant when:

- validation and authorization logic in apps assumes a different input shape,
- field-level allowlists/denylists are bypassed by transformation order,
- audit logs capture transformed payloads that no longer match incoming data.

### Recommended direction

Remove hardcoded field-name logic from core and replace with one of:

- **Schema-driven generic resolution** (preferred): detect layout fields by metadata (`ui_element/layout`) and resolve nested values generically.
- **Pluggable hook**: app can register a resolver for custom field mapping.
- **No implicit mapping**: require input to already match model shape; apps perform mapping explicitly.

### Decision tradeoff

- **Generic schema-driven core** gives best developer experience with minimal policy risk.
- **Explicit app mapping** gives strongest predictability and least surprise.

---

## Issue 2: Preserving unknown submitted keys in validated output

**Location:** `pydantic_schemaforms/validation.py` around unknown-key preservation

### Why this is risky

The current behavior appends keys from raw input if they are not part of validated model output.

This can leak unvalidated transport fields into the final `result.data` payload.

### Concrete failure modes

1. **Data contamination**
   - Output looks validated but includes non-model keys.
   - Downstream code may trust all keys in the payload.

2. **Privilege/flag smuggling**
   - Attackers can include fields like `is_admin`, `role`, `tenant_id`, `approved`, etc.
   - Even if model ignores them, preservation reintroduces them into the final payload.

3. **Mass assignment risk in follow-on layers**
   - If downstream persistence uses broad dict writes, unknown keys may be persisted or acted upon.

4. **Audit ambiguity**
   - “Validated data” is no longer strictly validated model data.

### Security severity

This is a **real security concern** in multi-layer systems where consumers assume validated output is safe.

Severity depends on what downstream does, but the default should be conservative.

### Recommended direction

Default policy should be:

- **Return only model-shaped validated data**.
- Do **not** merge unknown keys into validated output.

If compatibility is needed, use explicit opt-in modes:

- `strict` (default): model-only output.
- `include_raw_extra` (opt-in): include unknowns under a separate namespace, e.g. `_extra`.

This preserves debuggability without contaminating trusted data.

---

## Related Principle: Submit destination ownership

You noted: sending `?style={style}` in `submit_url` is app-owned and acceptable.

Agreed. The key security principle:

- Library may render whatever `submit_url` the app passes.
- Library must **not infer or auto-construct submission routes** beyond safe defaults.
- Library defaults should be inert (`/submit`), explicit, and overridable.

This keeps route ownership with the application and avoids accidental data exfiltration paths.

---

## Suggested policy decisions

Choose one policy set and apply consistently:

### Option A (recommended)

- Remove app-specific hardcoded mappings from core.
- Keep only generic schema-driven layout behavior.
- Return only validated model-shaped output.
- If extras are needed, expose separately (e.g. `_extra`) via opt-in.

### Option B (compatibility-first)

- Keep current behavior behind feature flags.
- Default to secure behavior for new users.
- Offer migration period for legacy apps.

---

## Migration plan (low risk)

1. Add a validation output policy setting with default `strict`.
2. Deprecate unknown-key merge behavior with warning.
3. Remove `comprehensive_tabs` special case and replace with generic resolver.
4. Add tests covering:
   - no app-specific field-name assumptions,
   - unknown key handling under strict/compat modes,
   - nested layout payload correctness.

---

## Bottom line

Both flagged items are valid concerns.

- The hardcoded `comprehensive_tabs` branch violates library/app separation.
- Unknown key preservation can blur trust boundaries and create security risk.

If your goal is a secure, framework-grade library contract, **Option A** is the safer long-term decision.
