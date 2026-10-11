"""Policy regression tests for Option A security/model-boundary behavior:
validated output only ever has the model's own shape."""

from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.validation import validate_form_data


class OrgForm(FormModel):
    company_name: str


class SettingsForm(FormModel):
    username: str
    theme: str


class WrapperForm(FormModel):
    org: OrgForm = Field(title='Organization')
    settings: SettingsForm = Field(title='Settings')


def test_validate_form_data_returns_model_shape_only():
    """Validated output must not include unknown submitted keys by default."""

    class StrictForm(FormModel):
        name: str

    result = validate_form_data(StrictForm, {'name': 'john', 'is_admin': True})

    assert result.is_valid is True
    assert result.data == {'name': 'john'}
    assert 'is_admin' not in result.data


def test_nested_forms_keep_only_model_shape_at_every_level():
    """Unknown keys are dropped at the top level and inside each sub-form."""

    result = validate_form_data(
        WrapperForm,
        [
            ('org.company_name', 'Acme'),
            ('org.is_admin', '1'),
            ('settings.username', 'alice'),
            ('settings.theme', 'dark'),
            ('is_admin', '1'),
        ],
    )

    assert result.is_valid is True
    assert result.data == {
        'org': {'company_name': 'Acme'},
        'settings': {'username': 'alice', 'theme': 'dark'},
    }
