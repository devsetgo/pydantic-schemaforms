"""``autosave=True`` and ``warn_unsaved=True``: keep what's typed, warn before leaving.

Both are browser-only and opt-in. ``autosave`` saves the form's values to
``localStorage`` as the user types and restores them after a reload, keyed by
the page's path and the model's name (and the step, in a ``save_steps``
wizard). A draft remembers a fingerprint of the values the page started with
and is restored only when the page starts with the same values again, so an
edit form keeps its unsaved edits, a record changed on the server meanwhile
drops the old draft, and a re-render after a failed submit keeps the server's
version. Drafts are cleared on submit and expire after 7 days. ``warn_unsaved``
asks before leaving a page whose values changed and weren't submitted.

Never saved: passwords, files, hidden inputs (CSRF, honeypot), the wizard's own
fields, and anything marked ``data-sf-no-autosave`` (the captcha's answer, and
fields with ``Field(ui_autosave=False)``).
"""

from __future__ import annotations

from typing import Any

from .tstring import SafeHTML, html

AUTOSAVE_ATTRIBUTE = 'data-sf-autosave'
WARN_ATTRIBUTE = 'data-sf-warn-unsaved'
NO_AUTOSAVE_ATTRIBUTE = 'data-sf-no-autosave'


def check_flag(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f'{name}= takes True or False, not {value!r}.')
    return value


# Sonar can't parse t-strings, so it would report both parameters as unused.
def draft_notice(alert_class: str, button_class: str) -> str:  # NOSONAR
    """The hidden "Draft restored · Discard" notice the script shows after restoring."""

    return str(
        html(
            t'<div class="{alert_class} sf-draft-notice" role="status" data-sf-draft-notice hidden>'
            t'<span>Your unsaved answers were restored.</span> '
            t'<button type="button" class="{button_class}" data-sf-draft-discard>Discard</button>'
            t'</div>'
        )
    )


