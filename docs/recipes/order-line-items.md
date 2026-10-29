# Order with Line Items

An order with any number of lines, each with a product, a quantity and a unit
price, and a total worked out on the server.

```python title="models.py"
--8<-- "docs_src/recipes/order_line_items/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/order_line_items/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/order_line_items/flask_app.py"
    ```

## How it works

- **`list[LineItem]`** is a repeating sub-form with an "Add a line" button.
  `min_length=1` means the form starts with one empty line and can't be sent
  with none; `max_length=50` caps it.
- **`ui_item_title_template="{product}"`** titles each line's card with its
  product as the user types it.
- **`ui_element="currency"`** shows the price as `$1,012.50` while the user
  types. The symbol and separators are removed before validation, so the
  field is still a `Decimal`.
- **`@computed_field` `total`** isn't an input: it's worked out from the
  validated line, so the route never trusts a total sent by the browser.
- **Errors name the line.** A bad price on the second line shows under that
  input, and in the summary as "Item #2 — Unit Price: ...".
