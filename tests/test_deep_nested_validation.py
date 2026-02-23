from examples.nested_forms_example import ComprehensiveTabbedForm, create_comprehensive_sample_data
from examples.shared_models import CompanyOrganizationForm, create_sample_nested_data
from pydantic_schemaforms.validation import validate_form_data


def test_company_org_deep_leaf_validation_path_includes_indices():
    """Deeply nested validation should fail and report a precise field path."""

    data = create_sample_nested_data()
    # Break a deep leaf: departments -> teams -> members -> name (min_length=2)
    data["departments"][0]["teams"][0]["members"][0]["name"] = "A"

    result = validate_form_data(CompanyOrganizationForm, data)

    assert result.is_valid is False
    # Ensure the error key preserves nested path + list indices.
    assert "departments[0].teams[0].members[0].name" in result.errors


def test_comprehensive_tabbed_form_validates_deep_organization_tab():
    """Layout-wrapped forms must still validate deeply nested organization data."""

    data = create_comprehensive_sample_data()
    data["organization"]["departments"][0]["teams"][0]["members"][0]["name"] = "A"

    result = validate_form_data(ComprehensiveTabbedForm, data)

    assert result.is_valid is False
    # Layout validation currently reports top-level keys from the nested form error.
    assert "departments" in result.errors
