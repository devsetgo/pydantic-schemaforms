"""Policy regression tests for Option A security/model-boundary behavior."""

from pydantic_schemaforms.form_field import FormField
from pydantic_schemaforms.form_layouts import TabbedLayout, VerticalLayout
from pydantic_schemaforms.rendering.layout_engine import get_nested_form_data
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.validation import validate_form_data


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
    org = OrgLayout()
    settings = SettingsLayout()


class WrapperForm(FormModel):
    tabs: GenericTabbed = FormField(
        default_factory=GenericTabbed,
        title="Wrapper",
        input_type="layout",
    )


def test_get_nested_form_data_schema_driven_for_tabbed_layouts():
    """Layout extraction should be generic and derived from layout schema, not field names."""

    flat_data = {
        "company_name": "Acme",
        "username": "alice",
        "theme": "dark",
        "unrelated": "ignored",
    }

    nested = get_nested_form_data("tabs", flat_data, GenericTabbed())

    assert nested == {
        "org": {"company_name": "Acme"},
        "settings": {"username": "alice", "theme": "dark"},
    }


def test_validate_form_data_returns_model_shape_only():
    """Validated output must not include unknown submitted keys by default."""

    class StrictForm(FormModel):
        name: str

    result = validate_form_data(StrictForm, {"name": "john", "is_admin": True})

    assert result.is_valid is True
    assert result.data == {"name": "john"}
    assert "is_admin" not in result.data


def test_validate_form_data_layout_wrapper_keeps_only_layout_model_shape():
    """Layout wrapper forms should return only wrapper model keys with nested tab payload."""

    result = validate_form_data(
        WrapperForm,
        {
            "company_name": "Acme",
            "username": "alice",
            "theme": "dark",
            "is_admin": "1",
        },
    )

    assert result.is_valid is True
    assert set(result.data.keys()) == {"tabs"}
    assert result.data["tabs"] == {
        "org": {"company_name": "Acme"},
        "settings": {"username": "alice", "theme": "dark"},
    }
