"""
Advanced layout system for pydantic-forms using Python 3.14 template strings.
Provides horizontal, vertical, grid, tab, and accordion layouts.
"""

from typing import List, Dict, Any, Optional, Union
# Python 3.14 template string support with fallback
try:
    from string.templatelib import Template, Interpolation
except ImportError:
    # Fallback for earlier Python versions
    from string import Template
    
    class Interpolation:
        def __init__(self, **kwargs):
            self.data = kwargs
        
        def __getattr__(self, name):
            return self.data.get(name, "")
        
        def __getitem__(self, key):
            return self.data.get(key, "")
        
        def __iter__(self):
            return iter(self.data)
        
        def keys(self):
            return self.data.keys()
        
        def values(self):
            return self.data.values()
        
        def items(self):
            return self.data.items()

from html import escape


class BaseLayout:
    """Base class for all layout components."""
    
    template: str = ""
    
    def __init__(self, content: Union[str, List[str]] = "", **kwargs):
        self.content = content if isinstance(content, str) else "\n".join(content)
        self.attributes = kwargs
        self.template_renderer = Template(self.template)
    
    def render(self, **kwargs) -> str:
        """Render the layout component."""
        # Merge instance attributes with render-time kwargs
        attrs = {**self.attributes, **kwargs}
        
        # Build CSS class string
        css_classes = []
        if "class_" in attrs:
            css_classes.append(attrs["class_"])
        if "css_class" in attrs:
            css_classes.append(attrs["css_class"])
        
        # Build style string
        styles = []
        if "style" in attrs:
            styles.append(attrs["style"])
        if "css_style" in attrs:
            styles.append(attrs["css_style"])
        
        try:
            interpolation = Interpolation(
                content=self.content,
                class_=" ".join(css_classes),
                style="; ".join(styles),
                **attrs
            )
            return self.template_renderer.substitute(interpolation.data)
        except Exception:
            # Fallback rendering
            return self._fallback_render(attrs)
    
    def _fallback_render(self, attrs: Dict[str, Any]) -> str:
        """Fallback rendering if template interpolation fails."""
        return f"<div>{self.content}</div>"


class HorizontalLayout(BaseLayout):
    """Horizontal layout using flexbox."""
    
    template = """<div class="horizontal-layout ${class_}" style="display: flex; flex-direction: row; ${style}">${content}</div>"""
    
    def __init__(self, content: Union[str, List[str]] = "", gap: str = "1rem", 
                 align_items: str = "flex-start", justify_content: str = "flex-start", **kwargs):
        super().__init__(content, **kwargs)
        self.gap = gap
        self.align_items = align_items
        self.justify_content = justify_content
    
    def render(self, **kwargs) -> str:
        additional_styles = [
            f"gap: {self.gap}",
            f"align-items: {self.align_items}",
            f"justify-content: {self.justify_content}"
        ]
        
        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join([current_style] + additional_styles).strip("; ")
        
        return super().render(**kwargs)


class VerticalLayout(BaseLayout):
    """Vertical layout using flexbox."""
    
    template = """<div class="vertical-layout ${class_}" style="display: flex; flex-direction: column; ${style}">${content}</div>"""
    
    def __init__(self, content: Union[str, List[str]] = "", gap: str = "1rem", 
                 align_items: str = "stretch", **kwargs):
        super().__init__(content, **kwargs)
        self.gap = gap
        self.align_items = align_items
    
    def render(self, **kwargs) -> str:
        additional_styles = [
            f"gap: {self.gap}",
            f"align-items: {self.align_items}"
        ]
        
        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join([current_style] + additional_styles).strip("; ")
        
        return super().render(**kwargs)


class GridLayout(BaseLayout):
    """CSS Grid layout for complex arrangements."""
    
    template = """<div class="grid-layout ${class_}" style="display: grid; grid-template-columns: ${columns}; ${style}">${content}</div>"""
    
    def __init__(self, content: Union[str, List[str]] = "", columns: str = "1fr 1fr", 
                 gap: str = "1rem", rows: Optional[str] = None, **kwargs):
        super().__init__(content, **kwargs)
        self.columns = columns
        self.gap = gap
        self.rows = rows
    
    def render(self, **kwargs) -> str:
        additional_styles = [f"gap: {self.gap}"]
        
        if self.rows:
            additional_styles.append(f"grid-template-rows: {self.rows}")
        
        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join([current_style] + additional_styles).strip("; ")
        kwargs["columns"] = self.columns
        
        return super().render(**kwargs)


