(function () {
    'use strict';
    if (window.schemaformsMaterial) {
        return;
    }
    window.schemaformsMaterial = true;

    var REQUIRED_MESSAGE = 'This field is required';

    function isEmpty(input) {
        if (input.type === 'checkbox' || input.type === 'radio') {
            var group = input.form && input.name ? input.form.querySelectorAll('[name="' + CSS.escape(input.name) + '"]') : [input];
            return !Array.prototype.some.call(group, function (el) { return el.checked; });
        }
        return !String(input.value || '').trim();
    }

    function supportingFor(field) {
        var supporting = field.querySelector(':scope > .md-field__supporting');
        if (!supporting) {
            supporting = document.createElement('div');
            supporting.className = 'md-field__supporting';
            field.appendChild(supporting);
        }
        return supporting;
    }

    function setRequiredError(input, field, missing) {
        input.classList.toggle('error', missing);
        if (missing) {
            field.classList.add('md-field--error');
            var supporting = supportingFor(field);
            var message = supporting.querySelector('.md-error-text');
            if (!message) {
                message = document.createElement('div');
                message.className = 'md-error-text';
                message.dataset.mdRequired = 'true';
                supporting.appendChild(message);
            }
            message.textContent = REQUIRED_MESSAGE;
            return;
        }
        var added = field.querySelector('.md-error-text[data-md-required]');
        if (added) {
            added.remove();
            if (!field.querySelector('.md-error-text')) {
                field.classList.remove('md-field--error');
            }
        }
    }

    function checkForm(form) {
        var first = null;
        form.querySelectorAll('input[required], select[required], textarea[required]').forEach(function (input) {
            // A field in a hidden tab, wizard step or collapsed panel can't show
            // a message; server validation reports it and opens that group.
            var field = input.closest('.md-field');
            if (!field || input.getClientRects().length === 0) {
                return;
            }
            var missing = isEmpty(input);
            setRequiredError(input, field, missing);
            if (missing && !first) {
                first = input;
            }
        });
        return first;
    }

    function syncSlider(input) {
        var min = parseFloat(input.min) || 0;
        var max = input.max === '' ? 100 : parseFloat(input.max);
        var value = parseFloat(input.value) || 0;
        var progress = max > min ? ((value - min) / (max - min)) * 100 : 0;
        input.style.setProperty('--md-slider-progress', progress + '%');
    }

    function init() {
        document.querySelectorAll('form.md-form').forEach(function (form) {
            if (form.dataset.mdReady) {
                return;
            }
            form.dataset.mdReady = 'true';
            form.querySelectorAll('input[type="range"]').forEach(syncSlider);
            form.addEventListener('input', function (event) {
                if (event.target.type === 'range') {
                    syncSlider(event.target);
                }
            });
            form.addEventListener('submit', function (event) {
                var first = checkForm(form);
                if (first) {
                    event.preventDefault();
                    first.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    first.focus({ preventScroll: true });
                }
            });
            form.addEventListener('focusout', function (event) {
                var input = event.target;
                if (!input.hasAttribute || !input.hasAttribute('required')) {
                    return;
                }
                var field = input.closest('.md-field');
                if (field && input.getClientRects().length > 0) {
                    setRequiredError(input, field, isEmpty(input));
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
