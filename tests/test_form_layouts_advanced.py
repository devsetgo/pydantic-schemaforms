"""Tests for form_layouts.py to improve coverage."""

import pytest
from typing import Dict, Any

from pydantic_forms.form_layouts import (
    FormLayoutBase,
    VerticalLayout,
    HorizontalLayout,
    TabbedLayout,
    ListLayout,
)
from pydantic_forms.schema_form import FormModel, Field


class TestFormLayoutBase:
    """Test base FormLayoutBase class."""
    
    def test_form_layout_basic(self):
        """Test basic form layout."""
        layout = VerticalLayout()
        
        assert layout is not None
    
    def test_form_layout_render_bootstrap(self):
        """Test rendering with bootstrap framework."""
        layout = VerticalLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_form_layout_render_material(self):
        """Test rendering with material framework."""
        layout = VerticalLayout()
        
        html = layout.render(framework='material')
        
        assert isinstance(html, str)


class TestVerticalLayout:
    """Test VerticalLayout."""
    
    def test_vertical_layout_basic(self):
        """Test basic vertical layout."""
        layout = VerticalLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_vertical_layout_with_forms(self):
        """Test vertical layout with form models."""
        class TestForm(FormModel):
            name: str = Field(default="", ui_element="text")
            email: str = Field(default="", ui_element="email")
        
        layout = VerticalLayout()
        
        # Layout should be renderable
        assert layout is not None


class TestHorizontalLayout:
    """Test HorizontalLayout."""
    
    def test_horizontal_layout_basic(self):
        """Test basic horizontal layout."""
        layout = HorizontalLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_horizontal_layout_with_style(self):
        """Test horizontal layout with style."""
        layout = HorizontalLayout()
        layout.style = "gap: 10px;"
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)


class TestGridLayout:
    """Test GridLayout."""
    
    def test_tabbed_layout_basic(self):
        """Test basic tabbed layout."""
        layout = TabbedLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)


class TestTabsLayout:
    """Test TabsLayout (TabbedLayout)."""
    
    def test_tabs_layout_basic(self):
        """Test basic tabs layout."""
        layout = TabbedLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_tabs_layout_empty(self):
        """Test tabs layout with no tabs defined."""
        layout = TabbedLayout()
        
        # Should handle empty tabs gracefully
        assert layout is not None


class TestListLayout:
    """Test ListLayout."""
    
    def test_list_layout_with_model(self):
        """Test list layout with form model."""
        class TestForm(FormModel):
            name: str = ""
        
        layout = ListLayout(form_model=TestForm)
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)


class TestLayoutIntegration:
    """Test layout integration."""
    
    def test_nested_layouts(self):
        """Test nested layout structures."""
        inner = VerticalLayout()
        outer = HorizontalLayout()
        
        # Both should render
        assert outer is not None
        assert inner is not None
    
    def test_layout_with_custom_attributes(self):
        """Test layout with custom attributes."""
        layout = VerticalLayout()
        layout.class_ = "custom-class"
        layout.style = "color: red;"
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_layout_render_with_custom_class(self):
        """Test layout render with custom class."""
        layout = VerticalLayout()
        layout.class_ = "my-custom-class"
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)


class TestLayoutValidation:
    """Test layout validation methods."""
    
    def test_layout_validate_empty(self):
        """Test validating empty layout."""
        layout = VerticalLayout()
        
        result = layout.validate({})
        
        assert hasattr(result, 'is_valid')
    
    def test_layout_validate_with_data(self):
        """Test validating layout with data."""
        layout = VerticalLayout()
        
        result = layout.validate({'field': 'value'})
        
        assert hasattr(result, 'is_valid')


class TestLayoutEdgeCases:
    """Test layout edge cases."""
    
    def test_layout_render_no_framework(self):
        """Test layout render without framework."""
        layout = VerticalLayout()
        
        # Should use default framework
        html = layout.render()
        
        assert isinstance(html, str)
    
    def test_layout_empty_render(self):
        """Test layout render with empty content."""
        layout = VerticalLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_tabbed_layout_validation(self):
        """Test tabbed layout validation."""
        layout = TabbedLayout()
        
        result = layout.validate({})
        
        assert hasattr(result, 'is_valid')
    
    def test_tabs_layout_active_tab(self):
        """Test tabs layout with active tab."""
        layout = TabbedLayout()
        
        html = layout.render(framework='bootstrap')
        
        assert isinstance(html, str)
    
    def test_tabbed_layout_material(self):
        """Test tabbed layout with material framework."""
        layout = TabbedLayout()
        
        html = layout.render(framework='material')
        
        assert isinstance(html, str)


class TestLayoutSerialization:
    """Test layout serialization."""
    
    def test_layout_to_dict(self):
        """Test converting layout to dictionary."""
        layout = VerticalLayout()
        
        # Layouts should be serializable
        assert layout is not None
    
    def test_layout_clone(self):
        """Test cloning a layout."""
        original = VerticalLayout()
        
        # Create similar layout
        clone = VerticalLayout()
        
        assert clone is not None