class ResponsiveGridLayout(GridLayout):
    """Responsive grid that adapts to screen size."""
    
    def __init__(self, content: Union[str, List[str]] = "", min_column_width: str = "300px", 
                 gap: str = "1rem", **kwargs):
        columns = f"repeat(auto-fit, minmax({min_column_width}, 1fr))"
        super().__init__(content, columns=columns, gap=gap, **kwargs)


class TabLayout:
    """Tab layout with JavaScript interactivity."""
    
    template = Template("""
<div class="tab-layout ${class_}" style="${style}">
    <div class="tab-navigation" role="tablist">
        ${tab_buttons}
    </div>
    <div class="tab-content">
        ${tab_panels}
    </div>
</div>
<script>
function switchTab(tabId, buttonElement) {
    // Hide all tab panels
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
    
    // Show selected tab panel
    const selectedPanel = document.getElementById(tabId);
    if (selectedPanel) {
        selectedPanel.style.display = 'block';
        selectedPanel.setAttribute('aria-hidden', 'false');
    }
    
    // Mark button as active
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
    """)
    
    def __init__(self, tabs: List[Dict[str, str]], **kwargs):
        """
        Initialize tab layout.
        
        Args:
            tabs: List of dicts with 'title' and 'content' keys
        """
        self.tabs = tabs
        self.attributes = kwargs
    
    def render(self, **kwargs) -> str:
        """Render tab layout with navigation and panels."""
        # Generate unique IDs for tabs
        tab_ids = [f"tab-{i}" for i in range(len(self.tabs))]
        
        # Build tab buttons
        tab_buttons = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs)):
            is_active = i == 0  # First tab is active by default
            active_class = " active" if is_active else ""
            aria_selected = "true" if is_active else "false"
            
            button = f'''
            <button class="tab-button{active_class}" 
                    role="tab" 
                    aria-selected="{aria_selected}"
                    aria-controls="{tab_id}"
                    onclick="switchTab('{tab_id}', this)">
                {escape(tab['title'])}
            </button>
            '''
            tab_buttons.append(button)
        
        # Build tab panels
        tab_panels = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs)):
            is_active = i == 0
            display_style = "block" if is_active else "none"
            aria_hidden = "false" if is_active else "true"
            active_class = " active" if is_active else ""
            
            panel = f'''
            <div id="{tab_id}" 
                 class="tab-panel{active_class}"
                 role="tabpanel"
                 style="display: {display_style};"
                 aria-hidden="{aria_hidden}">
                {tab['content']}
            </div>
            '''
            tab_panels.append(panel)
        
        # Merge attributes
        attrs = {**self.attributes, **kwargs}
        css_classes = attrs.get("class_", "")
        styles = attrs.get("style", "")
        
        interpolation = Interpolation(
            class_=css_classes,
            style=styles,
            tab_buttons="\n".join(tab_buttons),
            tab_panels="\n".join(tab_panels)
        )
        
        return self.template.substitute(interpolation.data)


class AccordionLayout:
    """Accordion layout with collapsible sections."""
    
    template = Template("""
<div class="accordion-layout ${class_}" style="${style}">
    ${accordion_sections}
</div>
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
    """)
    
    def __init__(self, sections: List[Dict[str, str]], **kwargs):
        """
        Initialize accordion layout.
        
        Args:
            sections: List of dicts with 'title' and 'content' keys
        """
        self.sections = sections
        self.attributes = kwargs
    
    def render(self, **kwargs) -> str:
        """Render accordion layout with collapsible sections."""
        # Generate unique IDs for sections
        section_ids = [f"accordion-{i}" for i in range(len(self.sections))]
        
        # Build accordion sections
        accordion_sections = []
        for i, (section_id, section) in enumerate(zip(section_ids, self.sections)):
            is_expanded = section.get('expanded', False)
            display_style = "block" if is_expanded else "none"
            aria_expanded = "true" if is_expanded else "false"
            expanded_class = " expanded" if is_expanded else ""
            
            section_html = f'''
            <div class="accordion-section">
                <button class="accordion-header{expanded_class}"
                        aria-expanded="{aria_expanded}"
                        aria-controls="{section_id}"
                        onclick="toggleAccordion('{section_id}', this)">
                    {escape(section['title'])}
                </button>
                <div id="{section_id}" 
                     class="accordion-content"
                     style="display: {display_style};">
                    {section['content']}
                </div>
            </div>
            '''
            accordion_sections.append(section_html)
        
        # Merge attributes
        attrs = {**self.attributes, **kwargs}
        css_classes = attrs.get("class_", "")
        styles = attrs.get("style", "")
        
        interpolation = Interpolation(
            class_=css_classes,
            style=styles,
            accordion_sections="\n".join(accordion_sections)
        )
        
        return self.template.substitute(interpolation.data)


