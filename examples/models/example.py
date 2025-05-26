from pydantic import Field, SecretStr
from PySchemaForms.schema_form import FormModel


class AddressModel(FormModel):
    street: str = Field(None, title="Street", ui_placeholder="123 Main St")
    city: str = Field(None, title="City", ui_placeholder="Metropolis")
    state: str = Field(None, title="State", ui_widget="select")
    zip: str = Field(None, title="ZIP Code", ui_placeholder="12345")


class ExperienceModel(FormModel):
    company: str = Field(..., title="Company", ui_placeholder="e.g. Acme Corp")
    role: str = Field(..., title="Role", ui_placeholder="e.g. Developer")
    years: int = Field(None, title="Years", ge=0)


class ExampleSchemaModel(FormModel):
    name: str = Field(
        ...,
        title="Full Name",
        min_length=2,
        max_length=40,
        description="Enter your full name.",
    )
    age: int = Field(
        ...,
        title="Age",
        ge=21,
        le=120,
    )
    gender: str = Field(
        None,
        title="Gender",
        enum=["male", "female", "other"],
    )
    bio: str = Field(
        ...,
        title="Biography",
        description="Tell us about yourself.",
        ui_widget="textarea",
        ui_options={"rows": 6, "placeholder": "Write a short bio..."},
    )
    email: str = Field(
        None,
        title="Email Address",
        format="email",
    )
    website: str = Field(
        None,
        title="Personal Website",
        format="uri",
    )
    option_string_test: str = Field(
        None,
        title="String Option Test",
        description="This is a string option test.",
        min_length=3,
        max_length=10,
        ui_widget="text",
        ui_options={"placeholder": "3-10 characters"},
    )
    password: SecretStr = Field(
        None,
        title="Password",
        min_length=6,
        ui_widget="password",
        ui_options={"placeholder": "Create a secure password"},
        type="string",
    )
    acceptTerms: bool = Field(
        ...,
        title="Accept Terms and Conditions",
        ui_widget="checkbox",
        ui_options={"label": "I agree to the terms and conditions"},
    )
    favoriteColor: str = Field(
        "#ff0000",
        title="Favorite Color",
        format="color",
        ui_widget="color",
    )
    skills: list[str] = Field(
        None,
        title="Skills",
        min_items=1,
        enum=["Python", "JavaScript", "C++", "Java", "Go", "Rust"],
        type="array",
    )
    experience: list[ExperienceModel] = Field(
        ...,
        title="Work Experience",
        description="List your work experience.",
        min_items=1,
        max_items=5,
        type="array",
    )
    address: AddressModel = Field(
        None,
        title="Address",
        type="object",
    )
    profilePhoto: str = Field(
        None,
        title="Profile Photo",
        ui_widget="file",
    )
    newsletter: bool = Field(
        False,
        title="Subscribe to newsletter",
        ui_help="Subscribe to receive updates.",
        type="boolean",
    )
    rating: int = Field(
        3,
        title="Rate your experience",
        ge=1,
        le=5,
        type="integer",
    )
    customSelect: str = Field(
        None,
        title="Custom Select",
        enum=["a", "b", "c"],
        ui_widget="radio",
        type="string",
    )
    readonlyField: str = Field(
        "This is read-only",
        title="Read Only Example",
        read_only=True,
        ui_readonly=True,
        type="string",
    )
    hiddenField: str = Field(
        "You should not see this",
        title="Hidden Example",
        ui_widget="hidden",
        type="string",
    )

    class Config:
        populate_by_name = True


example_data = {
    "name": "Ada Lovelace",
    "age": 36,
    "gender": "female",
    "bio": "First computer programmer.",
    "email": "ada@lovelace.org",
    "website": "https://en.wikipedia.org/wiki/Ada_Lovelace",
    "password": "securepassword",
    "acceptTerms": True,
    "favoriteColor": "#00bfff",
    "skills": ["Python", "JavaScript"],
    "experience": [{"company": "Analytical Engines", "role": "Mathematician", "years": 5}],
    "address": {
        "street": "123 Computing Ave",
        "city": "London",
        "state": "England",
        "zip": "12345",
    },
    "newsletter": True,
    "rating": 5,
    "customSelect": "b",
    "readonlyField": "This is read-only",
    "hiddenField": "You should not see this",
}
