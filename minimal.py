from pydantic import Field, model_validator

from PySchemaForms.render_form import SchemaFormValidationError
from PySchemaForms.schema_form import FormModel


class MinimalSchemaModel(FormModel):
    userName: str = Field(
        ...,
        alias="userName",
        description="Choose a username (at least 3 characters).",
        min_length=3,
        ui_autofocus=True,
    )
    password: str = Field(
        ...,
        alias="password",
        description="Password must be at least 8 characters and include 1 uppercase letter, 1 number, and 1 special character.",
        min_length=8,
        ui_element="password",
    )
    password_repeat: str = Field(
        ...,
        alias="passwordRepeat",
        description="Re-enter your password. Must match the password above.",
        title="Repeat Password",
        ui_element="password",
    )
    biography: str = Field(
        ...,
        alias="biography",
        description="Write a short biography.",
        title="Biography",
        min_length=1,
        max_length=500,
        ui_element="textarea",
        ui_options={"rows": 6},
    )

    @model_validator(mode="after")
    def check_all_errors(self):
        errors = []
        # Passwords must match
        if self.password != self.password_repeat:
            errors.append(
                {
                    "name": "passwordRepeat",
                    "property": ".passwordRepeat",
                    "message": "Passwords do not match",
                }
            )
        # Biography must not contain any bad words (case-insensitive)
        bad_words = ["buy", "sock", "chump","ministry", "company"]
        found = [w for w in bad_words if w in self.biography.lower()]
        if found:
            errors.append(
                {
                    "name": "biography",
                    "property": ".biography",
                    "message": f'The following word(s) are not allowed in the biography: {", ".join(found)}.'
                }
            )

        # I don't like Bob
        if "bob" in self.userName.lower():
            errors.append(
                {
                    "name": "userName",
                    "property": ".userName",
                    "message": "I don't like Bob.",
                }
            )
        if errors:
            raise SchemaFormValidationError(errors)
        return self

    class Config:
        populate_by_name = True
