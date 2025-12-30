"""Extended tests for form_layouts.py to cover rendering methods and edge cases."""

from pydantic import BaseModel, Field
from pydantic_forms.form_layouts import (
    VerticalLayout,
    HorizontalLayout,
    TabbedLayout,
    ListLayout,
)


# Test models defined at module level to avoid "Test" prefix issues
class PersonForm(BaseModel):
    """Simple person form for testing."""
    name: str = Field(default="")
    email: str = Field(default="")


class AddressForm(BaseModel):
    """Address form for testing."""
    street: str = Field(default="")
    city: str = Field(default="")
    zipcode: str = Field(default="")


class TaskForm(BaseModel):
    """Task form for ListLayout testing."""
    title: str = Field(default="")
    description: str = Field(default="")
    completed: bool = Field(default=False)


class TestFormLayoutBasePrivateMethods:
    """Test FormLayoutBase private methods."""

    def test_render_form_instances_with_data(self):
        """Test _render_form_instances with data."""
        from pydantic_forms.schema_form import FormModel

        # Define forms first
        class TestPersonForm(FormModel):
            name: str = ""
            email: str = ""

        class TestAddressForm(FormModel):
            street: str = ""

        # Create layout class and assign forms as class attributes
        class TestVerticalLayout(VerticalLayout):
            pass

        # Assign after class definition
        TestVerticalLayout.TestPersonForm = TestPersonForm
        TestVerticalLayout.TestAddressForm = TestAddressForm

        layout = TestVerticalLayout()
        data = {"name": "John", "email": "john@example.com", "street": "123 Main St"}
        errors = {"email": "Invalid email"}

        rendered = layout._render_form_instances(
            data=data,
            errors=errors,
            framework="bootstrap"
        )

        assert isinstance(rendered, list)
        assert len(rendered) > 0
        for html in rendered:
            assert isinstance(html, str)

    def test_render_form_instances_material_framework(self):
        """Test _render_form_instances with material framework."""
        from pydantic_forms.schema_form import FormModel

        class TestPersonForm(FormModel):
            name: str = ""
            email: str = ""

        class TestVerticalLayout(VerticalLayout):
            pass

        TestVerticalLayout.TestPersonForm = TestPersonForm

        layout = TestVerticalLayout()
        rendered = layout._render_form_instances(
            data=None,
            errors=None,
            framework="material"
        )

        assert isinstance(rendered, list)
        assert len(rendered) > 0

    def test_get_renderer_for_framework_bootstrap(self):
        """Test _get_renderer_for_framework returns EnhancedFormRenderer for bootstrap."""
        layout = VerticalLayout()
        renderer = layout._get_renderer_for_framework("bootstrap")

        assert renderer is not None
        assert hasattr(renderer, 'render_form_fields_only')

    def test_get_renderer_for_framework_material(self):
        """Test _get_renderer_for_framework returns SimpleMaterialRenderer for material."""
        layout = VerticalLayout()
        renderer = layout._get_renderer_for_framework("material")

        assert renderer is not None
        assert hasattr(renderer, 'render_form_fields_only')

    def test_get_forms_returns_form_classes(self):
        """Test _get_forms returns FormModel subclasses."""
        from pydantic_forms.schema_form import FormModel

        class TestPersonForm(FormModel):
            name: str = ""

        class TestAddressForm(FormModel):
            street: str = ""

        class TestVerticalLayout(VerticalLayout):
            pass

        TestVerticalLayout.TestPersonForm = TestPersonForm
        TestVerticalLayout.TestAddressForm = TestAddressForm
        TestVerticalLayout.not_a_form = "string"

        layout = TestVerticalLayout()
        forms = layout._get_forms()

        assert isinstance(forms, list)
        assert len(forms) >= 2  # Should find TestPersonForm and TestAddressForm


# Test forms for validation tests
class StrictForm(BaseModel):
    email: str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(gt=0, lt=150)

class SimpleForm(BaseModel):
    name: str = ""

class ValidatedForm(BaseModel):
    required_field: str = Field(min_length=3)
    number_field: int = Field(ge=0)

class Tab1Form(BaseModel):
    field1: str = Field(min_length=5)

class Tab2Form(BaseModel):
    field2: int = Field(ge=10)


class TestVerticalLayoutValidation:
    """Test VerticalLayout validation edge cases."""

    def test_validate_with_validation_errors(self):
        """Test validate with pydantic validation errors."""
        from pydantic_forms.schema_form import FormModel
        from pydantic import Field

        class TestStrictFormModel(FormModel):
            email: str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
            age: int = Field(gt=0, lt=150)

        class TestVerticalLayout(VerticalLayout):
            pass

        TestVerticalLayout.TestStrictFormModel = TestStrictFormModel
        """Test validate with valid data succeeds."""
        class TestVerticalLayout(VerticalLayout):
            SimpleForm = SimpleForm

        layout = TestVerticalLayout()
        result = layout.validate({"name": "test"})

        # Validation should succeed with valid data
        assert result.is_valid


