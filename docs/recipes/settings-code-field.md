# Settings with a Code Field

A settings form where part of the settings is JSON, TOML or a script, typed
into a text area with syntax highlighting and a Format button, and checked on
the server.

```python title="models.py"
--8<-- "docs_src/recipes/settings_code_field/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/settings_code_field/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/settings_code_field/flask_app.py"
    ```

## How it works

- **`ui_options={"language": ...}`** turns a text area into a small code
  editor: highlighting, Tab to indent, and a Format button. It's still a plain
  `<textarea>`, so it works without JavaScript.
- **The languages** are `json`, `yaml`, `toml`, `bash` and `python`. JSON,
  YAML and TOML are really reformatted. Bash and Python only get their
  whitespace cleaned up, and the button says so.
- **The validators parse the text** and turn a parse error into a message
  under the field. The browser's Format button already flags bad JSON, but
  only the server check counts.
- **`code_highlight=False`**, `code_format=False` and `code_tab_indent=False`
  turn off each part; `indent_size` sets the indent (default 2).

The value stays a string. Parse it again where you use it, as the route does,
or add a second field typed as a model if you want the parsed data validated
field by field.
