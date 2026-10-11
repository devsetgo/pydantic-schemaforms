from examples.nested_forms_example import ComprehensiveTabbedForm, create_comprehensive_sample_data
from examples.shared_models import CompanyOrganizationForm, create_sample_nested_data
from pydantic_schemaforms.form_data import flatten_nested_data
from pydantic_schemaforms.validation import validate_form_data


def test_company_org_deep_leaf_error_mirrors_the_data_path():
    """A deep failure is reported at the same path the value lives at."""

    data = create_sample_nested_data()
    # Break a deep leaf: departments -> teams -> members -> name (min_length=2)
    data['departments'][0]['teams'][0]['members'][0]['name'] = 'A'

    result = validate_form_data(CompanyOrganizationForm, data)

    assert result.is_valid is False
    assert result.errors['departments'][0]['teams'][0]['members'][0]['name']
    assert {'loc': ['departments', 0, 'teams', 0, 'members', 0, 'name']}.items() <= (
        result.error_list()[0].items()
    )


def test_comprehensive_tabbed_form_errors_are_namespaced_by_sub_form():
    """Each sub-form's errors live under its own field, so tabs never collide."""

    data = create_comprehensive_sample_data()
    data['organization']['departments'][0]['teams'][0]['members'][0]['name'] = 'A'

    result = validate_form_data(ComprehensiveTabbedForm, data)

    assert result.is_valid is False
    assert list(result.errors) == ['organization']
    assert result.errors['organization']['departments'][0]['teams'][0]['members'][0]['name']


def test_comprehensive_tabbed_form_accepts_the_wire_format():
    """The flat input names the browser submits decode into the same nested data."""

    data = create_comprehensive_sample_data()
    wire = list(flatten_nested_data(data).items())

    from_wire = validate_form_data(ComprehensiveTabbedForm, wire)
    from_json = validate_form_data(ComprehensiveTabbedForm, data)

    assert from_wire.is_valid and from_json.is_valid
    assert from_wire.data == from_json.data
    assert (
        from_wire.data['organization']['departments'][0]['teams'][0]['members'][0]['name']
        == (data['organization']['departments'][0]['teams'][0]['members'][0]['name'])
    )
