"""Default CSS/JS snippets for layout-oriented components."""

TAB_COMPONENT_ASSETS = """
<script>
function switchTab(tabId, buttonElement) {
    const tabLayout = buttonElement.closest('.tab-layout');
    const panels = tabLayout.querySelectorAll('.tab-panel');
    const buttons = tabLayout.querySelectorAll('.tab-button');

    panels.forEach(panel => {
        panel.style.display = 'none';
        panel.setAttribute('aria-hidden', 'true');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
        button.setAttribute('aria-selected', 'false');
    });

    const selectedPanel = document.getElementById(tabId);
    if (selectedPanel) {
        selectedPanel.style.display = 'block';
        selectedPanel.setAttribute('aria-hidden', 'false');
    }

    buttonElement.classList.add('active');
    buttonElement.setAttribute('aria-selected', 'true');
}
</script>
<style>
.tab-layout .tab-navigation {
    border-bottom: 2px solid #e0e0e0;
    margin-bottom: 1rem;
}
.tab-layout .tab-button {
    background: none;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-right: 0.5rem;
}
.tab-layout .tab-button:hover {
    background-color: #f5f5f5;
}
.tab-layout .tab-button.active {
    border-bottom-color: #007bff;
    color: #007bff;
}
.tab-layout .tab-panel {
    display: none;
}
.tab-layout .tab-panel.active {
    display: block;
}
</style>
"""

ACCORDION_COMPONENT_ASSETS = """
<script>
function toggleAccordion(sectionId, buttonElement) {
    const content = document.getElementById(sectionId);
    const isExpanded = buttonElement.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        content.style.display = 'none';
        buttonElement.setAttribute('aria-expanded', 'false');
        buttonElement.classList.remove('expanded');
    } else {
        content.style.display = 'block';
        buttonElement.setAttribute('aria-expanded', 'true');
        buttonElement.classList.add('expanded');
    }
}
</script>
<style>
.accordion-layout .accordion-section {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-bottom: 0.5rem;
}
.accordion-layout .accordion-header {
    background: none;
    border: none;
    width: 100%;
    text-align: left;
    padding: 1rem;
    cursor: pointer;
    background-color: #f8f9fa;
    font-weight: 500;
}
.accordion-layout .accordion-header:hover {
    background-color: #e9ecef;
}
.accordion-layout .accordion-header.expanded {
    background-color: #007bff;
    color: white;
}
.accordion-layout .accordion-content {
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
}
</style>
"""
