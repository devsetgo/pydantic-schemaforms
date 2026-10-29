# Forms Built at Runtime

Usually a form is a class you write. When the fields are only known while the
app runs, for example an admin screen where staff design a survey, or fields
stored in a database, build the `FormModel` class with Pydantic's
`create_model()`. The result is an ordinary `FormModel`: it renders,
validates and re-renders errors exactly like a class you wrote.

```python
--8<-- "docs_src/advanced/runtime_forms/feedback.py"
```

- `__base__=FormModel` makes the new class a form.
- Each field is a `(type, Field(...))` pair, with the same `Field()` settings
  as anywhere else: `title`, `ui_element`, constraints, `ui_options`.
- `...` as the default makes a field required.
- Build each class once, when the definition changes, rather than on every
  request: Pydantic does real work to create a model.

Treat stored field definitions as untrusted input if users can edit them:
choose the type and `ui_element` from a list you control, rather than
passing stored strings straight through.

!!! note "Coming: JSON Schema import"
    Building a form straight from a JSON Schema document is planned
    ([#235](https://github.com/devsetgo/pydantic-schemaforms/issues/235)).
    Until then, `create_model()` is the way to build a form at runtime.
