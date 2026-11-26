# Content-Security-Policy

A Content-Security-Policy (CSP) header tells the browser which scripts and
styles a page may run. The strictest useful policy allows only tags that
carry a fresh random **nonce** for each response:

```text
script-src 'nonce-r4nd0m'; style-src 'nonce-r4nd0m'
```

Forms render under this policy with nothing blocked. You don't need
`'unsafe-inline'` or `'unsafe-eval'`. The library writes no inline event
handlers (`onclick=`) and no `style="..."` attributes of its own. Every
`<script>` and `<style>` it writes takes your nonce.

## Give the library your nonce once per request

Your app already creates the nonce and sends the header. Open
`csp_nonces()` around the request with that nonce. Every form rendered,
validated or re-rendered during the request then gets it, with no change to
your routes.

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

### Or pass it to each call

Every render function also takes the nonce directly, which suits a single
page or a script outside a web request:

```python
html = ContactForm.render_form(submit_url='/contact', script_nonce=nonce, style_nonce=nonce)
result = ContactForm.validate(form, submit_url='/contact', script_nonce=nonce, style_nonce=nonce)
```

Pass it to `validate()` and `validate_step()` as well, because the error
page they render later reuses it. A nonce must be a base64 or base64url
token, such as one from `secrets.token_urlsafe(16)`; anything else raises
`ValueError`.

## Field styles

A field's `ui_style="font-weight: 600"` keeps working under the policy.
While a style nonce is set, the library puts that style in a stylesheet of
its own that carries the nonce, instead of a `style` attribute the policy
would block. `ui_style` holds declarations only, so it can't contain `{`,
`}` or `<`.

## What still needs your nonce

The library only adds the nonce to tags it writes. Add it yourself to:

- the `<script>` and `<style>` tags in your own page templates, for example
  `<script nonce="{{ request.state.csp_nonce }}">` in Jinja;
- anything you put in a content block with `ui_content=html(t'...')`. A
  `<script>` there never gets the nonce, so if untrusted text ever reached
  it, the policy would still block it.

Keep a script you render once at import, such as
`LiveValidator.render_htmx_script()`, out of module scope. Render it per
request, so it picks up that request's nonce.

## HTMX

HTMX re-creates the `<script>` tags in a fragment it swaps in, and runs them
only with the page's nonce. The fragment's own nonce came from a different
response, so it doesn't count. Give HTMX the page's nonce, before
`htmx.min.js` loads:

```html
<meta name="htmx-config"
      content='{"inlineScriptNonce": "{{ nonce }}", "inlineStyleNonce": "{{ nonce }}"}'>
```

`inlineStyleNonce` covers the small stylesheet HTMX adds for its loading
indicators.

## HTML comment markers

Each form is wrapped in `<!--- Start/End Pydantic-SchemaForms -->` comments
by default. CSP doesn't cover comments. If your site doesn't allow HTML
comments in its output, pass `include_html_markers=False`.
