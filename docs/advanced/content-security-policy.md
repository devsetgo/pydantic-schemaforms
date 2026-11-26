# Content-Security-Policy

## In plain English

A web page can contain small programs (scripts) and style rules. Most of
them are yours, but if an attacker ever manages to slip text into your page,
say through a comment box that wasn't escaped properly, the browser can't
tell their script from yours. It runs both. This is called cross-site
scripting (XSS).

A **Content-Security-Policy (CSP)** is a list of rules your server sends with
each page, telling the browser which scripts and styles it may run. Anything
not on the list is blocked, even if an attacker got it into the page.

The strictest useful rule is a **nonce**: a random password your server
makes up fresh for every page it sends. Your own scripts carry it, like a
wristband at an event. Injected scripts don't know this page's password, so
the browser turns them away. A new page gets a new nonce, so an attacker
can't reuse an old one.

**What the library does for you:** every script and style it puts in a form
wears your nonce, and it never uses the two habits a strict policy forbids:
code inside HTML attributes (`onclick="..."`) and inline `style="..."`
attributes. You tell it the nonce once per request, and every form, error
page, wizard step and review page on that request gets it.

**Do you need this?** If your site already sends a `Content-Security-Policy`
header, or a security review asks you to, yes. If not, your forms work
without it. Adding one is a good defense to have even though the library
already escapes everything it writes.

## The technical version

A policy that allows only nonced tags looks like this:

```text
Content-Security-Policy: script-src 'nonce-r4nd0m'; style-src 'nonce-r4nd0m'
```

The browser then runs a `<script>` or applies a `<style>` only when it has
`nonce="r4nd0m"`, the value in this response's header. It blocks:

- any `<script>` or `<style>` without the nonce;
- inline event handlers such as `onclick="..."`, nonce or not;
- `style="..."` attributes, even empty ones;
- `eval()` and `new Function()`.

Forms render under this policy with nothing blocked. You don't need
`'unsafe-inline'` or `'unsafe-eval'`, which would switch the protection off.

## Adding a CSP to a site, step by step

The same steps work for a new site and for one that already has a policy.

### 1. Make a nonce for each request

Use a random, unguessable value, new for every response:
`secrets.token_urlsafe(16)`. The nonce must be base64 or base64url, which
that is. Never reuse one across responses or users.

### 2. Hand it to the library, once

Open `csp_nonces()` around the request, in the same middleware that makes
the nonce. Everything rendered, validated or re-rendered during that
request then gets it, with no change to your routes.

```python title="models.py"
--8<-- "docs_src/advanced/content_security_policy/models.py"
```

=== "FastAPI"

    ```python title="main.py" hl_lines="13-20"
    --8<-- "docs_src/advanced/content_security_policy/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py" hl_lines="13-28"
    --8<-- "docs_src/advanced/content_security_policy/flask_app.py"
    ```

The error page from `render_with_errors()` and a saved wizard step from
`validate_step().render()` get the nonce the same way. So do
`render_display()`, `LiveValidator.render_htmx_script()` and the async
renderers.

### 3. Put the nonce on your own tags

The library only nonces what it writes. Your page templates need it too:

```html
<script nonce="{{ request.state.csp_nonce }}">...</script>
<style nonce="{{ request.state.csp_nonce }}">...</style>
```

In your own templates, also move any `onclick="..."` into a script that
calls `addEventListener`, and any `style="..."` into a class in your
stylesheet. A `<script src="...">` from your own site needs the nonce too,
or `'self'` in `script-src`.

### 4. If you use HTMX, give it the nonce

HTMX re-creates the `<script>` tags in each piece of page it swaps in, and
runs them only if they carry the page's nonce. Tell it the nonce before
`htmx.min.js` loads:

```html
<meta name="htmx-config"
      content='{"inlineScriptNonce": "{{ nonce }}", "inlineStyleNonce": "{{ nonce }}"}'>
```

`inlineStyleNonce` covers the small stylesheet HTMX adds for its loading
indicators.

### 5. Try it in report-only mode first

Send the policy as `Content-Security-Policy-Report-Only` for a while. The
browser then reports what it *would* block in its developer console
("Refused to execute inline script...") but blocks nothing, so you can find
the tags you missed without breaking the site. Load each page, submit each
form once with a mistake, and read the console.

### 6. Switch it on

When the console stays clean, rename the header to
`Content-Security-Policy`. Keep a test that loads your main pages and fails
on a `securitypolicyviolation` event, so a new tag without the nonce is
caught before it ships. This library's own example app does exactly that.

## Replacing a workaround

Before the library supported nonces, sites under a strict policy had to
work around it. If your site does one of these, replace it with steps 2 to 4
above and delete the workaround:

| Workaround | Why to remove it |
|---|---|
| Rewriting the rendered HTML with a regular expression to add `nonce="..."` | Fragile, and it can't fix `onclick=` or `style=` attributes, which the library no longer writes |
| `'unsafe-inline'` in `script-src` or `style-src` | It turns the protection off for every script on the page |
| `'unsafe-hashes'` or a list of script hashes | The library's scripts change between releases, so the hashes go stale |
| Passing `script_nonce=` to every render call | Easy to miss one, such as the error page from `render_with_errors()`; `csp_nonces()` covers the whole request |

## Reference

### Or pass the nonce to each call

Every render function also takes the nonce directly, which suits a single
page or a script outside a web request:

```python
html = ContactForm.render_form(submit_url='/contact', script_nonce=nonce, style_nonce=nonce)
result = ContactForm.validate(form, submit_url='/contact', script_nonce=nonce, style_nonce=nonce)
```

Pass it to `validate()` and `validate_step()` as well, because the error
page they render later reuses it. A nonce that isn't base64 or base64url
raises `ValueError`.

### Field styles

A field's `ui_style="font-weight: 600"` keeps working under the policy.
While a style nonce is set, the library puts that style in a stylesheet of
its own that carries the nonce, instead of a `style` attribute the policy
would block. `ui_style` holds declarations only, so it can't contain `{`,
`}` or `<`.

### What never gets the nonce

- Anything you put in a content block with `ui_content=html(t'...')`. A
  `<script>` there is never given the nonce, so if untrusted text ever
  reached it, the policy would still block it.
- A script you render once at import, such as
  `LiveValidator.render_htmx_script()` stored in a module-level variable. It
  was made before any request existed. Render it per request instead.
- The older layout classes (`ModalLayout(style=...)` and similar) rendered
  on their own, outside a form, still write a `style` attribute.

### HTML comment markers

Each form is wrapped in `<!--- Start/End Pydantic-SchemaForms -->` comments
by default. A CSP doesn't cover comments. If your site doesn't allow HTML
comments in its output, pass `include_html_markers=False`.

### Troubleshooting

| What you see | Cause and fix |
|---|---|
| Console: "Refused to execute inline script" pointing at your template | A tag in your own template lacks `nonce=`; add it (step 3) |
| Console: the same, pointing at a form's script | The form was rendered outside `csp_nonces()`, or at import time; render it inside the request |
| A form works, but its error page breaks | The nonce was passed to `render_form()` but not to `validate()`; use `csp_nonces()` |
| HTMX swaps work, but scripts in the swapped part don't run | The `htmx-config` meta tag is missing (step 4) |
| `ValueError` naming the nonce | It isn't base64 or base64url; use `secrets.token_urlsafe(16)` |
