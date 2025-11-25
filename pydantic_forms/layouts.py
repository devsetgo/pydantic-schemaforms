"""Advanced layout system built on the shared BaseLayout abstraction."""

from html import escape
from typing import Any, Dict, List, Optional, Union

from .layout_base import BaseLayout


class HorizontalLayout(BaseLayout):
    """Horizontal layout using flexbox."""

    template = """<div class="horizontal-layout ${class_}" style="display: flex; flex-direction: row; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Union[str, List[str]] = "",
        gap: str = "1rem",
        align_items: str = "flex-start",
        justify_content: str = "flex-start",
        **kwargs,
    ):
        super().__init__(content, **kwargs)
        self.gap = gap
        self.align_items = align_items
        self.justify_content = justify_content

    def render(self, **kwargs) -> str:
        additional_styles = [
            f"gap: {self.gap}",
            f"align-items: {self.align_items}",
            f"justify-content: {self.justify_content}",
        ]

        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join([current_style] + additional_styles).strip("; ")

        return super().render(**kwargs)


class VerticalLayout(BaseLayout):
    """Vertical layout using flexbox."""

    template = """<div class="vertical-layout ${class_}" style="display: flex; flex-direction: column; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Union[str, List[str]] = "",
        gap: str = "1rem",
        align_items: str = "stretch",
        **kwargs,
    ):
        super().__init__(content, **kwargs)
        self.gap = gap
        self.align_items = align_items

    def render(self, **kwargs) -> str:
        additional_styles = [f"gap: {self.gap}", f"align-items: {self.align_items}"]

        current_style = kwargs.get("style", "")
        kwargs["style"] = "; ".join([current_style] + additional_styles).strip("; ")

        return super().render(**kwargs)


class GridLayout(BaseLayout):
    """CSS Grid layout for complex arrangements."""

    template = """<div class="grid-layout ${class_}" style="display: grid; grid-template-columns: ${columns}; ${style}">${content}</div>"""

    def __init__(
        self,
        content: Union[str, List[str]] = "",
        columns: str = "1fr 1fr",
        gap: str = "1rem",
        rows: Optional[str] = None,
        **kwargs,
    ):
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

    def __init__(
        self,
        content: Union[str, List[str]] = "",
        min_column_width: str = "300px",
        gap: str = "1rem",
        **kwargs,
    ):
        columns = f"repeat(auto-fit, minmax({min_column_width}, 1fr))"
        super().__init__(content, columns=columns, gap=gap, **kwargs)


class TabLayout(BaseLayout):
    """Tab layout with JavaScript interactivity."""

    template = """
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
    """

    def __init__(self, tabs: List[Dict[str, str]], **kwargs: Any) -> None:
        super().__init__(content="", **kwargs)
        self.tabs = tabs

    def render(self, **kwargs: Any) -> str:
        tab_ids = [f"tab-{i}" for i in range(len(self.tabs))]

        tab_buttons = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == 0
            active_class = " active" if is_active else ""
            aria_selected = "true" if is_active else "false"
            tab_buttons.append(
                f"""
            <button class="tab-button{active_class}"
                    type="button"
                    role="tab"
                    aria-selected="{aria_selected}"
                    aria-controls="{tab_id}"
                    onclick="switchTab('{tab_id}', this)">
                {escape(tab['title'])}
            </button>
            """
            )

        tab_panels = []
        for i, (tab_id, tab) in enumerate(zip(tab_ids, self.tabs, strict=False)):
            is_active = i == 0
            display_style = "block" if is_active else "none"
            aria_hidden = "false" if is_active else "true"
            active_class = " active" if is_active else ""
            tab_panels.append(
                f"""
            <div id="{tab_id}"
                 class="tab-panel{active_class}"
                 role="tabpanel"
                 style="display: {display_style};"
                 aria-hidden="{aria_hidden}">
                {tab['content']}
            </div>
            """
            )

        return super().render(
            tab_buttons="\n".join(tab_buttons),
            tab_panels="\n".join(tab_panels),
            **kwargs,
        )


class AccordionLayout(BaseLayout):
    """Accordion layout with collapsible sections."""

    template = """
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
    """

    def __init__(self, sections: List[Dict[str, str]], **kwargs: Any) -> None:
        super().__init__(content="", **kwargs)
        self.sections = sections

    def render(self, **kwargs: Any) -> str:
        section_ids = [f"accordion-{i}" for i in range(len(self.sections))]
        accordion_sections = []
        for _i, (section_id, section) in enumerate(zip(section_ids, self.sections, strict=False)):
            is_expanded = section.get("expanded", False)
            display_style = "block" if is_expanded else "none"
            aria_expanded = "true" if is_expanded else "false"
            expanded_class = " expanded" if is_expanded else ""
            accordion_sections.append(
                f"""
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
            """
            )

        return super().render(
            accordion_sections="\n".join(accordion_sections),
            **kwargs,
        )


class ModalLayout(BaseLayout):
    """Modal dialog layout."""

    template = """
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
    """

    def __init__(self, modal_id: str, title: str, content: str, footer: str = "", **kwargs: Any) -> None:
        default_footer = footer or f"<button onclick=\"closeModal('{modal_id}')\">Close</button>"
        super().__init__(content=content, modal_id=modal_id, title=escape(title), footer=default_footer, **kwargs)
        self.modal_id = modal_id
        self.title = title
        self.footer = default_footer

    def render(self, **kwargs: Any) -> str:
        return super().render(**kwargs)


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
