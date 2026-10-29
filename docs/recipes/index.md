# Recipes

Complete forms for common jobs. Each one is a working app: copy the model and
the routes, run it, and change what you need. They assume you've read the
[Tutorial](../tutorial/index.md); each recipe explains only what is new.

| Recipe | What it shows |
|---|---|
| [Contact Form](contact-form.md) | A `Literal` dropdown, a text area and a honeypot against spam bots |
| [Login and Registration](login-registration.md) | Password fields, a matching confirmation, a required "accept the terms" box, and errors your route adds after validation |
| [Edit Form from a Database Row](edit-form.md) | Pre-filling a form from saved data and saving the changes |
| [Shipping and Billing Addresses](address-subform.md) | One sub-form model used twice, and an optional sub-form |
| [Order with Line Items](order-line-items.md) | A repeating sub-form with a computed total and currency input |
| [File Upload](file-upload.md) | A file input, and checking the file's type and size |
| [Multi-Step Application (Wizard)](wizard-application.md) | A job application split into steps |
| [Settings with a Code Field](settings-code-field.md) | JSON and TOML text areas with formatting, checked by validators |
| [Embedding in a Jinja Template](jinja-template.md) | Putting the form inside your own page template |

To import a CSV file into an editable, validated table, see
[Data Tables](../advanced/data-tables.md); its last section is a complete app.