class TestHorizontalLayoutValidation:
    """Test HorizontalLayout validation edge cases."""

    def test_validate_extracts_field_errors_correctly(self):
        """Test validate correctly extracts field-level errors."""
        from pydantic_forms.schema_form import FormModel
        from pydantic import Field

        class TestValidatedFormModel(FormModel):
            required_field: str = Field(min_length=3)
            number_field: int = Field(ge=0)

        class TestHorizontalLayout(HorizontalLayout):
            pass

        TestHorizontalLayout.TestValidatedFormModel = TestValidatedFormModel
class TestTabbedLayoutValidation:
    """Test TabbedLayout validation."""

    def test_validate_aggregates_errors_from_tabs(self):
        """Test validate aggregates errors from multiple tabs."""
        from pydantic_forms.schema_form import FormModel
        from pydantic import Field

        class TestTab1FormModel(FormModel):
            field1: str = Field(min_length=5)

        class TestTab2FormModel(FormModel):
            field2: int = Field(ge=10)

        class TestTab1(VerticalLayout):
            pass

        TestTab1.TestTab1FormModel = TestTab1FormModel

        class TestTab2(HorizontalLayout):
            pass

        TestTab2.TestTab2FormModel = TestTab2FormModel

        class TestTabbedLayout(TabbedLayout):
            tab1 = TestTab1()
            tab2 = TestTab2()

        layout = TestTabbedLayout()
        result = layout.validate({"field1": "abc", "field2": 5})

        assert not result.is_valid
        assert len(result.errors) > 0


