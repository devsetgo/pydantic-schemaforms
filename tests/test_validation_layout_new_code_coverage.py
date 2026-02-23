from pydantic_schemaforms.form_field import FormField
from pydantic_schemaforms.form_layouts import TabbedLayout, VerticalLayout
from pydantic_schemaforms.schema_form import Field, FormModel
from pydantic_schemaforms.validation import ValidationResult, validate_form_data


class LeafForm(FormModel):
    first_name: str = Field(..., min_length=2)


class RaisingValidateLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError("boom")


class BadGetFormsLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError("boom")

    def _get_forms(self):  # pragma: no cover - executed in tests
        raise RuntimeError("boom")


class NoCallableGetFormsLayout(VerticalLayout):
    form = LeafForm

    def __init__(self):
        super().__init__()
        # Make the attribute present but not callable.
        self._get_forms = None

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError("boom")


class EmptyDataValidateLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        # Return an empty dict to hit the `nested_result.data` falsey branch.
        return ValidationResult(is_valid=True, data={}, errors={})


class WrapperRaising(FormModel):
    # Use the same field name as the layout engine fallback mapping.
    vertical_tab: RaisingValidateLayout = FormField(default_factory=RaisingValidateLayout, input_type="layout")


class WrapperBadGetForms(FormModel):
    vertical_tab: BadGetFormsLayout = FormField(default_factory=BadGetFormsLayout, input_type="layout")


class WrapperNoCallableGetForms(FormModel):
    vertical_tab: NoCallableGetFormsLayout = FormField(default_factory=NoCallableGetFormsLayout, input_type="layout")


class WrapperEmptyData(FormModel):
    vertical_tab: EmptyDataValidateLayout = FormField(default_factory=EmptyDataValidateLayout, input_type="layout")


class OrgForm(FormModel):
    company_name: str


class SettingsForm(FormModel):
    username: str
    theme: str


class OrgLayout(VerticalLayout):
    form = OrgForm


class SettingsLayout(VerticalLayout):
    form = SettingsForm


class GenericTabbed(TabbedLayout):
    def __init__(self, form_config=None):
        super().__init__(form_config=form_config)
        self.org = OrgLayout()
        self.settings = SettingsLayout()

    def _get_layouts(self):
        return [("org", self.org), ("settings", self.settings)]


class WrapperTabbed(FormModel):
    tabs: GenericTabbed = FormField(default_factory=GenericTabbed, input_type="layout")


def test_layout_validate_raises_falls_back_to_get_forms_and_reports_errors():
    # Provide flat keys so Pydantic uses default_factory (layout instance)
    # and validate_form_data extracts nested payload via fallback mapping.
    result = validate_form_data(WrapperRaising, {"first_name": "A"})

    assert result.is_valid is False
    assert "first_name" in result.errors


def test_layout_get_forms_raises_is_safely_ignored():
    # This covers the fallback exception handler; it should not crash.
    result = validate_form_data(WrapperBadGetForms, {"first_name": "A"})

    assert result.is_valid is True
    assert result.data.get("vertical_tab") == {"first_name": "A"}


def test_layout_get_forms_not_callable_skips_fallback():
    result = validate_form_data(WrapperNoCallableGetForms, {"first_name": "A"})

    assert result.is_valid is True
    assert result.data.get("vertical_tab") == {"first_name": "A"}


def test_layout_validate_returns_empty_data_does_not_replace_payload():
    payload = {"first_name": "Ok"}
    result = validate_form_data(WrapperEmptyData, payload)

    assert result.is_valid is True
    # Because validate() returned empty data, validate_form_data keeps nested payload.
    assert result.data.get("vertical_tab") == {"first_name": "Ok"}


def test_layout_payload_removed_when_no_nested_data_extracted():
    # With no submitted tab payload and no flat keys matching the tab schema,
    # nested_layout_data is empty. validate_form_data should remove the
    # serialized layout wrapper (layout=True) from output.
    result = validate_form_data(WrapperTabbed, {})

    assert result.is_valid is True
    assert result.data == {}


def test_tabbed_layout_nested_payload_validation_sets_layout_errors():
    # Provide only settings fields; org tab is missing company_name.
    result = validate_form_data(
        WrapperTabbed,
        {"username": "alice", "theme": "dark"},
    )

    assert result.is_valid is False
    assert "company_name" in result.errors
    assert "tabs" in result.data
    assert "settings" in result.data["tabs"]
