from fastapi.testclient import TestClient

from examples.fastapi_example import app


def _valid_layout_post_payload() -> dict:
    # Note: LayoutDemonstrationForm renders nested layout fields without prefixes,
    # and model_list items use bracketed indices (parsed by parse_nested_form_data).
    return {
        # PersonalInfoForm (vertical_tab)
        "first_name": "Alex",
        "last_name": "Johnson",
        "email": "alex.johnson@example.com",
        # ContactInfoForm (horizontal_tab)
        "address": "456 Demo Street",
        "city": "San Francisco",
        # PreferencesForm (tabbed_tab) - defaults exist, but include one to ensure tab renders
        "notification_email": "true",
        "theme": "dark",
        "language": "en",
        # TaskListForm (list_tab) - must include at least one task
        "project_name": "Demo Project",
        "tasks[0].task_name": "Complete project setup",
        "tasks[0].priority": "high",
        "tasks[0].due_date": "2024-12-01",
    }


def test_layouts_post_rejects_blank_first_name_and_preferences_tab_renders():
    client = TestClient(app)
    payload = _valid_layout_post_payload()
    payload["first_name"] = ""  # invalid (min_length=2)

    resp = client.post("/layouts?style=bootstrap", data=payload)
    assert resp.status_code == 200

    html = resp.text
    assert "Layout Demonstration - Validation Errors" in html
    assert "First Name" in html
    # Error should be visible
    assert "at least 2" in html or "Must be at least 2" in html
    # Preferences tab content should still render (regression)
    assert "Email Notifications" in html
    assert "No layouts found in tabbed layout" not in html


def test_layouts_post_accepts_valid_payload():
    client = TestClient(app)
    resp = client.post("/layouts?style=bootstrap", data=_valid_layout_post_payload())

    assert resp.status_code == 200
    html = resp.text
    assert "Layout Demo Submitted Successfully" in html
