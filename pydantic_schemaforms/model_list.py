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

from typing import Any, Dict, List, Optional, Type

from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.themes import RendererTheme, get_theme_for_framework
from pydantic_schemaforms.schema_form import FormModel


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
        nested_errors: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None,
        is_required: bool = False,
        min_items: int = 0,
        max_items: int = 10,
        **kwargs,
    ) -> str:
        """Render a dynamic list of models with add/remove functionality.

        Args:
            field_name: Name of the field
            label: Display label for the field
            model_class: Pydantic model class for list items
            values: Current values for the list
            error: Validation error message
            nested_errors: Nested validation errors (e.g., {'0.weight': 'Must be greater than 0'})
            help_text: Help text for the field
            help_text: Help text for the field
            is_required: Whether the field is required
            min_items: Minimum number of items allowed
            max_items: Maximum number of items allowed
            **kwargs: Additional rendering options

        Returns:
            HTML string for the model list
        """
        values = values or []
        nested_errors = nested_errors or {}

        theme = self._resolve_theme()
        return self._render_list(
            theme,
            field_name,
            label,
            model_class,
            values,
            error,
            nested_errors,
            help_text,
            is_required,
            min_items,
            max_items,
        )

    def _render_list(
        self,
        theme: RendererTheme,
        field_name: str,
        label: str,
        model_class: Type[FormModel],
        values: List[Dict[str, Any]],
        error: Optional[str],
        nested_errors: Optional[Dict[str, str]],
        help_text: Optional[str],
        is_required: bool,
        min_items: int,
        max_items: int,
    ) -> str:
        """Render a model list using the provided theme fragments."""

        values = values or []
        nested_errors = nested_errors or {}
        model_label = model_class.__name__.replace("Model", "") or model_class.__name__
        add_button_label = f"Add {label or model_label}" if label else f"Add {model_label}"

        html_parts: List[str] = []

        for index, item_data in enumerate(values):
            item_body = self._render_item_body(
                field_name,
                model_class,
                index,
                item_data,
                nested_errors,
            )
            html_parts.append(
                theme.render_model_list_item(
                    field_name=field_name,
                    model_label=model_label,
                    index=index,
                    body_html=item_body,
                    remove_button_aria_label="Remove this item",
                )
            )

        if not values and min_items > 0:
            for index in range(min_items):
                item_body = self._render_item_body(
                    field_name,
                    model_class,
                    index,
                    {},
                    nested_errors,
                )
                html_parts.append(
                    theme.render_model_list_item(
                        field_name=field_name,
                        model_label=model_label,
                        index=index,
                        body_html=item_body,
                        remove_button_aria_label="Remove this item",
                    )
                )

        # Always include a hidden template item so lists can be emptied (min_items=0)
        # and still support adding new items afterwards.
        template_body = self._render_item_body(
            field_name,
            model_class,
            0,
            {},
            nested_errors,
        )
        template_item = theme.render_model_list_item(
            field_name=field_name,
            model_label=model_label,
            index=0,
            body_html=template_body,
            remove_button_aria_label="Remove this item",
        )
        # Note: do not set data-field-name here; JS looks up the list container by
        # [data-field-name="..."] and we don't want the template to be returned.
        template_html = (
            '<template class="model-list-item-template">'
            "{template_item}"
            "</template>"
        ).format(template_item=template_item)

        items_html = "\n".join([template_html, *html_parts])

        themed_container = theme.render_model_list_container(
            field_name=field_name,
            label=label,
            is_required=is_required,
            min_items=min_items,
            max_items=max_items,
            items_html=items_html,
            help_text=help_text,
            error=error,
            add_button_label=add_button_label,
        )
        if themed_container:
            return themed_container

        default_theme = RendererTheme()
        return default_theme.render_model_list_container(
            field_name=field_name,
            label=label,
            is_required=is_required,
            min_items=min_items,
            max_items=max_items,
            items_html=items_html,
            help_text=help_text,
            error=error,
            add_button_label=add_button_label,
        )

    def _resolve_theme(self) -> RendererTheme:
        return get_theme_for_framework(self.framework)

    def _render_item_body(
        self,
        field_name: str,
        model_class: Type[FormModel],
        index: int,
        item_data: Dict[str, Any],
        nested_errors: Optional[Dict[str, str]] = None,
    ) -> str:
        if self.framework == "material":
            return self._render_material_list_item(
                field_name,
                model_class,
                index,
                item_data,
                nested_errors,
            )
        return self._render_bootstrap_list_item(
            field_name,
            model_class,
            index,
            item_data,
            nested_errors,
        )

    def _render_bootstrap_list_item(
        self,
        field_name: str,
        model_class: Type[FormModel],
        index: int,
        item_data: Dict[str, Any],
        nested_errors: Optional[Dict[str, str]] = None,
    ) -> str:
        """Render a single Bootstrap list item."""

        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        renderer = EnhancedFormRenderer(framework="bootstrap")

        schema = model_class.model_json_schema()
        schema_defs = schema.get("$defs") or schema.get("definitions", {}) or {}
        nested_context = RenderContext(form_data=item_data or {}, schema_defs=schema_defs)
        required_fields = schema.get("required", [])
        nested_errors = nested_errors or {}

        html = ["<div class=\"row\">"]

        # Render each field in the model
        properties = schema.get("properties", {})

        for field_key, field_schema in properties.items():
            if field_key.startswith("_"):
                continue

            field_value = item_data.get(field_key, "")
            input_name = f"{field_name}[{index}].{field_key}"

            # Get the error for this specific field from nested errors
            # e.g., if nested_errors contains '0.weight': 'error', and we're at index 0, field_key 'weight'
            field_error = nested_errors.get(f"{index}.{field_key}")

            html.append(
                f"""
                <div class=\"col-md-6\">
                    {renderer._render_field(
                        input_name,
                        field_schema,
                        field_value,
                        field_error,
                        required_fields=required_fields,
                        context=nested_context,
                        layout="vertical",
                        all_errors=nested_errors,
                    )}
                </div>"""
            )

        html.append("</div>")

        return "\n".join(html)

    def _render_material_list_item(
        self,
        field_name: str,
        model_class: Type[FormModel],
        index: int,
        item_data: Dict[str, Any],
        nested_errors: Optional[Dict[str, str]] = None,
    ) -> str:
        """Render a single Material Design list item."""

        from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()

        schema = model_class.model_json_schema()
        schema_defs = schema.get("$defs") or schema.get("definitions", {}) or {}
        nested_context = RenderContext(form_data=item_data or {}, schema_defs=schema_defs)
        required_fields = schema.get("required", [])
        nested_errors = nested_errors or {}

        html = ["<div class=\"row\">"]

        # Render each field in the model
        properties = schema.get("properties", {})

        for field_key, field_schema in properties.items():
            if field_key.startswith("_"):
                continue

            field_value = item_data.get(field_key, "")
            input_name = f"{field_name}[{index}].{field_key}"

            # Get the error for this specific field from nested errors
            field_error = nested_errors.get(f"{index}.{field_key}")

            # Get field info from the model
            getattr(model_class.model_fields.get(field_key), "json_schema_extra", {}) or {}

            html.append(
                f"""
                        <div class=\"col-md-6\">
                            {renderer._render_field(
                                input_name,
                                field_schema,
                                field_value,
                                field_error,
                                required_fields,
                                context=nested_context,
                                all_errors=nested_errors,
                            )}
                        </div>"""
            )

        html.append("</div>")

        return "\n".join(html)

    def get_model_list_javascript(self) -> str:
        """Return JavaScript for model list functionality with collapsible card support."""
        return """
        <script>
        (function() {
            'use strict';

            // Ensure this runs after DOM is loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeModelLists);
            } else {
                initializeModelLists();
            }

            function initializeModelLists() {
                // Add item functionality
                const addButtons = document.querySelectorAll('.add-item-btn');
                addButtons.forEach(button => {
                    if (!button.hasAttribute('data-initialized')) {
                        button.setAttribute('data-initialized', 'true');
                        button.addEventListener('click', handleAddItem);
                    }
                });

                // Remove item functionality - use direct event listeners
                const removeButtons = document.querySelectorAll('.remove-item-btn');
                removeButtons.forEach(button => {
                    if (!button.hasAttribute('data-initialized')) {
                        button.setAttribute('data-initialized', 'true');
                        button.addEventListener('click', handleRemoveItem);
                    }
                });

                // Also set up delegation for dynamically added buttons
                document.addEventListener('click', function(e) {
                    const button = e.target.closest && e.target.closest('.remove-item-btn');
                    if (!button) return;

                    // Always handle delegated remove clicks.
                    // Newly-added items are cloned and may inherit `data-initialized`,
                    // which would otherwise prevent the fallback from running.
                    handleRemoveItem.call(button, e);
                });
            }

            function handleAddItem(e) {
                e.preventDefault();
                e.stopPropagation();

                const fieldName = this.dataset.target;
                const container = document.querySelector(
                    `.model-list-container[data-field-name="${fieldName}"], .model-list-block[data-field-name="${fieldName}"]`
                );
                if (!container) return;

                const itemsContainer = container.querySelector('.model-list-items');
                const maxItems = parseInt(container.dataset.maxItems || '10');
                const currentItems = itemsContainer.querySelectorAll('.model-list-item').length;

                if (currentItems >= maxItems) {
                    alert(`Maximum ${maxItems} items allowed.`);
                    return;
                }

                addNewListItem(fieldName, currentItems);
                updateItemIndices(itemsContainer);
            }

            function handleRemoveItem(e) {
                e.preventDefault();
                e.stopPropagation();

                // When called via event delegation, e.currentTarget is the document.
                // Always resolve the actual remove button from the click target.
                const button = (e.target && e.target.closest && e.target.closest('.remove-item-btn')) || e.currentTarget || this;
                const item = button.closest('.model-list-item');
                if (!item) return;

                const container = item.closest('.model-list-container');
                if (!container) return;

                const minItems = parseInt(container.dataset.minItems || '0');
                const itemsContainer = container.querySelector('.model-list-items');
                const currentItems = itemsContainer.querySelectorAll('.model-list-item').length;

                if (currentItems <= minItems) {
                    alert(`Minimum ${minItems} items required.`);
                    return;
                }

                // Check if item has data
                const hasData = Array.from(item.querySelectorAll('input, select, textarea')).some(input => {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        return input.checked;
                    }
                    return input.value && input.value.trim() !== '';
                });

                if (hasData) {
                    if (!confirm('Are you sure you want to remove this item? All data will be lost.')) {
                        return;
                    }
                }

                item.remove();
                updateItemIndices(itemsContainer);
            }

            // Update titles when input fields change
            document.addEventListener('input', function(e) {
                if (e.target.name && (e.target.name.includes('.name') || e.target.name.includes('.relationship'))) {
                    updateItemTitle(e.target);
                }
            });

            // Handle collapse icons
            document.addEventListener('click', function(e) {
                const collapseButton = e.target.closest('[data-bs-toggle="collapse"]');
                if (collapseButton) {
                    const icon = collapseButton.querySelector('.bi-chevron-down, .bi-chevron-right');
                    if (icon) {
                        setTimeout(() => {
                            const isExpanded = collapseButton.getAttribute('aria-expanded') === 'true';
                            icon.className = isExpanded ? 'bi bi-chevron-down me-2' : 'bi bi-chevron-right me-2';
                        }, 50);
                    }
                }
            });
        })();

        function addNewListItem(fieldName, index) {
            const container = document.querySelector(
                `.model-list-container[data-field-name="${fieldName}"], .model-list-block[data-field-name="${fieldName}"]`
            );
            const itemsContainer = container.querySelector('.model-list-items');

            // Prefer cloning an existing item (preserves any per-item chrome).
            // If the list is currently empty, fall back to a hidden <template>.
            let templateNode = itemsContainer.querySelector('.model-list-item');
            if (!templateNode) {
                const template = itemsContainer.querySelector('template.model-list-item-template');
                if (template && template.content && template.content.firstElementChild) {
                    templateNode = template.content.firstElementChild;
                }
            }

            if (templateNode) {
                const newItem = templateNode.cloneNode(true);

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
        """
