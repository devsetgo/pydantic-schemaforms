from models import live_validator

from pydantic_schemaforms import SafeHTML, html

VALIDATOR_SCRIPT = SafeHTML(live_validator.render_htmx_script())


def page(form_html: str) -> str:
    form = SafeHTML(form_html)  # trusted HTML from the library
    return html(t"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Contact</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <script src="https://unpkg.com/htmx.org@2.0.7"></script>
  {VALIDATOR_SCRIPT}
</head>
<body>
  <main class="container my-5">
    {form}
    <div id="name-feedback" aria-live="polite"></div>
    <div id="email-feedback" aria-live="polite"></div>
  </main>
</body>
</html>""")


def feedback(errors: list[str]) -> str:
    if not errors:
        return html(t'<span class="text-success">Looks good</span>')
    message = '; '.join(errors)  # may echo what the user typed: html() escapes it
    return html(t'<span class="text-danger">{message}</span>')
