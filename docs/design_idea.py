from datetime import date, datetime
from typing import Any, Dict

from pydantic_forms.schema_form import (
    FormDesign,
    FormModel,
    HorizontalLayout,
    SectionDesign,
    TabbedLayout,
    VerticalLayout,
    form_validator,
    FormField,
    EmailStr,
)

# types should have defaults based off python data types where applicable to apply pydantic input type
# e.g., str -> "", int -> 0, float -> 0.0,
# The Form Model should allow the user to specify a text area for a string field, a select dropdown for an enum field, etc.
# the library should provide an error when an invalid input type is specified for a given field type (checkbox for string, instead of boolean, etc.)


class SimpleForm(FormModel):
    title: str = FormField(
        ...,
        title="Title",
        input_type="text",
        placeholder="Enter title here",
        help_text="The title of the item.",
        icon="bi bi-card-text",
    )
    age: int = FormField(
        ...,
        title="Age",
        input_type="number",
        min=0,
        max=120,
        help_text="Your age in years.",
        icon="bi bi-person",
    )
    email: EmailStr = FormField(
        ...,
        title="Email",
        input_type="email",
        placeholder="example@example.com",
        help_text="Your email address.",
        icon="bi bi-envelope",
    )
    subscribe: bool = FormField(
        False,
        title="Subscribe to newsletter",
        input_type="checkbox",
        help_text="Check to receive our newsletter.",
        icon="bi bi-newspaper",
    )
    country: str = FormField(
        ...,
        title="Country",
        input_type="select",
        options=["USA", "Canada", "UK", "Australia"],
        help_text="Select your country of residence.",
        icon="bi bi-globe",
    )
    birth_date: date = FormField(
        ...,
        title="Birth Date",
        input_type="date",
        help_text="Your date of birth.",
        icon="bi bi-calendar",
    )
    appointment_time: datetime = FormField(
        None,
        title="Appointment Time",
        type="datetime",
        help_text="Preferred time for appointment.",
        icon="bi bi-clock",
    )
    credit_card_number: str = FormField(
        ...,
        title="Credit Card Number",
        type="credit_card",
        placeholder="1234 5678 9012 3456",
        help_text="Enter your credit card number.",
        icon="bi bi-credit-card",
    )

    @form_validator
    # if under 18, must have parental consent
    def check_age_and_consent(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        age = values.get("age")
        parental_consent = values.get("parental_consent")
        if age is not None and age < 18 and not parental_consent:
            raise ValueError("Parental consent is required for users under 18.")
        return values


class UserProfile(FormModel):
    bio: str = FormField(
        None,
        title="Biography",
        input_type="textarea",
        placeholder="Tell us about yourself",
        help_text="A brief biography.",
        icon="bi bi-info-circle",
    )
    profile_picture: str = FormField(
        None,
        title="Profile Picture",
        type="file",
        help_text="Upload your profile picture.",
        icon="bi bi-image",
    )


class LayoutOne(VerticalLayout):
    form: SimpleForm  # layout with simple form is a vertical layout
    form_config = SectionDesign(
        section_title="User Profile Section",
        section_description="Fill out your profile information below.",
        icon="bi bi-people",  # bootstrap icon name
        collapsible=True,
    )


class LayoutTwo(HorizontalLayout):
    profile: UserProfile  # layout with user profile form is a horizontal layout
    form_config = SectionDesign(
        section_title="Additional Profile Details",
        section_description="Provide additional details for your profile.",
        icon="bi bi-person-badge",  # bootstrap icon name
        collapsible=False,
    )


class UserProfileLayout(TabbedLayout):
    tab_one: LayoutOne  # order of tabs is determined by the order of declaration this would be the first tab
    tab_two: LayoutTwo  # this would be the second tab

    form_config = FormDesign(
        ui_theme="material",  # UI framework (bootstrap, material, shadcn, tailwind, semantic, custom)
        ui_theme_custom_css="<url for custom css>",  # custom css styles if ui_theme is set to custom - ignored unless custom is selected
        form_name="User Profile",  # form name displayed at the top of the form
        form_enctype="application/x-www-form-urlencoded",  # form encoding type only for post method
        form_width="600px",  # desired form width
        target_url="/api/endpoint/for/form",  # target URL for form submission - full url or relative path
        form_method="post",  # post (default), get
        error_notification_style="inline",  # toast, inline,
        show_debug_info=True,  # default is False
    )


# Everything above this line is part of the design idea
# HTML Generation of the form should include the HTML form, the CSS for the selected UI framework, and any JavaScript needed for client-side validation and interactivity.
# this allows a simple embeddable form that can be included in any web page with minimal effort.
# use the bootstrap icons from https://icons.getbootstrap.com/ for the icons specified in the design

# Example Flask Endpoint - Simple Concept


@app.route("/user-profile", methods=["GET", "POST"])
def user_profile():
    """
    Simple example showing UserProfileLayout usage:
    - GET: Generate form HTML
    - POST: Validate and process submission
    """

    # Create the layout instance
    layout = UserProfileLayout()

    if request.method == "GET":
        # Single call to generate the complete form
        return layout.render()

    elif request.method == "POST":
        # Single call to validate and get result
        result = layout.validate(request.form.to_dict(), files=request.files)

        if result.is_valid:
            # Success - data is automatically validated and cleaned
            validated_data = result.data
            return f"Success! Data: {validated_data}"
        else:
            # Validation failed - form is re-rendered with errors
            return result.render_with_errors()
