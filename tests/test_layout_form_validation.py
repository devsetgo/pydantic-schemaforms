
from examples.shared_models import LayoutDemonstrationForm
from pydantic_schemaforms.validation import validate_form_data


def test_layout_form_rejects_blank_first_name():
    data = {
        # Vertical tab (PersonalInfoForm)
        "first_name": "",
        "last_name": "Johnson",
        "email": "alex.johnson@example.com",
        # Horizontal tab (ContactInfoForm)
        "address": "456 Demo Street",
        "city": "San Francisco",
        # Tabbed tab (PreferencesForm)
        "notification_email": True,
        "notification_sms": False,
        "theme": "dark",
        "language": "en",
        # List tab (TaskListForm)
        "project_name": "Demo Project",
        "tasks": [
            {
                "task_name": "Complete project setup",
                "priority": "high",
                "due_date": "2024-12-01",
            }
        ],
    }

    result = validate_form_data(LayoutDemonstrationForm, data)
    assert result.is_valid is False
    assert "first_name" in result.errors


def test_layout_form_rejects_missing_first_name():
    data = {
        # Vertical tab (PersonalInfoForm)
        "last_name": "Johnson",
        "email": "alex.johnson@example.com",
        # Horizontal tab (ContactInfoForm)
        "address": "456 Demo Street",
        "city": "San Francisco",
        # List tab (TaskListForm)
        "project_name": "Demo Project",
        "tasks": [
            {
                "task_name": "Write documentation",
                "priority": "medium",
                "due_date": "2024-12-15",
            }
        ],
    }

    result = validate_form_data(LayoutDemonstrationForm, data)
    assert result.is_valid is False
    assert "first_name" in result.errors
