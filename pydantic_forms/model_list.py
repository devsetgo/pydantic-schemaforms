#!/usr/bin/env python3
"""
Model List Handling for Pydantic Forms
======================================

This module provides functionality for rendering dynamic lists of nested models
with add/remove functionality in forms.

Features:
- Dynamic add/remove buttons for list items
- Nested model validation
- Bootstrap and Material Design styling
- JavaScript interactions for seamless UX
- Configurable min/max items
"""

from typing import Any, Dict, List, Optional, Type, Union
from html import escape
from pydantic import BaseModel
from pydantic_forms.schema_form import FormModel


class ModelListRenderer:
    """Renderer for dynamic model lists with add/remove functionality."""
    
    def __init__(self, framework: str = "bootstrap"):
        """Initialize the model list renderer.
        
        Args:
            framework: UI framework to use ("bootstrap" or "material")
        """
        self.framework = framework
    
    def render_model_list(
        self,
        field_name: str,
        label: str,
        model_class: Type[FormModel],
        values: List[Dict[str, Any]] = None,
        error: Optional[str] = None,
        help_text: Optional[str] = None,
        is_required: bool = False,
        min_items: int = 0,
        max_items: int = 10,
        **kwargs
    ) -> str:
        """Render a dynamic list of models with add/remove functionality.
        
        Args:
            field_name: Name of the field
            label: Display label for the field
            model_class: Pydantic model class for list items
            values: Current values for the list
            error: Validation error message
            help_text: Help text for the field
            is_required: Whether the field is required
            min_items: Minimum number of items allowed
            max_items: Maximum number of items allowed
            **kwargs: Additional rendering options
            
        Returns:
            HTML string for the model list
        """
        values = values or []
        
        if self.framework == "material":
            return self._render_material_list(
                field_name, label, model_class, values, error, help_text,
                is_required, min_items, max_items, **kwargs
            )
        else:
            return self._render_bootstrap_list(
                field_name, label, model_class, values, error, help_text,
                is_required, min_items, max_items, **kwargs
            )
    
    def _render_bootstrap_list(
        self,
        field_name: str,
        label: str,
        model_class: Type[FormModel],
        values: List[Dict[str, Any]],
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        min_items: int,
        max_items: int,
        **kwargs
    ) -> str:
        """Render Bootstrap-styled model list."""
        
        error_class = " is-invalid" if error else ""
        
        html = f'''
        <div class="mb-3">
            <label class="form-label fw-bold">
                {escape(label)}{' <span class="text-danger">*</span>' if is_required else ''}
            </label>
            
            <div class="model-list-container" 
                 data-field-name="{field_name}"
                 data-min-items="{min_items}"
                 data-max-items="{max_items}">
                
                <div class="model-list-items" id="{field_name}-items">'''
        
        # Render existing items
        for i, item_data in enumerate(values):
            html += self._render_bootstrap_list_item(
                field_name, model_class, i, item_data
            )
        
        # If no items and min_items > 0, add empty items
        if not values and min_items > 0:
            for i in range(min_items):
                html += self._render_bootstrap_list_item(
                    field_name, model_class, i, {}
                )
        
        html += f'''
                </div>
                
                <div class="model-list-controls mt-2">
                    <button type="button" 
                            class="btn btn-outline-primary btn-sm add-item-btn"
                            data-target="{field_name}">
                        <i class="bi bi-plus-circle"></i> Add {model_class.__name__.replace('Model', '')}
                    </button>
                </div>
            </div>'''
        
        if help_text:
            html += f'''
            <div class="form-text text-muted">
                <i class="bi bi-info-circle"></i> {escape(help_text)}
            </div>'''
        
        if error:
            html += f'''
            <div class="invalid-feedback d-block">
                <i class="bi bi-exclamation-triangle"></i> {escape(error)}
            </div>'''
        
        html += '</div>'
        return html
    
    def _render_bootstrap_list_item(
        self,
        field_name: str,
        model_class: Type[FormModel],
        index: int,
        item_data: Dict[str, Any]
    ) -> str:
        """Render a single Bootstrap list item."""
        
        # Import here to avoid circular imports
        from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
        
        renderer = EnhancedFormRenderer(framework="bootstrap")
        
        html = f'''
        <div class="model-list-item border rounded p-3 mb-2 bg-light" data-index="{index}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0 text-primary">
                    <i class="bi bi-card-list"></i> 
                    {model_class.__name__.replace('Model', '')} #{index + 1}
                </h6>
                <button type="button" 
                        class="btn btn-outline-danger btn-sm remove-item-btn"
                        data-index="{index}">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
            
            <div class="row">'''
        
        # Render each field in the model
        schema = model_class.model_json_schema()
        properties = schema.get('properties', {})
        
        for field_key, field_schema in properties.items():
            if field_key.startswith('_'):
                continue
                
            field_value = item_data.get(field_key, '')
            input_name = f"{field_name}[{index}].{field_key}"
            
            html += f'''
                <div class="col-md-6">
                    {renderer._render_field(
                        input_name,
                        field_schema,
                        field_value,
                        None,  # error
                        [],   # required_fields
                        "vertical"  # layout
                    )}
                </div>'''
        
        html += '''
            </div>
        </div>'''
        
        return html
    
    def _render_material_list(
        self,
        field_name: str,
        label: str,
        model_class: Type[FormModel],
        values: List[Dict[str, Any]],
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        min_items: int,
        max_items: int,
        **kwargs
    ) -> str:
        """Render Material Design-styled model list."""
        
        html = f'''
        <div class="mdc-form-field-container mb-4">
            <h6 class="mdc-typography--subtitle1 mb-3">
                {escape(label)}{' *' if is_required else ''}
            </h6>
            
            <div class="model-list-container" 
                 data-field-name="{field_name}"
                 data-min-items="{min_items}"
                 data-max-items="{max_items}">
                
                <div class="model-list-items" id="{field_name}-items">'''
        
        # Render existing items
        for i, item_data in enumerate(values):
            html += self._render_material_list_item(
                field_name, model_class, i, item_data
            )
        
        # If no items and min_items > 0, add empty items
        if not values and min_items > 0:
            for i in range(min_items):
                html += self._render_material_list_item(
                    field_name, model_class, i, {}
                )
        
        html += f'''
                </div>
                
                <div class="model-list-controls mt-3">
                    <button type="button" 
                            class="mdc-button mdc-button--outlined add-item-btn"
                            data-target="{field_name}">
                        <span class="mdc-button__ripple"></span>
                        <i class="material-icons mdc-button__icon">add_circle</i>
                        <span class="mdc-button__label">Add {model_class.__name__.replace('Model', '')}</span>
                    </button>
                </div>
            </div>'''
        
        if help_text:
            html += f'''
            <div class="mdc-text-field-helper-text">
                {escape(help_text)}
            </div>'''
        
        if error:
            html += f'''
            <div class="mdc-text-field-helper-text mdc-text-field-helper-text--validation-msg">
                {escape(error)}
            </div>'''
        
        html += '</div>'
        return html
    
    def _render_material_list_item(
        self,
        field_name: str,
        model_class: Type[FormModel],
        index: int,
        item_data: Dict[str, Any]
    ) -> str:
        """Render a single Material Design list item."""
        
        # Import here to avoid circular imports
        from pydantic_forms.material_renderer import MaterialDesign3Renderer
        
        renderer = MaterialDesign3Renderer()
        
        html = f'''
        <div class="model-list-item mdc-card mdc-card--outlined mb-3" data-index="{index}">
            <div class="mdc-card__primary-action">
                <div class="mdc-card__content">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mdc-typography--subtitle2 mb-0">
                            {model_class.__name__.replace('Model', '')} #{index + 1}
                        </h6>
                        <button type="button" 
                                class="mdc-icon-button remove-item-btn"
                                data-index="{index}">
                            <i class="material-icons">delete</i>
                        </button>
                    </div>
                    
                    <div class="row">'''
        
        # Render each field in the model
        schema = model_class.model_json_schema()
        properties = schema.get('properties', {})
        
        for field_key, field_schema in properties.items():
            if field_key.startswith('_'):
                continue
                
            field_value = item_data.get(field_key, '')
            input_name = f"{field_name}[{index}].{field_key}"
            
            # Get field info from the model
            field_info = getattr(model_class.model_fields.get(field_key), 'json_schema_extra', {}) or {}
            
            html += f'''
                        <div class="col-md-6">
                            {renderer._render_material_field(
                                input_name,
                                field_schema,
                                field_value,
                                None,  # error
                                [],   # required_fields
                                "vertical"  # layout
                            )}
                        </div>'''
        
        html += '''
                    </div>
                </div>
            </div>
        </div>'''
        
        return html

    def get_model_list_javascript(self) -> str:
        """Return JavaScript for model list functionality with collapsible card support."""
        return '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            initializeModelLists();
        });
        
        function initializeModelLists() {
            // Add item functionality
            document.querySelectorAll('.add-item-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const fieldName = this.dataset.target;
                    const container = document.querySelector(`[data-field-name="${fieldName}"]`);
                    const itemsContainer = container.querySelector('.model-list-items');
                    const maxItems = parseInt(container.dataset.maxItems);
                    const currentItems = itemsContainer.querySelectorAll('.model-list-item').length;
                    
                    if (currentItems >= maxItems) {
                        alert(`Maximum ${maxItems} items allowed.`);
                        return;
                    }
                    
                    // Clone the template or create new item
                    addNewListItem(fieldName, currentItems);
                    updateItemIndices(itemsContainer);
                });
            });
            
            // Remove item functionality
            document.addEventListener('click', function(e) {
                if (e.target.closest('.remove-item-btn')) {
                    const button = e.target.closest('.remove-item-btn');
                    const item = button.closest('.model-list-item');
                    const container = item.closest('.model-list-container');
                    const minItems = parseInt(container.dataset.minItems);
                    const itemsContainer = container.querySelector('.model-list-items');
                    const currentItems = itemsContainer.querySelectorAll('.model-list-item').length;
                    
                    if (currentItems <= minItems) {
                        alert(`Minimum ${minItems} items required.`);
                        return;
                    }
                    
                    // Confirm deletion if item has data
                    const hasData = item.querySelectorAll('input, select, textarea').some(input => 
                        input.type === 'checkbox' ? input.checked : input.value.trim() !== ''
                    );
                    
                    if (hasData && !confirm('Are you sure you want to remove this item? All data will be lost.')) {
                        return;
                    }
                    
                    item.remove();
                    updateItemIndices(itemsContainer);
                }
            });
            
            // Update titles when input fields change (for dynamic title updates)
            document.addEventListener('input', function(e) {
                if (e.target.name && (e.target.name.includes('.name') || e.target.name.includes('.relationship'))) {
                    updateItemTitle(e.target);
                }
            });
            
            // Toggle collapse state icons
            document.addEventListener('click', function(e) {
                if (e.target.closest('[data-bs-toggle="collapse"]')) {
                    const button = e.target.closest('[data-bs-toggle="collapse"]');
                    const icon = button.querySelector('.bi-chevron-down, .bi-chevron-right');
                    if (icon) {
                        setTimeout(() => {
                            const isExpanded = button.getAttribute('aria-expanded') === 'true';
                            icon.className = isExpanded ? 'bi bi-chevron-down me-2' : 'bi bi-chevron-right me-2';
                        }, 50);
                    }
                }
            });
        }
        
        function addNewListItem(fieldName, index) {
            const container = document.querySelector(`[data-field-name="${fieldName}"]`);
            const itemsContainer = container.querySelector('.model-list-items');
            
            // Get the first item as a template if it exists
            const firstItem = itemsContainer.querySelector('.model-list-item');
            if (firstItem) {
                const newItem = firstItem.cloneNode(true);
                
                // Clear all input values
                newItem.querySelectorAll('input, select, textarea').forEach(input => {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                });
                
                // Update data-index
                newItem.dataset.index = index;
                
                // Update field names and IDs
                updateFieldNames(newItem, fieldName, index);
                
                // Update collapse IDs
                updateCollapseIds(newItem, fieldName, index);
                
                // Expand the new item
                const collapseDiv = newItem.querySelector('.collapse');
                if (collapseDiv) {
                    collapseDiv.classList.add('show');
                }
                
                // Update collapse button aria-expanded
                const collapseButton = newItem.querySelector('[data-bs-toggle="collapse"]');
                if (collapseButton) {
                    collapseButton.setAttribute('aria-expanded', 'true');
                    const icon = collapseButton.querySelector('.bi-chevron-down, .bi-chevron-right');
                    if (icon) {
                        icon.className = 'bi bi-chevron-down me-2';
                    }
                }
                
                itemsContainer.appendChild(newItem);
            }
        }
        
        function updateItemIndices(container) {
            const items = container.querySelectorAll('.model-list-item');
            items.forEach((item, index) => {
                item.dataset.index = index;
                
                // Update field names first
                const fieldName = container.closest('.model-list-container').dataset.fieldName;
                updateFieldNames(item, fieldName, index);
                updateCollapseIds(item, fieldName, index);
                
                // Update title using the dynamic template
                updateItemTitleFromData(item, index);
            });
        }
        
        function updateFieldNames(item, fieldName, index) {
            item.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.name) {
                    // Update name attribute to use correct index
                    input.name = input.name.replace(/\\[\\d+\\]/, `[${index}]`);
                }
                if (input.id) {
                    // Update id attribute
                    input.id = input.id.replace(/\\[\\d+\\]/, `[${index}]`);
                }
            });
            
            item.querySelectorAll('label').forEach(label => {
                if (label.getAttribute('for')) {
                    label.setAttribute('for', label.getAttribute('for').replace(/\\[\\d+\\]/, `[${index}]`));
                }
            });
        }
        
        function updateCollapseIds(item, fieldName, index) {
            const collapseDiv = item.querySelector('.collapse');
            const collapseButton = item.querySelector('[data-bs-toggle="collapse"]');
            
            if (collapseDiv && collapseButton) {
                const newId = `${fieldName}_item_${index}_content`;
                collapseDiv.id = newId;
                collapseButton.setAttribute('data-bs-target', `#${newId}`);
                collapseButton.setAttribute('aria-controls', newId);
            }
        }
        
        function updateItemTitle(inputElement) {
            const item = inputElement.closest('.model-list-item');
            if (!item) return;
            
            updateItemTitleFromData(item);
        }
        
        function updateItemTitleFromData(item, forceIndex = null) {
            const index = forceIndex !== null ? forceIndex : parseInt(item.dataset.index);
            const titleTemplate = item.dataset.titleTemplate || 'Item #{index}';
            const titleElement = item.querySelector('h6 button, h6 span');
            
            if (!titleElement) return;
            
            // Extract current form data from the item
            const formData = { index: index + 1 };
            item.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.name) {
                    // Extract field name (e.g., "pets[0].name" -> "name")
                    const fieldMatch = input.name.match(/\\.([^.]+)$/);
                    if (fieldMatch) {
                        const fieldName = fieldMatch[1];
                        if (input.type === 'checkbox') {
                            formData[fieldName] = input.checked;
                        } else {
                            formData[fieldName] = input.value || '';
                        }
                    }
                }
            });
            
            // Generate title from template
            let newTitle;
            try {
                newTitle = titleTemplate.replace(/\\{([^}]+)\\}/g, (match, key) => {
                    return formData[key] || '';
                });
            } catch (e) {
                newTitle = `Item #${index + 1}`;
            }
            
            // Update the title while preserving icons
            const cardIcon = '<i class="bi bi-card-list me-2"></i>';
            if (titleElement.tagName === 'BUTTON') {
                const chevronIcon = titleElement.querySelector('.bi-chevron-down, .bi-chevron-right');
                const chevronHtml = chevronIcon ? chevronIcon.outerHTML : '<i class="bi bi-chevron-down me-2"></i>';
                titleElement.innerHTML = `${chevronHtml}${cardIcon}${newTitle}`;
            } else {
                titleElement.innerHTML = `${cardIcon}${newTitle}`;
            }
        }
        </script>
        '''