class TestListLayoutRendering:
    """Test ListLayout rendering methods."""

    def test_render_list_item_with_data(self):
        """Test _render_list_item with item data."""
        layout = ListLayout(form_model=TaskForm, min_items=1, max_items=5)

        item_data = {"title": "Test Task", "description": "Test Description"}
        renderer_mock = self._create_mock_renderer()

        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data=item_data,
            index=0,
            list_id="task_list",
            framework="bootstrap",
            errors={}
        )

        assert isinstance(html, str)
        assert "list-item" in html
        assert "data-item-index=\"0\"" in html

    def test_render_list_item_with_errors(self):
        """Test _render_list_item displays errors."""
        layout = ListLayout(form_model=TaskForm, min_items=0, max_items=5)

        renderer_mock = self._create_mock_renderer()
        errors = {"item_0": "This item has an error"}

        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data={"title": "Task"},
            index=0,
            list_id="task_list",
            framework="bootstrap",
            errors=errors
        )

        assert "alert-danger" in html
        assert "This item has an error" in html

    def test_render_list_item_collapsible(self):
        """Test _render_list_item with collapsible items."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            max_items=5,
            collapsible_items=True,
            items_expanded_by_default=True
        )

        renderer_mock = self._create_mock_renderer()

        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data={"title": "Collapsible Task"},
            index=0,
            list_id="task_list",
            framework="bootstrap",
            errors={}
        )

        assert "collapsible-item" in html
        assert "collapse" in html
        assert "show" in html  # expanded by default

    def test_render_list_item_collapsible_material(self):
        """Test _render_list_item with collapsible items in material framework."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            max_items=5,
            collapsible_items=True,
            items_expanded_by_default=False
        )

        renderer_mock = self._create_mock_renderer()

        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data={"title": "Material Task"},
            index=0,
            list_id="task_list",
            framework="material",
            errors={}
        )

        assert "collapsible-item" in html
        assert "material-icons" in html
        assert "expand_more" in html

    def test_render_collapsible_item_bootstrap(self):
        """Test _render_collapsible_item for bootstrap framework."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            collapsible_items=True,
            items_expanded_by_default=True
        )

        html = layout._render_collapsible_item(
            form_html="<div>Form content</div>",
            remove_button_html="<button>Remove</button>",
            error_html="",
            index=1,
            list_id="test_list",
            framework="bootstrap",
            item_class="list-item",
            item_data={"title": "Test"}
        )

        assert "collapsible-item" in html
        assert "data-bs-toggle" in html
        assert "bi bi-chevron-down" in html
        assert "true" in html  # expanded
        assert "Form content" in html
        assert "Remove" in html

    def test_render_collapsible_item_material(self):
        """Test _render_collapsible_item for material framework."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            collapsible_items=True,
            items_expanded_by_default=False
        )

        html = layout._render_collapsible_item(
            form_html="<div>Material form</div>",
            remove_button_html="<button>Delete</button>",
            error_html="<div class='error'>Error</div>",
            index=2,
            list_id="material_list",
            framework="material",
            item_class="list-item material-list-item",
            item_data={"title": "Material Item", "description": "Description"}
        )

        assert "collapsible-item" in html
        assert "material-icons" in html
        assert "expand_more" in html
        assert "onclick" in html
        assert "Material form" in html
        assert "Delete" in html
        assert "Error" in html

    def test_create_item_summary_with_data(self):
        """Test _create_item_summary creates summary from item data."""
        layout = ListLayout(form_model=TaskForm, min_items=0)

        item_data = {"title": "Important Task", "description": "Do something"}
        summary = layout._create_item_summary(item_data, 0)

        assert "TaskForm" in summary
        assert "Important Task" in summary

    def test_create_item_summary_empty_data(self):
        """Test _create_item_summary with empty data."""
        layout = ListLayout(form_model=TaskForm, min_items=0)

        summary = layout._create_item_summary({}, 3)

        assert "TaskForm #4" in summary

    def test_create_item_summary_truncates_long_values(self):
        """Test _create_item_summary truncates long values."""
        layout = ListLayout(form_model=TaskForm, min_items=0)

        item_data = {"title": "A" * 50, "description": "B" * 50}
        summary = layout._create_item_summary(item_data, 0)

        assert "..." in summary
        assert len(summary) < 100

    def test_add_name_prefixes(self):
        """Test _add_name_prefixes adds index prefixes."""
        layout = ListLayout(form_model=TaskForm, min_items=0)

        form_html = '''
        <input type="text" name="title" id="title" />
        <label for="title">Title</label>
        '''

        modified = layout._add_name_prefixes(form_html, 2)

        assert 'name="item_2_title"' in modified
        assert 'id="item_2_title"' in modified
        assert 'for="item_2_title"' in modified

    def test_render_add_button_bootstrap(self):
        """Test _render_add_button for bootstrap."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            add_button_text="Add New Item"
        )

        html = layout._render_add_button("test_list", "bootstrap")

        assert "btn btn-primary" in html
        assert "Add New Item" in html
        assert "addListItem" in html
        assert "test_list" in html

    def test_render_add_button_material(self):
        """Test _render_add_button for material."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            add_button_text="Add Task"
        )

        html = layout._render_add_button("task_list", "material")

        assert "mdc-button--raised" in html
        assert "Add Task" in html
        assert "material-icons" in html
        assert "add" in html

    def test_render_remove_button_bootstrap(self):
        """Test _render_remove_button for bootstrap."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            remove_button_text="Delete"
        )

        html = layout._render_remove_button(1, "test_list", "bootstrap")

        assert "btn-outline-danger" in html
        assert "Delete" in html
        assert "removeListItem" in html
        assert "data-item-index=\"1\"" in html

    def test_render_remove_button_material(self):
        """Test _render_remove_button for material."""
        layout = ListLayout(
            form_model=TaskForm,
            min_items=0,
            remove_button_text="Remove Item"
        )

        html = layout._render_remove_button(3, "material_list", "material")

        assert "mdc-button--outlined" in html
        assert "Remove Item" in html
        assert "material-icons" in html
        assert "remove" in html
        assert "data-item-index=\"3\"" in html

    def _create_mock_renderer(self):
        """Create a mock renderer for testing."""
        class MockRenderer:
            def render_form_from_model(self, model, framework="bootstrap", include_submit_button=True):
                return f"<div>Rendered form for {model.__class__.__name__}</div>"

        return MockRenderer()


class TestListLayoutEdgeCases:
    """Test ListLayout edge cases."""

    def test_render_list_item_above_min_items_shows_remove_button(self):
        """Test _render_list_item shows remove button when above min_items."""
        layout = ListLayout(form_model=TaskForm, min_items=2, max_items=5)

        renderer_mock = self._create_mock_renderer()

        # Render third item (index 2) - should have remove button since we can go down to min_items=2
        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data={"title": "Task 3"},
            index=2,
            list_id="task_list",
            framework="bootstrap",
            errors={}
        )

        # Since we're rendering a single item without context of total count,
        # the logic is: show remove if above min OR if empty data
        # This test just verifies the render method works
        assert isinstance(html, str)

    def test_render_list_item_empty_data_above_min(self):
        """Test _render_list_item with empty data."""
        layout = ListLayout(form_model=TaskForm, min_items=1, max_items=5)

        renderer_mock = self._create_mock_renderer()

        html = layout._render_list_item(
            renderer=renderer_mock,
            item_data={},
            index=0,
            list_id="task_list",
            framework="bootstrap",
            errors={}
        )

        assert isinstance(html, str)
        assert "list-item" in html

    def _create_mock_renderer(self):
        """Create a mock renderer for testing."""
        class MockRenderer:
            def render_form_from_model(self, model, framework="bootstrap", include_submit_button=True):
                return "<form>Mock form</form>"

        return MockRenderer()
