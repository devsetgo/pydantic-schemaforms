#!/usr/bin/env python3
"""
Model List Handling for Pydantic Forms
======================================

Client-side glue (add/remove/collapse interactions) for the model_list
fields rendered by rendering.field_renderer.FieldRenderer. The actual
per-field HTML is produced by FieldRenderer._render_model_list_field /
render_model_list_from_schema, which resolves the item model from the
list[ItemModel] type annotation; this module only supplies the shared
JavaScript.
"""

from __future__ import annotations


class ModelListRenderer:
    """Provides the shared add/remove/collapse JavaScript for model_list fields."""

    def __init__(self, framework: str = 'bootstrap'):
        """Initialize the model list renderer.

        Args:
            framework: UI framework to use ("bootstrap" or "material")
        """
        self.framework = framework

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
