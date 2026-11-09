"""``progress=True``: how many required fields are filled in, as the user types.

Counted in the browser from what the form already renders: an input with the
``required`` attribute counts while it isn't disabled (a hidden ``show_when``
field is), a radio or checkbox group counts once, and ``model_list`` items count
as they are added. "Complete" means filled in, not valid; the server still
validates. A plain or grouped form gets one bar at the top. A wizard ticks each
step in its header instead, since the header is already its progress display.
Without JavaScript nothing shows: a count from the server would go stale.
"""

from __future__ import annotations

from .tstring import SafeHTML

PROGRESS_ATTRIBUTE = 'data-sf-progress'
# On a wizard's root: tick its header steps instead of showing a bar.
WIZARD_TICKS_CLASS = 'wizard-progress-ticks'

PROGRESS_BAR = SafeHTML(
    '<div class="sf-progress" data-sf-progress hidden>'
    '<div class="sf-progress__label"><span>Required fields</span>'
    '<span class="sf-progress__count" aria-live="polite"></span></div>'
    '<progress class="sf-progress__bar" value="0" max="1"'
    ' aria-label="Required fields complete"></progress></div>'
)

# Plain JavaScript in a Python string: a '#' comment would kill it.
PROGRESS_ASSETS = SafeHTML("""<script data-schemaforms-progress>
(function () {
    if (window.schemaformsProgress) { window.schemaformsProgress.refresh(); return; }

    function counted(scope) {
        var form = scope.closest('form') || scope;
        var names = {};
        var order = [];
        scope.querySelectorAll('input[required], select[required], textarea[required]')
            .forEach(function (control) {
                if (control.closest('template') || control.matches(':disabled')) { return; }
                if (control.type === 'hidden') { return; }
                var filled;
                if (control.type === 'checkbox' || control.type === 'radio') {
                    filled = Array.from(form.querySelectorAll('[name="' + CSS.escape(control.name) + '"]'))
                        .some(function (other) { return other.checked; });
                } else if (control.type === 'file') {
                    filled = control.files && control.files.length > 0;
                } else {
                    filled = control.value.trim() !== '';
                }
                var key = control.name || control.id;
                if (!(key in names)) { order.push(key); names[key] = true; }
                names[key] = names[key] && filled;
            });
        var done = order.filter(function (key) { return names[key]; }).length;
        return { done: done, total: order.length };
    }

    // Write only what changed: the observer below sees every write, even an
    // unchanged one, and would refresh again forever.
    function setHidden(el, value) { if (el.hidden !== value) { el.hidden = value; } }
    function setText(el, value) { if (el.textContent !== value) { el.textContent = value; } }

    function updateBar(bar) {
        var count = counted(bar.closest('form'));
        setHidden(bar, count.total === 0);
        var progress = bar.querySelector('progress');
        progress.max = Math.max(count.total, 1);
        progress.value = count.done;
        var text = count.done + ' of ' + count.total + ' complete';
        setText(bar.querySelector('.sf-progress__count'), text);
    }

    function updateTicks(root) {
        var active = parseInt(root.dataset.activeStep, 10) || 0;
        var passed = parseInt(root.dataset.sfPassed || '-1', 10);
        if (active - 1 > passed) { passed = active - 1; root.dataset.sfPassed = String(passed); }
        var items = Array.from(root.querySelectorAll('.wizard-progress-item'))
            .filter(function (item) { return item.closest('.form-wizard') === root; });
        items.forEach(function (item, index) {
            var step = root.querySelector('[data-wizard-step="' + index + '"]');
            if (!step || step.closest('.form-wizard') !== root) { return; }
            if (step.querySelector('[data-wizard-review]')) { return; }
            var count = counted(step);
            var done = count.total > 0 ? count.done === count.total : index <= passed;
            var number = item.querySelector('.wizard-progress-number');
            var said = item.querySelector('[data-step-done]');
            // The wizard renumbers the steps that apply (#327); fall back to position.
            var plain = item.dataset.stepNumber || String(index + 1);
            if (number) { setText(number, done ? '✓' : plain); }
            if (said) { setHidden(said, !done); }
        });
    }

    function refresh() {
        document.querySelectorAll('[data-sf-progress]').forEach(updateBar);
        document.querySelectorAll('.form-wizard.wizard-progress-ticks').forEach(updateTicks);
    }

    var queued = false;
    function soon() {
        if (queued) { return; }
        queued = true;
        window.requestAnimationFrame(function () { queued = false; refresh(); });
    }

    window.schemaformsProgress = { refresh: refresh };
    document.addEventListener('input', soon);
    document.addEventListener('change', soon);
    document.addEventListener('click', soon);
    if (window.MutationObserver) {
        new MutationObserver(soon).observe(document.documentElement, {
            subtree: true, childList: true, attributes: true,
            attributeFilter: ['disabled', 'hidden', 'data-active-step']
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', refresh);
    } else {
        refresh();
    }
})();
</script>
<style data-schemaforms-progress>
.sf-progress { margin: 0 0 1rem; }
.sf-progress__label {
    display: flex; justify-content: space-between; gap: 1rem;
    font-size: 0.875rem; margin-bottom: 0.25rem;
}
.sf-progress__bar {
    display: block; width: 100%; height: 0.5rem;
    accent-color: var(--sf-primary, #0d6efd);
}
</style>""")
