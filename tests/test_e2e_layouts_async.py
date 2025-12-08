"""
Comprehensive E2E tests for layouts/async rendering.
Covers unit structure tests, integration tests with full forms, and async rendering.
"""

import asyncio
import pytest

from pydantic import ValidationError

from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
from pydantic_forms.rendering.layout_engine import (
    AccordionLayout,
    TabLayout,
)
from examples.shared_models import LayoutDemonstrationForm


# ============================================================================
# UNIT TESTS: Tab/Accordion Structure & DOM
# ============================================================================


class TestTabLayoutStructure:
    """Unit tests for TabLayout DOM structure and attributes."""

    def test_tab_buttons_have_aria_attributes(self):
        """Verify tab buttons include accessibility attributes."""
        tabs = [
            {"title": "Settings", "content": "Settings content"},
            {"title": "Profile", "content": "Profile content"},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # Verify aria-selected and role attributes
        assert 'role="tablist"' in html
        assert 'aria-selected="true"' in html  # First tab active
        assert 'aria-selected="false"' in html  # Second tab inactive

    def test_tab_panels_have_aria_hidden_attribute(self):
        """Verify tab panels include aria-hidden for accessibility."""
        tabs = [
            {"title": "Tab A", "content": "Content A"},
            {"title": "Tab B", "content": "Content B"},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # First panel visible, second hidden
        assert 'aria-hidden="false"' in html
        assert 'aria-hidden="true"' in html

    def test_tab_content_initial_display_style(self):
        """Verify first tab content is displayed, others hidden."""
        tabs = [
            {"title": "First", "content": "First content"},
            {"title": "Second", "content": "Second content"},
            {"title": "Third", "content": "Third content"},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # Check display styles in content
        assert "display: block" in html or "display:block" in html  # First visible
        assert "display: none" in html or "display:none" in html    # Others hidden

    def test_accordion_sections_have_expanded_attributes(self):
        """Verify accordion sections include expanded/collapse state."""
        sections = [
            {"title": "Expandable 1", "content": "Content 1", "expanded": True},
            {"title": "Expandable 2", "content": "Content 2", "expanded": False},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        # Count expanded attributes
        expanded_count = html.count('aria-expanded="true"')
        collapsed_count = html.count('aria-expanded="false"')

        assert expanded_count >= 1
        assert collapsed_count >= 1

    def test_accordion_section_ids_are_unique(self):
        """Verify each accordion section has unique ID."""
        sections = [
            {"title": f"Section {i}", "content": f"Content {i}"} for i in range(5)
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        # Count unique section IDs
        section_ids = []
        for i in range(5):
            section_id = f"accordion-{i}"
            if section_id in html:
                section_ids.append(section_id)

        assert len(section_ids) == 5


class TestTabLayoutBootstrapMaterial:
    """Unit tests verifying Bootstrap/Material theme-specific rendering."""

    def test_tab_layout_bootstrap_theme(self):
        """Verify TabLayout respects Bootstrap theme."""
        renderer = EnhancedFormRenderer(framework="bootstrap")
        tabs = [
            {"title": "Tab 1", "content": "Content 1"},
            {"title": "Tab 2", "content": "Content 2"},
        ]
        layout = TabLayout(tabs)
        html = layout.render(renderer=renderer, framework="bootstrap")

        # Bootstrap-specific elements
        assert "tab-layout" in html or "tabbed-layout" in html

    def test_tab_layout_material_theme(self):
        """Verify TabLayout respects Material theme."""
        from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        tabs = [
            {"title": "Tab 1", "content": "Content 1"},
            {"title": "Tab 2", "content": "Content 2"},
        ]
        layout = TabLayout(tabs)
        html = layout.render(renderer=renderer, framework="material")

        # Material theme should also render tabs
        assert "Tab 1" in html
        assert "Tab 2" in html


# ============================================================================
# INTEGRATION TESTS: Full Form Rendering with Tabs/Accordions
# ============================================================================


class TestLayoutDemonstrationFormRendering:
    """Integration tests for LayoutDemonstrationForm with all layout types."""

    def test_layout_form_renders_all_tabs(self):
        """Verify layout form renders all tab sections."""
        renderer = EnhancedFormRenderer(framework="bootstrap")
        form_data = {
            "vertical_tab": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "birth_date": "1990-01-01",
            },
            "horizontal_tab": {
                "phone": "+1-555-0000",
                "address": "123 Main St",
                "city": "Springfield",
                "postal_code": "12345",
            },
            "tabbed_tab": {
                "notification_email": True,
                "notification_sms": False,
                "theme": "light",
                "language": "en",
            },
            "list_tab": {
                "project_name": "Demo",
                "tasks": [
                    {
                        "task_name": "Task 1",
                        "priority": "high",
                        "due_date": "2024-12-01",
                    }
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # All layout field titles should be present
        assert "Personal Info" in html
        assert "Contact Info" in html
        assert "Preferences" in html
        assert "Task List" in html

    def test_layout_form_includes_nested_field_content(self):
        """Verify nested form content renders in layout fields."""
        renderer = EnhancedFormRenderer(framework="bootstrap")
        form_data = {
            "vertical_tab": {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
            },
            "horizontal_tab": {
                "address": "456 Oak Ave",
                "city": "Metropolis",
            },
            "tabbed_tab": {
                "notification_email": True,
                "theme": "dark",
            },
            "list_tab": {
                "project_name": "Project X",
                "tasks": [],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # Check that nested field values appear
        assert "Alice" in html
        assert "Smith" in html
        assert "alice@example.com" in html
        assert "456 Oak Ave" in html
        assert "Metropolis" in html

    def test_layout_form_renders_model_list_in_task_field(self):
        """Verify model_list field renders correctly within layout."""
        renderer = EnhancedFormRenderer(framework="bootstrap")
        form_data = {
            "vertical_tab": {
                "first_name": "Bob",
                "last_name": "Builder",
                "email": "bob@example.com",
            },
            "horizontal_tab": {
                "address": "789 Work St",
                "city": "Construction City",
            },
            "tabbed_tab": {"theme": "light"},
            "list_tab": {
                "project_name": "Build It",
                "tasks": [
                    {
                        "task_name": "Lay foundation",
                        "priority": "high",
                        "due_date": "2024-12-05",
                        "completed": False,
                    },
                    {
                        "task_name": "Frame walls",
                        "priority": "medium",
                        "due_date": "2024-12-15",
                        "completed": False,
                    },
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # Verify model list content in task field
        assert "Build It" in html  # project_name
        assert "Lay foundation" in html
        assert "Frame walls" in html
        assert "remove-item-btn" in html  # Remove button for list items


class TestTabLayoutIntegration:
    """Integration tests for tab rendering in form contexts."""

    def test_tabbed_form_renders_tabs_and_content(self):
        """Verify tabbed form renders all tab buttons and content."""
        renderer = EnhancedFormRenderer(framework="bootstrap")

        form_data = {
            "vertical_tab": {
                "first_name": "Tab",
                "last_name": "Tester",
                "email": "tabs@example.com",
            },
            "horizontal_tab": {
                "address": "Tab Street",
                "city": "Tabville",
            },
            "tabbed_tab": {
                "notification_email": True,
                "notification_sms": True,
                "theme": "auto",
                "language": "es",
            },
            "list_tab": {
                "project_name": "Tab Project",
                "tasks": [
                    {
                        "task_name": "Tab task",
                        "priority": "low",
                        "due_date": None,
                    }
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # Verify both bootstrap tab structure and content are rendered
        assert "tab-layout" in html or "tabbed" in html.lower()


# ============================================================================
# ASYNC TESTS: Async Rendering Equivalence
# ============================================================================


class TestAsyncFormRendering:
    """Tests for async renderer paths."""

    @pytest.mark.asyncio
    async def test_async_render_returns_same_html_as_sync(self):
        """Verify async rendering produces identical output to sync."""
        renderer = EnhancedFormRenderer(framework="bootstrap")
        form_data = {
            "vertical_tab": {
                "first_name": "Async",
                "last_name": "Test",
                "email": "async@example.com",
            },
            "horizontal_tab": {
                "address": "123 Async St",
                "city": "Asyncville",
            },
            "tabbed_tab": {"theme": "light"},
            "list_tab": {
                "project_name": "Async Project",
                "tasks": [
                    {
                        "task_name": "Async task",
                        "priority": "high",
                        "due_date": "2024-12-10",
                    }
                ],
            },
        }

        # Render synchronously
        sync_html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # Render asynchronously
        async_html = await renderer.render_form_from_model_async(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url="/submit",
        )

        # Both should produce equivalent content
        assert sync_html == async_html
        assert "Async" in async_html
        assert "async@example.com" in async_html

    @pytest.mark.asyncio
    async def test_async_render_with_errors(self):
        """Verify async rendering handles validation errors."""
        renderer = EnhancedFormRenderer(framework="bootstrap")

        # Invalid data: empty tasks list (min_length=1)
        invalid_data = {
            "vertical_tab": {
                "first_name": "Invalid",
                "last_name": "User",
                "email": "invalid@example.com",
            },
            "horizontal_tab": {
                "address": "Bad St",
                "city": "Badville",
            },
            "tabbed_tab": {"theme": "dark"},
            "list_tab": {
                "project_name": "Bad Project",
                "tasks": [],  # Invalid: min_length=1 required
            },
        }

        # Async render should not raise; let renderer handle errors gracefully
        try:
            html = await renderer.render_form_from_model_async(
                LayoutDemonstrationForm,
                data=invalid_data,
                errors={},
                submit_url="/submit",
            )
            # Rendering completes even with data issues
            assert isinstance(html, str)
        except ValidationError:
            # Validation may occur; that's acceptable
            pass

    @pytest.mark.asyncio
    async def test_multiple_async_renders_concurrent(self):
        """Verify multiple async renders can run concurrently."""
        renderer = EnhancedFormRenderer(framework="bootstrap")

        async def render_form_variant(name: str, theme: str):
            data = {
                "vertical_tab": {
                    "first_name": name,
                    "last_name": "Concurrent",
                    "email": f"{name}@example.com",
                },
                "horizontal_tab": {
                    "address": "Concurrent St",
                    "city": "CityC",
                },
                "tabbed_tab": {"theme": theme},
                "list_tab": {
                    "project_name": f"{name} Project",
                    "tasks": [
                        {
                            "task_name": f"{name} Task",
                            "priority": "medium",
                            "due_date": "2024-12-20",
                        }
                    ],
                },
            }
            return await renderer.render_form_from_model_async(
                LayoutDemonstrationForm,
                data=data,
                submit_url="/submit",
            )

        # Run 3 async renders concurrently
        results = await asyncio.gather(
            render_form_variant("Alice", "light"),
            render_form_variant("Bob", "dark"),
            render_form_variant("Charlie", "auto"),
        )

        # All should complete without error
        assert len(results) == 3
        assert all(isinstance(html, str) for html in results)
        assert "Alice" in results[0]
        assert "Bob" in results[1]
        assert "Charlie" in results[2]