# Plain JavaScript in a Python string: a '#' comment would kill it.
AUTOSAVE_ASSETS = SafeHTML("""<script data-schemaforms-autosave>
(function () {
    if (window.schemaformsAutosave) { window.schemaformsAutosave.initAll(); return; }
    var WEEK = 7 * 24 * 60 * 60 * 1000;
    var SKIPPED_TYPES = ['password', 'file', 'hidden', 'submit', 'button', 'reset', 'image'];

    function storage() {
        try { return window.localStorage; } catch (error) { return null; }
    }

    function fields(form) {
        return Array.from(form.elements).filter(function (control) {
            if (!control.name || control.name.indexOf('_sf_') === 0) { return false; }
            if (SKIPPED_TYPES.indexOf(control.type) !== -1) { return false; }
            if (control.closest('template') || control.closest('[data-sf-no-autosave]')) { return false; }
            return true;
        });
    }

    function snapshot(form) {
        var values = {};
        fields(form).forEach(function (control) {
            var list = values[control.name] || (values[control.name] = []);
            if (control.type === 'checkbox' || control.type === 'radio') {
                if (control.checked) { list.push(control.value); }
            } else if (control.multiple && control.options) {
                Array.from(control.selectedOptions).forEach(function (o) { list.push(o.value); });
            } else {
                list.push(control.value);
            }
        });
        return values;
    }

    function fingerprint(values) {
        var text = JSON.stringify(values);
        var hash = 5381;
        for (var i = 0; i < text.length; i++) { hash = ((hash * 33) + text.charCodeAt(i)) % 4294967296; }
        return String(hash) + ':' + text.length;
    }

    function keyFor(form) {
        var name = form.getAttribute('data-sf-autosave');
        var same = Array.from(document.querySelectorAll('form[data-sf-autosave]'))
            .filter(function (other) { return other.getAttribute('data-sf-autosave') === name; });
        var key = 'sf-draft:' + window.location.pathname + ':' + name;
        if (same.length > 1) { key += ':' + same.indexOf(form); }
        var step = form.querySelector('input[name="_sf_wizard_step"]');
        if (step) { key += ':step' + step.value; }
        return key;
    }

    // Lists first, so every saved item has inputs to fill. Extra items are
    // emptied before their remove button is clicked, so it doesn't ask.
    function matchLists(form, values) {
        form.querySelectorAll('.model-list-container[data-field-name], .model-list-block[data-field-name]')
            .forEach(function (container) {
                var name = container.getAttribute('data-field-name');
                var prefix = name + '[';
                var wanted = -1;
                Object.keys(values).forEach(function (key) {
                    if (key.indexOf(prefix) !== 0) { return; }
                    var index = parseInt(key.slice(prefix.length), 10);
                    if (index > wanted) { wanted = index; }
                });
                var items = function () {
                    return Array.from(container.querySelectorAll('.model-list-item'))
                        .filter(function (item) { return !item.closest('template'); });
                };
                var add = container.querySelector('.add-item-btn');
                var guard = 0;
                while (add && items().length < wanted + 1 && guard++ < 100) { add.click(); }
                while (items().length > wanted + 1 && guard++ < 200) {
                    var last = items()[items().length - 1];
                    last.querySelectorAll('input, select, textarea').forEach(function (c) {
                        if (c.type === 'checkbox' || c.type === 'radio') { c.checked = false; } else { c.value = ''; }
                    });
                    var remove = last.querySelector('.remove-item-btn');
                    if (!remove) { break; }
                    remove.click();
                }
            });
    }

    function restore(form, values) {
        matchLists(form, values);
        var seen = {};
        fields(form).forEach(function (control) {
            var saved = values[control.name];
            if (!saved) { return; }
            var before = control.type === 'checkbox' || control.type === 'radio' ? control.checked : control.value;
            if (control.type === 'checkbox' || control.type === 'radio') {
                control.checked = saved.indexOf(control.value) !== -1;
            } else if (control.multiple && control.options) {
                Array.from(control.options).forEach(function (o) { o.selected = saved.indexOf(o.value) !== -1; });
            } else {
                var position = seen[control.name] || 0;
                seen[control.name] = position + 1;
                if (position < saved.length) { control.value = saved[position]; }
            }
            var after = control.type === 'checkbox' || control.type === 'radio' ? control.checked : control.value;
            if (before !== after || control.multiple) {
                control.dispatchEvent(new Event('input', { bubbles: true }));
                control.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    function init(form) {
        if (form.dataset.sfAutosaveReady) { return; }
        form.dataset.sfAutosaveReady = 'true';
        var store = storage();
        var saving = form.hasAttribute('data-sf-autosave') && store;
        var warning = form.hasAttribute('data-sf-warn-unsaved');
        var initial = snapshot(form);
        var initialText = JSON.stringify(initial);
        var base = fingerprint(initial);
        var key = saving ? keyFor(form) : null;
        var submitted = false;

        if (saving) {
            var draft = null;
            try { draft = JSON.parse(store.getItem(key) || 'null'); } catch (error) { draft = null; }
            var fresh = draft && draft.base === base && Date.now() - draft.time < WEEK;
            if (fresh && JSON.stringify(draft.values) !== initialText) {
                restore(form, draft.values);
                var notice = form.querySelector('[data-sf-draft-notice]');
                if (notice) { notice.hidden = false; }
            } else if (draft && !fresh) {
                store.removeItem(key);
            }
        }

        var timer = null;
        function save() {
            timer = null;
            if (!saving || submitted) { return; }
            var values = snapshot(form);
            if (JSON.stringify(values) === initialText) { store.removeItem(key); return; }
            try {
                store.setItem(key, JSON.stringify({ base: base, time: Date.now(), values: values }));
            } catch (error) { saving = false; }
        }
        function soon() { if (timer) { clearTimeout(timer); } timer = setTimeout(save, 400); }
        form.addEventListener('input', soon);
        form.addEventListener('change', soon);

        var discard = form.querySelector('[data-sf-draft-discard]');
        if (discard) {
            discard.addEventListener('click', function () {
                if (saving) { store.removeItem(key); }
                submitted = true;
                window.location.reload();
            });
        }

        // After the form's own handlers and confirm=: only a submit that goes
        // ahead clears the draft.
        form.addEventListener('submit', function (event) {
            setTimeout(function () {
                if (event.defaultPrevented) { return; }
                submitted = true;
                if (timer) { clearTimeout(timer); timer = null; }
                if (saving) { store.removeItem(key); }
            }, 0);
        });

        if (warning) {
            window.addEventListener('beforeunload', function (event) {
                if (submitted || JSON.stringify(snapshot(form)) === initialText) { return; }
                event.preventDefault();
                event.returnValue = '';
            });
        }
    }

    window.schemaformsAutosave = {
        initAll: function () {
            document.querySelectorAll('form[data-sf-autosave], form[data-sf-warn-unsaved]').forEach(init);
        }
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.schemaformsAutosave.initAll);
    } else {
        window.schemaformsAutosave.initAll();
    }
})();
</script>""")
