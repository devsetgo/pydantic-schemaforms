"""Default CSS/JS snippets for layout-oriented components."""

TAB_COMPONENT_SCRIPT = """
<script>
function switchTab(tabId, buttonElement) {
    const tabLayout = buttonElement.closest('.tab-layout');
    const own = selector => Array.from(tabLayout.querySelectorAll(selector))
        .filter(el => el.closest('.tab-layout') === tabLayout);
    const panels = own('.tab-panel');
    const buttons = own('.tab-button');

    panels.forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
        panel.setAttribute('aria-hidden', 'true');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
        button.setAttribute('aria-selected', 'false');
    });

    const selectedPanel = panels.find(panel => panel.id === tabId);
    if (selectedPanel) {
        selectedPanel.style.display = 'block';
        selectedPanel.classList.add('active');
        selectedPanel.setAttribute('aria-hidden', 'false');
    }

    buttonElement.classList.add('active');
    buttonElement.setAttribute('aria-selected', 'true');
}
</script>
"""

TAB_COMPONENT_STYLE = """<style>
.tab-layout .tab-navigation {
    border-bottom: 2px solid var(--sf-outline-variant, #e0e0e0);
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
    background-color: var(--sf-surface-low, #f5f5f5);
}
.tab-layout .tab-button.active {
    border-bottom-color: var(--sf-primary, #007bff);
    color: var(--sf-primary, #007bff);
}
.tab-layout .tab-panel {
    display: none;
}
.tab-layout .tab-panel.active {
    display: block;
}
</style>
"""

TAB_COMPONENT_ASSETS = TAB_COMPONENT_SCRIPT + TAB_COMPONENT_STYLE

ACCORDION_COMPONENT_SCRIPT = """
<script>
function toggleAccordion(sectionId, buttonElement) {
    const content = Array.from(buttonElement.parentElement.children)
        .find(el => el.id === sectionId);
    if (!content) { return; }
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
"""

ACCORDION_COMPONENT_STYLE = """<style>
.accordion-layout .accordion-section {
    border: 1px solid var(--sf-outline-variant, #e0e0e0);
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
    background-color: var(--sf-surface-low, #f8f9fa);
    font-weight: 500;
}
.accordion-layout .accordion-header:hover {
    background-color: var(--sf-surface-low, #e9ecef);
}
.accordion-layout .accordion-header.expanded {
    background-color: var(--sf-primary, #007bff);
    color: var(--sf-on-primary, white);
}
.accordion-layout .accordion-content {
    padding: 1rem;
    border-top: 1px solid var(--sf-outline-variant, #e0e0e0);
}
</style>
"""

ACCORDION_COMPONENT_ASSETS = ACCORDION_COMPONENT_SCRIPT + ACCORDION_COMPONENT_STYLE

