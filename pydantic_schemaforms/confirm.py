"""``confirm=``: ask before a form is submitted, in a native ``<dialog>``.

``render_form_html(..., confirm=True)``, or a dict of ``title``, ``message``,
``confirm_label`` and ``cancel_label``. The dialog opens when the form's own
submit button (or Enter) submits it. Buttons with a name, such as a
``save_steps`` wizard's Back and Next or a table's Load button, submit without
asking. Without JavaScript the form submits as it always did.
"""

from __future__ import annotations

from typing import Any

from .tstring import SafeHTML

CONFIRM_ATTRIBUTE = 'data-sf-confirm'
CONFIRM_DEFAULTS = {
    'title': 'Submit this form?',
    'message': '',
    'confirm_label': 'Submit',
    'cancel_label': 'Cancel',
}


def check_confirm(value: Any) -> dict[str, Any] | None:
    """The dialog's texts, or None when the form doesn't ask."""

    if value is None or value is False:
        return None
    if value is True:
        return dict(CONFIRM_DEFAULTS)
    if not isinstance(value, dict):
        raise ValueError(f'confirm= takes True or a dict, not {value!r}.')
    unknown = set(value) - set(CONFIRM_DEFAULTS)
    if unknown or not all(isinstance(text, str) for text in value.values()):
        raise ValueError(
            f'confirm= takes a dict of {sorted(CONFIRM_DEFAULTS)} with text values, not {value!r}.'
        )
    return {**CONFIRM_DEFAULTS, **value}


# One listener on the document, after the form's own (a wizard stops a submit
# before its last step first). Plain JavaScript: a '#' comment would kill it.
CONFIRM_ASSETS = SafeHTML("""<script data-schemaforms-confirm>
(function () {
    if (window.schemaformsConfirm) { return; }
    window.schemaformsConfirm = true;

    document.addEventListener('submit', function (event) {
        var form = event.target;
        var dialog = form.querySelector ? form.querySelector('dialog[data-sf-confirm]') : null;
        if (!dialog || event.defaultPrevented || typeof dialog.showModal !== 'function') { return; }
        var submitter = event.submitter;
        // A named button is a step of the form (Back, Next, Load), not its submit.
        if (submitter && submitter.name) { return; }
        if (form.dataset.sfConfirmed) { delete form.dataset.sfConfirmed; return; }
        event.preventDefault();
        dialog.sfSubmitter = submitter || null;
        dialog.showModal();
    });

    document.addEventListener('click', function (event) {
        var button = event.target.closest('[data-sf-confirm-ok], [data-sf-confirm-cancel]');
        var dialog = button ? button.closest('dialog[data-sf-confirm]') : null;
        if (!dialog) { return; }
        dialog.close();
        if (!button.hasAttribute('data-sf-confirm-ok')) { return; }
        var form = dialog.closest('form');
        form.dataset.sfConfirmed = 'true';
        if (form.requestSubmit) {
            form.requestSubmit(dialog.sfSubmitter || undefined);
        } else {
            form.submit();
        }
    });
})();
</script>
<style data-schemaforms-confirm>
dialog.sf-confirm {
    border: 1px solid var(--sf-outline-variant, #dee2e6); border-radius: 0.75rem;
    padding: 1.5rem; max-width: min(28rem, calc(100% - 2rem));
    background: var(--sf-surface, #ffffff); color: var(--sf-on-surface, #212529);
}
dialog.sf-confirm::backdrop { background: var(--sf-scrim, rgba(0, 0, 0, 0.45)); }
dialog.sf-confirm .sf-confirm__title { font-size: 1.25rem; margin: 0 0 0.75rem; }
dialog.sf-confirm .sf-confirm__message { margin: 0 0 1.25rem; }
dialog.sf-confirm .sf-confirm__actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
</style>""")
