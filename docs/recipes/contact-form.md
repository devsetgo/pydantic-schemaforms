# Contact Form

A contact form with a topic, a message and a hidden trap for spam bots.

```python title="models.py"
--8<-- "docs_src/recipes/contact_form/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/contact_form/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/contact_form/flask_app.py"
    ```

## How it works

- **`topic: Literal[...]`** becomes a dropdown of the three topics, with
  "Question" selected by default.
- **`max_length=2000`** on the message limits it in the browser and on the
  server.
- **`ui_element="honeypot"`** renders a text box that people can't see or
  tab to, but bots that fill in every input will. When it comes back filled
  in, the route answers as if the message was sent and drops it, so the bot
  learns nothing.

A honeypot stops simple bots. For more, add a `captcha` field; see
[Input Types](../reference/inputs.md).