class ModalLayout:
    """Modal dialog layout."""
    
    template = Template("""
<div class="modal-overlay ${class_}" id="${modal_id}" style="display: none; ${style}">
    <div class="modal-dialog" role="dialog" aria-labelledby="${modal_id}-title">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="${modal_id}-title" class="modal-title">${title}</h2>
                <button class="modal-close" onclick="closeModal('${modal_id}')" aria-label="Close">×</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                ${footer}
            </div>
        </div>
    </div>
</div>
<script>
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        modal.focus();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close modal when clicking overlay
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal-overlay[style*="flex"]');
        if (openModal) {
            closeModal(openModal.id);
        }
    }
});
</script>
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
.modal-dialog {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    max-width: 90vw;
    max-height: 90vh;
    overflow: auto;
}
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e0e0e0;
}
.modal-title {
    margin: 0;
    font-size: 1.25rem;
}
.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
}
.modal-body {
    padding: 1rem;
}
.modal-footer {
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
    text-align: right;
}
</style>
    """)
    
    def __init__(self, modal_id: str, title: str, content: str, footer: str = "", **kwargs):
        self.modal_id = modal_id
        self.title = title
        self.content = content
        self.footer = footer or f'<button onclick="closeModal(\'{modal_id}\')">Close</button>'
        self.attributes = kwargs
    
    def render(self, **kwargs) -> str:
        """Render modal layout."""
        attrs = {**self.attributes, **kwargs}
        css_classes = attrs.get("class_", "")
        styles = attrs.get("style", "")
        
        interpolation = Interpolation(
            modal_id=self.modal_id,
            title=escape(self.title),
            content=self.content,
            footer=self.footer,
            class_=css_classes,
            style=styles
        )
        
        return self.template.substitute(interpolation.data)


class CardLayout(BaseLayout):
    """Card layout for grouped content."""
    
    template = """
<div class="card-layout ${class_}" style="${style}">
    <div class="card-header">
        <h3 class="card-title">${title}</h3>
    </div>
    <div class="card-body">
        ${content}
    </div>
    <div class="card-footer">
        ${footer}
    </div>
</div>
<style>
.card-layout {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}
.card-header {
    padding: 1rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
    border-radius: 8px 8px 0 0;
}
.card-title {
    margin: 0;
    font-size: 1.1rem;
}
.card-body {
    padding: 1rem;
}
.card-footer {
    padding: 1rem;
    background-color: #f8f9fa;
    border-top: 1px solid #e0e0e0;
    border-radius: 0 0 8px 8px;
}
</style>
    """
    
    def __init__(self, title: str, content: str, footer: str = "", **kwargs):
        super().__init__(content, **kwargs)
        self.title = title
        self.footer = footer
    
    def render(self, **kwargs) -> str:
        kwargs["title"] = escape(self.title)
        kwargs["footer"] = self.footer
        return super().render(**kwargs)


# Layout factory for easy creation
class LayoutFactory:
    """Factory for creating layout instances."""
    
    @staticmethod
    def horizontal(*content, **kwargs) -> HorizontalLayout:
        return HorizontalLayout(list(content), **kwargs)
    
    @staticmethod
    def vertical(*content, **kwargs) -> VerticalLayout:
        return VerticalLayout(list(content), **kwargs)
    
    @staticmethod
    def grid(*content, columns: str = "1fr 1fr", **kwargs) -> GridLayout:
        return GridLayout(list(content), columns=columns, **kwargs)
    
    @staticmethod
    def responsive_grid(*content, min_width: str = "300px", **kwargs) -> ResponsiveGridLayout:
        return ResponsiveGridLayout(list(content), min_column_width=min_width, **kwargs)
    
    @staticmethod
    def tabs(tabs: List[Dict[str, str]], **kwargs) -> TabLayout:
        return TabLayout(tabs, **kwargs)
    
    @staticmethod
    def accordion(sections: List[Dict[str, str]], **kwargs) -> AccordionLayout:
        return AccordionLayout(sections, **kwargs)
    
    @staticmethod
    def modal(modal_id: str, title: str, content: str, **kwargs) -> ModalLayout:
        return ModalLayout(modal_id, title, content, **kwargs)
    
    @staticmethod
    def card(title: str, content: str, **kwargs) -> CardLayout:
        return CardLayout(title, content, **kwargs)


# Convenience alias
Layout = LayoutFactory