# Idempotent: every wizard on a page ships this snippet, but the functions are
# defined once and each `.form-wizard` is wired up once (data-wizard-ready).
# Without JavaScript the `wizard-enhanced` class never appears, so every step
# stays visible and the navigation stays hidden: the form still submits.
WIZARD_COMPONENT_ASSETS = """
<script>
(function () {
    if (window.schemaformsWizard) { window.schemaformsWizard.initAll(); return; }

    function own(root, selector) {
        return Array.from(root.querySelectorAll(selector))
            .filter(function (el) { return el.closest('.form-wizard') === root; });
    }

    function stepIsValid(step) {
        var fields = step.querySelectorAll('input, select, textarea');
        for (var i = 0; i < fields.length; i++) {
            var field = fields[i];
            if (field.disabled || field.closest('template')) { continue; }
            if (!field.checkValidity()) {
                var details = field.closest('details');
                if (details) { details.open = true; }
                field.reportValidity();
                return false;
            }
        }
        return true;
    }

    function init(root) {
        if (root.dataset.wizardReady) { return; }
        root.dataset.wizardReady = 'true';
        root.classList.add('wizard-enhanced');

        var steps = own(root, '[data-wizard-step]');
        var items = own(root, '[data-wizard-goto]');
        var back = own(root, '[data-wizard-back]')[0];
        var next = own(root, '[data-wizard-next]')[0];
        var form = root.closest('form');
        var submits = form ? Array.from(form.querySelectorAll('[type="submit"]'))
            .filter(function (b) { return !root.contains(b); }) : [];
        var linear = root.dataset.linear !== 'false';
        var last = steps.length - 1;
        var current = Math.min(Math.max(parseInt(root.dataset.activeStep, 10) || 0, 0), last);

        function show(index) {
            current = index;
            steps.forEach(function (step, i) {
                step.classList.toggle('active', i === index);
                step.setAttribute('aria-hidden', i === index ? 'false' : 'true');
            });
            items.forEach(function (item, i) {
                item.classList.toggle('active', i === index);
                item.classList.toggle('complete', i < index);
                if (i === index) { item.setAttribute('aria-current', 'step'); }
                else { item.removeAttribute('aria-current'); }
            });
            if (back) { back.style.display = index === 0 ? 'none' : ''; }
            if (next) { next.style.display = index === last ? 'none' : ''; }
            submits.forEach(function (b) { b.style.display = index === last ? '' : 'none'; });
            root.dataset.activeStep = String(index);
        }

        function goTo(target) {
            if (target === current || target < 0 || target > last) { return; }
            if (target > current && linear) {
                for (var i = current; i < target; i++) {
                    show(i);
                    if (!stepIsValid(steps[i])) { return; }
                }
            }
            show(target);
            var top = root.getBoundingClientRect().top;
            if (top < 0) { root.scrollIntoView({ block: 'start' }); }
        }

        if (back) { back.addEventListener('click', function () { goTo(current - 1); }); }
        if (next) { next.addEventListener('click', function () { goTo(current + 1); }); }
        items.forEach(function (item, i) {
            item.addEventListener('click', function () { goTo(i); });
        });
        // Before the last step, Enter in a field means "Next", never a
        // submission of half-filled steps (implicit submission, or a
        // submit button the page added itself).
        root.addEventListener('keydown', function (event) {
            var target = event.target;
            if (event.key !== 'Enter' || current === last || target.tagName !== 'INPUT') { return; }
            event.preventDefault();
            goTo(current + 1);
        });
        if (form) {
            form.addEventListener('submit', function (event) {
                // A submit button inside a step (e.g. DataTableLayout's "Load
                // CSV") is a deliberate action of that step; let it through.
                var submitter = event.submitter;
                if (submitter && root.contains(submitter)) { return; }
                if (current < last) { event.preventDefault(); goTo(current + 1); }
            });
        }
        show(current);
    }

    window.schemaformsWizard = {
        init: init,
        initAll: function () { document.querySelectorAll('.form-wizard').forEach(init); },
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.schemaformsWizard.initAll);
    } else {
        window.schemaformsWizard.initAll();
    }
})();
</script>
<style>
.form-wizard:not(.wizard-enhanced) .wizard-progress,
.form-wizard:not(.wizard-enhanced) .wizard-footer { display: none; }
.form-wizard.wizard-enhanced .wizard-step:not(.active) { display: none; }
.form-wizard .wizard-progress {
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    list-style: none; padding: 0; margin: 0 0 1.25rem;
}
.form-wizard .wizard-progress-item {
    display: flex; align-items: center; gap: 0.5rem;
    background: none; border: 1px solid var(--sf-outline, #ced4da); border-radius: 999px;
    padding: 0.35rem 0.9rem; color: inherit; cursor: pointer; font: inherit;
}
.form-wizard .wizard-progress-number {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.5rem; height: 1.5rem; border-radius: 50%;
    background: var(--sf-surface-low, #e9ecef); font-size: 0.8rem; font-weight: 600;
}
.form-wizard .wizard-progress-item.active { border-color: var(--sf-primary, #0d6efd); color: var(--sf-primary, #0d6efd); font-weight: 600; }
.form-wizard .wizard-progress-item.active .wizard-progress-number { background: var(--sf-primary, #0d6efd); color: var(--sf-on-primary, #fff); }
.form-wizard .wizard-progress-item.complete .wizard-progress-number { background: var(--sf-success, #198754); color: var(--sf-on-primary, #fff); }
.form-wizard .wizard-progress-item.has-error { border-color: var(--sf-error, #dc3545); }
.form-wizard .wizard-progress-item.has-error .wizard-progress-number { background: var(--sf-error, #dc3545); color: var(--sf-on-primary, #fff); }
.form-wizard .wizard-footer {
    display: flex; justify-content: space-between; gap: 0.5rem; margin: 1rem 0;
}
.form-wizard .wizard-footer [data-wizard-next] { margin-left: auto; }
</style>
"""

# Bootstrap supplies its own dark colors under data-bs-theme="dark"; this points
# the library's --sf-* tokens (widgets, tabs, accordion, wizard) at them.
BOOTSTRAP_DARK_TOKENS = """<style data-schemaforms-dark-tokens>
[data-bs-theme="dark"] {
    --sf-primary: var(--bs-primary-text-emphasis);
    --sf-on-primary: var(--bs-body-bg);
    --sf-outline: var(--bs-secondary-color);
    --sf-outline-variant: var(--bs-border-color);
    --sf-error: var(--bs-danger-text-emphasis);
    --sf-error-container: var(--bs-danger-bg-subtle);
    --sf-success: var(--bs-success-text-emphasis);
    --sf-surface: var(--bs-body-bg);
    --sf-surface-low: var(--bs-tertiary-bg);
    --sf-on-surface: var(--bs-body-color);
    --sf-on-surface-variant: var(--bs-body-color);
    --sf-chip-bg: var(--bs-primary-bg-subtle);
    --sf-chip-fg: var(--bs-primary-text-emphasis);
    --sf-star-filled: var(--bs-warning-text-emphasis);
    --sf-star-empty: var(--bs-secondary-color);
}
</style>"""
