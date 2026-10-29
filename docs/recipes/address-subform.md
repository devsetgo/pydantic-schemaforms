# Shipping and Billing Addresses

One `Address` model, used for both the shipping and the billing address. The
billing address is optional: it's only needed when it differs.

```python title="models.py"
--8<-- "docs_src/recipes/address_subform/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/address_subform/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/address_subform/flask_app.py"
    ```

## How it works

- **The same model, twice.** Each field gets its own section with its own
  inputs (`shipping.city`, `billing.city`), and errors are reported under the
  right one.
- **`billing: Address | None`** is an optional sub-form. Its inputs aren't
  required in the browser, and when it comes back blank (or still at its
  defaults, such as the country), `validate()` returns `None` for it. As soon
  as the user fills in part of it, the whole sub-form is checked.
- **`ui_collapsed=True`** starts the billing section folded away. It opens by
  itself when it contains an error.
- **The model validator** asks for a billing address only when the box is
  unticked, and its message is shown at the top of the form.
- **`result.instance`** is the validated `CheckoutForm` object, so the route
  can call `billing_address()` on it.
